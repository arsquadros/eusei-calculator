import streamlit as st
import numpy as np

from src.calculator import ComplexityCalculator
from src.config import METRICS_CONFIG

st.set_page_config(page_title="Complexity Engine v2", layout="wide") # Changed to wide for better layout

st.title("⚖️ Entity-user Synthetic Engineering Index (EuSEI)")

# 1. Metric Selection
available_labels = {v["display_name"]: k for k, v in METRICS_CONFIG.items()}
selected_labels = st.multiselect(
    "Selecione as métricas para o cálculo:",
    options=list(available_labels.keys()),
    default=list(available_labels.keys())
)

# 2. Dynamic Input Rendering
inputs = {}
with st.sidebar:
    st.header("⚙️ Parâmetros da Task")
    for label in selected_labels:
        key = available_labels[label]
        conf = METRICS_CONFIG[key]
        
        if conf["type"] == "number":
            inputs[key] = st.number_input(label, min_value=conf["min"], max_value=conf["max"], value=0.0)
        else:
            inputs[key] = st.slider(label, int(conf["min"]), int(conf["max"]), 5)

# 3. Calculation Logic
calc = ComplexityCalculator(weights=METRICS_CONFIG)
score, margin = calc.calculate_score(inputs)

# --- NEW: Fibonacci Classification Logic ---
def get_fibonacci_class(val):
    fib_sequence = [1, 2, 3, 5, 8, 13, 21, 34]
    labels = ["Trivial", "Muito Simples", "Simples", "Moderada", "Complexa", "Muito Complexa", "Épica", "Fora de Escala"]
    colors = ["#f0f2f6", "#d1e7dd", "#cfe2ff", "#fff3cd", "#ffe5d0", "#f8d7da", "#f5c2c7", "#842029"]
    
    for i, f_val in enumerate(fib_sequence):
        if val <= f_val:
            return labels[i], colors[i], fib_sequence[i]
    return labels[-1], colors[-1], fib_sequence[-1]

category, bg_color, fib = get_fibonacci_class(score)

# 4. Results Display
st.divider()

# Metric Cards
m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("Índice EuSEI", f"{score}")
m_col2.metric("Margem de Incerteza", f"± {margin}%")
m_col3.markdown(
    f"""<div style="background-color:{bg_color}; padding:10px; border-radius:10px; text-align:center;">
        <span style="color:black; font-weight:bold;">Classe: {category}</span>
    </div>""", 
    unsafe_allow_html=True
)

# Consistently formatted response
st.info("### 📝 Resumo da Estimativa")
lower_bound = round(score * (1 - margin/100), 2)
upper_bound = round(score * (1 + margin/100), 2)

st.markdown(f"""
O esforço calculado para esta tarefa, considerando as métricas selecionadas, é de:
**{score} (±{margin}%)**.

> **Intervalo de Confiança:** O índice real de complexidade está entre **{lower_bound}** e **{upper_bound}**.

### 🧩 Classificação Fibonacci
A tarefa foi classificada como **{category}**. No contexto de engenharia sintética, isso sugere que o esforço 
está alinhado com o valor de Fibonacci mais próximo superior ao score obtido **({fib})**.
""")