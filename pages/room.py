import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from google.cloud import firestore
from google.oauth2 import service_account
from typing import Tuple

# Mantendo suas importações de lógica de negócio
from src.calculator import ComplexityCalculator
from src.config import METRICS_CONFIG, DISCRETE_SCALE

st.set_page_config(page_title="EuSEI - Sala Virtual", layout="wide")

if "room_id" not in st.session_state or "user_name" not in st.session_state:
    st.warning("Por favor, faça login pela página inicial.")
    st.stop()

# Recupera o tipo de usuário (owner ou squad)
user_type = st.session_state.get("user_type", "squad")


def reorder_cols(df: pd.DataFrame, new_order: list):
    return df[new_order]


def rename_cols(df: pd.DataFrame, new_cols: list):
    return df.rename(columns={df.columns[i]: new_cols[i] for i in range(len(df.columns))})

def get_room_report(room_ref, report_type="Completo"):
    """
    Gera o relatório baseado na escolha do usuário.
    'Completo': Todos os votos de todos os usuários.
    'Médias por Tarefa': Apenas os resultados finais de cada task.
    """
    all_rows = []
    tasks = room_ref.collection("tasks").stream()
    
    for task in tasks:
        task_id = task.id
        task_data = task.to_dict()
        
        if report_type == "Completo":
            votes = task.reference.collection("votes").stream()
            for vote in votes:
                data = vote.to_dict()
                data['task_id'] = task_id
                data['voter_name'] = vote.id
                all_rows.append(data)
        else:
            # Puxa apenas o nó de 'results' definido no seu schema
            results = task_data.get("results", {})
            if results:
                row = {
                    'task_id': task_id,
                    'status': results.get('status'),
                    'total_average': results.get('averages', {}).get('total_average'),
                    **results.get('averages', {}) # Explode as médias individuais
                }
                all_rows.append(row)
    
    if not all_rows:
        return None
        
    df = pd.DataFrame(all_rows)
    return df.to_csv(index=False).encode('utf-8')

# --- Database & Schema Helpers ---

def get_db_client() -> firestore.Client:
    if "db" not in st.session_state:
        creds_info = st.secrets["firestore"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        st.session_state["db"] = firestore.Client(credentials=creds)
    return st.session_state["db"]

db = get_db_client()

# Definição das referências baseadas no novo Schema
room_id = st.session_state.get("room_id")
user_name = st.session_state.get("user_name")
task_id = st.session_state.get("current_task_id", "default_task") # ID único por tarefa

collection_name = f"{st.secrets['firestore']['collection_name']}-{st.secrets['firestore']['environment']}"

room_ref = db.collection(collection_name).document(room_id)
task_ref = room_ref.collection("tasks").document(task_id)
votes_ref = task_ref.collection("votes")

# --- Lógica de Persistência ---

def save_final_results(votes_dict: dict):
    """Calcula as médias e salva no campo 'results' da task."""
    calc = ComplexityCalculator(weights=METRICS_CONFIG)
    
    # 1. Calcular Médias por critério
    averages = {}
    for key in METRICS_CONFIG.keys():
        averages[key] = np.mean([v[key] for v in votes_dict.values()])
    
    # 2. Calcular Score Total
    total_score, margin = calc.calculate_score(averages)
    
    # 3. Salvar no Firestore seguindo o Schema
    task_ref.set({
        "results": {
            "status": "finished",
            "averages": {**averages, "total_average": total_score},
            "uncertainty_margin": margin
        }
    }, merge=True)

# --- UI Components ---

def get_fibonacci_class(val: float) -> Tuple[str, str, int]:
    fib_sequence = [1, 3, 5, 8, 13, 21, 34]
    labels = ["Trivial", "Simples", "Moderada", "Complexa", "Muito Complexa", "Épica", "Fora de Escala"]
    colors = ["#f0f2f6", "#cfe2ff", "#fff3cd", "#ffe5d0", "#f8d7da", "#f5c2c7", "#842029"]
    for i, f_val in enumerate(fib_sequence):
        if val <= f_val: return labels[i], colors[i], fib_sequence[i]
    return labels[-1], colors[-1], fib_sequence[-1]

# --- Bloco de Sincronização Global ---

def sync_room_state():
    """Busca o estado mais recente da sala no Firestore."""
    # 1. Puxa o ponteiro da tarefa atual
    room_doc = room_ref.get()
    room_info = room_doc.to_dict() if room_doc.exists else {}
    
    # 2. Atualiza o ID da tarefa na sessão
    st.session_state["current_task_id"] = room_info.get("current_task_id", "task_1")
    
    # 3. Força o Streamlit a processar a página com os novos dados
    # (Opcional: você pode disparar um toast para avisar que sincronizou)
    st.toast(f"Sincronizado: {st.session_state['current_task_id']}")

# --- Função de display avançado de resultados ---

def display_discussion_results(voted_users, score, margin):
    df_votes = pd.DataFrame.from_dict(voted_users, orient='index')
    
    # 1. Cálculo de Métricas de Discordância
    # 'Score Final' deve ser calculado para cada linha (usuário)
    calc = ComplexityCalculator(weights=METRICS_CONFIG)
    df_votes['Score Final'] = df_votes.apply(lambda r: calc.calculate_score(r.to_dict())[0], axis=1)

    std_dev = df_votes['Score Final'].std()
    max_score = df_votes['Score Final'].max()
    min_score = df_votes['Score Final'].min()
    range_gap = max_score - min_score

    # 2. Header de Consenso
    if range_gap > 8: # Exemplo: gap maior que um degrau grande da Fibonacci
        st.error(f"### 🚩 Alta Divergência ({range_gap:.1f} pontos)")
        st.markdown("_O time possui visões muito diferentes sobre esta tarefa._")
    elif range_gap <= 3:
        st.success("### ✅ Forte Consenso")
    else:
        st.warning("### ⚠️ Consenso Moderado")

    # 3. Painel de Extremos (Incentivo à Discussão)
    col_min, col_max = st.columns(2)
    
    user_min = df_votes['Score Final'].idxmin()
    user_max = df_votes['Score Final'].idxmax()

    with col_min:
        st.metric("Voto Mais Simples", f"{min_score:.1f}", f"Usuário: {user_min}", delta_color="normal")
        if range_gap > 8:
            st.caption(f"**Com divergência Alta.**")
        elif range_gap <= 3:
            st.caption(f"**Com divergência Baixa.**")
        else:
            st.caption(f"**Com divergência Média.**")

    with col_max:
        st.metric("Voto Mais Complexo", f"{max_score:.1f}", f"Usuário: {user_max}", delta_color="inverse")
        if range_gap > 8:
            st.caption(f"**Com divergência Alta.**")
        elif range_gap <= 3:
            st.caption(f"**Com divergência Baixa.**")
        else:
            st.caption(f"**Com divergência Média.**")

    st.divider()

    # 4. Gráfico de Dispersão por Critério (Onde está o conflito?)
    st.write("### 🔍 Scores por Critério")
    
    # Transformamos o DF para o formato longo (long format) para o Plotly
    df_long = df_votes.drop(columns=['Score Final', 'user_type']).reset_index().melt(id_vars='index')
    
    fig = px.box(
        df_long, 
        x="variable", 
        y="value", 
        points="all", 
        color="variable",
        labels={"variable": "Critério", "value": "Peso do Voto", "index": "Usuário"},
        title="Distribuição de Votos por Critério"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("💡 **Dica:** Se uma coluna estiver muito 'comprida', o time não concorda sobre aquele requisito específico.")

    df_votes = reorder_cols(df_votes, ["user_type", "hours", "manual_effort", "tech_complexity", "uncertainty", "Score Final"])
    df_votes = rename_cols(df_votes, ["Tipo de User", "Horas", "Esforço Manual", "Complexidade Técnica", "Incertezas", "Score Final"])

    # 5. Tabela Detalhada com Color Scale
    with st.expander("📋 Tabela Comparativa de Votos"):
        st.dataframe(
            df_votes.style.background_gradient(cmap='RdYlGn_r', subset=['Score Final']),
            use_container_width=True
        )

# --- Main Logic ---

room_info = room_ref.get().to_dict()
db_current_task_id = room_info.get("current_task_id", "task_1")

# Atualiza o session_state para que toda a UI aponte para a tarefa correta
st.session_state["current_task_id"] = db_current_task_id

# Referência da Task e Votos baseada no ID sincronizado
task_ref = room_ref.collection("tasks").document(db_current_task_id)
votes_ref = task_ref.collection("votes")

# --- Interface do Owner para mudar a Task ---

if user_type == "owner":
    with st.expander("🛠️ Painel de Controle do Owner"):
        new_task_name = st.text_input("Definir ID da Próxima Tarefa", value=db_current_task_id)
        if st.button("Atualizar Task para Todos"):
            if new_task_name != db_current_task_id:
                # Atualiza o ponteiro na sala. Isso disparará a mudança para todos.
                room_ref.update({"current_task_id": new_task_name})
                st.success(f"Tarefa alterada para {new_task_name}!")
                st.rerun()
else:
    st.info(f"📌 Tarefa Atual: **{db_current_task_id}**")

col_title, col_sync = st.columns([4, 1])

with col_title:
    st.title(f"⚖️ Sala: {room_id}")

with col_sync:
    # Este botão é a "âncora" de atualização da Squad
    if st.button("🔄 Sync", help="Clique para ver se o Owner mudou a tarefa ou liberou resultados"):
        sync_room_state()
        st.rerun()

# A partir daqui, todas as referências usam o ID que acabou de ser sincronizado
current_task = st.session_state.get("current_task_id", "task_1")
task_ref = room_ref.collection("tasks").document(current_task)

task_doc = task_ref.get()
task_data = task_doc.to_dict() if task_doc.exists else {"results": {"status": "voting"}}
current_status = task_data.get("results", {}).get("status", "voting")

# Sidebar para Votação
with st.sidebar:
    st.header(f"👤 {st.session_state['user_name']}")
    st.caption(f"Papel: {user_type.capitalize()}")
    
    current_inputs = {"user_type": user_type}
    for key, conf in METRICS_CONFIG.items():
        if conf["type"] == "number":
            current_inputs[key] = st.number_input(conf["display_name"], min_value=0.0, value=0.0)
        else:
            current_inputs[key] = st.select_slider(conf["display_name"], options=DISCRETE_SCALE, value=3)

    if st.button("🚀 Enviar Voto", disabled=(current_status == "finished")):
        votes_ref.document(user_name).set(current_inputs)
        st.success("Voto computado!")

# Área Principal: Resultados
st.divider()

all_votes_docs = list(votes_ref.stream())
voted_users = {doc.id: doc.to_dict() for doc in all_votes_docs}

if current_status == "voting":
    st.info(f"🗳️ Status: **Em votação** ({len(voted_users)} votos)")
    
    if user_type == "owner" and len(voted_users) > 0:
        if st.button("🔓 Encerrar e Gerar Resultados", type="primary"):
            save_final_results(voted_users)
            st.rerun()
else:
    # Exibir resultados persistidos no Firestore
    res = task_data["results"]
    averages = res["averages"]
    score = averages["total_average"]
    margin = res.get("uncertainty_margin", 0)
    
    category, bg_color, fib = get_fibonacci_class(score)

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Média EuSEI", f"{score:.2f}")
    m_col2.metric("Incerteza", f"± {margin}%")
    m_col3.markdown(f'<div style="background-color:{bg_color}; color:black; padding:10px; border-radius:10px; text-align:center;"><b>{category} ({fib})</b></div>', unsafe_allow_html=True)

    with st.expander("📊 Detalhamento Técnico"):
        st.write("### Médias por critério:")
        # Preparar dados (remover o score total para não poluir o gráfico de critérios)
        criteria_data = {k: v for k, v in averages.items() if k != 'total_average'}
        df_radar = pd.DataFrame(list(criteria_data.items()), columns=['Critério', 'Média'])
        # Criar colunas para o gráfico e o botão de download
        col_graph, col_download = st.columns([3, 1])

        with col_graph:
            # Gráfico de Barras Horizontais com Gradiente
            fig_criteria = px.bar(
                df_radar, 
                x='Média', 
                y='Critério', 
                orientation='h',
                color='Média',
                color_continuous_scale='GnBu',
                text='Média',
                labels={'Média': 'Peso Médio', 'Critério': ''}
            )
            fig_criteria.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_criteria.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig_criteria, use_container_width=True)

        with col_download:
            st.write("#### 📂 Exportar")
            
            # Opção de tipo de relatório
            report_kind = st.selectbox(
                "Tipo de Relatório",
                ["Completo", "Médias por Tarefa"],
                help="Completo: Votos individuais por pessoa. Médias: Apenas o resultado final de cada task."
            )
            
            csv_bytes = get_room_report(room_ref, report_type=report_kind)
            
            if csv_bytes:
                st.download_button(
                    label=f"Baixar CSV ({report_kind})",
                    data=csv_bytes,
                    file_name=f"relatorio_{report_kind.lower()}_{room_id}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # Aqui você pode chamar sua função display_advanced_results do código original
        display_discussion_results(voted_users, score, margin)

    if st.button("🆕 Iniciar Nova Task"):
        # Apenas limpa o ID da sessão para criar um novo documento em /tasks/
        st.session_state["current_task_id"] = f"task_{np.random.randint(1000, 9999)}"
        st.rerun()
        