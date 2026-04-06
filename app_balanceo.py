import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
import os
from PIL import Image
from datetime import date

# Configuración de la interfaz
st.set_page_config(page_title="Balanceo Trituradora 405CR01", layout="centered")

# --- 1. LOGO Y TÍTULOS ---
col_logo1, col_logo2, col_logo3 = st.columns([2, 1, 2])
with col_logo2:
    try:
        if os.path.exists("LOGOUNACEM.jpg"):
            st.image("LOGOUNACEM.jpg", use_container_width=True)
    except:
        st.info("ℹ️ Logo no encontrado.")

st.markdown("""
    <style>
    .titulo-principal {
        text-align: center; 
        color: #1E3A8A; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: bold;
        margin-top: -15px;
    }
    </style>
    <h1 class='titulo-principal'>Sistema de Balanceo Trituradora ⚖️</h1>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE SOPORTE ---
def limpiar_pantalla():
    """Función Callback para resetear todos los valores de forma segura"""
    st.session_state["tec_val"] = None
    st.session_state["v1_val"] = None
    for i in range(2, 5):
        st.session_state[f"v{i}_val"] = None
        st.session_state[f"p{i}_val"] = None
        st.session_state[f"a{i}_val"] = float((i-2)*120.0)

def obtener_interseccion(c1x, c1y, c2x, c2y, r1, r2):
    d = math.sqrt((c2x - c1x)**2 + (c2y - c1y)**2)
    if d > (r1 + r2) or d < abs(r1 - r2) or d == 0: return []
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(max(0, r1**2 - a**2))
    x0 = c1x + a * (c2x - c1x) / d
    y0 = c1y + a * (c2y - c1y) / d
    return [(x0 + h * (c2y - c1y) / d, y0 - h * (c2x - c1x) / d),
            (x0 - h * (c2y - c1y) / d, y0 + h * (c2x - c1x) / d)]

# --- 3. CREACIÓN DE PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Calculador de Balanceo", "📖 Procedimiento Técnico"])

# --- PESTAÑA 1: CALCULADOR ---
with tab1:
    with st.sidebar:
        st.header("👤 Datos del Servicio")
        tecnico = st.text_input("Técnico Responsable", value=None, placeholder="Ing. Juan Granja", key="tec_val")
        fecha_hoy = st.date_input("Fecha", date.today())
        
        st.divider()
        sentido = st.radio("Sentido de los Ángulos:", ["Antihorario (CCW)", "Horario (CW)"])
        s_mult = 1 if sentido == "Antihorario (CCW)" else -1
        
        st.button("🧹 LIMPIAR PANTALLA", on_click=limpiar_pantalla, use_container_width=True)
    
        st.header("📥 Mediciones")
        v1 = st.number_input("Vibración Inicial (V1)", value=None, placeholder="mm/s", step=0.1, key="v1_val")
        
        st.divider()
        meds = []
        for i in range(2, 5):
            st.subheader(f"Medición {i}")
            v = st.number_input(f"Vibración V{i}", value=None, placeholder="mm/s", key=f"v{i}_val")
            p = st.number_input(f"Peso Prueba P{i}", value=None, placeholder="gramos", key=f"p{i}_val")
            a_def = float((i-2)*120.0)
            a = st.number_input(f"Ángulo V{i} (°)", value=a_def, key=f"a{i}_val")
            meds.append({'v': v, 'p': p, 'a': a})

if st.button("⚖️ CALCULAR BALANCEO Y GENERAR PDF", type="primary", use_container_width=True):
    if not tecnico or v1 is None or any(m['v'] is None or m['p'] is None for m in meds):
        st.error("⚠️ **Faltan datos obligatorios.**")
    else:
        try:
            # --- CÁLCULOS ---
            centros = []
            for m in meds:
                # 0° Norte (Y+), sentido según s_mult
                rad = math.radians(90 - (m['a'] * s_mult))
                centros.append((v1 * math.cos(rad + math.pi), v1 * math.sin(rad + math.pi)))

            i12 = obtener_interseccion(centros[0][0], centros[0][1], centros[1][0], centros[1][1], meds[0]['v'], meds[1]['v'])
            i23 = obtener_interseccion(centros[1][0], centros[1][1], centros[2][0], centros[2][1], meds[1]['v'], meds[2]['v'])
            i31 = obtener_interseccion(centros[2][0], centros[2][1], centros[0][0], centros[0][1], meds[2]['v'], meds[0]['v'])

            if i12 and i23 and i31:
                mejor_tri = None
                perimetro_minimo = float('inf')
                for p1 in i12:
                    for p2 in i23:
                        for p3 in i31:
                            d = math.dist(p1, p2) + math.dist(p2, p3) + math.dist(p3, p1)
                            if d < perimetro_minimo:
                                perimetro_minimo = d
                                mejor_tri = (p1, p2, p3)

                bx = sum(p[0] for p in mejor_tri) / 3
                by = sum(p[1] for p in mejor_tri) / 3
                mag_res = math.sqrt(bx**2 + by**2)
                
                # Cálculo de ángulo final basado en el sentido elegido
                ang_raw = math.degrees(math.atan2(bx, by))
                ang_res = (ang_raw * s_mult + 360) % 360
                
                p_prueba_avg = sum(m['p'] for m in meds) / 3
                peso_total = (v1 / mag_res) * p_prueba_avg if mag_res != 0 else 0
                
                # --- GRÁFICO ---
                fig, ax = plt.subplots(figsize=(8,8), dpi=200)
                ax.set_aspect('equal')
                lim_max = (v1 + max(m['v'] for m in meds)) * 1.2

                # Guías angulares dinámicas
                for ang_guia in range(0, 360, 72):
                    rad_plot = math.radians(90 - (ang_guia * s_mult))
                    ax.plot([0, lim_max * 1.1 * math.cos(rad_plot)], [0, lim_max * 1.1 * math.sin(rad_plot)], 
                            color='gray', linestyle='--', linewidth=0.8, alpha=0.2)
                    ax.text(lim_max * 1.2 * math.cos(rad_plot), lim_max * 1.2 * math.sin(rad_plot), 
                            f"{ang_guia}°", color='black', fontsize=9, ha='center', va='center', fontweight='bold')

                # Círculos de medición (Menos opacos / Más visibles)
                colores = ['#3B82F6', '#10B981', '#F59E0B']
                for i in range(3):
                    ax.add_patch(plt.Circle(centros[i], meds[i]['v'], fill=False, color=colores[i], alpha=0.8, lw=2))
                
                ax.add_patch(plt.Polygon(mejor_tri, color='red', alpha=0.4, edgecolor='darkred', lw=2))
                ax.annotate('', xy=(bx, by), xytext=(0, 0), arrowprops=dict(facecolor='red', edgecolor='black', width=2, headwidth=10))

                ax.set_xlim(-lim_max*1.4, lim_max*1.4); ax.set_ylim(-lim_max*1.4, lim_max*1.4)
                ax.axhline(0, color='black', lw=1, alpha=0.5); ax.axvline(0, color='black', lw=1, alpha=0.5)
                
                st.pyplot(fig, use_container_width=True)

                instruccion = f"INSTALAR {round(peso_total, 2)}g en {round(ang_res, 1)}° (Sentido {sentido})"
                st.success(f"✅ **ACCIÓN RECOMENDADA:** {instruccion}")
