import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

# Configuración de la interfaz
st.set_page_config(page_title="Balanceo Trituradora 405CR01", layout="centered")

# --- 1. LOGO ---
try:
    imagen = Image.open("logo.jpeg") 
    st.image(imagen, width=150) 
except:
    st.info("ℹ️ Para ver tu logo, guarda una imagen como 'logo.png' en la misma carpeta.")

st.title("⚖️ Balanceo: Trituradora 405CR01")
st.write("Sistema: 0° Norte (Eje Y+) | Sentido: Antihorario")

# --- FUNCIONES MATEMÁTICAS ---
def obtener_interseccion(c1x, c1y, c2x, c2y, r1, r2):
    d = math.sqrt((c2x - c1x)**2 + (c2y - c1y)**2)
    if d > (r1 + r2) or d < abs(r1 - r2) or d == 0:
        return []
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(max(0, r1**2 - a**2))
    x0 = c1x + a * (c2x - c1x) / d
    y0 = c1y + a * (c2y - c1y) / d
    return [
        (x0 + h * (c2y - c1y) / d, y0 - h * (c2x - c1x) / d),
        (x0 - h * (c2y - c1y) / d, y0 + h * (c2x - c1x) / d)
    ]

def calcular_area(p1, p2, p3):
    return 0.5 * abs(p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1]))

# --- ENTRADA DE DATOS ---
with st.sidebar:
    st.header("📥 Datos de Entrada")
    v1 = st.number_input("Vibración Inicial (V1)", value=3.0, step=0.1)
    st.divider()
    meds = []
    for i in range(2, 5):
        st.subheader(f"Medición {i}")
        v = st.number_input(f"Vibración (V{i})", value=4.0, key=f"v{i}")
        p = st.number_input(f"Peso Prueba (P{i})", value=10.0, key=f"p{i}")
        a = st.number_input(f"Ángulo (°)", value=(i-2)*120.0, key=f"a{i}")
        meds.append({'v': v, 'p': p, 'a': a})

if st.button("CALCULAR Y GENERAR VECTOR", type="primary"):
    # Centros: 0° Norte (Y+), Antihorario (X=-sen, Y=cos)
    centros = []
    for m in meds:
        rad = math.radians(m['a'])
        centros.append((-v1 * math.sin(rad), v1 * math.cos(rad)))

    # Intersecciones
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

        # Baricentro
        bx = sum(p[0] for p in mejor_tri) / 3
        by = sum(p[1] for p in mejor_tri) / 3
        mag_res = math.sqrt(bx**2 + by**2)
        ang_res = (math.degrees(math.atan2(-bx, by)) + 360) % 360
        
        # Peso Total (V1/Vres * P_promedio)
        p_prueba_avg = sum(m['p'] for m in meds) / 3
        peso_total = (v1 / mag_res) * p_prueba_avg if mag_res != 0 else 0
        
        # Eyectores (Corrección a 180° del baricentro)
        ang_corr = (ang_res + 180) % 360 
        sector = 72
        lim_bajo = math.floor(ang_corr / sector) * sector
        lim_alto = lim_bajo + sector
        
        # --- GRÁFICO ---
        fig, ax = plt.subplots(figsize=(8,8))
        
        # Dibujar Círculos
        for i in range(3):
            c = plt.Circle(centros[i], meds[i]['v'], fill=False, color='blue', alpha=0.2)
            ax.add_patch(c)
        
        # Área mínima
        poly = plt.Polygon(mejor_tri, color='yellow', alpha=0.4, label='Área Mínima')
        ax.add_patch(poly)
        
        # VECTOR (Flecha Roja)
        ax.annotate('', xy=(bx, by), xytext=(0, 0),
                    arrowprops=dict(facecolor='red', edgecolor='red', headwidth=12, headlength=12, width=2.5))
        
        # ETIQUETA DEL VECTOR (Texto junto a la flecha)
        ax.text(bx, by + 0.5, f"V: {round(mag_res,2)}\n{round(ang_res,1)}°", 
                color='red', fontweight='bold', fontsize=10, ha='center',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

        # Eyectores y límites automáticos
        lim_max = max([m['v'] + v1 for m in meds]) * 1.2
        for e in range(6):
            ang_e = math.radians(e * 72)
            ex, ey = -lim_max * math.sin(ang_e), lim_max * math.cos(ang_e)
            ax.plot([0, ex], [0, ey], 'gray', lw=0.8, ls='--')
            ax.text(ex*0.9, ey*0.9, f"{e*72}°", ha='center', fontsize=9, fontweight='bold')

        ax.set_aspect('equal')
        ax.set_xlim(-lim_max, lim_max)
        ax.set_ylim(-lim_max, lim_max)
        ax.grid(True, linestyle=':', alpha=0.5)
        

        st.pyplot(fig)

        # --- RESULTADOS FINALES Y DISTRIBUCIÓN ---
        st.divider()
        st.subheader("📋 Resumen de Corrección")
        
        # --- 1. CÁLCULO DE ÁNGULO DE CORRECCIÓN Y PESOS ---
        
        # Eliminamos el +180 para que la corrección sea en el mismo punto de la vibración
        ang_corr = ang_res  
        
        sector = 72
        # Determinamos el límite inferior y superior del sector de 72°
        lim_bajo = math.floor(ang_corr / sector) * sector
        lim_alto = lim_bajo + sector
        
        # Descomposición por Regla de Senos (Paralelogramo)
        rad_total = math.radians(sector)
        rad_opuesto_bajo = math.radians(lim_alto - ang_corr)
        rad_opuesto_alto = math.radians(ang_corr - lim_bajo)
        
        p_bajo = peso_total * (math.sin(rad_opuesto_bajo) / math.sin(rad_total))
        p_alto = peso_total * (math.sin(rad_opuesto_alto) / math.sin(rad_total))

        # --- 2. MÉTRICAS PRINCIPALES ---
        m1, m2 = st.columns(2)
        m1.metric("Vibración Resultante", round(mag_res, 3))
        m2.metric("Peso Total Necesario", f"{round(peso_total, 2)} g")

       # --- 3. LÓGICA DE VISUALIZACIÓN (MAYOR VS MENOR) ---
        st.write(f"### 🚀 Distribución en Eyectores ({lim_bajo}° - {lim_alto}°)")
        col_res1, col_res2 = st.columns(2)
        
        if p_bajo >= p_alto:
            # Caso donde el peso bajo (lim_bajo) es el mayor
            col_res1.metric(f"⭐ Eyector {lim_bajo}° (Mayor)", f"{round(p_bajo, 2)} g")
            col_res2.metric(f"Eyector {lim_alto}° (Menor)", f"{round(p_alto, 2)} g")
            
            st.success(f"✅ **Instrucción:** Poner el peso mayor ({round(p_bajo, 2)}g) en el ángulo {lim_bajo}°, y poner el peso menor ({round(p_alto, 2)}g) en el ángulo {lim_alto}°.")
        else:
            # Caso donde el peso alto (lim_alto) es el mayor
            col_res1.metric(f"⭐ Eyector {lim_alto}° (Mayor)", f"{round(p_alto, 2)} g")
            col_res2.metric(f"Eyector {lim_bajo}° (Menor)", f"{round(p_bajo, 2)} g")
            
            st.success(f"✅ **Instrucción:** Poner el peso mayor ({round(p_alto, 2)}g) en el ángulo {lim_alto}°, y poner el peso menor ({round(p_bajo, 2)}g) en el ángulo {lim_bajo}°.")


# El botón de limpiar debe ir al final de todo el archivo, pegado al borde izquierdo
if st.sidebar.button("Limpiar Pantalla", key="btn_limpiar_total"):
    # Borra los datos de la sesión y reinicia la app
    st.cache_data.clear() 
    st.rerun()