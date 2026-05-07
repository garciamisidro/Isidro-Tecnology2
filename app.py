import streamlit as st
import pandas as pd
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="Control de Presupuesto PRO", layout="wide")

# Inicializar el estado de la sesión para evitar errores de "AttributeError"
if "datos_presupuesto" not in st.session_state:
    st.session_state.datos_presupuesto = pd.DataFrame(
        columns=["Albarán", "Fecha", "Trabajador", "Partida", "Gasto (€)", "Comentarios"]
    )

st.title("💰 Gestión de Presupuesto y Albaranes")

# --- 2. FORMULARIO DE ENTRADA CON EXTRAS ---
with st.form("form_presupuesto", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        n_albaran = st.text_input("Número de Albarán")
        fecha = st.date_input("Fecha", date.today())
        trabajador = st.text_input("Trabajador responsable")
    
    with col2:
        partidas = ["Materiales Eléctricos", "Mecanismos", "Pequeño Material", "Maquinaria", "Mano de Obra", "Otros"]
        partida_sel = st.selectbox("Partida asociada:", partidas)
        gasto = st.number_input("Gastos del albarán (€):", min_value=0.0, step=0.1)
    
    comentarios = st.text_area("Comentarios adicionales")
    
    # EXTRA NOTA: Subida de foto
    foto = st.file_uploader("Subir foto del albarán", type=["jpg", "png", "pdf"])
    
    enviado = st.form_submit_button("Registrar Gasto")

# --- 3. LÓGICA DE GUARDADO ---
if enviado:
    if n_albaran and trabajador and gasto > 0:
        nuevo_gasto = {
            "Albarán": n_albaran, "Fecha": fecha, "Trabajador": trabajador,
            "Partida": partida_sel, "Gasto (€)": gasto, "Comentarios": comentarios
        }
        st.session_state.datos_presupuesto = pd.concat(
            [st.session_state.datos_presupuesto, pd.DataFrame([nuevo_gasto])], 
            ignore_index=True
        )
        st.success(f"✅ Albarán {n_albaran} registrado.")
    else:
        st.warning("⚠️ Rellena el Albarán, el Trabajador y el Gasto.")

# --- 4. DASHBOARD DE CONTROL (EXTRA MODIFICACIÓN 1) ---
if not st.session_state.datos_presupuesto.empty:
    st.divider()
    st.subheader("📊 Análisis de Gastos y Alertas")

    # Definición de límites para las alertas
    limites = {"Materiales Eléctricos": 1000, "Mecanismos": 800, "Pequeño Material": 200, 
               "Maquinaria": 500, "Mano de Obra": 1500, "Otros": 100}

    gastos_actuales = st.session_state.datos_presupuesto.groupby("Partida")["Gasto (€)"].sum()

    col_a, col_b = st.columns(2)
    
    with col_a:
        for p, limite in limites.items():
            actual = gastos_actuales.get(p, 0.0)
            porcentaje = min(actual / limite, 1.0)
            st.write(f"**{p}** ({actual}€ / {limite}€)")
            if actual >= limite:
                st.error("Límite superado")
            elif actual >= limite * 0.8:
                st.warning("Cerca del límite (80%)")
            st.progress(porcentaje)

    with col_b:
        # Predicción IA Sencilla
        total = st.session_state.datos_presupuesto["Gasto (€)"].sum()
        dias = (date.today() - st.session_state.datos_presupuesto["Fecha"].min()).days + 1
        diario = total / dias
        st.metric("Gasto Total Acumulado", f"{total:.2f} €")
        st.metric("Media Diaria", f"{diario:.2f} €")
        st.info(f"💡 Proyección: A este ritmo, el gasto mensual será de {(diario * 30):.2f} €")

    # --- 5. EXPORTACIÓN Y ENVÍO ---
    st.divider()
    st.dataframe(st.session_state.datos_presupuesto)
    
    archivo = "reporte_presupuesto.xlsx"
    st.session_state.datos_presupuesto.to_excel(archivo, index=False)
    
    c1, c2 = st.columns(2)
    with c1:
        with open(archivo, "rb") as f:
            st.download_button("📥 Descargar Excel", f, file_name=archivo)
    
    with c2:
        if st.button("📧 Enviar a Contabilidad"):
            try:
                u, p, prof = st.secrets["email"]["user"], st.secrets["email"]["pass"], st.secrets["email"]["profe"]
                msg = MIMEMultipart()
                msg['From'], msg['To'], msg['Subject'] = u, f"{prof}, {u}", "Reporte de Presupuesto"
                msg.attach(MIMEText("Adjunto reporte de gastos por albarán.", 'plain'))
                
                with open(archivo, "rb") as adj:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(adj.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename={archivo}")
                    msg.attach(part)
                
                s = smtplib.SMTP('smtp.gmail.com', 587)
                s.starttls()
                s.login(u, p)
                s.send_message(msg)
                s.quit()
                st.success("✅ Correo enviado.")
            except Exception as e:
                st.error(f"Error de configuración: {e}. Revisa tus Secrets.")
else:
    st.info("👋 Registra tu primer albarán para ver el análisis de presupuesto.")
