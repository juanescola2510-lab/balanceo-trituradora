import streamlit as st
import numpy as np
import plotly.graph_objects as go

def calcular_y_graficar():
    st.title("⚖️ Balanceo Industrial con Gráfico Polar")

    # --- CONFIGURACIÓN EN BARRA LATERAL ---
    with st.sidebar:
        sentido = st.radio("Sentido de Rotación:", ["Antihorario (CCW)", "Horario (CW)"])
        # Ajuste matemático: CCW es positivo en math, CW es negativo
        s_mult = 1 if sentido == "Antihorario (CCW)" else -1

    # --- ENTRADA DE DATOS ---
    c1, c2 = st.columns(2)
    with c1:
        v0_amp = st.number_input("Amp Inicial (V0)", value=5.0)
        v0_fase = st.number_input("Fase Inicial °", value=30.0)
        mp_masa = st.number_input("Masa Prueba", value=10.0)
        mp_fase = st.number_input("Ángulo Prueba °", value=0.0)
    with c2:
        v1_amp = st.number_input("Amp con Prueba (V1)", value=8.0)
        v1_fase = st.number_input("Fase con Prueba °", value=120.0)

    # --- CÁLCULOS ---
    to_c = lambda a, f: a * np.exp(1j * np.radians(f * s_mult))
    
    V0 = to_c(v0_amp, v0_fase)
    Mp = to_c(mp_masa, mp_fase)
    V1 = to_c(v1_amp, v1_fase)
    
    alpha = (V1 - V0) / Mp
    Mc = -V0 / alpha
    
    masa_final = np.abs(Mc)
    fase_final = (np.degrees(np.angle(Mc)) * s_mult) % 360

    # --- RESULTADOS ---
    st.divider()
    res1, res2 = st.columns(2)
    res1.metric("Masa de Corrección", f"{masa_final:.2f}")
    res2.metric("Ángulo de Instalación", f"{fase_final:.2f} °")

    # --- GRÁFICO POLAR ---
    fig = go.Figure()

    # Configuración de dirección del gráfico
    dir_polar = "counterclockwise" if sentido == "Antihorario (CCW)" else "clockwise"

    # Vector V0
    fig.add_trace(go.Scatterpolar(r=[0, v0_amp], theta=[0, v0_fase], 
                                 mode='lines+markers', name='V0 (Inicial)', line=dict(color='blue')))
    # Vector V1
    fig.add_trace(go.Scatterpolar(r=[0, v1_amp], theta=[0, v1_fase], 
                                 mode='lines+markers', name='V1 (Con Masa)', line=dict(color='green')))
    # Vector Masa de Corrección (Normalizado para ver dirección)
    fig.add_trace(go.Scatterpolar(r=[0, masa_final], theta=[0, fase_final], 
                                 mode='lines+markers', name='Mc (Masa Corr)', line=dict(color='red', width=4)))

    fig.update_layout(
        polar=dict(
            angularaxis=dict(direction=dir_polar, rotation=90), # 90 pone el 0 arriba o ajusta según tu sensor
        ),
        showlegend=True,
        title="Mapa de Vectores de Balanceo"
    )

    st.plotly_chart(fig, use_container_width=True)

calcular_y_graficar()
