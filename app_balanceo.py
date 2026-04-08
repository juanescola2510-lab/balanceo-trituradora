import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Optimizador de Gastos", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>💰 Asistente de Optimización Financiera</h1>", unsafe_allow_html=True)

# --- 1. ENTRADA DE DATOS (INGRESOS) ---
st.subheader("📥 Tus Ingresos")
ingreso_total = st.number_input("Ingreso Mensual Total ($)", min_value=0.0, step=100.0, value=0.0)

# --- 2. REGISTRO DE EGRESOS (EGRESOS) ---
st.subheader("💸 Tus Gastos Mensuales")

col1, col2 = st.columns(2)
with col1:
    vivienda = st.number_input("Vivienda (Renta/Hipoteca)", min_value=0.0, step=10.0)
    alimentacion = st.number_input("Alimentación", min_value=0.0, step=10.0)
    transporte = st.number_input("Transporte", min_value=0.0, step=10.0)
with col2:
    servicios = st.number_input("Servicios (Luz, Agua, Internet)", min_value=0.0, step=10.0)
    ocio = st.number_input("Ocio y Entretenimiento", min_value=0.0, step=10.0)
    otros = st.number_input("Otros Gastos", min_value=0.0, step=10.0)

egreso_total = vivienda + alimentacion + transporte + servicios + ocio + otros
saldo = ingreso_total - egreso_total

# --- 3. ANÁLISIS Y GRÁFICOS ---
if st.button("📊 ANALIZAR MIS FINANZAS", type="primary", use_container_width=True):
    if ingreso_total == 0:
        st.warning("Por favor, ingresa tu nivel de ingresos para empezar.")
    else:
        st.divider()
        
        # Métricas principales
        c1, c2, c3 = st.columns(3)
        c1.metric("Egresos Totales", f"${egreso_total:,.2f}")
        c2.metric("Saldo Disponible", f"${saldo:,.2f}", delta=f"{saldo:,.2f}")
        
        porcentaje_ahorro = (saldo / ingreso_total) * 100 if ingreso_total > 0 else 0
        c3.metric("Capacidad de Ahorro", f"{porcentaje_ahorro:.1f}%")

        # Gráfico de distribución
        datos = {
            'Categoría': ['Vivienda', 'Alimentación', 'Transporte', 'Servicios', 'Ocio', 'Otros'],
            'Monto': [vivienda, alimentacion, transporte, servicios, ocio, otros]
        }
        df = pd.DataFrame(datos)
        df = df[df['Monto'] > 0] # Solo mostrar categorías con gasto

        if not df.empty:
            fig, ax = plt.subplots()
            ax.pie(df['Monto'], labels=df['Categoría'], autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
            ax.axis('equal')
            st.pyplot(fig)

        # --- 4. CONSEJOS DE OPTIMIZACIÓN ---
        st.subheader("💡 Consejos de Optimización")
        
        consejos = []

        # Regla 50/30/20
        if ocio > (ingreso_total * 0.30):
            consejos.append("⚠️ **Reduce Ocio:** Estás gastando más del 30% en entretenimiento. Intenta buscar actividades gratuitas o reducir suscripciones.")
        
        if vivienda > (ingreso_total * 0.35):
            consejos.append("⚠️ **Vivienda Alta:** Tus gastos de vivienda superan el 35% de tus ingresos. Considera renegociar servicios o buscar alternativas más económicas.")
            
        if servicios > (transporte * 1.5):
            consejos.append("💡 **Eficiencia Energética:** Tus servicios básicos son altos comparados con otros gastos. Revisa fugas de agua o apaga equipos que no uses.")
        
        if saldo < 0:
            consejos.append("🚨 **ALERTA ROJA:** Tus gastos superan tus ingresos. Es urgente recortar 'Gastos Hormiga' (cafés, snacks, compras impulsivas).")
        elif porcentaje_ahorro < 20:
            consejos.append("📈 **Mejora tu Ahorro:** La meta ideal es el 20%. Intenta automatizar un ahorro del 5% adicional este mes.")
        else:
            consejos.append("🌟 **¡Excelente trabajo!** Estás manteniendo una buena salud financiera. Considera invertir tu excedente.")

        for c in consejos:
            st.info(c)

# --- SIDEBAR: RECURSOS ---
st.sidebar.header("📖 Recursos Útiles")
st.sidebar.markdown("""
- **Regla 50/30/20:**
    - 50% Necesidades.
    - 30% Deseos (Ocio).
    - 20% Ahorro/Deuda.
- **Fondo de Emergencia:** Deberías tener guardado de 3 a 6 meses de tus gastos totales.
""")
