import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
import base64
from PIL import Image

st.set_page_config(
    page_title="Seguimiento de Presupuesto",
    page_icon="💰",
    layout="centered"
)

# LOGO DE LA EMPRESA
logo_url = "https://i.postimg.cc/66Hm1Vpz/Captura-de-pantalla-2026-05-12-212819.png"

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(logo_url, width=150)

st.title("💰 Seguimiento de Presupuesto")
st.markdown("---")

partidas_presupuesto = [
    "01 - Trazado y marcado",
    "02 - Rozas en paredes y techos",
    "03 - Montaje de soportes",
    "04 - Colocación tubos y conductos",
    "05 - Tendido de cables",
    "06 - Identificación y etiquetado",
    "07 - Conexionado de cables",
    "08 - Instalación de mecanismos",
    "09 - Cuadro eléctrico - Carril DIN",
    "10 - Cuadro eléctrico - Cableado interno",
    "11 - Equipos domóticos",
    "12 - Sensores/actuadores",
    "13 - Pruebas de continuidad",
    "14 - Pruebas de aislamiento",
    "15 - Verificación de tierras",
    "16 - Programación automatismo",
    "17 - Pruebas de funcionamiento",
    "99 - Otros"
]

if 'df_presupuesto' not in st.session_state:
    st.session_state.df_presupuesto = pd.DataFrame(columns=[
        "Numero_Albaran",
        "Fecha",
        "Trabajador",
        "Partida",
        "Gasto_Euros",
        "Comentarios",
        "Hora_Registro",
        "Foto_Nombre"
    ])

if 'fotos_guardadas' not in st.session_state:
    st.session_state.fotos_guardadas = {}

st.subheader("➕ Nuevo Registro de Gasto")

with st.form("form_presupuesto"):
    col1, col2 = st.columns(2)
    
    with col1:
        num_albaran = st.text_input("📄 Número de albarán", placeholder="Ej: ALB-2024-001")
        fecha = st.date_input("📅 Fecha", datetime.now(), format="DD/MM/YYYY")
        trabajador = st.text_input("👷 Trabajador", placeholder="Ej: Pedro Martínez")
    
    with col2:
        partida = st.selectbox("📂 Partida presupuestaria", partidas_presupuesto)
        gasto = st.number_input("💶 Gasto (€)", min_value=0.0, step=10.0, format="%.2f")
    
    comentarios = st.text_area("📝 Comentarios", placeholder="Detalles adicionales del gasto...")
    
    st.markdown("📸 **Adjuntar foto del albarán (opcional)**")
    foto_subida = st.file_uploader("Seleccionar imagen", type=["jpg", "jpeg", "png"])
    
    submitted = st.form_submit_button("💾 Guardar Registro", use_container_width=True)
    
    if submitted:
        errores = []
        if not num_albaran:
            errores.append("Número de albarán")
        if not trabajador:
            errores.append("Nombre del trabajador")
        if gasto <= 0:
            errores.append("Gasto debe ser mayor que 0")
        
        if errores:
            st.error(f"❌ Faltan campos obligatorios: {', '.join(errores)}")
        else:
            nombre_foto = ""
            if foto_subida is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_foto = f"albaran_{num_albaran}_{timestamp}.jpg"
                st.session_state.fotos_guardadas[nombre_foto] = foto_subida.getvalue()
            
            hora_espana = (datetime.now() + timedelta(hours=2)).strftime("%H:%M:%S")
            
            nuevo_registro = pd.DataFrame([{
                "Numero_Albaran": num_albaran,
                "Fecha": fecha.strftime("%d/%m/%Y"),
                "Trabajador": trabajador,
                "Partida": partida,
                "Gasto_Euros": gasto,
                "Comentarios": comentarios,
                "Hora_Registro": hora_espana,
                "Foto_Nombre": nombre_foto
            }])
            st.session_state.df_presupuesto = pd.concat([st.session_state.df_presupuesto, nuevo_registro], ignore_index=True)
            st.success(f"✅ Registro guardado correctamente - Albarán: {num_albaran} - Gasto: {gasto}€")
            st.balloons()

st.markdown("---")

st.subheader("📊 Registros de Gastos")

if not st.session_state.df_presupuesto.empty:
    df_mostrar = st.session_state.df_presupuesto.copy()
    df_mostrar = df_mostrar.drop(columns=["Foto_Nombre"], errors='ignore')
    st.dataframe(df_mostrar, use_container_width=True, height=300)
    
    st.subheader("📈 Resumen del Presupuesto")
    total_gastado = st.session_state.df_presupuesto["Gasto_Euros"].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Gastado", f"{total_gastado:,.2f} €")
    with col2:
        st.metric("Nº Albaranes", len(st.session_state.df_presupuesto))
    with col3:
        st.metric("Partidas utilizadas", st.session_state.df_presupuesto["Partida"].nunique())
    
    gastos_partida = st.session_state.df_presupuesto.groupby("Partida")["Gasto_Euros"].sum().sort_values(ascending=False)
    st.bar_chart(gastos_partida.head(10))
    
    if st.session_state.fotos_guardadas:
        with st.expander("📸 Ver fotos de albaranes guardadas"):
            for nombre_foto, datos_foto in list(st.session_state.fotos_guardadas.items()):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.image(datos_foto, caption=nombre_foto, width=200)
                with col2:
                    if st.button(f"🗑️ Eliminar {nombre_foto}", key=f"del_{nombre_foto}"):
                        del st.session_state.fotos_guardadas[nombre_foto]
                        st.rerun()
else:
    st.info("ℹ️ No hay registros aún. Complete el formulario para comenzar.")

st.markdown("---")

def generar_excel():
    if st.session_state.df_presupuesto.empty:
        return None
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export = st.session_state.df_presupuesto.drop(columns=["Foto_Nombre"], errors='ignore')
        df_export.to_excel(writer, sheet_name='Seguimiento_Presupuesto', index=False)
        
        worksheet = writer.sheets['Seguimiento_Presupuesto']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 40)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output

st.subheader("💾 Exportar Datos")

col1, col2, col3 = st.columns(3)

with col1:
    if not st.session_state.df_presupuesto.empty:
        excel_data = generar_excel()
        if excel_data:
            b64 = base64.b64encode(excel_data.getvalue()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="presupuesto_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx">📥 Descargar Excel</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No hay datos")

with col2:
    if st.button("🗑️ Limpiar registros", use_container_width=True):
        st.session_state.df_presupuesto = pd.DataFrame(columns=[
            "Numero_Albaran", "Fecha", "Trabajador", "Partida", 
            "Gasto_Euros", "Comentarios", "Hora_Registro", "Foto_Nombre"
        ])
        st.session_state.fotos_guardadas = {}
        st.rerun()

st.markdown("---")

st.subheader("📧 Enviar por Correo Electrónico")

if 'email_config_presupuesto' not in st.session_state:
    st.session_state.email_config_presupuesto = {
        'destinatario': 'profesora@email.com',
        'remitente': 'tu_email@gmail.com',
        'password': ''
    }

with st.expander("⚙️ Configurar envío de correo"):
    destinatario = st.text_input("📧 Correo del destinatario", 
                                 value=st.session_state.email_config_presupuesto['destinatario'])
    remitente = st.text_input("📤 Correo remitente (tu correo)", 
                              value=st.session_state.email_config_presupuesto['remitente'])
    password = st.text_input("🔑 Contraseña de aplicación (Gmail)", 
                             type="password",
                             value=st.session_state.email_config_presupuesto.get('password', ''))
    
    st.caption("Para Gmail, usa una [Contraseña de aplicación](https://myaccount.google.com/apppasswords)")
    
    if st.button("💾 Guardar configuración"):
        st.session_state.email_config_presupuesto['destinatario'] = destinatario
        st.session_state.email_config_presupuesto['remitente'] = remitente
        st.session_state.email_config_presupuesto['password'] = password
        st.success("Configuración guardada")

def enviar_email(destinatario, remitente, password, archivo_excel):
    try:
        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = destinatario
        msg['Subject'] = f"Informe Presupuesto Obra - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        total = st.session_state.df_presupuesto["Gasto_Euros"].sum() if not st.session_state.df_presupuesto.empty else 0
        
        cuerpo = f"""
        Informe de seguimiento de PRESUPUESTO generado desde la app.
        
        Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        Total de registros: {len(st.session_state.df_presupuesto)}
        GASTO TOTAL: {total:,.2f} €
        
        Adjunto encontrará el archivo Excel con todos los registros.
        {'Las fotos de los albaranes se adjuntan por separado.' if st.session_state.fotos_guardadas else ''}
        
        ---
        Generado automáticamente por App Seguimiento de Presupuesto
        """
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
        
        if archivo_excel:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(archivo_excel.getvalue())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 
                           f'attachment; filename=presupuesto_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
            msg.attach(part)
        
        if st.session_state.fotos_guardadas:
            for nombre_foto, datos_foto in st.session_state.fotos_guardadas.items():
                part_img = MIMEBase('application', 'octet-stream')
                part_img.set_payload(datos_foto)
                encoders.encode_base64(part_img)
                part_img.add_header('Content-Disposition', f'attachment; filename={nombre_foto}')
                msg.attach(part_img)
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, password)
            server.send_message(msg)
        
        return True, f"Correo enviado con {len(st.session_state.fotos_guardadas)} fotos adjuntas"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

col1, col2 = st.columns([2, 1])
with col1:
    if st.button("📧 Enviar Excel y fotos por correo", use_container_width=True, type="primary"):
        if st.session_state.df_presupuesto.empty:
            st.warning("⚠️ No hay registros para enviar")
        elif not st.session_state.email_config_presupuesto.get('password'):
            st.error("❌ Configure la contraseña en el panel de configuración")
        else:
            with st.spinner("Enviando correo..."):
                excel_data = generar_excel()
                if excel_data:
                    success, message = enviar_email(
                        st.session_state.email_config_presupuesto['destinatario'],
                        st.session_state.email_config_presupuesto['remitente'],
                        st.session_state.email_config_presupuesto['password'],
                        excel_data
                    )
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("No se pudo generar el archivo")

with col2:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.rerun()

st.markdown("---")
st.caption("""
**ℹ️ Nota importante:** 
- Los datos se guardan solo mientras la app está activa (~2-3 horas)
- Descarga el Excel periódicamente para conservar los registros
- Las fotos se adjuntan automáticamente al enviar por correo
""")

st.markdown("---")
st.markdown("💰 **App Seguimiento de Presupuesto** | Desarrollado para Fundación Masaveu")
