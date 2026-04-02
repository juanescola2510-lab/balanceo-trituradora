import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
from datetime import date

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema de Balanceo Universal", layout="centered")

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

# --- INTERFAZ DE USUARIO ---
st.title("⚖️ Sistema de Balanceo Dinámico Universal")

with st.sidebar:
    st.header("⚙️ Configuración del Rotor")
    n_aletas = st.number_input("Número de Álabes/Aletas", min_value=2, max_value=36, value=5)
    sentido = st.radio("Sentido de Giro (visto de frente)", ["Antihorario (CCW)", "Horario (CW)"])
    angulo_sector = 360 / n_aletas
    
    st.divider()
    st.header("👤 Datos del Servicio")
    tecnico = st.text_input("Técnico Responsable", placeholder="Ej. Ing. Juan Granja")
    v1 = st.number_input("Vibración Inicial (V1) [mm/s]", format="%.2f")

# --- ENTRADA DE MEDICIONES ---
col1, col2, col3 = st.columns(3)
meds = []
for i, col in enumerate([col1, col2, col3], 2):
    with col:
        st.subheader(f"Prueba {i}")
        v = st.number_input(f"V{i} (mm/s)", key=f"v{i}", format="%.2f")
        p = st.number_input(f"Peso {i} (g)", key=f"p{i}", format="%.2f")
        # Ángulo sugerido automático basado en aspas
        a_sug = (i-2) * angulo_sector
        a = st.number_input(f"Ángulo {i} (°)", value=float(a_sug), key=f"a{i}")
        meds.append({'v': v, 'p': p, 'a': a})

# --- PROCESAMIENTO ---
if st.button("CALCULAR BALANCEO", type="primary", use_container_width=True):
    if v1 > 0 and all(m['v'] > 0 for m in meds):
        # Lógica de coordenadas según sentido
        # Si es Horario, invertimos el signo del ángulo en el cálculo
        mult = 1 if sentido == "Antihorario (CCW)" else -1
        
        centros = []
        for m in meds:
            rad = math.radians(m['a'] * mult)
            centros.append((-v1 * math.sin(rad), v1 * math.cos(rad)))

        # Intersecciones (Triángulo de error)
        i12 = obtener_interseccion(centros[0][0], centros[0][1], centros[1][0], centros[1][1], meds[0]['v'], meds[1]['v'])
        i23 = obtener_interseccion(centros[1][0], centros[1][1], centros[2][0], centros[2][1], meds[1]['v'], meds[2]['v'])
        i31 = obtener_interseccion(centros[2][0], centros[2][1], centros[0][0], centros[0][1], meds[2]['v'], meds[0]['v'])

        if i12 and i23 and i31:
            # Encontrar el triángulo más pequeño
            mejor_tri = None
            min_dist = float('inf')
            for p1 in i12:
                for p2 in i23:
                    for p3 in i31:
                        d = math.dist(p1, p2) + math.dist(p2, p3) + math.dist(p3, p1)
                        if d < min_dist:
                            min_dist = d
                            mejor_tri = (p1, p2, p3)

            # Centroide del error (Punto de vibración resultante)
            bx = sum(p[0] for p in mejor_tri) / 3
            by = sum(p[1] for p in mejor_tri) / 3
            
            mag_res = math.sqrt(bx**2 + by**2)
            # Ajuste de ángulo según sentido
            ang_vibracion = (math.degrees(math.atan2(-bx, by)) + 360) % 360
            if sentido == "Horario (CW)":
                ang_vibracion = (360 - ang_vibracion) % 360
            
            # --- CÁLCULO DE PESO DE CORRECCIÓN ---
            p_prueba_avg = sum(m['p'] for m in meds) / 3
            peso_total = (v1 / mag_res) * p_prueba_avg
            
            # Ángulo de corrección (180° opuesto a la vibración)
            ang_correccion = (ang_vibracion + 180) % 360
            
            # Descomposición en Aletas
            idx_bajo = math.floor(ang_correccion / angulo_sector)
            lim_bajo = idx_bajo * angulo_sector
            lim_alto = lim_bajo + angulo_sector
            
            # Ley de Senos para repartición de masas
            p_bajo = peso_total * (math.sin(math.radians(lim_alto - ang_correccion)) / math.sin(math.radians(angulo_sector)))
            p_alto = peso_total * (math.sin(math.radians(ang_correccion - lim_bajo)) / math.sin(math.radians(angulo_sector)))

            # --- RESULTADOS ---
            st.success(f"### Resultado: Aplicar {round(peso_total, 2)}g a {round(ang_correccion, 1)}°")
            c1, c2 = st.columns(2)
            c1.metric("Aleta Inferior", f"{round(lim_bajo)}°", f"{round(p_bajo, 1)} g")
            c2.metric("Aleta Superior", f"{round(lim_alto)}°", f"{round(p_alto, 1)} g")

            # --- GRÁFICO ---
            fig, ax = plt.subplots(figsize=(7,7))
            ax.set_aspect('equal')
            max_v = max(v1, mag_res) * 1.5
            
            # Dibujar sectores (Aletas)
            for i in range(n_aletas):
                ang = i * angulo_sector
                # Ajuste visual: 0° es arriba, Horario hacia derecha, Antihorario hacia izquierda
                dir_plot = 1 if sentido == "Antihorario (CCW)" else -1
                rad_plot = math.radians(90 + ang * dir_plot)
                ax.plot([0, max_v * math.cos(rad_plot)], [0, max_v * math.sin(rad_plot)], 'gray', lw=0.5, ls='--')
                ax.text(max_v * 1.1 * math.cos(rad_plot), max_v * 1.1 * math.sin(rad_plot), f"{int(ang)}°", ha='center')

            # Vector de Vibración (Rojo)
            rad_v = math.radians(90 + ang_vibracion * (1 if sentido == "Antihorario (CCW)" else -1))
            ax.arrow(0, 0, mag_res * math.cos(rad_v), mag_res * math.sin(rad_v), head_width=max_v/20, color='red', label='Vibración')
            
            # Vector de Corrección (Verde)
            rad_c = math.radians(90 + ang_correccion * (1 if sentido == "Antihorario (CCW)" else -1))
            ax.arrow(0, 0, mag_res * math.cos(rad_c), mag_res * math.sin(rad_c), head_width=max_v/20, color='green', label='Corrección')

            ax.set_xlim(-max_v*1.3, max_v*1.3); ax.set_ylim(-max_v*1.3, max_v*1.3)
            plt.legend()
            st.pyplot(fig)
    else:
        st.error("Por favor, ingresa valores válidos de vibración.")
Usa el código con precaución.

¿Qué hace este código nuevo?
Parámetro n_aletas: Calcula automáticamente el ángulo entre cada una (ej. 360/5 = 72°, 360/4 = 90°).
Lógica de Sentido: Si eliges Horario, el programa invierte la dirección de los ángulos para que el gráfico y el cálculo coincidan con lo que ves físicamente en el rotor.
Repartición de Pesos: Si el punto de equilibrio cae entre la aleta 1 (0°) y la aleta 2 (72°), te dice exactamente cuántos gramos poner en cada una usando la ley de senos.

                   
