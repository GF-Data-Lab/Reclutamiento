import os
import time
import json
import base64
import PyPDF2
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# Librerías para autenticación
from streamlit_oauth import OAuth2Component
from pydantic import ValidationError, BaseModel, Field
from typing import Optional

# Importa tus clases/funciones principales
from functions import Agent, EmbeddingAgent, Client, RelationalClient

# --- IMPORTANTE: Azure Blob Storage con SAS ---
from azure.storage.blob import ContainerClient

# ---------------------------
# 1) CONFIGURAR SAS Y CONTENEDOR
# ---------------------------
SAS_TOKEN = "sp=racwdlmeop&st=2025-03-19T19:26:46Z&se=2026-03-20T03:26:46Z&spr=https&sv=2024-11-04&sr=c&sig=GoTbNoTgOrPC4SDjSv51K40Ifb7KC7TQBH00dEp87Gg%3D"
ACCOUNT_NAME = "adlgfprod001"
CONTAINER_NAME = "reclutamientogf"

CONTAINER_URL = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}?{SAS_TOKEN}"
container_client = ContainerClient.from_container_url(CONTAINER_URL)

# ---------------------------
# 2) Funciones para subir y descargar PDFs
# ---------------------------
def upload_pdf_to_blob(run_value: str, pdf_bytes: bytes):
    safe_run = run_value.replace(".", "").replace("-", "").replace(" ", "")
    blob_name = f"curriculums/{safe_run}.pdf"
    blob_client = container_client.get_blob_client(blob=blob_name)
    blob_client.upload_blob(pdf_bytes, overwrite=True)

def download_pdf_from_blob(run_value: str) -> Optional[bytes]:
    safe_run = run_value.replace(".", "").replace("-", "").replace(" ", "")
    blob_name = f"curriculums/{safe_run}.pdf"
    blob_client = container_client.get_blob_client(blob=blob_name)
    try:
        downloader = blob_client.download_blob()
        return downloader.readall()
    except Exception:
        return None

# ---------------------------
# Modelo Pydantic para parsear el JSON
# ---------------------------
class CVData(BaseModel):
    Nombre: str = Field("No especificado", alias="Nombre")
    Ciudad: str = Field("No especificado", alias="Ciudad")
    País: str = Field("No especificado", alias="País")
    Fecha_de_Nacimiento: str = Field("No especificado", alias="Fecha de Nacimiento")
    Carrera: str = Field("No especificado", alias="Carrera")
    Número_de_Teléfono: str = Field("No especificado", alias="Número de Teléfono")
    Correo: str = Field("No especificado", alias="Correo")
    Entidad_Donde_Estudió: str = Field("No especificado", alias="Entidad Donde Estudió")
    Resumen_del_Postulante: str = Field("No especificado", alias="Resumen del Postulante")
    RUN: str = Field("No especificado", alias="RUN del postulante")

    class Config:
        extra = "ignore"
        allow_population_by_field_name = True

def main():
    # Configuración inicial de la página
    st.set_page_config(
        page_title="Caza Talentos: Encontrar al Candidato Ideal",
        page_icon=":mag_right:",
        layout="centered"
    )

    # -------------------------------------------------------------------------
    # 1) BLOQUE DE AUTENTICACIÓN
    # -------------------------------------------------------------------------
    AUTHORIZE_URL = os.environ.get(
        'AUTHORIZE_URL',
        "https://login.microsoftonline.com/46ae710d-4335-430b-b7c8-f87b925b1d44/oauth2/v2.0/authorize"
    )
    TOKEN_URL = os.environ.get(
        'TOKEN_URL',
        "https://login.microsoftonline.com/46ae710d-4335-430b-b7c8-f87b925b1d44/oauth2/v2.0/token"
    )
    REFRESH_TOKEN_URL = os.environ.get('REFRESH_TOKEN_URL', TOKEN_URL)
    REVOKE_TOKEN_URL = os.environ.get('REVOKE_TOKEN_URL', None) 
    CLIENT_ID = os.environ.get('CLIENT_ID', "a55dc350-8107-46dd-bd32-a46f921a65ba")
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET', "5x_8Q~aHSERSz5jTocAS2V42GnJ5DJPUQgRCjbOq")
    REDIRECT_URI = os.environ.get('REDIRECT_URI', "http://localhost:8501")
    # REDIRECT_URI = os.environ.get('REDIRECT_URI', "https://reclutamientogf-e9gugtbef9bvcpf8.brazilsouth-01.azurewebsites.net/")

    SCOPE = os.environ.get('SCOPE', "User.Read")

    oauth2 = OAuth2Component(
        CLIENT_ID,
        CLIENT_SECRET,
        AUTHORIZE_URL,
        TOKEN_URL,
        REFRESH_TOKEN_URL,
        REVOKE_TOKEN_URL
    )

    if 'token' not in st.session_state:
        st.session_state['token'] = None

    if st.session_state['token'] is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("garces_data_analytics.png", width=300)
            st.markdown(
                "<h3 style='text-align: center;'>Inicia sesión para continuar</h3>",
                unsafe_allow_html=True
            )
            with st.spinner("Esperando autenticación..."):
                result = oauth2.authorize_button(
                    "🟦 Iniciar sesión con Microsoft",
                    REDIRECT_URI,
                    SCOPE
                )
            if result and 'token' in result:
                st.session_state.token = result.get('token')
                st.rerun()
        st.stop()

    # -------------------------------------------------------------------------
    # 2) OBJETOS PRINCIPALES Y FUNCIONES AUXILIARES
    # -------------------------------------------------------------------------
    embed_agent = EmbeddingAgent()
    client = Client()
    relational_client = RelationalClient()

    def read_file(file):
        text = ""
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def limpiar_output(json_str):
        json_str = json_str.strip('```')
        json_str = json_str.replace('json', '')
        return json_str.strip()

    def process_pdf(pdf_text, prompt):
        user_prompt = prompt + f"{pdf_text}"
        agent = Agent(user_prompt)
        raw_output = agent.getResp()
        raw_output = limpiar_output(raw_output)

        if not raw_output.strip().startswith("{") or not raw_output.strip().endswith("}"):
            first_brace_index = raw_output.find("{")
            last_brace_index = raw_output.rfind("}")
            if first_brace_index == -1 or last_brace_index == -1:
                raise ValueError(
                    "No se encontró JSON válido en la respuesta del modelo.\n\n"
                    f"Respuesta completa:\n{raw_output}"
                )
            raw_output = raw_output[first_brace_index:last_brace_index+1]

        try:
            cv_data = CVData.parse_raw(raw_output)
        except ValidationError as ve:
            raise ValueError(
                f"El modelo no devolvió JSON válido o faltan campos: {ve}\n\nRespuesta:\n{raw_output}"
            )
        except json.JSONDecodeError as je:
            raise ValueError(
                f"No se pudo decodificar el JSON: {je}\n\nRespuesta:\n{raw_output}"
            )

        data_dict = cv_data.dict(by_alias=True)
        df = pd.DataFrame([data_dict])
        return df

    # -------------------------------------------------------------------------
    # 3) INTERFAZ PRINCIPAL CON PESTAÑAS
    # -------------------------------------------------------------------------
    st.title("Caza Talentos: Encontrar al Candidato Ideal")
    st.markdown(
        """
        Bienvenido a la herramienta de **gestión de CVs**.
        Sube un currículum PDF, extrae datos relevantes, almacénalo y consúltalo en la base de datos.
        """
    )
    st.divider()

    # Barra lateral
    st.sidebar.header("Instrucciones")
    st.sidebar.markdown(
        """
        - **Cargar PDF:** Sube un solo PDF para extraer y editar la información.
        - **Chat:** Realiza búsquedas y consulta candidatos.
        - **Tabla:** Visualiza todos los candidatos registrados.
        """
    )

    tab1, tab2, tab3 = st.tabs(["📁 Cargar PDF", "💬 Chat", "📊 Tabla"])

    # -------------------------
    # Pestaña 1: Cargar PDF
    # -------------------------
    with tab1:
        st.subheader("Subir y Procesar PDF")
        st.write(
            """
            Sube un archivo PDF. Se extraerán los datos y se mostrarán en un DataFrame editable.
            Cuando estés conforme, haz clic en **Subir a la base de datos** para guardar la información.
            """
        )

        pdf_file = st.file_uploader(
            "Arrastra o haz clic para subir un PDF",
            type=["pdf"],
            accept_multiple_files=False
        )

        if pdf_file:
            with st.spinner("Extrayendo información del PDF..."):
                pdf_text = read_file(pdf_file)
            if not pdf_text.strip():
                st.warning(f"El archivo '{pdf_file.name}' no contiene texto y será omitido.")
            else:
                # Prompt para extracción de datos
                prompt = (
                    "A continuación verás un currículum vitae. "
                    "Extrae los siguientes campos y devuélvelos ÚNICAMENTE en formato JSON válido: "
                    '{"Nombre": "...", "Ciudad": "...", "País": "...", "Fecha de Nacimiento": "...", '
                    '"Carrera": "...", "Número de Teléfono": "...", "Correo": "...", '
                    '"Entidad Donde Estudió": "...", "Resumen del Postulante": "...", "RUN del postulante": ""} '
                    "No incluyas texto adicional, ni bloques de código.\nCurrículum:\n"
                )

                try:
                    df = process_pdf(pdf_text, prompt)
                except Exception as e:
                    st.error(f"Error al procesar el PDF: {e}")
                    st.stop()

                df["pdf_name"] = pdf_file.name
                run_value = df.iloc[0]["RUN del postulante"]

                # -------- Subir a Blob en lugar de guardarlo localmente --------
                pdf_bytes = pdf_file.getvalue()
                try:
                    upload_pdf_to_blob(run_value, pdf_bytes)
                    st.success("PDF procesado y subido correctamente a Blob Storage.")
                except Exception as e:
                    st.error(f"Error subiendo el PDF a Blob: {e}")
                    st.stop()
                # ---------------------------------------------------------------

                st.markdown("### Revisa y edita la información extraída")
                if "editable_df" not in st.session_state:
                    st.session_state.editable_df = df.copy()
                else:
                    st.session_state.editable_df = df.copy()

                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(st.session_state.editable_df)
                gb.configure_default_column(editable=True, filter=True, sortable=True)
                gridOptions = gb.build()

                # Calcular la altura de la tabla en función del número de filas
                num_filas = st.session_state.editable_df.shape[0]
                altura = num_filas * 35 + 50

                grid_response = AgGrid(
                    st.session_state.editable_df,
                    gridOptions=gridOptions,
                    update_mode="MODEL_CHANGED",
                    theme="blue",
                    height=altura,
                    fit_columns_on_grid_load=True
                )
                st.session_state.editable_df = pd.DataFrame(grid_response["data"])

                if st.button("Subir a la base de datos"):
                    def valid_run(x):
                        x_str = str(x).strip().lower()
                        return x_str != "" and x_str != "no especificado"

                    df_edited = st.session_state.editable_df
                    print(df_edited)
                    mask = df_edited["RUN del postulante"].apply(valid_run)
                    valid_rows = df_edited[mask]
                    invalid_rows = df_edited[~mask]

                    if not valid_rows.empty:
                        try:
                            st.info("Insertando en la base de datos...")
                            relational_client.insert_to_db(valid_rows)
                            time.sleep(1)
                            st.info("Ejecutando proceso de Merge...")
                            relational_client.executeSPCandidatos()
                            time.sleep(1)
                            st.info("Obteniendo candidatos insertados...")
                            df_insertados = relational_client.getInsertedCandidates()
                            time.sleep(1)
                            df_updated = relational_client.getUpdatedCandidates()
                            time.sleep(1)
                            run_insertados = df_insertados['RUN'].unique()
                            run_updated = df_updated['RUN'].unique()

                            st.info(f"Se insertaron RUN: {run_insertados}")
                            st.info(f"Se actualizaron RUN: {run_updated}")

                            st.info("Insertando en Milvus...")
                            if run_value in run_insertados:
                                client.insert(pdf_file, run_value)
                            if run_value in run_updated:
                                client.deleteByRun(run_value=run_value)
                                client.insert(pdf_file, run_value)

                            st.info("Ejecutando proceso de limpieza...")
                            relational_client.executeSPTruncate()

                            st.success("¡Datos subidos correctamente!")
                            # Se conservan solo las filas inválidas para revisión
                            st.session_state.editable_df = invalid_rows.copy()

                        except Exception as e:
                            st.error(f"Error al subir a la base de datos: {e}")
                    else:
                        st.warning("No hay un RUN válido para subir.")
        else:
            st.info("Por favor, sube un archivo PDF para comenzar.")

    # -------------------------
    # Pestaña 2: Chat (Usando la API de Chat de Streamlit)
    # -------------------------
    with tab2:
        st.subheader("Chat de Búsqueda y Prueba")
        st.write(
            """
            Realiza búsquedas en el sistema vectorial. 
            Ejemplo: "Busco un desarrollador con experiencia en Python".
            """
        )

        # Creamos en session_state la lista de mensajes si no existe
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Botón para limpiar historial
        if st.button("Limpiar historial"):
            st.session_state.messages = []
            st.experimental_rerun()

        # Mostramos todos los mensajes hasta ahora
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Campo de entrada estilo chat
        user_input = st.chat_input("Escribe tu consulta aquí...")
        if user_input:
            # Añadimos el mensaje del usuario al historial
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Mostramos el mensaje del usuario
            with st.chat_message("user"):
                st.write(user_input)

            # Obtenemos la respuesta del modelo
            with st.chat_message("assistant"):
                with st.spinner("Consultando..."):
                    try:
                        respuesta = client.question(user_input)
                    except Exception as e:
                        respuesta = f"Error en la consulta: {e}"
                st.write(respuesta)

            # Guardamos el mensaje del Bot en el historial
            st.session_state.messages.append({"role": "assistant", "content": respuesta})

    # -------------------------------------------------------------------------
    # Pestaña 3: Tabla de Candidatos (★ Sección con el “botón” Ver PDF)
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("Tabla de Candidatos")
        st.write("Visualiza la información actual de la base de datos relacional.")

        try:
            with st.spinner("Cargando datos..."):
                to_show = relational_client.getAllCandidates()

                def generate_pdf_link(run_value):
                    pdf_bytes = download_pdf_from_blob(str(run_value))
                    if pdf_bytes:
                        b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                        link = f'<a href="data:application/pdf;base64,{b64}" target="_blank">Ver PDF</a>'
                    else:
                        link = "No disponible"
                    return link

                to_show["Ver PDF"] = to_show["RUN del postulante"].apply(generate_pdf_link)
                st.write(to_show.to_html(escape=False, index=False), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"No se pudo cargar la tabla de candidatos: {e}")

        st.divider()
        st.markdown("Utiliza las herramientas de la tabla para ordenar y filtrar la información.")

if __name__ == "__main__":
    main()
