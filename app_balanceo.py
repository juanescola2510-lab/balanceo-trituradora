import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- LÓGICA DE CÁLCULO ---
def calcular_balanceo(v0_amp, v0_fase, mp_masa, mp_fase, v1_amp, v1_fase):
    to_comp = lambda a, f: a * np.exp(1j * np.radians(f))
    
    V0 = to_comp(v0_amp, v0_fase)
    Mp = to_comp(mp_masa, mp_fase)
    V1 = to_comp(v1_amp, v1_fase)
    
    alpha = (V1 - V0) / Mp
    Mc = -V0 / alpha
    
    return {
        "mc_masa": np.abs(Mc),
        "mc_fase": np.degrees(np.angle(Mc)) % 360,
        "V0": V0,
        "V1": V1,
        "Mc": Mc
    }

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Balanceo Mono-Plano", page_icon="⚙️")
st.title("⚙️ Calculadora de Balanceo (1 Plano)")
st.markdown("Método de Coeficientes de Influencia")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Vibración Inicial")
    v0_amp = st.number_input("Amplitud Inicial (V0)", value=5.0, step=0.1)
    v0_fase = st.number_input("Fase Inicial (V0) °", value=30.0, step=1.0)

    st.subheader("2. Masa de Prueba")
    mp_masa = st.number_input("Masa de Prueba (Mp)", value=10.0, step=0.1)
    mp_fase = st.number_input("Ángulo Masa de Prueba °", value=0.0, step=1.0)

with col2:
    st.subheader("3. Vibración con Masa de Prueba")
    v1_amp = st.number_input("Amplitud Resultante (V1)", value=8.0, step=0.1)
    v1_fase = st.number_input("Fase Resultante (V1) °", value=120.0, step=1.0)

# Cálculo al vuelo
res = calcular_balanceo(v0_amp, v0_fase, mp_masa, mp_fase, v1_amp, v1_fase)

st.divider()

# --- RESULTADOS ---
st.header("🎯 Resultado de Corrección")
c1, c2 = st.columns(2)
c1.metric("Masa a colocar", f"{res['mc_masa']:.2f} unidades")
c2.metric("Ángulo de colocación", f"{res['mc_fase']:.2f} °")

# --- GRÁFICO DE FASORES ---
fig = go.Figure()

# Vector V0
fig.add_trace(go.Scatterpolar(r=[0, v0_amp], theta=[0, v0_fase], mode='lines+markers', name='V0 (Inicial)'))
# Vector V1
fig.add_trace(go.Scatterpolar(r=[0, v1_amp], theta=[0, v1_fase], mode='lines+markers', name='V1 (Con Masa Prueba)'))
# Vector Masa de Corrección (Escalado para visualización)
fig.add_trace(go.Scatterpolar(r=[0, res['mc_masa']], theta=[0, res['mc_fase']], 
                             mode='lines+markers', name='Mc (Masa Corrección)', line=dict(dash='dash', color='red')))

fig.update_layout(polar=dict(angularaxis=dict(direction="counterclockwise")), showlegend=True)
st.plotly_chart(fig, use_container_width=True)

st.info("Nota: El ángulo de la masa de corrección se mide desde la misma referencia que usaste para la masa de prueba.")
