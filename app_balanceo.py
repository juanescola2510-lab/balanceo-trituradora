import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
import os
from datetime import date

# Configuración de la interfaz
st.set_page_config(page_title="Balanceo Trituradora 405CR01", layout="centered")

# --- 1. LOGO Y TÍTULOS ---
col_logo1, col_logo2, col_logo3 = st.columns([1,1,1])
with col_logo2:
    if os.path.exists("LOGOUNACEM.jpg"):
        st.image("LOGOUNACEM.jpg", use_container_width=True)

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Sistema de Balanceo Trituradora ⚖️</h1>", unsafe_allow_html=True)

# --- 2. FUNCIONES DE SOPORTE ---
def limpiar_pantalla():
    for key in st.session_state.keys():
        del st.session_state[key]

def obtener_interseccion(c1x, c1y, c2x, c2y, r1, r2):
    d = math.sqrt((c2x - c1x)**2 + (c2y - c1y)**2)
    if d > (r1 + r2) or d < abs(r1 - r2) or d == 0: return []
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(max(0, r1**2 - a**2))
    x0 = c1x + a * (c2x - c1x) / d
    y0 = c1y + a * (c2y - c1y) / d
    return [(x0 + h * (c2y - c1y) / d, y0 - h * (c2x - c1x) / d),
            (x0 - h * (c2y - c1y) / d, y0 + h * (c2x - c1x) / d)]

# --- 3. INTERFAZ DE USUARIO ---
tab1, tab2 = st.tabs(["📊 Calculador", "📖 Procedimiento"])

with tab1:
    with st.sidebar:
        st.header("👤 Servicio")
        tecnico = st.text_input("Técnico", placeholder="Ing. Juan Granja")
        sentido = st.radio("Sentido de Giro:", ["Antihorario (CCW)", "Horario (CW)"])
        s_mult = 1 if sentido == "Antihorario (CCW)" else -1
        st.button("🧹 LIMPIAR", on_click=limpiar_pantalla)
    
        st.header("📥 Entrada")
        v1 = st.number_input("Vib. Inicial (V1)", min_value=0.0, step=0.1)
        mp = st.number_input("Masa de Prueba (g)", min_value=0.0, step=1.0)
        
        meds = []
        for i in range(2, 5):
            st.divider()
            v = st.number_input(f"Vibración V{i}", key=f"v{i}")
            a = st.number_input(f"Ángulo Posición {i} (°)", value=float((i-2)*120), key=f"a{i}")
            meds.append({'v': v, 'a': a})

    if st.button("⚖️ CALCULAR", type="primary", use_container_width=True):
        try:
            # 1. Centros de círculos
            centros = []
            for m in meds:
                rad = math.radians(90 - (m['a'] * s_mult))
                centros.append((v1 * math.cos(rad + math.pi), v1 * math.sin(rad + math.pi)))

            # 2. Intersecciones
            i12 = obtener_interseccion(centros[0][0], centros[0][1], centros[1][0], centros[1][1], meds[0]['v'], meds[1]['v'])
            i23 = obtener_interseccion(centros[1][0], centros[1][1], centros[2][0], centros[2][1], meds[1]['v'], meds[2]['v'])
            i31 = obtener_interseccion(centros[2][0], centros[2][1], centros[0][0], centros[0][1], meds[2]['v'], meds[0]['v'])

            if i12 and i23 and i31:
                # 3. Hallar baricentro del mejor triángulo
                mejor_tri = None
                d_min = float('inf')
                for p1 in i12:
                    for p2 in i23:
                        for p3 in i31:
                            d = math.dist(p1,p2) + math.dist(p2,p3) + math.dist(p3,p1)
                            if d < d_min: d_min = d; mejor_tri = (p1, p2, p3)
                
                bx, by = sum(p[0] for p in mejor_tri)/3, sum(p[1] for p in mejor_tri)/3
                mag_res = math.sqrt(bx**2 + by**2)
                ang_res = (math.degrees(math.atan2(bx, by)) * s_mult + 360) % 360
                peso_total = (v1 / mag_res) * mp if mag_res > 0 else 0

                # 4. REPARTICIÓN DE PESOS (Sectores de 72°)
                sector = 72
                fijacion_baja = math.floor(ang_res / sector) * sector
                fijacion_alta = (fijacion_baja + sector) % 360
                
                # Ley de senos para descomposición
                dif_ang = math.radians(ang_res - fijacion_baja)
                sec_rad = math.radians(sector)
                peso_alto = peso_total * (math.sin(dif_ang) / math.sin(sec_rad))
                peso_bajo = peso_total * (math.sin(sec_rad - dif_ang) / math.sin(sec_rad))

                # 5. GRÁFICO
                fig, ax = plt.subplots(figsize=(7,7))
                lim = (v1 + max(m['v'] for m in meds)) * 1.2
                for i in range(3):
                    ax.add_patch(plt.Circle(centros[i], meds[i]['v'], fill=False, color='blue', alpha=0.6, lw=2))
                ax.add_patch(plt.Polygon(mejor_tri, color='red', alpha=0.3))
                ax.annotate('', xy=(bx, by), xytext=(0,0), arrowprops=dict(facecolor='red', width=2))
                
                # Guías visuales
                for g in range(0, 360, 72):
                    r_g = math.radians(90 - (g * s_mult))
                    ax.plot([0, lim*math.cos(r_g)], [0, lim*math.sin(r_g)], color='gray', ls='--', alpha=0.3)
                    ax.text(lim*1.1*math.cos(r_g), lim*1.1*math.sin(r_g), f"{g}°", fontweight='bold')
                
                ax.set_xlim(-lim*1.3, lim*1.3); ax.set_ylim(-lim*1.3, lim*1.3); ax.set_aspect('equal')
                st.pyplot(fig)

                # 6. RESULTADOS
                st.success(f"🎯 **RESULTADO:** Instalar un total de **{round(peso_total, 2)}g**")
                c1, c2 = st.columns(2)
                c1.info(f"**Punto {fijacion_baja}°**\n\n Peso: {round(peso_bajo, 2)} g")
                c2.info(f"**Punto {fijacion_alta}°**\n\n Peso: {round(peso_alto, 2)} g")
            else:
                st.warning("⚠️ No se encontró intersección. Use una masa de prueba más pesada.")
        
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

with tab2:
    st.write("Coloque la masa de prueba en 3 posiciones distintas y anote la amplitud resultante.")
