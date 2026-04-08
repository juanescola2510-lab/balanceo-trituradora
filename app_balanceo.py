python
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Optimizador de Gastos", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>💰 Asistente de Optimización Financiera</h1>", unsafe_allow_html=True)

# --- 1. ENTRADA DE DATOS (INGRESOS) ---
st.subheader("📥 Tus Ingresos")
ingreso_total = st.number_input("Ingreso Mensual Total ($)", min_value=0.0, step=100.0, value=0.0)

# --- 2. REGISTRO DE EGRESOS ---
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
if st.button("📊 ANALIZAR Y PREPARAR EXCEL", type="primary", use_container_width=True):
    if ingreso_total == 0 and egreso_total == 0:
        st.warning("Por favor, ingresa tus valores para empezar.")
    else:
        st.divider()
        
        # Métricas principales
        c1, c2, c3 = st.columns(3)
        c1.metric("Egresos Totales", f"${egreso_total:,.2f}")
        c2.metric("Saldo Disponible", f"${saldo:,.2f}")
        porcentaje_ahorro = (saldo / ingreso_total) * 100 if ingreso_total > 0 else 0
        c3.metric("Capacidad de Ahorro", f"{porcentaje_ahorro:.1f}%")

        # Preparar DataFrame para el Excel y Gráfico
        datos_dict = {
            'Categoría': ['Ingreso Total', 'Vivienda', 'Alimentación', 'Transporte', 'Servicios', 'Ocio', 'Otros', 'Saldo Final'],
            'Monto ($)': [ingreso_total, vivienda, alimentacion, transporte, servicios, ocio, otros, saldo]
        }
        df_completo = pd.DataFrame(datos_dict)

        # Mostrar gráfico de gastos
        df_gastos = df_completo[1:-1] # Excluimos ingreso y saldo para el gráfico
        df_plot = df_gastos[df_gastos['Monto ($)'] > 0]
        
        if not df_plot.empty:
            fig, ax = plt.subplots()
            ax.pie(df_plot['Monto ($)'], labels=df_plot['Categoría'], autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)

        # --- FUNCIÓN PARA GENERAR EXCEL ---
        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Resumen_Financiero')
            return output.getvalue()

        excel_data = to_excel(df_completo)

        st.download_button(
            label="📥 DESCARGAR EXCEL DE GASTOS",
            data=excel_data,
            file_name=f"Resumen_Financiero_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # Consejos rápidos
        st.subheader("💡 Consejos de Optimización")
        if saldo < 0:
            st.error("🚨 Tus gastos superan tus ingresos. Prioriza recortar Ocio y Otros Gastos.")
        elif porcentaje_ahorro < 20:
            st.info("📈 Intenta reducir un 10% en Ocio para alcanzar la meta de ahorro del 20%.")
        else:
            st.success("🌟 ¡Excelente salud financiera! Mantén ese nivel de ahorro.")

# Sidebar
st.sidebar.info("Registra tus datos y descarga el reporte en Excel para llevar tu control histórico.")
