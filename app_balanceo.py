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
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    try:
        # Intenta cargar el logo para la interfaz
        imagen = Image.open("LOGOUNACEM.jpg") 
        st.image(imagen, width=200) 
    except:
        st.info("ℹ️ Logo 'LOGOUNACEM.jpg' no encontrado para la vista previa.")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>⚖️ Sistema de Balanceo Trituradora</h1>", unsafe_allow_html=True)

# --- 2. CREACIÓN DE PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Calculador de Balanceo", "📖 Procedimiento Técnico"])

# --- PESTAÑA 1: CALCULADOR ---
with tab1:
    st.markdown("<p style='text-align: center; font-weight: bold;'>Sistema: 0° Norte (Y+) | Sentido: Antihorario</p>", unsafe_allow_html=True)
    
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

    # --- ENTRADA DE DATOS (BARRA LATERAL) ---
    with st.sidebar:
        st.header("👤 Datos del Servicio")
        tecnico = st.text_input("Técnico Responsable", value="Ing. Juan Granja")
        fecha_hoy = st.date_input("Fecha", date.today())
        
        st.divider()
        st.header("📥 Mediciones")
        
        v1 = st.number_input("Vibración Inicial (V1)", value=None, placeholder="Ej: 3.0 mm/s", step=0.1)
        
        st.divider()
        meds = []
        for i in range(2, 5):
            st.subheader(f"Medición {i}")
            v = st.number_input(f"Vibración V{i}", value=None, placeholder="0.0 mm/s", key=f"v{i}")
            p = st.number_input(f"Peso Prueba P{i}", value=None, placeholder="0.0 gramos", key=f"p{i}")
            angulo_sugerido = (i-2)*120.0
            a = st.number_input(f"Ángulo V{i}", value=float(angulo_sugerido), format="%.1f", key=f"a{i}")
            meds.append({'v': v, 'p': p, 'a': a})

    # --- BOTÓN DE CÁLCULO Y VALIDACIÓN ---
    if st.button("⚖️ CALCULAR BALANCEO Y GENERAR PDF", type="primary"):
        # 1. Lista de validación de campos vacíos
        errores = []
        if v1 is None: errores.append("Vibración Inicial (V1)")
        for i, m in enumerate(meds, 2):
            if m['v'] is None: errores.append(f"Vibración V{i}")
            if m['p'] is None: errores.append(f"Peso Prueba P{i}")

        if errores:
            # Mostrar mensaje detallado de qué falta
            msg = "⚠️ **Faltan los siguientes datos:**\n\n"
            for e in errores: msg += f"* {e}\n"
            st.error(msg)
        else:
            # PROCEDER CON EL CÁLCULO SI NO HAY ERRORES
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

                bx, by = sum(p[0] for p in mejor_tri) / 3, sum(p[1] for p in mejor_tri) / 3
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

                # Gráfico
                fig, ax = plt.subplots(figsize=(8,8))
                for i in range(3):
                    ax.add_patch(plt.Circle(centros[i], meds[i]['v'], fill=False, color='#3B82F6', alpha=0.3))
                ax.add_patch(plt.Polygon(mejor_tri, color='#FDE047', alpha=0.5))
                ax.annotate('', xy=(bx, by), xytext=(0, 0), arrowprops=dict(facecolor='red', width=2))
                
                lim_max = max([m['v'] + v1 for m in meds]) * 1.2
                for e in range(6):
                    ang_e = math.radians(e * 72)
                    ex, ey = -lim_max * math.sin(ang_e), lim_max * math.cos(ang_e)
                    ax.plot([0, ex], [0, ey], 'gray', lw=0.5, ls='--')
                    ax.text(ex*0.9, ey*0.9, f"{e*72}°", ha='center', fontweight='bold')
                
                ax.set_aspect('equal')
                ax.set_xlim(-lim_max, lim_max); ax.set_ylim(-lim_max, lim_max)
                st.pyplot(fig)

                instruccion = f"MAYOR: {round(max(p_bajo, p_alto), 2)}g en {lim_bajo if p_bajo > p_alto else lim_alto}° / MENOR: {round(min(p_bajo, p_alto), 2)}g en {lim_alto if p_bajo > p_alto else lim_bajo}°"
                st.success(f"✅ **ACCIÓN:** {instruccion}")

                # --- PDF GENERACIÓN ---
                def export_pdf():
                    hora_actual = datetime.now().strftime("%H:%M:%S")
                    pdf = FPDF()
                    pdf.add_page()
                    # Carga el logo para el PDF
                    if os.path.exists("LOGOUNACEM.jpg"):
                        pdf.image("LOGOUNACEM.jpg", x=85, y=10, w=40)
                    pdf.ln(45)
                    pdf.set_font("Arial", "B", 16)
                    pdf.cell(0, 10, "REPORTE TÉCNICO DE BALANCEO", ln=True, align='C')
                    pdf.set_font("Arial", "", 10)
                    pdf.cell(100, 8, f"Técnico: {tecnico}", ln=0)
                    pdf.cell(90, 8, f"Fecha: {fecha_hoy} | Hora: {hora_actual}", ln=True, align='R')
                    
                    pdf.ln(5); pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, "MEDICIONES DE PRUEBA", ln=True)
                    pdf.cell(63, 7, "Punto", 1); pdf.cell(63, 7, "Peso (g)", 1); pdf.cell(64, 7, "Angulo", 1, ln=True)
                    pdf.set_font("Arial", "", 10)
                    for i, m in enumerate(meds, 2):
                        pdf.cell(63, 7, f"V{i}", 1); pdf.cell(63, 7, str(m['p']), 1); pdf.cell(64, 7, f"{m['a']}°", 1, ln=True)

                    pdf.ln(5); pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, "RESULTADOS", ln=True)
                    pdf.set_font("Arial", "", 10)
                    pdf.cell(100, 7, "Vibración Inicial:", 1); pdf.cell(90, 7, f"{v1} mm/s", 1, ln=True)
                    pdf.cell(100, 7, "Peso Total Corrección:", 1); pdf.cell(90, 7, f"{round(peso_total, 2)} g", 1, ln=True)
                    pdf.multi_cell(0, 10, f"INSTRUCCIÓN: {instruccion}", border=1)

                    img_buf = io.BytesIO()
                    fig.savefig(img_buf, format='png', dpi=120); img_buf.seek(0)
                    with open("temp_report.png", "wb") as f: f.write(img_buf.read())
                    pdf.image("temp_report.png", x=45, y=pdf.get_y() + 10, w=120)
                    return pdf.output(dest='S').encode('latin-1')

                st.download_button("💾 DESCARGAR REPORTE (PDF)", data=export_pdf(), file_name=f"Reporte_Balanceo_{fecha_hoy}.pdf", mime="application/pdf")
            else:
                st.error("❌ Intersección no válida. Verifique las magnitudes de vibración.")

# --- PESTAÑA 2: PROCEDIMIENTO ---
with tab2:
    st.header("📋 Procedimiento de Balanceo en 4 Puntos")
    st.subheader("⚠️ Protocolo de Seguridad Obligatorio")
    st.error("""
    **ANTES DE INICIAR CUALQUIER TAREA:**
    1.  **Comunicación Eléctrica:** Informar a la **Planta Eléctrica** que se iniciarán los trabajos de balanceo.
    2.  **Gestión de Sensores:** Comunicarse con **Panel de Control** para solicitar que se **congelen los sensores de vibración**.
    3.  **Bloqueo y Etiquetado (LOTO):** Al colocar pesos, el equipo debe estar **totalmente apagado y bloqueado**.
    """)
    st.markdown("""
    ### Pasos Técnicos:
    * **V1:** Medición original sin pesos.
    * **V2, V3, V4:** Mediciones colocando peso de prueba en 0°, 120° y 240° respectivamente.
    * **Distribución:** El software divide el peso total entre los eyectores a 72° más cercanos.
    """)
# Botón Limpiar en Sidebar
if st.sidebar.button("🗑️ Limpiar Pantalla"):
    st.rerun()
      

     
       
      
        
      
        
           

       
       
      
