import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
import os
from PIL import Image
from fpdf import FPDF
from datetime import date, datetime
import pytz


# Configuración de la interfaz
st.set_page_config(page_title="Balanceo Trituradora 405CR01", layout="centered")

# --- 1. LOGO Y TÍTULOS ---
col_logo1, col_logo2, col_logo3 = st.columns([2, 1, 2])

with col_logo2:
    try:
        st.image("LOGOUNACEM.jpg", use_container_width=True, output_format="JPEG")
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

# --- 2. CREACIÓN DE PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Calculador de Balanceo", "📖 Procedimiento Técnico"])

# --- FUNCIONES DE SOPORTE ---
def limpiar_pantalla():
    st.session_state["tec_val"] = ""
    st.session_state["v1_val"] = None
    st.session_state["p_unico"] = None
    st.session_state["v_final_val"] = None
    for i in range(2, 5):
        st.session_state[f"v{i}_val"] = None
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

# --- PESTAÑA 1: CALCULADOR ---
with tab1:
    st.markdown("<p style='text-align: center; font-weight: bold;'>Sistema: 0° Norte (Y+) | </p>", unsafe_allow_html=True)
    
# --- BARRA LATERAL ---
with st.sidebar:
    st.header("👤 Datos del Servicio")
    tecnico = st.text_input("Técnico Responsable", key="tec_val")
    fecha_hoy = st.date_input("Fecha", date.today())
    
    st.divider()
    sentido = st.radio("Sentido de los Ángulos:", ["Antihorario (CCW)", "Horario (CW)"])
    
    st.button("🧹 LIMPIAR PANTALLA", on_click=limpiar_pantalla, use_container_width=True)

    st.header("📥 Mediciones")
    v1 = st.number_input("Vibración Inicial (V1)", value=None, placeholder="mm/s", key="v1_val")
    p_prueba = st.number_input("Peso de prueba único (gramos)", value=None, placeholder="g", key="p_unico")
    
    meds = []
    for i in range(2, 5):
        st.subheader(f"Medición {i}")
        v = st.number_input(f"Vibración V{i}", value=None, key=f"v{i}_val")
        a_def = float((i-2)*120.0)
        a = st.number_input(f"Ángulo V{i} (°)", value=a_def, key=f"a{i}_val")
        meds.append({'v': v, 'p': p_prueba, 'a': a})

    st.divider()
    v_final = st.number_input("Vibración Final Post-Balanceo (mm/s)", value=None, key="v_final_val")

# --- BOTÓN DE PROCESAMIENTO ---
if st.button("⚖️ CALCULAR BALANCEO", type="primary", use_container_width=True):
    if not tecnico or v1 is None or p_prueba is None or any(m['v'] is None for m in meds):
        st.error("⚠️ Faltan datos obligatorios.")
    else:
        try:
            s_mult = 1 if sentido == "Antihorario (CCW)" else -1

            centros_base = []
            for m in meds:
                rad = math.radians(90 + (m['a'] * s_mult))
                cx = v1 * math.cos(rad)
                cy = v1 * math.sin(rad)
                centros_base.append((cx, cy))

            c1x, c1y = centros_base[0][0], centros_base[0][1]
            c2x, c2y = centros_base[1][0], centros_base[1][1]
            c3x, c3y = centros_base[2][0], centros_base[2][1]
            
            i12 = obtener_interseccion(c1x, c1y, c2x, c2y, meds[0]['v'], meds[1]['v'])
            i23 = obtener_interseccion(c2x, c2y, c3x, c3y, meds[1]['v'], meds[2]['v'])
            i31 = obtener_interseccion(c3x, c3y, c1x, c1y, meds[2]['v'], meds[0]['v'])

            if i12 and i23 and i31:
                mejor_tri = None
                per_min = float('inf')
                for p1 in i12:
                    for p2 in i23:
                        for p3 in i31:
                            d = math.dist(p1, p2) + math.dist(p2, p3) + math.dist(p3, p1)
                            if d < per_min:
                                per_min = d
                                mejor_tri = (p1, p2, p3)

                bx = sum(p[0] for p in mejor_tri) / 3
                by = sum(p[1] for p in mejor_tri) / 3
                mag_res = math.sqrt(bx**2 + by**2)
                
                ang_math = math.degrees(math.atan2(by, bx))
                ang_res = ((ang_math - 90) * s_mult) % 360
                
                peso_total = (v1 / mag_res) * p_prueba if mag_res != 0 else 0
                
                sector = 72
                lim_bajo = math.floor(ang_res / sector) * sector
                lim_alto = (lim_bajo + sector) % 360
                p_alto = peso_total * (math.sin(math.radians(ang_res - lim_bajo)) / math.sin(math.radians(sector)))
                p_bajo = peso_total * (math.sin(math.radians(lim_alto - ang_res)) / math.sin(math.radians(sector)))

                # --- 4. GRÁFICO ---
                fig, ax = plt.subplots(figsize=(8,8), dpi=200)
                ax.set_aspect('equal')
                lim_max = max([m['v'] + v1 for m in meds]) * 1.3
                
                for ang_guia in range(0, 360, 72):
                    rad_plot = math.radians(90 + (ang_guia * s_mult)) 
                    ax.plot([0, lim_max * 1.1 * math.cos(rad_plot)], [0, lim_max * 1.1 * math.sin(rad_plot)], 
                            color='gray', linestyle='--', alpha=0.4)
                    ax.text(lim_max * 1.2 * math.cos(rad_plot), lim_max * 1.2 * math.sin(rad_plot), 
                            f"{ang_guia}°", ha='center', va='center', fontweight='bold')

                for i in range(3):
                    ax.add_patch(plt.Circle(centros_base[i], meds[i]['v'], fill=False, color='#3B82F6', alpha=0.9, lw=1.5))
                
                ax.add_patch(plt.Polygon(mejor_tri, color='red', alpha=0.3))
                ax.annotate('', xy=(bx, by), xytext=(0, 0), 
                            arrowprops=dict(facecolor='red', edgecolor='red', width=0.5, headwidth=5))
                
                info_text = (
                    f"Módulo: {round(mag_res, 2)} mm/s\n"
                    f"Ángulo: {round(ang_res, 1)}°\n"
                    f"Peso Total: {round(peso_total, 2)} g"
                )

                ax.text(0.95, 0.95, info_text, 
                        transform=ax.transAxes, 
                        fontsize=10, 
                        fontweight='bold',
                        color='red',
                        va='top', 
                        ha='right',
                        bbox=dict(facecolor='white', alpha=0.8, edgecolor='red', boxstyle='round,pad=0.5'))

                ax.set_xlim(-lim_max*1.4, lim_max*1.4); ax.set_ylim(-lim_max*1.4, lim_max*1.4)
                ax.axhline(0, color='black', lw=1, alpha=0.3); ax.axvline(0, color='black', lw=1, alpha=0.3)
                
                st.pyplot(fig, use_container_width=True)

                st.success(f"✅ **ACCIÓN RECOMENDADA:** Poner **{round(p_bajo, 2)}g** en {lim_bajo}° y **{round(p_alto, 2)}g** en {lim_alto}°")

                # --- FUNCIÓN PDF ---
                def export_pdf():
                    pdf = FPDF()
                    pdf.add_page()
                    if os.path.exists("LOGOUNACEM.jpg"):
                        pdf.image("LOGOUNACEM.jpg", x=88, y=10, w=30)
                    
                    pdf.ln(32)
                    pdf.set_font("Arial", "B", 18); pdf.set_text_color(20, 50, 100)
                    pdf.cell(0, 10, "REPORTE TÉCNICO DE BALANCEO", ln=True, align='C')
                    pdf.set_draw_color(20, 50, 100); pdf.line(20, pdf.get_y()+2, 190, pdf.get_y()+2)
                    pdf.ln(5)

                    pdf.set_font("Arial", "B", 10); pdf.set_text_color(0)
                    tz_ec = pytz.timezone('America/Guayaquil')
                    ahora = datetime.now(tz_ec)
                    pdf.cell(95, 8, f"TÉCNICO: {tecnico.upper()}", ln=0)
                    pdf.cell(95, 8, f"FECHA: {ahora.strftime('%d/%m/%Y')} | HORA: {ahora.strftime('%H:%M:%S')}", ln=1, align='R')
                    pdf.ln(5)

                    pdf.set_fill_color(20, 50, 100); pdf.set_text_color(255); pdf.set_font("Arial", "B", 11)
                    pdf.cell(0, 10, "  VALORES MEDIDOS", ln=True, fill=True)
                    pdf.set_text_color(0); pdf.set_font("Arial", "B", 10)
                    pdf.cell(60, 8, "Punto", border=1, align='C'); pdf.cell(65, 8, "Vibración (mm/s)", border=1, align='C'); pdf.cell(65, 8, "Peso Prueba (g)", border=1, align='C', ln=1)
                    pdf.set_font("Arial", "", 10)
                    pdf.cell(60, 8, "V1 (Inicial)", border=1, align='C'); pdf.cell(65, 8, f"{v1}", border=1, align='C'); pdf.cell(65, 8, "-", border=1, align='C', ln=1)
                    for i, m in enumerate(meds, 2):
                        pdf.cell(60, 8, f"V{i}", border=1, align='C'); pdf.cell(65, 8, f"{m['v']}", border=1, align='C'); pdf.cell(65, 8, f"{m['p']}", border=1, align='C', ln=1)

                    pdf.ln(8)
                    pdf.set_fill_color(20, 50, 100); pdf.set_text_color(255); pdf.set_font("Arial", "B", 11)
                    pdf.cell(0, 10, "  RESULTADOS DE COMPENSACIÓN", ln=True, fill=True)
                    pdf.set_text_color(0); pdf.set_font("Arial", "B", 10)
                    pdf.cell(47, 8, "Peso Total (g)", border=1, align='C'); pdf.cell(47, 8, "Ángulo Corr.", border=1, align='C'); pdf.cell(48, 8, f"Peso {lim_bajo} (g)", border=1, align='C'); pdf.cell(48, 8, f"Peso {lim_alto} (g)", border=1, align='C', ln=1)
                    pdf.cell(47, 10, f"{round(peso_total, 2)}", border=1, align='C'); pdf.cell(47, 10, f"{round(ang_res, 1)}", border=1, align='C'); pdf.cell(48, 10, f"{round(p_bajo, 2)}", border=1, align='C'); pdf.cell(48, 10, f"{round(p_alto, 2)}", border=1, align='C', ln=1)

                    # --- NUEVA SECCIÓN: VERIFICACIÓN POST-CORRECCIÓN EN EL PDF ---
                    if v_final is not None:
                        pdf.ln(8)
                        pdf.set_fill_color(0, 100, 0); pdf.set_text_color(255); pdf.set_font("Arial", "B", 11)
                        pdf.cell(0, 10, "  VERIFICACIÓN FINAL POST-CORRECCIÓN", ln=True, fill=True)
                        pdf.set_text_color(0); pdf.set_font("Arial", "B", 10)
                        mejora_pdf = ((v1 - v_final) / v1) * 100
                        pdf.cell(95, 10, f"Vibración Final: {v_final} mm/s", border=1, align='C')
                        pdf.cell(95, 10, f"Efectividad de Mejora: {round(mejora_pdf, 1)}%", border=1, align='C', ln=1)

                    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0)
                    with open("temp_plt.png", "wb") as f: f.write(buf.read())
                    pdf.image("temp_plt.png", x=55, y=pdf.get_y()+10, w=100)
                    return pdf.output(dest='S').encode('latin-1', errors='replace')

                st.download_button("📥 DESCARGAR REPORTE (PDF)", data=export_pdf(), file_name=f"Reporte_{fecha_hoy}.pdf", mime="application/pdf", use_container_width=True)

            else:
                st.error("❌ Los círculos no se cortan.")
        except Exception as ex:
            st.error(f"Error: {ex}")

# --- SECCIÓN DE VERIFICACIÓN FINAL EN PANTALLA ---
if v1 is not None and v_final is not None:
    st.divider()
    st.subheader("🏁 Verificación Post-Corrección")
    reduccion = ((v1 - v_final) / v1) * 100
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Reducción de Amplitud", f"{reduccion:.1f}%", delta=f"{-reduccion:.1f}%", delta_color="inverse")
    with c2:
        if v_final <= 2.8: st.success("✅ **ESTADO: EXCELENTE**")
        elif v_final <= 7.1: st.warning("⚠️ **ESTADO: SATISFACTORIO**")
        else: st.error("🚨 **ESTADO: ALERTA**")

# --- SEGURIDAD ---
st.sidebar.divider()
seguridad = st.sidebar.checkbox("🔒 Protocolo LOTO ejecutado")

# --- PESTAÑA 2: PROCEDIMIENTO ---
with tab2:
    st.header("📋 Procedimiento de Balanceo en 4 Puntos")
    
    st.subheader("⚠️ Protocolo de Seguridad Obligatorio")
    st.error("""
    **ANTES DE INICIAR CUALQUIER TAREA:**
    1.  **Comunicación Eléctrica:** Pedir autorización a la **Planta Eléctrica** que se iniciarán los trabajos de balanceo.
    2.  **Gestión de Sensores:** Comunicarse con **Panel de Control** para solicitar que se **congelen los sensores de vibración** del equipo para evitar disparos falsos.
    3.  **Bloqueo y Etiquetado (LOTO):** Al momento de colocar o retirar los pesos de prueba, el equipo debe estar **totalmente apagado, desenergizado y bloqueado**. ¡Nunca manipule el rotor en movimiento!
    """)

    st.divider()

    st.markdown("""
    ### 1. Medición Inicial (V1)
    *   Arranque la trituradora y mida el nivel de vibración inicial.
    *   Anote este valor como **Vibración Inicial (V1)** en la barra lateral.
    
    ### 2. Colocación de Pesos de Prueba
    Se deben realizar 3 mediciones adicionales colocando un peso conocido en ángulos específicos:
    *   **Medición V2:** Coloque el peso de prueba en **0°**.
    *   **Medición V3:** Coloque el peso de prueba en **72°/144°/216°/288°**.
    *   **Medición V4:** Coloque el peso de prueba en **72°/144°/216°/288°**.
    *   *Nota: Asegúrese de retirar el peso anterior antes de colocar el siguiente.*
    
    ### 3. Ingreso de Datos
    *   Ingrese los valores de vibración y pesos obtenidos en la pestaña **Calculador**.
    *   El software generará un gráfico de intersección cuyo centro representa el vector de desbalance.
    
    ### 4. Ejecución de la Corrección
    *   El sistema calculará el **Peso Total** necesario y su ubicación exacta.
    *   Dado que la trituradora usa **eyectores a 72°**, el software distribuirá el peso entre los dos eyectores más cercanos.
    *   Suelde o fije los pesos según la **Acción Recomendada**.
    """)
