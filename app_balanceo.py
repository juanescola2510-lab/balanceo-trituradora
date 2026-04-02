import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Balanceo Universal Trituradora", layout="centered")

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

# --- INTERFAZ DE USUARIO ---
st.title("⚖️ Sistema de Balanceo Dinámico Universal")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Configuración del Rotor")
    n_aletas = st.number_input("Número de Aletas/Álabes", min_value=2, max_value=36, value=5)
    sentido = st.radio("Sentido de Giro (Visto de frente)", ["Antihorario (CCW)", "Horario (CW)"])
    
    st.divider()
    st.header("👤 Datos del Servicio")
    tecnico = st.text_input("Técnico Responsable", placeholder="Ej. Ing. Juan Granja")
    v1 = st.number_input("Vibración Inicial (V1) [mm/s]", min_value=0.0, format="%.2f")
    
    angulo_paso = 360 / n_aletas

# --- ENTRADA DE MEDICIONES ---
st.subheader("📥 Registro de Pruebas")
col1, col2, col3 = st.columns(3)
meds = []
for i, col in enumerate([col1, col2, col3], 2):
    with col:
        st.markdown(f"**Prueba {i}**")
        v = st.number_input(f"V{i} (mm/s)", key=f"v{i}", format="%.2f")
        p = st.number_input(f"Peso {i} (g)", key=f"p{i}", format="%.2f")
        # Sugerir ángulo por defecto según aletas
        a_sug = float((i-2) * angulo_paso)
        a = st.number_input(f"Ángulo {i} (°)", value=a_sug, key=f"a{i}")
        meds.append({'v': v, 'p': p, 'a': a})

# --- PROCESAMIENTO ---
if st.button("⚖️ CALCULAR Y GRAFICAR", type="primary", use_container_width=True):
    if v1 > 0 and all(m['v'] > 0 for m in meds):
        try:
            # 1. Definir Centros de los Círculos
            centros = []
            inv = 1 if sentido == "Antihorario (CCW)" else -1
            
            for m in meds:
                # 90° es el Norte (Y+). El ángulo avanza según el sentido.
                rad = math.radians(90 + (m['a'] * inv))
                centros.append((v1 * math.cos(rad), v1 * math.sin(rad)))

            # 2. Intersecciones para el Triángulo de Error
            # Buscamos la intersección de los tres círculos de vibración
            i12 = obtener_interseccion(centros[0][0], centros[0][1], centros[1][0], centros[1][1], meds[0]['v'], meds[1]['v'])
            i23 = obtener_interseccion(centros[1][0], centros[1][1], centros[2][0], centros[2][1], meds[1]['v'], meds[2]['v'])
            i31 = obtener_interseccion(centros[2][0], centros[2][1], centros[0][0], centros[0][1], meds[2]['v'], meds[0]['v'])

            if i12 and i23 and i31:
                # Encontrar el triángulo de error más pequeño
                mejor_tri = []
                min_err = float('inf')
                for p1 in i12:
                    for p2 in i23:
                        for p3 in i31:
                            err = math.dist(p1, p2) + math.dist(p2, p3) + math.dist(p3, p1)
                            if err < min_err:
                                min_err = err
                                mejor_tri = [p1, p2, p3]

                # Centroide del punto resultante (Ubicación del Peso de Corrección)
                bx = sum(p[0] for p in mejor_tri) / 3
                by = sum(p[1] for p in mejor_tri) / 3
                mag_res = math.sqrt(bx**2 + by**2)
                
                # Ángulo de CORRECCIÓN (apunta directamente al centroide)
                # Ajustado a sistema 0° Norte (Eje Y+)
                ang_corr = (math.degrees(math.atan2(by, bx)) - 90) * inv
                ang_corr = (360 - ang_corr) % 360 if sentido == "Horario (CW)" else (ang_corr + 360) % 360
                
                # --- CÁLCULO DE MAGNITUD DEL PESO ---
                peso_avg = sum(m['p'] for m in meds) / 3
                peso_total = (v1 / mag_res) * peso_avg if mag_res != 0 else 0

                # --- REPARTICIÓN EN ALETAS ---
                idx_bajo = int(ang_corr // angulo_paso)
                aleta_bajo = idx_bajo
                aleta_alto = (idx_bajo + 1) % n_aletas
                
                theta = ang_corr - (aleta_bajo * angulo_paso)
                alfa = angulo_paso
                
                # Repartición vectorial de la masa de corrección
                p_alto = peso_total * (math.sin(math.radians(theta)) / math.sin(math.radians(alfa)))
                p_bajo = peso_total * (math.sin(math.radians(alfa - theta)) / math.sin(math.radians(alfa)))

                # --- GRÁFICO ---
                fig, ax = plt.subplots(figsize=(8,8), dpi=100)
                ax.set_aspect('equal')
                lim_vista = max(v1 + max(m['v'] for m in meds), mag_res) * 1.3
                
                # Líneas de Aletas
                for i in range(n_aletas):
                    ang_plot = math.radians(90 + (i * angulo_paso * inv))
                    ax.plot([0, lim_vista*math.cos(ang_plot)], [0, lim_vista*math.sin(ang_plot)], color='gray', lw=0.7, ls='--')
                    ax.text(lim_vista*1.1*math.cos(ang_plot), lim_vista*1.1*math.sin(ang_plot), f"{int(i*angulo_paso)}°", ha='center', fontsize=8)

                # Dibujar Círculos de Vibración
                colores = ['#FF5733', '#33FF57', '#3357FF']
                for i in range(3):
                    c = plt.Circle(centros[i], meds[i]['v'], fill=False, color=colores[i], label=f"V{i+2} (Círculo)", lw=1.2)
                    ax.add_patch(c)
                    ax.plot(centros[i][0], centros[i][1], 'o', color=colores[i], markersize=4)

                # Triángulo de error
                ax.add_patch(plt.Polygon(mejor_tri, color='yellow', alpha=0.3, label='Zona de Intersección'))
                
                # Vector de CORRECCIÓN (Apunta directamente a la intersección)
                ax.quiver(0, 0, bx, by, angles='xy', scale_units='xy', scale=1, color='green', label='Vector Corrección', width=0.015)

                ax.set_xlim(-lim_vista, lim_vista); ax.set_ylim(-lim_vista, lim_vista)
                ax.axhline(0, color='black', lw=0.8); ax.axvline(0, color='black', lw=0.8)
                plt.legend(loc='upper right', fontsize='small')
                st.pyplot(fig)

                # --- TABLA DE RESULTADOS ---
                st.success(f"### Resultado: Colocar {round(peso_total, 2)} g a {round(ang_corr, 1)}°")
                
                data_final = {
                    "Ubicación": [f"Aleta {aleta_bajo} ({int(aleta_bajo * angulo_paso)}°)", 
                                 f"Aleta {aleta_alto} ({int((aleta_bajo + 1) * angulo_paso)}°)", 
                                 "TOTAL"],
                    "Peso a Soldar / Colocar": [f"{round(p_bajo, 2)} g", f"{round(p_alto, 2)} g", f"{round(peso_total, 2)} g"]
                }
                st.table(data_final)
                
            else:
                st.error("❌ No se encontró intersección entre los círculos. Revisa que V2, V3 y V4 sean coherentes con V1.")
        except Exception as e:
            st.error(f"Error en el cálculo: {e}")
    else:
        st.warning("⚠️ Ingrese valores de vibración inicial (V1) y de pruebas válidos.")

st.markdown("---")
st.caption(f"Sistema de Balanceo Universal - {date.today()} | Técnico: {tecnico if tecnico else 'No especificado'}")
Usa el código con precaución.

Cambios realizados:
Lógica del Vector: Se eliminó la suma de 
 al ángulo resultante. Ahora el vector verde (corrección) apunta directamente hacia el centro del triángulo formado por la intersección de los tres círculos.
Cálculo de Aletas: La tabla de pesos ahora descompone el vector de corrección directamente en las dos aletas más cercanas a ese punto de intersección.
Visualización: El gráfico muestra claramente cómo las circunferencias se cruzan en un punto, y el vector nace del centro del rotor hacia ese punto específico.
