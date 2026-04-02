import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io

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

# --- INTERFAZ ---
st.title("⚖️ Balanceo Universal con Circunferencias")

with st.sidebar:
    st.header("⚙️ Configuración")
    n_aletas = st.number_input("Número de Aletas", min_value=2, max_value=24, value=5)
    sentido = st.radio("Sentido de Giro", ["Antihorario (CCW)", "Horario (CW)"])
    v1 = st.number_input("Vibración Inicial (V1)", min_value=0.01, step=0.1, format="%.2f")
    angulo_paso = 360 / n_aletas

# --- ENTRADA DE DATOS ---
col1, col2, col3 = st.columns(3)
meds = []
for i, col in enumerate([col1, col2, col3], 2):
    with col:
        st.subheader(f"Prueba {i}")
        v = st.number_input(f"V{i} (mm/s)", key=f"v{i}", value=0.0)
        p = st.number_input(f"Peso {i} (g)", key=f"p{i}", value=0.0)
        # Sugerir ángulo basado en aletas (0, 1, 2... sectores)
        a = st.number_input(f"Ángulo {i} (°)", value=float((i-2)*angulo_paso), key=f"a{i}")
        meds.append({'v': v, 'p': p, 'a': a})

if st.button("⚖️ GENERAR GRÁFICO Y CÁLCULO", type="primary", use_container_width=True):
    if v1 > 0 and all(m['v'] > 0 for m in meds):
        # 1. Definir centros de los círculos (Posición de los pesos de prueba)
        # En el diagrama de balanceo, el centro de cada círculo V_n está a una distancia V1
        # en el ángulo donde se colocó el peso de prueba.
        centros = []
        inv = 1 if sentido == "Antihorario (CCW)" else -1
        
        for m in meds:
            rad = math.radians(90 + (m['a'] * inv)) # 90 para que 0° sea arriba (Eje Y+)
            centros.append((v1 * math.cos(rad), v1 * math.sin(rad)))

        # 2. Intersecciones para el triángulo de error
        # Usamos las coordenadas de los centros y los radios (vibraciones medidas)
        i12 = obtener_interseccion(centros[0][0], centros[0][1], centros[1][0], centros[1][1], meds[0]['v'], meds[1]['v'])
        i23 = obtener_interseccion(centros[1][0], centros[1][1], centros[2][0], centros[2][1], meds[1]['v'], meds[2]['v'])
        i31 = obtener_interseccion(centros[2][0], centros[2][1], centros[0][0], centros[0][1], meds[2]['v'], meds[0]['v'])

        if i12 and i23 and i31:
            # Encontrar el triángulo más pequeño entre todas las intersecciones posibles
            puntos_tri = []
            min_err = float('inf')
            for p1 in i12:
                for p2 in i23:
                    for p3 in i31:
                        err = math.dist(p1, p2) + math.dist(p2, p3) + math.dist(p3, p1)
                        if err < min_err:
                            min_err = err
                            puntos_tri = [p1, p2, p3]

            # 3. Calcular Resultados
            bx = sum(p[0] for p in puntos_tri) / 3
            by = sum(p[1] for p in puntos_tri) / 3
            
            mag_res = math.sqrt(bx**2 + by**2)
            # Ángulo de la vibración resultante (corregido por el desfase de 90°)
            ang_vibracion = (math.degrees(math.atan2(by, bx)) - 90) * inv
            ang_vibracion = (360 - ang_vibracion) % 360 if sentido == "Horario (CW)" else (ang_vibracion + 360) % 360
            
            # Peso de corrección (Oposición)
            peso_total = (v1 / mag_res) * (sum(m['p'] for m in meds)/3)
            ang_corr = (ang_vibracion + 180) % 360

            # --- GRÁFICO ---
            fig, ax = plt.subplots(figsize=(8,8))
            ax.set_aspect('equal')
            lim = max(v1 + max(m['v'] for m in meds), mag_res) * 1.2
            
            # Dibujar Aletas y Grados
            for i in range(n_aletas):
                ang_r = math.radians(90 + (i * angulo_paso * inv))
                ax.plot([0, lim*math.cos(ang_r)], [0, lim*math.sin(ang_r)], color='gray', lw=0.8, ls='--')
                ax.text(lim*1.05*math.cos(ang_r), lim*1.05*math.sin(ang_r), f"{int(i*angulo_paso)}°", ha='center')

            # DIBUJAR CIRCUNFERENCIAS
            colores = ['#FF5733', '#33FF57', '#3357FF']
            for i in range(3):
                circle = plt.Circle(centros[i], meds[i]['v'], fill=False, color=colores[i], label=f"Círculo V{i+2}", lw=1.5, alpha=0.7)
                ax.add_patch(circle)
                ax.plot(centros[i][0], centros[i][1], 'o', color=colores[i]) # Centro del círculo

            # Dibujar Triángulo de Error
            tri = plt.Polygon(puntos_tri, color='yellow', alpha=0.4, label='Zona de Error')
            ax.add_patch(tri)
            
            # Vector Resultante
            ax.quiver(0, 0, bx, by, angles='xy', scale_units='xy', scale=1, color='red', label='Vibración Res.')

            ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
            ax.axhline(0, color='black', lw=1); ax.axvline(0, color='black', lw=1)
            plt.legend(loc='upper right', fontsize='small')
            st.pyplot(fig)

            # --- MÉTRICAS ---
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Peso Corrección", f"{round(peso_total, 2)} g")
            c2.metric("Ángulo Exacto", f"{round(ang_corr, 1)}°")
            c3.metric("Vibración Final Est.", f"{round(mag_res, 2)} mm/s")
    else:
        st.warning("⚠️ Asegúrate de que todos los valores de vibración sean mayores a 0.")
