import streamlit as st
import numpy as np
import plotly.graph_objects as go

def resolver_4_corridas_flexible(v0, v_list, ang_list, mp_masa):
    # v0: Amplitud inicial
    # v_list: Lista de amplitudes con masa de prueba [v1, v2, v3]
    # ang_list: Lista de ángulos de las masas [a1, a2, a3] (en grados)
    
    # Convertir a radianes
    rads = np.radians(ang_list)
    
    # Creamos un sistema para hallar las componentes del desbalance original (Ux, Uy)
    # Ecuación: Vi^2 = V0^2 + (S*mp)^2 + 2*V0*S*mp*cos(phi - theta_i)
    # Donde S es la sensibilidad y phi la fase del desbalance.
    
    # Para simplificar y dar una respuesta robusta, usamos una aproximación 
    # de mínimos cuadrados sobre las componentes vectoriales:
    A = []
    B = []
    for i in range(len(v_list)):
        A.append([np.cos(rads[i]), np.sin(rads[i])])
        # El cambio en la energía de vibración (aproximado)
        B.append((v_list[i]**2 - v0**2))
    
    A = np.array(A)
    B = np.array(B)
    
    # Resolvemos para las componentes del vector de influencia
    try:
        res, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
        ux, uy = res
        
        # Ángulo del punto pesado
        angulo_desbalance = np.degrees(np.arctan2(uy, ux)) % 360
        # Ángulo de corrección (opuesto)
        angulo_correccion = (angulo_desbalance + 180) % 360
        
        # Cálculo de masa de corrección basado en el promedio de sensibilidad
        sensibilidades = []
        for i in range(len(v_list)):
            cambio = np.abs(v_list[i] - v0)
            if cambio > 0:
                sensibilidades.append(cambio / mp_masa)
        
        s_media = np.mean(sensibilidades) if sensibilidades else 1
        m_corr = v0 / s_media
        
        return m_corr, angulo_correccion
    except:
        return 0, 0

# --- INTERFAZ STREAMLIT ---
st.title("🎯 Balanceo de 4 Corridas (Ángulos Flexibles)")
st.markdown("Ideal cuando no puedes usar posiciones fijas de 120°.")

col0_1, col0_2 = st.columns(2)
v0 = col0_1.number_input("Vibración Inicial (V0)", value=5.0)
mp_masa = col0_2.number_input("Masa de Prueba", value=10.0)

st.divider()
st.subheader("Mediciones con Masa de Prueba")

c1, c2, c3 = st.columns(3)

with c1:
    st.info("Corrida 1")
    v1 = st.number_input("Amplitud V1", value=6.2, key="v1")
    a1 = st.number_input("Ángulo Posición 1°", value=0.0, key="a1")

with c2:
    st.info("Corrida 2")
    v2 = st.number_input("Amplitud V2", value=4.5, key="v2")
    a2 = st.number_input("Ángulo Posición 2°", value=90.0, key="a2")

with c3:
    st.info("Corrida 3")
    v3 = st.number_input("Amplitud V3", value=7.8, key="v3")
    a3 = st.number_input("Ángulo Posición 3°", value=180.0, key="a3")

if st.button("CALCULAR SOLUCIÓN"):
    v_vals = [v1, v2, v3]
    a_vals = [a1, a2, a3]
    
    m_res, a_res = resolver_4_corridas_flexible(v0, v_vals, a_vals, mp_masa)
    
    st.success("### Resultado Sugerido")
    res_c1, res_c2 = st.columns(2)
    res_c1.metric("Masa de Corrección", f"{m_res:.2f}")
    res_c2.metric("Ángulo de Instalación", f"{a_res:.2f} °")

    # Gráfico Polar
    fig = go.Figure()
    # Puntos de medición (donde se puso la masa)
    fig.add_trace(go.Scatterpolar(r=v_vals, theta=a_vals, mode='markers+text', 
                                 text=["V1", "V2", "V3"], name='Mediciones'))
    # Vector de corrección
    fig.add_trace(go.Scatterpolar(r=[0, v0], theta=[0, a_res], 
                                 mode='lines+markers', name='Vector Corrección', 
                                 line=dict(color='red', width=4)))
    
    fig.update_layout(polar=dict(angularaxis=dict(direction="counterclockwise", rotation=90)))
    st.plotly_chart(fig)


