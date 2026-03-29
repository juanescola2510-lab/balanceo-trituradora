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
        imagen = Image.open("LOGOUNACEM.jpg") 
        st.image(imagen, width=150) 
    except:
        st.info("ℹ️ Archivo 'LOGOUNACEM.jpg' no encontrado para la vista previa.")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>⚖️ Sistema de Balanceo Trituradora</h1>", unsafe_allow_html=True)

# --- 2. CREACIÓN DE PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Calculador de Balanceo", "📖 Procedimiento Técnico"])

# --- FUNCIONES DE SOPORTE ---
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

def calcular_area(p1, p2, p3):
    return 0.5 * abs(p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1]))

# --- PESTAÑA 1: CALCULADOR ---
with tab1:
    st.markdown("<p style='text-align: center; font-weight: bold;'>Sistema: 0° Norte (Y+) | Sentido: Antihorario</p>", unsafe_allow_html=True)
    
    # --- BARRA LATERAL ---
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
            p = st.number_input(f"Peso Prueba P{i}", value=None, placeholder="0.0 gramos", key=f"p{i}_val")
            a_def = float((i-2)*120.0)
            a = st.number_input(f"Ángulo V{i} (°)", value=a_def, key=f"a{i}_val")
            meds.append({'v': v, 'p': p, 'a': a})

    # --- BOTÓN DE PROCESAMIENTO ---
    if st.button("⚖️ CALCULAR BALANCEO Y GENERAR PDF", type="primary", use_container_width=True):
        errores = []
        if not tecnico: errores.append("Nombre del Técnico")
        if v1 is None: errores.append("Vibración Inicial (V1)")
        for i, m in enumerate(meds, 2):
            if m['v'] is None: errores.append(f"Vibración V{i}")
            if m['p'] is None: errores.append(f"Peso Prueba P{i}")

        if errores:
            st.error("⚠️ **Faltan datos obligatorios:**")
            for e in errores: st.write(f"* {e}")
        else:
            try:
                # 1. Centros de los círculos
                centros = []
                for m in meds:
                    rad = math.radians(m['a'])
                    centros.append((-v1 * math.sin(rad), v1 * math.cos(rad)))

                # 2. Intersecciones
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

                    # 3. Gráfico con Valores de Módulo y Ángulo
                    fig, ax = plt.subplots(figsize=(8,8))
                    for i in range(3):
                        ax.add_patch(plt.Circle(centros[i], meds[i]['v'], fill=False, color='#3B82F6', alpha=0.3, ls='--'))
                    ax.add_patch(plt.Polygon(mejor_tri, color='#FDE047', alpha=0.6))
                    
                    # Vector de desbalance
                    ax.annotate('', xy=(bx, by), xytext=(0, 0), arrowprops=dict(facecolor='red', width=2, headwidth=10))
                   # 1. CÁLCULO DE POSICIÓN DINÁMICA PARA LA ETIQUETA
# Usamos un offset para que el texto no toque la punta de la flecha
offset = lim_max * 0.1  
tx = bx + (offset if bx >= 0 else -offset)
ty = by + (offset if by >= 0 else -offset)

# Alineación dinámica según el cuadrante
ha = 'left' if bx >= 0 else 'right'
va = 'bottom' if by >= 0 else 'top'

# 2. ETIQUETA MEJORADA (SIN CRUCES)
ax.text(tx, ty, f" Módulo: {round(mag_res, 2)} mm/s\n Ángulo: {round(ang_res, 1)}°", 
        color='red', fontweight='bold', fontsize=11, 
        ha=ha, va=va,
        bbox=dict(facecolor='white', alpha=0.9, edgecolor='red', lw=1, boxstyle='round,pad=0.5'))

# 3. EJES ANGULARES (CORREGIDOS A 60° PARA CUBRIR 360°)
for deg in range(0, 360, 60):
    rad = math.radians(deg)
    # Si tu 0° es arriba (estilo balanceo mecánico común):
    ex, ey = lim_max * math.sin(rad), lim_max * math.cos(rad)
    ax.plot([0, ex], [0, ey], 'gray', lw=0.5, ls='--')
    ax.text(ex*1.1, ey*1.1, f"{deg}°", ha='center', va='center', fontsize=9, color='gray')

# 4. CONFIGURACIÓN FINAL
ax.set_aspect('equal')
ax.set_xlim(-lim_max * 1.3, lim_max * 1.3) # Más espacio para que no corte el texto
ax.set_ylim(-lim_max * 1.3, lim_max * 1.3)
ax.axis('off') # Limpia el recuadro exterior para que se vea más profesional
st.pyplot(fig)
 
                   
                       

                    # 4. Generación de PDF
                    def export_pdf():
                        pdf = FPDF()
                        pdf.add_page()
                        if os.path.exists("LOGOUNACEM.jpg"):
                            pdf.image("LOGOUNACEM.jpg", x=85, y=10, w=40)
                        pdf.ln(40); pdf.set_font("Arial", "B", 16)
                        pdf.cell(0, 10, "REPORTE TÉCNICO DE BALANCEO", ln=True, align='C')
                        pdf.set_font("Arial", "", 10)
                        pdf.cell(100, 8, f"Técnico: {tecnico}", ln=0)
                        pdf.cell(90, 8, f"Fecha: {fecha_hoy} | Hora: {datetime.now().strftime('%H:%M')}", ln=True, align='R')
                        
                        pdf.ln(5); pdf.set_fill_color(230,230,230)
                        pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, " MEDICIONES DE PRUEBA", ln=True, fill=True)
                        pdf.set_font("Arial", "", 10)
                        pdf.cell(63, 7, "Punto", 1); pdf.cell(63, 7, "Vibración (mm/s)", 1); pdf.cell(64, 7, "Peso (g)", 1, ln=True)
                        for i, m in enumerate(meds, 2):
                            pdf.cell(63, 7, f"V{i}", 1); pdf.cell(63, 7, str(m['v']), 1); pdf.cell(64, 7, str(m['p']), 1, ln=True)

                        pdf.ln(5); pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, " RESULTADOS FINAL", ln=True, fill=True)
                        pdf.set_font("Arial", "", 10)
                        pdf.cell(100, 7, "Vibración Inicial (V1):", 1); pdf.cell(90, 7, f"{v1} mm/s", 1, ln=True)
                        pdf.cell(100, 7, "Peso Total Corrección:", 1); pdf.cell(90, 7, f"{round(peso_total, 2)} g", 1, ln=True)
                        pdf.multi_cell(0, 8, f"INSTRUCCIÓN DE MONTAJE: {instruccion}", border=1)

                        img_buf = io.BytesIO()
                        fig.savefig(img_buf, format='png', dpi=150); img_buf.seek(0)
                        with open("temp_plt.png", "wb") as f: f.write(img_buf.read())
                        pdf.image("temp_plt.png", x=45, y=pdf.get_y()+10, w=120)
                        return pdf.output(dest='S').encode('latin-1')

                    st.download_button("📥 DESCARGAR REPORTE (PDF)", data=export_pdf(), file_name=f"Reporte_{fecha_hoy}.pdf", mime="application/pdf")
                else:
                    st.error("❌ Los círculos no se cortan. Verifique sus lecturas.")
            except Exception as ex:
                st.error(f"Error en el proceso: {ex}")

# --- PESTAÑA 2: PROCEDIMIENTO ---
with tab2:
    st.header("📋 Procedimiento de Balanceo en 4 Puntos")
    
    st.subheader("⚠️ Protocolo de Seguridad Obligatorio")
    st.error("""
    **ANTES DE INICIAR CUALQUIER TAREA:**
    1.  **Comunicación Eléctrica:** Informar a la **Planta Eléctrica** que se iniciarán los trabajos de balanceo.
    2.  **Gestión de Sensores:** Comunicarse con **Panel de Control** para solicitar que se **congelen los sensores de vibración** del equipo para evitar disparos falsos.
    3.  **Bloqueo y Etiquetado (LOTO):** Al momento de colocar o retirar los pesos de prueba, el equipo debe estar **totalmente apagado, desenergizado y bloqueado**. ¡Nunca manipule el rotor en movimiento!
    """)

    st.divider()

    st.markdown("""
    ### 1. Medición Inicial (V1)
    *   Arranque la trituradora y mida el nivel de vibración global en el punto de apoyo.
    *   Anote este valor como **Vibración Inicial (V1)** en la barra lateral.
    
    ### 2. Colocación de Pesos de Prueba
    Se deben realizar 3 mediciones adicionales colocando un peso conocido en ángulos específicos:
    *   **Medición V2:** Coloque el peso de prueba en **0°**.
    *   **Medición V3:** Coloque el peso de prueba en **120°**.
    *   **Medición V4:** Coloque el peso de prueba en **240°**.
    *   *Nota: Asegúrese de retirar el peso anterior antes de colocar el siguiente.*
    
    ### 3. Ingreso de Datos
    *   Ingrese los valores de vibración y pesos obtenidos en la pestaña **Calculador**.
    *   El software generará un gráfico de intersección cuyo centro representa el vector de desbalance.
    
    ### 4. Ejecución de la Corrección
    *   El sistema calculará el **Peso Total** necesario y su ubicación exacta.
    *   Dado que la trituradora usa **eyectores a 72°**, el software distribuirá el peso entre los dos eyectores más cercanos.
    *   Suelde o fije los pesos según la **Acción Recomendada**.
    """)
