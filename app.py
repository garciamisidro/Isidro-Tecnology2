import streamlit as st
import pandas as pd
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- 1. ESTO EVITA EL ERROR DE TU IMAGEN ---
# Inicializamos el contenedor de datos nada más empezar
if "datos_obra" not in st.session_state:
    st.session_state.datos_obra = pd.DataFrame(columns=["Fecha", "Trabajador", "Tarea", "Estado"])

st.title("🏗️ Seguimiento de Obra")

# --- 2. FORMULARIO ---
with st.form("registro_obra", clear_on_submit=True):
    trabajador = st.text_input("Nombre del Trabajador")
    
    tareas = ["Trazado", "Rozas", "Tendido de cables", "Conexionado", "Pruebas"] # (Pon tu lista completa aquí)
    tarea_sel = st.selectbox("Tarea:", tareas)
    
    estados = ["25%", "50%", "75%", "OK"]
    estado_sel = st.selectbox("Estado:", estados)
    
    boton = st.form_submit_button("Registrar")

if boton and trabajador:
    nuevo = {"Fecha": date.today(), "Trabajador": trabajador, "Tarea": tarea_sel, "Estado": estado_sel}
    st.session_state.datos_obra = pd.concat([st.session_state.datos_obra, pd.DataFrame([nuevo])], ignore_index=True)
    st.success("¡Registrado!")

# --- 3. MOSTRAR TABLA Y EXPORTAR (Solo si hay datos) ---
if not st.session_state.datos_obra.empty:
    st.subheader("📋 Registros")
    st.dataframe(st.session_state.datos_obra) # Ahora ya no fallará
    
    # Generar Excel
    nombre_archivo = "reporte.xlsx"
    st.session_state.datos_obra.to_excel(nombre_archivo, index=False)
    
    with open(nombre_archivo, "rb") as f:
        st.download_button("📥 Descargar Excel", f, file_name=nombre_archivo)
else:
    st.info("Escribe algo y pulsa Registrar para empezar.")
