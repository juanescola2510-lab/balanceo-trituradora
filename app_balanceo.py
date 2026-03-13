import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image
from fpdf import FPDF
from datetime import date

# Configuración de la interfaz
st.set_page_config(page_title="Balanceo Trituradora 405CR01", layout="centered")

# --- 1. LOGO CENTRADO ---
col_logo1, col_logo2, col_logo3 = st.columns([1, 1, 1])
with col_logo2:
    try:
        imagen = Image.open("logo.jpeg") 
        st.image(imagen, width=150) 
    except:
        st.info("ℹ️ Logo no encontrado.")

st.markdown("<h1 style='text-align: center;'>⚖️ Balanceo: Trituradora 405CR01</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Sistema: 0° Norte (Y+) | Sentido: Antihorario</p>", unsafe_allow_html=True)

# --- FUNCIONES MATEMÁTICAS ---
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

# --- ENTRADA DE DATOS ---
with st.sidebar:
    st.header("👤 Información del Servicio")
    tecnico = st.text_input("Nombre del Técnico", "Ing. Juan Granja")
    fecha_servicio = st.date_input("Fecha del Servicio", date.today())
    
    st.divider()
    st.header("📥 Datos de Entrada")
    v1 = st.number_input("Vibración Inicial (V1)", value=3.0, step=0.1)
    st.divider()
    meds = []
    for i in range(2, 5):
        st.subheader(f"Medición {i}")
        v = st.number_input(f"Vibración", value=4.0, key=f"v{i}")
        p = st.number_input(f"Peso Prueba (P{i})", value=10.0, key=f"p{i}")
        a = st.number_input(f"Ángulo (°)", value=(i-2)*120.0, key=f"a{i}")
        meds.append({'v': v, 'p': p, 'a': a})

if st.button("CALCULAR Y GENERAR REPORTE", type="primary"):
    centros = []
    for m in meds:
        rad = math.radians(m['a'])
        centros.append((-v1 * math.sin(rad), v1 * math.cos(rad)))

    i12 = obtener_interseccion(centros[0][0], centros[0][1], centros[1][0], centros[1][1], meds[0]['v'], meds[1]['v'])
    i23 = obtener_interseccion(centros[1][0], centros[1][1], centros[2][0], centros[2][1], meds[1]['v'], meds[2]['v'])
    i31 = obtener_interseccion(centros[2][0], centros[2][1], centros[0][0], centros[0][1], meds[2]['v'], meds[0]['v'])

    if i12 and i23 and i31:
        min_area = float('inf')
        mejor_tri = None
        for p1 in i12:
            for p2 in i23:
                for p3 in i31:
                    area = calcular_area(p1, p2, p3)
                    if area < min_area:
                        min_area = area
                        mejor_tri = (p1, p2, p3)

        bx = sum(p[0] for p in mejor_tri) / 3
        by = sum(p[1] for p in mejor_tri) / 3
        mag_res = math.sqrt(bx**2 + by**2)
        ang_res = (math.degrees(math.atan2(-bx, by)) + 360) % 360
        p_prueba_avg = sum(m['p'] for m in meds) / 3
        peso_total = (v1 / mag_res) * p_prueba_avg if mag_res != 0 else 0
        
        # --- LÓGICA DE DISTRIBUCIÓN ---
        ang_corr = ang_res  
        sector = 72
        lim_bajo = math.floor(ang_corr / sector) * sector
        lim_alto = lim_bajo + sector
        rad_total = math.radians(sector)
        p_bajo = peso_total * (math.sin(math.radians(lim_alto - ang_corr)) / math.sin(rad_total))
        p_alto = peso_total * (math.sin(math.radians(ang_corr - lim_bajo)) / math.sin(rad_total))

        # --- GRÁFICO ---
        fig, ax = plt.subplots(figsize=(8,8))
        for i in range(3):
            ax.add_patch(plt.Circle(centros[i], meds[i]['v'], fill=False, color='blue', alpha=0.2))
        ax.add_patch(plt.Polygon(mejor_tri, color='yellow', alpha=0.4))
        ax.annotate('', xy=(bx, by), xytext=(0, 0), arrowprops=dict(facecolor='red', edgecolor='red', width=2.5))
        ax.text(bx, by + 0.5, f"V: {round(mag_res,2)}\n{round(ang_res,1)}°", color='red', fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.7))
        
        lim_max = max([m['v'] + v1 for m in meds]) * 1.2
        for e in range(6):
            ang_e = math.radians(e * 72)
            ex, ey = -lim_max * math.sin(ang_e), lim_max * math.cos(ang_e)
            ax.plot([0, ex], [0, ey], 'gray', lw=0.8, ls='--')
            ax.text(ex*0.9, ey*0.9, f"{e*72}°", ha='center', fontweight='bold')
        
        ax.set_aspect('equal')
        ax.set_xlim(-lim_max, lim_max); ax.set_ylim(-lim_max, lim_max)
        st.pyplot(fig)

        # --- RESULTADOS Y MENSAJES ---
        st.divider()
        st.subheader("📋 Resumen de Resultados")
        c_res1, c_res2 = st.columns(2)
        c_res1.metric("Vibración Resultante", round(mag_res, 3))
        c_res2.metric("Peso Total (gr)", round(peso_total, 2))

        instruccion = ""
        if p_bajo >= p_alto:
            st.success(f"✅ **Instrucción:** Poner el peso mayor ({round(p_bajo, 2)}g) en el ángulo {lim_bajo}°, y el menor ({round(p_alto, 2)}g) en el ángulo {lim_alto}°.")
            instruccion = f"Mayor: {round(p_bajo, 2)}g en {lim_bajo} deg / Menor: {round(p_alto, 2)}g en {lim_alto} deg"
        else:
            st.success(f"✅ **Instrucción:** Poner el peso mayor ({round(p_alto, 2)}g) en el ángulo {lim_alto}°, y el menor ({round(p_bajo, 2)}g) en el ángulo {lim_bajo}°.")
            instruccion = f"Mayor: {round(p_alto, 2)}g en {lim_alto} deg / Menor: {round(p_bajo, 2)}g en {lim_bajo} deg"

        # --- GENERACIÓN DE PDF ---
        def create_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "REPORTE TECNICO DE BALANCEO", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.cell(200, 10, f"Tecnico: {tecnico}", ln=True)
            pdf.cell(200, 10, f"Fecha: {fecha_servicio}", ln=True)
            pdf.cell(200, 10, f"Equipo: Trituradora 405CR01", ln=True)
            pdf.divider_line = "________________________________________________"
            pdf.ln(5)
            pdf.cell(200, 10, f"Vibracion Inicial: {v1}", ln=True)
            pdf.cell(200, 10, f"Vibracion Resultante: {round(mag_res, 3)}", ln=True)
            pdf.cell(200, 10, f"Peso Total Necesario: {round(peso_total, 2)} g", ln=True)
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 10, f"ACCION RECOMENDADA: {instruccion}")
            
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format='png')
            img_buf.seek(0)
            with open("chart_temp.png", "wb") as f: f.write(img_buf.read())
            pdf.image("chart_temp.png", x=25, y=120, w=160)
            return pdf.output(dest='S').encode('latin-1')

        st.download_button(
            label="💾 GUARDAR REPORTE (PDF)",
            data=create_pdf(),
            file_name=f"Reporte_{tecnico}_{fecha_servicio}.pdf",
            mime="application/pdf"
        )

if st.sidebar.button("Limpiar Pantalla"):
    st.rerun()

  
      

     
       
      
        
      
        
           

       
       
      
