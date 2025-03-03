import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import requests
import PyPDF2
import json
import pandas as pd
import time
from functions import Agent, get_current_id, EmbeddingAgent, Client, RelationalClient


#### 19-02-2025 ####
from pydantic import ValidationError
from typing import Optional
from pydantic import BaseModel, Field

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
    RUN: str = Field("No especificado", alias = "RUN del postulante")

    class Config:
        extra = "ignore"
        allow_population_by_field_name = True
#### 19-02-2025 ####




# Instanciamos los objetos necesarios
embed_agent = EmbeddingAgent()
client = Client()
relational_client = RelationalClient()

def read_file(file):
    """
    Lee un PDF (ya sea ruta local o un objeto de Streamlit) y devuelve todo el texto.
    """
    text = ""
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def limpiar_output(json_str):
    """
    Limpia el string JSON que regresa el modelo para poder parsearlo correctamente.
    """
    json_str = json_str.strip('```')  
    json_str = json_str.replace('json', '')  
    return json_str.strip()


#### 19-02-2025 ####
## Descomentar la función si no corre el código
# def process_pdf(pdf_text, prompt):
#     """
#     Recibe el texto de un PDF y un prompt, llama a la clase Agent,
#     interpreta la respuesta como JSON y la devuelve en un DataFrame.
#     """
#     user_prompt = prompt + f'{pdf_text}'
#     agent = Agent(user_prompt)
#     output = agent.getResp()

#     output = limpiar_output(output)
#     output = json.loads(output)

#     # Creamos un DataFrame con una sola fila
#     df = pd.DataFrame([output])
#     return df

def process_pdf(pdf_text, prompt):
    """
    Recibe el texto de un PDF y un prompt, llama a la clase Agent,
    interpreta la respuesta como JSON y la devuelve en un DataFrame.
    """
    user_prompt = prompt + f"{pdf_text}"
    agent = Agent(user_prompt)
    raw_output = agent.getResp()

    # Primero limpiamos el output de backticks y palabras sueltas:
    raw_output = limpiar_output(raw_output)

    # Intentamos aislar solo la parte JSON (en caso de que el modelo
    # haya agregado texto extra o disclaimers antes/después).
    if not raw_output.strip().startswith("{") or not raw_output.strip().endswith("}"):
        first_brace_index = raw_output.find("{")
        last_brace_index = raw_output.rfind("}")
        if first_brace_index == -1 or last_brace_index == -1:
            raise ValueError(
                f"No se encontró JSON válido en la respuesta del modelo.\n\nRespuesta completa:\n{raw_output}"
            )
        # Extraemos únicamente el contenido entre las primeras y últimas llaves.
        raw_output = raw_output[first_brace_index:last_brace_index+1]

    # Ahora parseamos con Pydantic para asegurarnos de que cumpla la estructura
    try:
        cv_data = CVData.parse_raw(raw_output)
    except ValidationError as ve:
        # Puede fallar porque falta un campo o porque la estructura no coincide.
        raise ValueError(f"El modelo no devolvió JSON válido o faltan campos: {ve}\n\nRespuesta:\n{raw_output}")
    except json.JSONDecodeError as je:
        # Ocurre si la cadena no es parseable como JSON.
        raise ValueError(f"No se pudo decodificar el JSON: {je}\n\nRespuesta:\n{raw_output}")

    # Convertimos el objeto Pydantic a diccionario y luego a DataFrame
    data_dict = cv_data.dict(by_alias=True)
    df = pd.DataFrame([data_dict])
    return df
#### 19-02-2025 ####

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import requests
import PyPDF2
import json
import time
from functions import Agent, get_current_id, EmbeddingAgent, Client, RelationalClient

from pydantic import ValidationError
from typing import Optional
from pydantic import BaseModel, Field

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

# Instanciamos los objetos necesarios
embed_agent = EmbeddingAgent()
client = Client()
relational_client = RelationalClient()

def read_file(file):
    """
    Lee un PDF (ya sea ruta local o un objeto de Streamlit) y devuelve todo el texto.
    """
    text = ""
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def limpiar_output(json_str):
    """
    Limpia el string JSON que regresa el modelo para poder parsearlo correctamente.
    """
    json_str = json_str.strip('```')
    json_str = json_str.replace('json', '')
    return json_str.strip()

def process_pdf(pdf_text, prompt):
    """
    Recibe el texto de un PDF y un prompt, llama a la clase Agent,
    interpreta la respuesta como JSON y la devuelve en un DataFrame.
    """
    user_prompt = prompt + f"{pdf_text}"
    agent = Agent(user_prompt)
    raw_output = agent.getResp()

    # Primero limpiamos el output de backticks y palabras sueltas:
    raw_output = limpiar_output(raw_output)

    # Intentamos aislar solo la parte JSON
    if not raw_output.strip().startswith("{") or not raw_output.strip().endswith("}"):
        first_brace_index = raw_output.find("{")
        last_brace_index = raw_output.rfind("}")
        if first_brace_index == -1 or last_brace_index == -1:
            raise ValueError(
                f"No se encontró JSON válido en la respuesta del modelo.\n\nRespuesta completa:\n{raw_output}"
            )
        raw_output = raw_output[first_brace_index:last_brace_index+1]

    try:
        cv_data = CVData.parse_raw(raw_output)
    except ValidationError as ve:
        raise ValueError(f"El modelo no devolvió JSON válido o faltan campos: {ve}\n\nRespuesta:\n{raw_output}")
    except json.JSONDecodeError as je:
        raise ValueError(f"No se pudo decodificar el JSON: {je}\n\nRespuesta:\n{raw_output}")

    data_dict = cv_data.dict(by_alias=True)
    df = pd.DataFrame([data_dict])
    return df

def main():
    st.set_page_config(
        page_title="Caza Talentos: Encontrar al Candidato Ideal",
        page_icon=":mag_right:",
        layout="centered"
    )

    st.title("Caza Talentos: Encontrar al Candidato Ideal")
    st.markdown(
        """
        Bienvenido a la herramienta de **gestión de CVs**. 
        Aquí puedes subir currículums en PDF, extraer datos relevantes, 
        almacenarlos y consultarlos en una base de datos, y realizar búsquedas específicas.
        """
    )
    st.divider()

    # Se crean las tres pestañas
    tab1, tab2, tab3 = st.tabs(["📁 Cargar PDF", "💬 Chat", "📊 Tabla"])

    # ------------------
    # Pestaña 1: Cargar PDF
    # ------------------
    with tab1:
        prompt = """
        A continuación verás un currículum vitae. 
        Extrae los siguientes campos y devuélvelos ÚNICAMENTE en formato JSON válido: 
        {
          "Nombre": "...",
          "Ciudad": "...",
          "País": "...",
          "Fecha de Nacimiento": "...",
          "Carrera": "...",
          "Número de Teléfono": "...",
          "Correo": "...",
          "Entidad Donde Estudió": "...",
          "Resumen del Postulante": "...",
          "RUN del postulante": ""
        }
        
        No incluyas texto adicional, ni bloques de código. 
        Currículum:
        """

        st.subheader("Subir y Procesar PDF")
        st.write(
            """
            Sube uno o más archivos PDF. Se extraerán los datos y se mostrarán en un DataFrame editable.
            Cuando estés conforme, haz clic en "**Subir a la base de datos**" para guardar la información.
            """
        )

        uploaded_files = st.file_uploader(
            "Arrastra o haz clic para subir PDFs",
            type=["pdf"], 
            accept_multiple_files=True
        )

        if uploaded_files:
            all_dfs = []
            for pdf_file in uploaded_files:
                pdf_text = read_file(pdf_file)
                if not pdf_text.strip():
                    st.warning(f"El archivo '{pdf_file.name}' no contiene texto y será omitido.")
                    continue
                df = process_pdf(pdf_text, prompt)
                all_dfs.append(df)

            if all_dfs:
                final_df = pd.concat(all_dfs, ignore_index=True)
                st.markdown("### Vista previa del DataFrame editable")
                
                # Guardamos el DataFrame en el estado de sesión la primera vez
                if "editable_df" not in st.session_state:
                    st.session_state.editable_df = final_df.copy()
                
                # Mostrar el DataFrame editable con AgGrid
                gb = GridOptionsBuilder.from_dataframe(st.session_state.editable_df)
                gb.configure_default_column(editable=True)
                gridOptions = gb.build()
                grid_response = AgGrid(
                    st.session_state.editable_df,
                    gridOptions=gridOptions,
                    update_mode="MODEL_CHANGED",
                    theme="blue"
                )
                # Actualizamos el DataFrame editable según las ediciones
                st.session_state.editable_df = pd.DataFrame(grid_response["data"])
                
                if st.button("Subir a la base de datos"):
                    def valid_run(x):
                        x_str = str(x).strip().lower()
                        return x_str != "" and x_str != "no especificado"
                    
                    mask = st.session_state.editable_df["RUN del postulante"].apply(valid_run)
                    valid_rows = st.session_state.editable_df[mask]
                    invalid_rows = st.session_state.editable_df[~mask]
                    
                    if not valid_rows.empty:
                        try:
                            with st.spinner("Subiendo datos..."):
                                relational_client.insert_to_db(valid_rows)
                            st.success("¡Datos subidos correctamente!")
                            # Actualizamos el DataFrame en el estado de sesión para conservar solo las filas sin RUN válido
                            st.session_state.editable_df = invalid_rows.copy()
                        except Exception as e:
                            st.error(f"Error al subir a la base de datos: {e}")
                    else:
                        st.info("No hay filas con un RUN válido para subir.")
            else:
                st.info("No se procesaron archivos válidos para mostrar vista previa.")
        else:
            st.info("Por favor, sube al menos un archivo PDF.")

    # ------------------
    # Pestaña 2: Chat
    # ------------------
    with tab2:
        st.subheader("Chat de Búsqueda y Prueba")
        st.write(
            """
            Aquí puedes realizar **búsquedas** en el sistema vectorial (Milvus). 
            Por ejemplo, escribe algo como "busco un desarrollador con experiencia en Python" 
            y verás los resultados más relacionados con ese texto.
            """
        )
        # Inicializar el historial del chat en el estado de sesión
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        st.markdown("### Historial del Chat")
        for chat in st.session_state.chat_history:
            st.markdown(f"**{chat['sender']}**: {chat['message']}")
        
        user_input = st.text_input("Pregunta o consulta:", placeholder="Ejemplo: 'Busco un ingeniero en Chile'")
    
        if st.button("Enviar Consulta"):
            if user_input.strip():
                with st.spinner("Consultando..."):
                    r = client.question(user_input)
                st.session_state.chat_history.append({"sender": "Usuario", "message": user_input})
                st.session_state.chat_history.append({"sender": "Bot", "message": r})
            else:
                st.warning("Por favor, escribe un mensaje antes de enviar.")

    # ------------------
    # Pestaña 3: Tabla
    # ------------------
    with tab3:
        st.subheader("Tabla de Candidatos")
        st.write(
            """
            A continuación, se muestra la información actual de la base de datos relacional.
            """
        )

        try:
            with st.spinner("Cargando datos desde la base de datos..."):
                to_show = relational_client.getAllCandidates()
                st.dataframe(to_show, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo cargar la tabla de candidatos: {e}")

        st.divider()

main()

