import streamlit as st
import numpy as np
import plotly.graph_objects as go

def resolver_4_corridas(v0, v1, v2, v3, mp_masa):
    # v0: inicial
    # v1: masa a 0°
    # v2: masa a 120°
    # v3: masa a 240°
    
    # Coordenadas de los centros de los círculos (posiciones de la masa de prueba)
    # Usamos cos y sin para ubicar los vectores unitarios a 0, 120 y 240
    x = np.array([1, np.cos(np.radians(120)), np.cos(np.radians(240))])
    y = np.array([0, np.sin(np.radians(120)), np.sin(np.radians(240))])
    
    # Magnitudes al cuadrado para el sistema lineal
    # La ecuación es: (x-xi)^2 + (y-yi)^2 = r_i^2
    # Donde r_i es la amplitud medida en cada posición
    b = np.array([
        v1**2 - v0**2 - 1,
        v2**2 - v0**2 - 1,
        v3**2 - v0**2 - 1
    ])
    
    # Simplificación geométrica para hallar el vector de desbalance (U)
    # U_x = (v1^2 - v2^2) / (3 * v0) ... simplificado:
    ux = (2*v1**2 - v2**2 - v3**2) / (6 * v0)
    uy = (v2**2 - v3**2) / (2 * np.sqrt(3) * v0)
    
    angulo_desbalance = np.degrees(np.arctan2(uy, ux)) % 360
    # La masa de corrección debe ir opuesta al punto pesado (180°)
    angulo_correccion = (angulo_desbalance + 180) % 360
    
    # Sensibilidad (Magnitud de la masa de corrección)
    # Relación aproximada entre el cambio de vibración y la masa
    # Una forma común es usar el promedio de los cambios
    cambio_avg = (np.abs(v1-v0) + np.abs(v2-v0) + np.abs(v3-v0)) / 3
    if cambio_avg == 0: return 0, 0
    
    mc_masa = (v0 / cambio_avg) * mp_masa
    
    return mc_masa, angulo_correccion

# --- INTERFAZ STREAMLIT ---
st.title("🎯 Balanceo: Método de las 4 Corridas")
st.subheader("Sin sensor de fase (Solo Amplitud)")

with st.sidebar:
    st.info("""
    **Instrucciones:**
    1. Mida vibración original (V0).
    2. Coloque masa de prueba en 0° y mida (V1).
    3. Mueva la MISMA masa a 120° y mida (V2).
    4. Mueva la MISMA masa a 240° y mida (V3).
    """)

col1, col2 = st.columns(2)

with col1:
    v0 = st.number_input("Vibración Inicial (V0)", value=5.0)
    mp_masa = st.number_input("Valor Masa de Prueba", value=10.0)
    v1 = st.number_input("Vibración con Masa a 0° (V1)", value=6.2)

with col2:
    v2 = st.number_input("Vibración con Masa a 120° (V2)", value=4.1)
    v3 = st.number_input("Vibración con Masa a 240° (V3)", value=7.5)

if st.button("CALCULAR CORRECCIÓN"):
    m_corr, a_corr = resolver_4_corridas(v0, v1, v2, v3, mp_masa)
    
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Masa de Corrección", f"{m_corr:.2f}")
    c2.metric("Ángulo de Instalación", f"{a_corr:.2f} °")

    # --- GRÁFICO DE APOYO ---
    fig = go.Figure()
    # Puntos de prueba
    fig.add_trace(go.Scatterpolar(r=[v1, v2, v3], theta=[0, 120, 240], 
                                 mode='markers', name='Mediciones', marker=dict(size=12, color='blue')))
    # Vector de corrección
    fig.add_trace(go.Scatterpolar(r=[0, m_corr], theta=[0, a_corr], 
                                 mode='lines+markers', name='Masa Corrección', line=dict(color='red', width=4)))
    
    fig.update_layout(polar=dict(angularaxis=dict(direction="counterclockwise", rotation=90)))
    st.plotly_chart(fig)
