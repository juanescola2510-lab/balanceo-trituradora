import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
import os
from PIL import Image
from fpdf import FPDF
from datetime import date, datetime

# Configuración de la interfaz
st.set_page_config(page_title="Balanceo Trituradora 405CR01", layout="centered")

# --- 1. LOGO Y TÍTULOS ---
col_logo1, col_logo2, col_logo3 = st.columns()
with col_logo2:
    try:
        imagen = Image.open("LOGOUNACEM.jpg") 
        st.image(imagen, width=200) 
    except:
        st.info("ℹ️ Logo 'LOGOUNACEM.jpg' no encontrado.")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>⚖️ Sistema de Balanceo Trituradora</h1>", unsafe_allow_html=True)

# --- 2. CREACIÓN DE PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Calculador de Balanceo", "📖 Procedimiento Técnico"])

# --- FUNCIONES DE SOPORTE ---
def limpiar_pantalla():
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

def calcular_area(p1, p2, p3):
    return 0.5 * abs(p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1]))

# --- PESTAÑA 1: CALCULADOR ---
with tab1:
    st.markdown("<p style='text-align: center; font-weight: bold;'>Sistema: 0° Norte (Y+) | Sentido: Antihorario</p>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("👤 Datos del Servicio")
        tecnico = st.text_input("Técnico Responsable", value=None, placeholder="Ej: Ing. Juan Granja", key="tec_val")
        fecha_hoy = st.date_input("Fecha", date.today())
        st.divider()
        st.button("🧹 LIMPIAR PANTALLA", on_click=limpiar_pantalla, use_container_width=True)

        st.header("📥 Mediciones")
        v1 = st.number_input("Vibración Inicial (V1)", value=None, placeholder="Ej: 3.0 mm/s", step=0.1, key="v1_val")
        st.divider()
        meds = []
        for i in range(2, 5):
            st.subheader(f"Medición {i}")
            v = st.number_input(f"Vibración V{i}", value=None, placeholder="0.0 mm/s", key=f"v{i}_val")
            p = st.number_input(f"Peso Prueba P{i}", value=None, placeholder="0.0 g", key=f"p{i}_val")
            a_def = float((i-2)*120.0)
            a = st.number_input(f"Ángulo V{i} (°)", value=a_def, key=f"a{i}_val")
            meds.append({'v': v, 'p': p, 'a': a})

    if st.button("⚖️ CALCULAR BALANCEO Y GENERAR PDF", type="primary", use_container_width=True):
        errores = []
        if not tecnico: errores.append("Nombre del Técnico")
        if v1 is None: errores.append("Vibración Inicial (V1)")
        for i, m in enumerate(meds, 2):
            if m['v'] is None: errores.append(f"Vibración V{i}")
            if m['p'] is None: errores.append(f"Peso Prueba P{i}")

        if errores:
            st.error("⚠️ **Faltan datos:**")
            for e in errores: st.write(f"* {e}")
        else:
            try:
                centros = []
                for m in meds:
                    rad = math.radians(m['a'])
                    centros.append((-v1 * math.sin(rad), v1 * math.cos(rad)))

                i12 = obtener_interseccion(centros[0][0], centros[0][1], centros[1][0], centros[1][1], meds[0]['v'], meds[1]['v'])
                i23 = obtener_interseccion(centros[1][0], centros[1][1], centros[2][0], centros[2][1], meds[1]['v'], meds[2]['v'])
                i31 = obtener_interseccion(centros[2][0], centros[2][1], centros[0][0], centros[0][1], meds[2]['v'], meds[0]['v'])

                if i12 and i23 and i31:
                    mejor_tri = None
                    min_area = float('inf')
                    for p1 in i12:
                        for p2 in i23:
                            for p3 in i31:
                                area = calcular_area(p1, p2, p3)
                                if area < min_area:
                                    min_area = area
                                    mejor_tri = (p1, p2, p3)

                    bx, by = sum(p[0] for p in mejor_tri)/3, sum(p[1] for p in mejor_tri)/3
                    mag_res = math.sqrt(bx**2 + by**2)
                    ang_res = (math.degrees(math.atan2(-bx, by)) + 360) % 360
                    
                    p_prueba_avg = sum(m['p'] for m in meds) / 3
                    peso_total = (v1 / mag_res) * p_prueba_avg if mag_res != 0 else 0
                    
                    sector = 72
                    lim_bajo = math.floor(ang_res / sector) * sector
                    lim_alto = lim_bajo + sector
                    rad_total = math.radians(sector)
                    p_bajo = peso_total * (math.sin(math.radians(lim_alto - ang_res)) / math.sin(rad_total))
                    p_alto = peso_total * (math.sin(math.radians(ang_res - lim_bajo)) / math.sin(rad_total))

                    # --- GRÁFICO CON VALORES ---
                    fig, ax = plt.subplots(figsize=(8,8))
                    for i in range(3):
                        ax.add_patch(plt.Circle(centros[i], meds[i]['v'], fill=False, color='#3B82F6', alpha=0.3, ls='--'))
                    ax.add_patch(plt.Polygon(mejor_tri, color='#FDE047', alpha=0.6))
                    
                    # Flecha del vector
                    ax.annotate('', xy=(bx, by), xytext=(0, 0), arrowprops=dict(facecolor='red', width=2, headwidth=10))
                    
                    # --- ETIQUETA DE VALORES EN EL GRÁFICO ---
                    ax.text(bx, by, f" {round(mag_res, 2)} mm/s\n {round(ang_res, 1)}°", 
                            color='red', fontweight='bold', fontsize=12, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
                    
                    lim_max = max([m['v'] + v1 for m in meds]) * 1.2
                    for e in range(6):
                        ang_e = math.radians(e * 72)
                        ex, ey = -lim_max * math.sin(ang_e), lim_max * math.cos(ang_e)
                        ax.plot([0, ex], [0, ey], 'gray', lw=0.6, ls=':')
                        ax.text(ex*1.05, ey*1.05, f"{e*72}°", ha='center', fontsize=10, fontweight='bold')
                    
                    ax.set_aspect('equal'); ax.set_xlim(-lim_max, lim_max); ax.set_ylim(-lim_max, lim_max)
                    ax.axhline(0, color='black', lw=1); ax.axvline(0, color='black', lw=1)
                    st.pyplot(fig)

                    instruccion = f"MAYOR: {round(max(p_bajo, p_alto), 2)}g en {lim_bajo if p_bajo > p_alto else lim_alto}° / MENOR: {round(min(p_bajo, p_alto), 2)}g en {lim_alto if p_bajo > p_alto else lim_bajo}°"
                    st.success(f"✅ **ACCIÓN:** {instruccion}")

                    def export_pdf():
                        pdf = FPDF()
                        pdf.add_page()
                        if os.path.exists("LOGOUNACEM.jpg"): pdf.image("LOGOUNACEM.jpg", x=85, y=10, w=40)
                        pdf.ln(40); pdf.set_font("Arial", "B", 16)
                        pdf.cell(0, 10, "REPORTE TÉCNICO DE BALANCEO", ln=True, align='C')
                        pdf.set_font("Arial", "", 10)
                        pdf.cell(100, 8, f"Técnico: {tecnico}", ln=0)
                        pdf.cell(90, 8, f"Fecha: {fecha_hoy}", ln=True, align='R')
                        pdf.ln(5); pdf.set_fill_color(230,230,230); pdf.set_font("Arial", "B", 10)
                        pdf.cell(0, 8, " RESULTADOS", ln=True, fill=True)
                        pdf.set_font("Arial", "", 10)
                        pdf.cell(100, 7, f"Peso Total Corrección: {round(peso_total, 2)} g", 1, ln=True)
                        pdf.multi_cell(0, 8, f"INSTRUCCIÓN: {instruccion}", border=1)
                        img_buf = io.BytesIO()
                        fig.savefig(img_buf, format='png', dpi=150); img_buf.seek(0)
                        with open("temp_p.png", "wb") as f: f.write(img_buf.read())
                        pdf.image("temp_p.png", x=45, y=pdf.get_y()+10, w=120)
                        return pdf.output(dest='S').encode('latin-1')

                    st.download_button("📥 DESCARGAR REPORTE (PDF)", data=export_pdf(), file_name=f"Reporte_{fecha_hoy}.pdf", mime="application/pdf")
                else:
                    st.error("❌ Los círculos no se cortan. Aumente el peso de prueba.")
            except Exception as ex:
                st.error(f"Error: {ex}")

# --- PESTAÑA 2: PROCEDIMIENTO ---
with tab2:
    st.header("📋 Procedimiento Técnico")
    st.error("**PROTOCOLO DE SEGURIDAD:** 1. Planta Eléctrica. 2. Congelar sensores. 3. Bloqueo LOTO.")
    st.markdown("""
    ### Pasos:
    1. Medir V1 inicial.
    2. Medir V2, V3, V4 con peso de prueba en 0°, 120°, 240°.
    3. Ingresar datos y ejecutar corrección en eyectores a 72°.
    """)

