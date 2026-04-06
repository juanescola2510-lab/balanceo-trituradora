import streamlit as st
import numpy as np

# --- LÓGICA DE BALANCEO ---
def calcular_balanceo_pro(v0_amp, v0_fase, mp_masa, mp_fase, v1_amp, v1_fase, sentido):
    # Ajuste de fase según sentido de giro
    # Si es Horario (CW), a veces los instrumentos miden en sentido opuesto al estándar matemático
    sentido_mult = 1 if sentido == "Antihorario (CCW)" else -1
    
    to_comp = lambda a, f: a * np.exp(1j * np.radians(f * sentido_mult))
    
    V0 = to_comp(v0_amp, v0_fase)
    Mp = to_comp(mp_masa, mp_fase)
    V1 = to_comp(v1_amp, v1_fase)
    
    alpha = (V1 - V0) / Mp
    Mc = -V0 / alpha
    
    # Extraer magnitud y fase, regresando a la convención del usuario
    masa_final = np.abs(Mc)
    fase_final = (np.degrees(np.angle(Mc)) * sentido_mult) % 360
    
    return masa_final, fase_final

# --- INTERFAZ ---
st.title("⚖️ Balanceo Industrial Configurable")

with st.sidebar:
    st.header("Configuración de Máquina")
    sentido = st.radio("Sentido de Rotación (visto desde el sensor):", 
                       ["Antihorario (CCW)", "Horario (CW)"])
    st.info("Nota: La fase se mide en el sentido de rotación seleccionado.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos Iniciales")
    v0_a = st.number_input("Amplitud V0", value=5.0)
    v0_f = st.number_input("Fase V0 °", value=30.0)
    st.subheader("Masa de Prueba")
    m_p = st.number_input("Peso Mp", value=10.0)
    a_p = st.number_input("Ángulo Mp °", value=0.0)

with col2:
    st.subheader("Datos con Masa de Prueba")
    v1_a = st.number_input("Amplitud V1", value=8.0)
    v1_f = st.number_input("Fase V1 °", value=120.0)

if st.button("CALCULAR"):
    masa, fase = calcular_balanceo_pro(v0_a, v0_f, m_p, a_p, v1_a, v1_f, sentido)
    
    st.success(f"### RESULTADO")
    st.metric("Masa de Corrección", f"{masa:.2f} unidades")
    st.metric("Ángulo a instalar", f"{fase:.2f} °")
    st.write(f"Instalar la masa a **{fase:.2f}°** en sentido **{sentido}** desde la marca de referencia.")
