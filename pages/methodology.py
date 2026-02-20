import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


from src.config import METRICS_CONFIG

st.set_page_config(page_title="EuSEI - Metodologia", layout="wide")

st.title("📖 Guia de Referência e Escalas")

# --- Subseção: Escala de Complexidade (1-10) ---
st.header("🔢 Escala de Intensidade (1 a 10)")
st.markdown("""
Para os critérios de **Complexidade Técnica**, **Esforço Manual** e **Incertezas**, 
utilize a tabela abaixo para calibrar seu voto:
""")

# Criando uma tabela de referência clara
escala_data = {
    "Nível": ["1 - 3 (Baixo)", "4 - 7 (Médio)", "8 - 10 (Alto)"],
    "Descrição": [
        "Tarefa trivial, conhecida ou com zero dependências externas.",
        "Requer pesquisa, envolve refatoração ou possui dependências moderadas.",
        "Alta criticidade, tecnologia nova ou requisitos muito vagos/bloqueados."
    ],
    "Exemplo": [
        "Alteração de label, ajuste de CSS, fix de bug simples.",
        "Criação de novo endpoint, integração com serviço interno estável.",
        "Mudança de arquitetura, integração com API externa sem documentação."
    ]
}
st.table(pd.DataFrame(escala_data))

st.divider()

# --- Subseção: Escala de Tempo (Horas) ---
st.header("⏱️ Escala de Tempo Estimado")
st.markdown(f"""
Diferente dos sliders, o tempo é inserido em horas brutas. No algoritmo, 
as horas são normalizadas em relação ao teto de capacidade da Sprint.
""")

with st.container(border=True):
    col_h1, col_h2 = st.columns([1, 2])
    # Puxamos o valor MAX_HOURS diretamente do seu arquivo de cálculo
    from src.calculator import MAX_HOURS
    
    col_h1.metric("Capacidade Máxima (Teto)", f"{MAX_HOURS}h")
    col_h2.info(f"""
    **Como estimar:** - Considere apenas o tempo de 'mão na massa'.
    - Se a tarefa exceder {MAX_HOURS}h, ela é considerada um **Épico** e deve ser decomposta.
    - O sistema aplica um teto automático (cap) para que horas excessivas não distorçam o índice.
    """)

# --- Renderização Dinâmica das Métricas (Separadas por Tipo) ---
st.divider()
    
st.set_page_config(page_title="EuSEI - Metodologia", layout="wide")

st.title("📖 Documentação da Metodologia EuSEI")

st.markdown("""
Esta página detalha como o índice de complexidade é calculado. O objetivo do **EuSEI** é 
transformar percepções subjetivas em um índice quantitativo e comparável.
""")

# --- 1. A Matemática do Cálculo ---
st.header("🧮 O Algoritmo")
st.markdown(f"""
O cálculo segue três etapas fundamentais:
1. **Normalização:** Todos os inputs (incluindo horas) são convertidos para uma escala de 0 a 10.
2. **Média Ponderada:** Aplica-se o peso definido para cada métrica.
3. **Escalonamento Não-Linear:** Aplicamos uma curva exponencial para penalizar a complexidade alta.
""")

# Exibição da Fórmula em LaTeX
st.latex(r"Score = (\sum_{i=1}^{n} \text{valor}_i \times \text{peso}_i)^{1.5}")

# --- 2. Distribuição de Pesos ---
st.subheader("⚖️ Pesos dos Critérios")
df_weights = pd.DataFrame([
    {"Critério": v["display_name"], "Peso": v["weight"]} 
    for k, v in METRICS_CONFIG.items()
])
fig = px.pie(df_weights, values='Peso', names='Critério', hole=.3, 
             title="Impacto de cada métrica no Score Final")
st.plotly_chart(fig, use_container_width=True)


# Filtramos as métricas para exibição organizada
sliders = {k: v for k, v in METRICS_CONFIG.items() if v["type"] == "slider"}
numbers = {k: v for k, v in METRICS_CONFIG.items() if v["type"] == "number"}

st.subheader("Critérios Qualitativos (Sliders)")
cols_s = st.columns(len(sliders))
for i, (key, info) in enumerate(sliders.items()):
    with cols_s[i]:
        st.markdown(f"**{info['display_name']} (Peso {info['weight']*100}%)**")
        st.caption(info["description"])
        st.write(info.get("how_to_estimate", "Use a escala 1-10."))

st.subheader("Critérios Quantitativos (Numérico)")
for key, info in numbers.items():
    st.markdown(f"**{info['display_name']} (Peso {info['weight']*100}%)**")
    st.write(info.get("how_to_estimate", "Baseado em horas reais."))

# --- 4. Curva de Complexidade Visual ---
st.header("📈 Por que a pontuação sobe tão rápido?")
st.markdown("""
Utilizamos uma curva de potência para que a diferença entre uma tarefa 'Fácil' e 'Média' 
seja visualmente menor do que a diferença entre 'Difícil' e 'Crítica'.
""")

x = np.linspace(0, 10, 100)
y = np.power(x, 1.5)
df_curve = pd.DataFrame({"Base (Média Ponderada)": x, "Resultado Final (EuSEI)": y})
fig_curve = px.line(df_curve, x="Base (Média Ponderada)", y="Resultado Final (EuSEI)")
st.plotly_chart(fig_curve, use_container_width=True)