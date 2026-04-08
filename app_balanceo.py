import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Historial de Gastos", layout="centered")

# Inicializar el historial en la memoria de la sesión si no existe
if 'historial_datos' not in st.session_state:
    st.session_state['historial_datos'] = pd.DataFrame(columns=[
        'Fecha Registro', 'Ingresos', 'Vivienda', 'Alimentación', 
        'Transporte', 'Servicios', 'Ocio', 'Otros', 'Saldo Mensual'
    ])

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>💰 Control Financiero Histórico</h1>", unsafe_allow_html=True)

# --- 1. ENTRADA DE DATOS ---
with st.expander("➕ Registrar Nuevos Datos del Mes", expanded=True):
    fecha_reg = st.date_input("Mes de referencia", datetime.now())
    ingreso = st.number_input("Ingreso Total ($)", min_value=0.0, step=100.0)
    
    c1, c2 = st.columns(2)
    with c1:
        vivienda = st.number_input("Vivienda", min_value=0.0)
        alimentacion = st.number_input("Alimentación", min_value=0.0)
        transporte = st.number_input("Transporte", min_value=0.0)
    with c2:
        servicios = st.number_input("Servicios", min_value=0.0)
        ocio = st.number_input("Ocio", min_value=0.0)
        otros = st.number_input("Otros", min_value=0.0)

    egreso_total = vivienda + alimentacion + transporte + servicios + ocio + otros
    saldo = ingreso - egreso_total

    if st.button("📥 GUARDAR EN HISTORIAL", use_container_width=True):
        # Crear nueva fila
        nueva_fila = {
            'Fecha Registro': fecha_reg.strftime('%Y-%m'),
            'Ingresos': ingreso,
            'Vivienda': vivienda,
            'Alimentación': alimentacion,
            'Transporte': transporte,
            'Servicios': servicios,
            'Ocio': ocio,
            'Otros': otros,
            'Saldo Mensual': saldo
        }
        # Añadir al historial
        st.session_state['historial_datos'] = pd.concat([st.session_state['historial_datos'], pd.DataFrame([nueva_fila])], ignore_index=True)
        st.success("✅ Datos guardados en el historial local.")

# --- 2. VISUALIZACIÓN DEL HISTORIAL ---
if not st.session_state['historial_datos'].empty:
    st.divider()
    st.subheader("📜 Historial Acumulado")
    
    # Mostrar la tabla
    st.dataframe(st.session_state['historial_datos'], use_container_width=True)

    # --- 3. DESCARGA EXCEL ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Mi_Historial')
        return output.getvalue()

    excel_data = to_excel(st.session_state['historial_datos'])
    
    st.download_button(
        label="📥 DESCARGAR HISTORIAL COMPLETO (EXCEL)",
        data=excel_data,
        file_name=f"Historial_Financiero_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # Gráfico de tendencia de ingresos vs gastos
    st.subheader("📈 Tendencia")
    fig, ax = plt.subplots()
    df_h = st.session_state['historial_datos']
    ax.plot(df_h['Fecha Registro'], df_h['Ingresos'], label='Ingresos', marker='o')
    ax.plot(df_h['Fecha Registro'], df_h['Saldo Mensual'], label='Saldo (Ahorro)', marker='s')
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(fig)

else:
    st.info("Aún no hay datos guardados. Ingresa los valores arriba y dale a 'Guardar'.")

# Botón para borrar todo
if st.sidebar.button("🗑️ Borrar Historial"):
    st.session_state['historial_datos'] = pd.DataFrame(columns=st.session_state['historial_datos'].columns)
    st.rerun()

