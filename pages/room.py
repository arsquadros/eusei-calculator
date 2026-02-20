import streamlit as st

import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from google.cloud import firestore
from google.oauth2 import service_account

from typing import Dict, Any, Tuple

from src.calculator import ComplexityCalculator
from src.config import METRICS_CONFIG


st.set_page_config(page_title="EuSEI - Sala Virtual", layout="wide")


def display_advanced_results(voted_users, score, margin, category, bg_color):
    """
    Renderiza visualizações avançadas: métricas, gráficos de distribuição e outliers.
    """
    # 1. Preparação dos Dados
    # Criamos um DataFrame para facilitar a plotagem e cálculos estatísticos
    df_votes = pd.DataFrame.from_dict(voted_users, orient='index')
    
    # Calculamos o score individual para cada usuário (usando a mesma lógica do Calculator)
    calc = ComplexityCalculator(weights=METRICS_CONFIG)
    user_scores = {name: calc.calculate_score(votes)[0] for name, votes in voted_users.items()}
    df_votes['Final_Score'] = pd.Series(user_scores)
    
    # Identificação de Outliers (Afastados > 1.5 desvios padrão da média)
    mean_score = df_votes['Final_Score'].mean()
    std_score = df_votes['Final_Score'].std() if len(df_votes) > 1 else 0
    
    def is_outlier(val):
        if len(df_votes) <= 2: return False
        return abs(val - mean_score) > (1.5 * std_score)

    # 2. Gráfico de Distribuição (Plotly)
    st.markdown("### 📊 Distribuição de Esforço")
    fig = px.bar(
        df_votes.reset_index(),
        x='Final_Score',
        y='index',
        orientation='h',
        labels={'index': 'Integrante', 'Final_Score': 'Índice EuSEI'},
        color='Final_Score',
        color_continuous_scale='Blues'
    )
    # Linha vertical indicando a média
    fig.add_vline(x=score, line_dash="dash", line_color="red", annotation_text="Média do Time")
    st.plotly_chart(fig, use_container_width=True)

    # 3. Seções Omitíveis (Expanders)
    with st.expander("📋 Detalhamento dos Votos e Outliers"):
        cols = st.columns(2)
        
        for i, (name, row) in enumerate(df_votes.iterrows()):
            target_col = cols[i % 2]
            outlier_alert = "⚠️ **Outlier**" if is_outlier(row['Final_Score']) else ""
            
            with target_col:
                st.markdown(f"""
                **{name}** {outlier_alert}
                - Score: `{row['Final_Score']:.2f}`
                """)
                # Barra de progresso visual para cada usuário
                st.progress(min(row['Final_Score'] / 34.0, 1.0)) # Normalizado pela escala Fibonacci
                
    with st.expander("🔍 Analisar Métricas por Critério"):
        # Mostra a média de cada métrica individual (Complexidade, Incerteza, etc.)
        metric_averages = df_votes.drop(columns=['Final_Score']).mean()
        st.dataframe(metric_averages.rename("Média do Critério"), use_container_width=True)

# --- Database Connection ---
def get_db_client() -> firestore.Client:
    """Inicializa o cliente Firestore usando secrets do Streamlit."""
    if "db" not in st.session_state:
        creds_info = st.secrets["firestore"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        st.session_state["db"] = firestore.Client(credentials=creds)
    return st.session_state["db"]

db = get_db_client()

# --- Helper Functions ---
def get_fibonacci_class(val: float) -> Tuple[str, str, int]:
    """Retorna categoria, cor e valor Fibonacci correspondente ao score."""
    fib_sequence = [1, 2, 3, 5, 8, 13, 21, 34]
    labels = ["Trivial", "Muito Simples", "Simples", "Moderada", "Complexa", "Muito Complexa", "Épica", "Fora de Escala"]
    colors = ["#f0f2f6", "#d1e7dd", "#cfe2ff", "#fff3cd", "#ffe5d0", "#f8d7da", "#f5c2c7", "#842029"]
    
    for i, f_val in enumerate(fib_sequence):
        if val <= f_val:
            return labels[i], colors[i], fib_sequence[i]
    return labels[-1], colors[-1], fib_sequence[-1]

# --- Room Validation ---
if "room_id" not in st.session_state:
    st.warning("⚠️ ID da sala não encontrado. Voltando para o início...")
    st.button("Ir para Home", on_click=lambda: st.switch_page("main.py"))
    st.stop()

room_id = st.session_state["room_id"]
user_name = st.session_state["user_name"]

# Firestore Refs
room_ref = db.collection("rooms").document(room_id)
votes_ref = room_ref.collection("votes")

# --- UI Header ---
st.title(f"⚖️ Sala: {room_id}")
st.caption(f"Logado como: **{user_name}**")

# Sync Room State
room_doc = room_ref.get()
room_data = room_doc.to_dict() if room_doc.exists else {"status": "voting", "task_title": ""}

# Task Title Management (Apenas o primeiro ou admin muda, aqui simplificado para todos)
new_task_title = st.text_input("📌 Nome da Task / User Story", 
                               value=room_data.get("task_title", ""),
                               placeholder="Ex: Integração de API de Pagamentos")

if new_task_title != room_data.get("task_title"):
    room_ref.set({"task_title": new_task_title, "status": room_data.get("status")}, merge=True)

# --- Sidebar: User Inputs (Visual do v1) ---
with st.sidebar:
    st.header("⚙️ Seus Parâmetros")
    current_inputs = {}
    for key, conf in METRICS_CONFIG.items():
        # Capturamos a descrição para usar como ajuda contextual
        help_text = conf.get("description", "Sem descrição disponível.")
        
        if conf["type"] == "number":
            current_inputs[key] = st.number_input(
                conf["display_name"], 
                min_value=conf["min"], 
                max_value=conf["max"], 
                value=0.0,
                help=help_text  # Adiciona o ícone de "info"
            )
        else:
            current_inputs[key] = st.slider(
                conf["display_name"], 
                int(conf["min"]), 
                int(conf["max"]), 
                5,
                help=help_text  # Adiciona o ícone de "info"
            )

    if st.button("🚀 Enviar/Atualizar Voto", use_container_width=True):
        votes_ref.document(user_name).set(current_inputs)
        st.success("Voto enviado!")

# --- Main Logic: Reveal Mechanism ---
st.divider()

@st.fragment(run_every=5)  # Atualiza a cada 5 segundos
def auto_refresh_votes(votes_ref, room_ref):
    """
    Atualiza apenas a contagem de votos e o status da sala 
    sem interferir nos sliders ou campos de texto do usuário.
    """
    all_votes = list(votes_ref.stream())
    room_data = room_ref.get().to_dict()
    
    col_status, col_refresh = st.columns([4, 1])
    
    with col_status:
        if room_data.get("status") == "voting":
            st.info(f"🗳️ **Status: Em votação.** {len(all_votes)} votos computados.")
        else:
            st.success("✅ Resultados revelados!")
            
    with col_refresh:
        if st.button("🔄 Sync", help="Forçar atualização manual"):
            st.rerun()
            
    return all_votes, room_data

# --- No corpo principal do app ---

# Substitua a lógica de exibição de status por:
voted_docs, current_room_data = auto_refresh_votes(votes_ref, room_ref)

all_votes_docs = list(votes_ref.stream())
voted_users = {doc.id: doc.to_dict() for doc in all_votes_docs}

if room_data.get("status") == "voting":
    if st.button("🔓 Revelar Resultados para o Time", type="primary"):
        room_ref.update({"status": "revealed"})
        st.rerun()
else:
    # --- Results Display (O melhor do v1 com dados do v2) ---
    if voted_users:
        # 1. Calcular médias
        avg_inputs = {k: np.mean([v[k] for v in voted_users.values()]) for k in METRICS_CONFIG.keys()}
        
        calc = ComplexityCalculator(weights=METRICS_CONFIG)
        score, margin = calc.calculate_score(avg_inputs)
        category, bg_color, fib = get_fibonacci_class(score)
        
        # 2. Visualização de Métricas
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Índice Médio EuSEI", f"{score}")
        m_col2.metric("Incerteza do Time", f"± {margin}%")
        m_col3.markdown(
            f"""<div style="background-color:{bg_color}; padding:10px; border-radius:10px; text-align:center;">
                <span style="color:black; font-weight:bold;">Classe: {category}</span>
            </div>""", 
            unsafe_allow_html=True
        )

        # 3. Resumo Detalhado
        lower_bound = round(score * (1 - margin/100), 2)
        upper_bound = round(score * (1 + margin/100), 2)

        st.markdown(f"""
        ### 🧩 Classificação Fibonacci
        A tarefa foi classificada como **{category} ({fib} Story Points)**.
        
        > **Intervalo de Confiança Coletivo:** O índice real está entre **{lower_bound}** e **{upper_bound}**.
        """)

        # 4. Detalhamento de Membros (Expander do v2)
        with st.expander("📋 Ver votos individuais"):
            display_advanced_results(voted_users, score, margin, category, bg_color)
            #for name, user_votes in voted_users.items():
            #    st.write(f"**{name}:** {user_votes}")

    if st.button("🔒 Resetar Sala para Nova Task"):
        for doc in all_votes_docs:
            doc.reference.delete()
        room_ref.update({"status": "voting", "task_title": ""})
        st.rerun()
