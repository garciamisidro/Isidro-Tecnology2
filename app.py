import streamlit as st
import pandas as pd
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control de Presupuesto", layout="centered")
st.title("💰 Seguimiento de Presupuesto y Albaranes")

# --- FORMULARIO DE ENTRADA ---
with st.form("formulario_presupuesto", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        n_albaran = st.text_input("Número de Albarán")
        fecha = st.date_input("Fecha", date.today())
        trabajador = st.text_input("Trabajador")
    
    with col2:
        # Partidas típicas de obra
        partidas = [
            "Materiales Eléctricos", "Mecanismos y Cuadros", 
            "Pequeño Material", "Maquinaria", 
            "Mano de Obra Externa", "Otros Gastos"
        ]
        partida_sel = st.selectbox("Partida del presupuesto:", partidas)
        gasto = st.number_input("Gastos de esta partida (€):", min_value=0.0, step=0.01)
    
    comentarios = st.text_area("Comentarios")
    
    # NOTA EXTRA: Subida de foto del albarán
    foto_albaran = st.file_uploader("Subir foto del albarán (Imagen o PDF)", type=["png", "jpg", "jpeg", "pdf"])
    # También puedes usar st.camera_input("Hacer foto con el móvil") si prefieres usar la cámara directamente.

    enviado = st.form_submit_button("Registrar Albarán")

# --- GESTIÓN DE DATOS (Pandas) ---
if "datos_presupuesto" not in st.session_state:
    st.session_state.datos_presupuesto = pd.DataFrame(
        columns=["Albarán", "Fecha", "Trabajador", "Partida", "Gasto (€)", "Comentarios"]
    )

if enviado:
    nuevo_gasto = {
        "Albarán": n_albaran, 
        "Fecha": fecha, 
        "Trabajador": trabajador, 
        "Partida": partida_sel, 
        "Gasto (€)": gasto, 
        "Comentarios": comentarios
    }
    st.session_state.datos_presupuesto = pd.concat(
        [st.session_state.datos_presupuesto, pd.DataFrame([nuevo_gasto])], 
        ignore_index=True
    )
    st.success(f"Albarán {n_albaran} registrado correctamente.")

# --- VISUALIZACIÓN / DASHBOARD (RA4) ---
if not st.session_state.datos_presupuesto.empty:
    st.divider()
    st.subheader("📊 Resumen de Gastos")
    
    # Cálculo por partida para el Dashboard
    resumen = st.session_state.datos_presupuesto.groupby("Partida")["Gasto (€)"].sum()
    st.bar_chart(resumen)
    
    total_acumulado = st.session_state.datos_presupuesto["Gasto (€)"].sum()
    st.metric("Gasto Total Acumulado", f"{total_acumulado:,.2f} €")
    
    # Mostrar tabla
    st.dataframe(st.session_state.datos_presupuesto)

  # --- 5. EXPORTACIÓN Y ENVÍO POR CORREO ---
    st.divider()
    st.dataframe(st.session_state.datos_obra)
    
    nombre_archivo = "reporte_obra.xlsx"
    st.session_state.datos_obra.to_excel(nombre_archivo, index=False)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        with open(nombre_archivo, "rb") as f:
            st.download_button("📥 Descargar Excel", f, file_name=nombre_archivo)
            
    with col_btn2:
        if st.button("📧 Enviar Reporte por Correo"):
            try:
                # Datos desde Secrets
                u = st.secrets["email"]["user"]
                p = st.secrets["email"]["pass"]
                prof = st.secrets["email"]["profe"]

                msg = MIMEMultipart()
                msg['From'], msg['To'], msg['Subject'] = u, f"{prof}, {u}", "Reporte Seguimiento de Obra"
                msg.attach(MIMEText("Se adjunta el archivo Excel con el seguimiento de obra.", 'plain'))

                with open(nombre_archivo, "rb") as adj:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(adj.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename={nombre_archivo}")
                    msg.attach(part)

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(u, p)
                server.send_message(msg)
                server.quit()
                st.success("✅ Correo enviado con éxito.")
            except Exception as e:
                st.error(f"Error: {e}. Revisa tus Secrets.")
else:
    st.info("👋 Registra una tarea para activar el análisis y las opciones de exportación.")
# --- MODIFICACIÓN 1: ALERTAS DE DESVÍO Y CONTROL DE LÍMITES ---

if not st.session_state.datos_presupuesto.empty:
    st.divider()
    st.subheader("⚠️ Control de Límites Presupuestarios")

    # 1. Definimos los límites (puedes ajustar estos importes según la obra)
    limites_presupuesto = {
        "Materiales Eléctricos": 2000.0,
        "Mecanismos y Cuadros": 1500.0,
        "Pequeño Material": 500.0,
        "Maquinaria": 1200.0,
        "Mano de Obra Externa": 3000.0,
        "Otros Gastos": 300.0
    }

    # 2. Agrupamos los gastos actuales por partida
    gastos_por_partida = st.session_state.datos_presupuesto.groupby("Partida")["Gasto (€)"].sum()

    # 3. Creamos columnas para mostrar las alertas de forma visual
    cols = st.columns(2)
    for i, (partida, limite) in enumerate(limites_presupuesto.items()):
        gasto_actual = gastos_por_partida.get(partida, 0.0)
        porcentaje = (gasto_actual / limite)
        
        # Seleccionamos la columna (izq o der)
        with cols[i % 2]:
            st.write(f"**{partida}**")
            
            # Lógica de alertas (IA de control)
            if porcentaje >= 1.0:
                st.error(f"¡PRESUPUESTO AGOTADO! ({gasto_actual:.2f}€ / {limite}€)")
                progreso_color = "red"
            elif porcentaje >= 0.8:
                st.warning(f"Atención: 80% alcanzado ({gasto_actual:.2f}€ / {limite}€)")
            else:
                st.success(f"Presupuesto OK ({gasto_actual:.2f}€ / {limite}€)")
            
            # Barra de progreso visual
            st.progress(min(porcentaje, 1.0))
