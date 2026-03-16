import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image
from fpdf import FPDF
from datetime import date, datetime

# Configuración de la interfaz
st.set_page_config(page_title="Balanceo Trituradora 405CR01", layout="centered")

# --- 1. LOGO Y TÍTULOS ---
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    try:
        imagen = Image.open("logo.jpeg") 
        st.image(imagen, width=200) 
    except:
        st.info("ℹ️ Logo 'logo.jpeg' no encontrado.")

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
        tecnico = st.text_input("Técnico Responsable", "Ing. Juan Granja")
        fecha_hoy = st.date_input("Fecha", date.today())
        
        st.divider()
        st.header("📥 Mediciones")
        v1 = st.number_input("Vibración Inicial (V1)", value=3.0, step=0.1)
        st.divider()
        meds = []
        for i in range(2, 5):
            st.subheader(f"Medición {i}")
            v = st.number_input(f"Vibración (V{i})", value=4.0, key=f"v{i}")
            p = st.number_input(f"Peso Prueba (P{i})", value=10.0, key=f"p{i}")
            a = st.number_input(f"Ángulo (°)", value=(i-2)*120.0, key=f"a{i}")
            meds.append({'v': v, 'p': p, 'a': a})

    # --- PROCESAMIENTO ---
    if st.button("CALCULAR BALANCEO Y GENERAR PDF", type="primary"):
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

            def export_pdf():
                hora_actual = datetime.now().strftime("%H:%M:%S")
                pdf = FPDF()
                pdf.add_page()
                try: pdf.image("LOGOUNACEM.jpeg", x=85, y=10, w=40)
                except: pass
                pdf.ln(45)
                pdf.set_font("Arial", "B", 16)
                pdf.cell(200, 10, "REPORTE TÉCNICO DE BALANCEO", ln=True, align='C')
                pdf.set_font("Arial", "", 10)
                pdf.cell(100, 8, f"Técnico: {tecnico}", ln=0)
                pdf.cell(90, 8, f"Fecha: {fecha_hoy} | Hora: {hora_actual}", ln=True)
                
                # Tabla Mediciones
                pdf.ln(5); pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, "MEDICIONES DE PRUEBA", ln=True, fill=True)
                pdf.cell(63, 7, "Punto", 1); pdf.cell(63, 7, "Peso (g)", 1); pdf.cell(64, 7, "Angulo", 1, ln=True)
                pdf.set_font("Arial", "", 10)
                for i, m in enumerate(meds, 2):
                    pdf.cell(63, 7, f"V{i}", 1); pdf.cell(63, 7, str(m['p']), 1); pdf.cell(64, 7, f"{m['a']}°", 1, ln=True)

                pdf.ln(5); pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, "RESULTADOS", ln=True)
                pdf.cell(100, 7, "Vibración Inicial:", 1); pdf.cell(90, 7, str(v1), 1, ln=True)
                pdf.cell(100, 7, "Peso Total Corrección:", 1); pdf.cell(90, 7, f"{round(peso_total, 2)} g", 1, ln=True)
                pdf.multi_cell(0, 10, f"INSTRUCCIÓN: {instruccion}", border=1)

                img_buf = io.BytesIO()
                fig.savefig(img_buf, format='png', dpi=120); img_buf.seek(0)
                with open("temp_report.png", "wb") as f: f.write(img_buf.read())
                pdf.image("temp_report.png", x=50, y=160, w=110)
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("💾 DESCARGAR REPORTE (PDF)", data=export_pdf(), file_name=f"Reporte_{fecha_hoy}.pdf", mime="application/pdf")
        else:
            st.error("❌ Intersección no válida.")

# --- PESTAÑA 2: PROCEDIMIENTO ---
with tab2:
    st.header("📋 Procedimiento de Balanceo en 4 Puntos")
    st.markdown("""
    Este método (basado en el método de las 4 carreras sin fase) se utiliza cuando no se dispone de un sensor de fase (fotocelda).
    
    ### 1. Medición Inicial (V1)
    *   Arranque la trituradora y mida el nivel de vibración global en el punto de apoyo.
    *   Anote este valor como **Vibración Inicial (V1)**.
    
    ### 2. Colocación de Pesos de Prueba
    Se deben realizar 3 mediciones adicionales colocando un peso conocido en ángulos específicos:
    *   **Medición V2:** Coloque el peso de prueba en **0°**.
    *   **Medición V3:** Coloque el peso de prueba en **120°**.
    *   **Medición V4:** Coloque el peso de prueba en **240°**.
    *   *Nota: Asegúrese de retirar el peso anterior antes de colocar el siguiente.*
    
    ### 3. Ingreso de Datos
    *   Ingrese los valores de vibración obtenidos en cada corrida en la pestaña **Calculador**.
    *   El software generará un triángulo de intersección cuyo centro representa el vector de desbalance.
    
    ### 4. Ejecución de la Corrección
    *   El sistema calculará el **Peso Total** necesario.
    *   Dado que la trituradora usa **eyectores a 72°**, el software distribuirá el peso total entre los dos eyectores más cercanos al punto de corrección.
    *   Suelde o fije los pesos según la **Acción Recomendada** en color verde.
    
    ⚠️ **Seguridad:** Asegúrese de que el equipo esté completamente bloqueado (LOTO) antes de ingresar a colocar los pesos.
    """)

# Botón Limpiar en Sidebar
if st.sidebar.button("🗑️ Limpiar Pantalla"):
    st.rerun()
      

     
       
      
        
      
        
           

       
       
      
