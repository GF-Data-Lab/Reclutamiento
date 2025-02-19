import streamlit as st
import requests
import PyPDF2
import json
import pandas as pd
import time
from functions import Agent, get_current_id, EmbeddingAgent, Client, RelationalClient


#### 19-02-2025 ####
from pydantic import BaseModel, Field
from pydantic import ValidationError
class CVData(BaseModel):
    Nombre: str = Field(..., description="Nombre del candidato")
    Ciudad: str = Field(..., description="Ciudad de residencia")
    País: str = Field(..., description="País de residencia")
    Fecha_de_Nacimiento: str = Field(..., description="Cadena con la fecha, ejemplo: 1 de Enero de 1990")
    Carrera: str = Field(..., description="Carrera estudiada (ej: Ingeniería en Informática)")
    Número_de_Teléfono: str = Field(..., alias="Número de Teléfono", description="Número de contacto")
    Correo: str = Field(..., description="Email del candidato")
    Entidad_Donde_Estudió: str = Field(..., alias="Entidad Donde Estudió", description="Institución educativa")
    Resumen_del_Postulante: str = Field(..., alias="Resumen del Postulante", description="Breve descripción o resumen del perfil")
    
    class Config:
        # Si quieres permitir que Pydantic ignore campos extras que el modelo devuelva
        # en lugar de lanzar un error, activa "extra='ignore'":
        extra = 'ignore'
        # Si quieres que Pydantic casee automáticamente los alias, setea
        # "allow_population_by_field_name = True". Así
        # si tu JSON viene con "Entidad Donde Estudió": "Universidad X"
        # Pydantic lo va a mapear al campo "Entidad_Donde_Estudió"
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
    user_prompt = prompt + f'{pdf_text}'
    agent = Agent(user_prompt)
    raw_output = agent.getResp()

    raw_output = limpiar_output(raw_output)
    
    try:
        # Pydantic puede parsear directamente el string JSON
        cv_data = CVData.parse_raw(raw_output)
    except ValidationError as ve:
        # Maneja el caso en que la IA devuelva JSON malformado
        # o sin las claves obligatorias
        print("Error de validación Pydantic:", ve)
        # Aquí podrías generar una excepción propia o retornar un df vacío:
        raise ValueError(f"Respuesta del modelo no cumple formato JSON esperado: {ve}")

    # Conviertes el objeto pydantic a dict y luego a DataFrame
    df = pd.DataFrame([cv_data.dict(by_alias=True)])
    return df
#### 19-02-2025 ####

def main():
    # Configura la página
    st.set_page_config(
        page_title="Caza Talentos: Encontrar al Candidato Ideal",
        page_icon=":mag_right:",
        layout="centered"
    )

    # Título principal de la aplicación
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
        st.subheader("Subir y Procesar PDF")
        st.write(
            """
            Sube uno o más archivos PDF con el botón de abajo.
            Después, haz clic en "**Procesar PDFs**" para extraer información 
            y almacenarla tanto en Milvus (para búsquedas vectoriales) como en 
            la base de datos relacional.
            """
        )

        # prompt = """Quiero los siguientes datos del siguiente currículum vitae:
        #         Nombre, Ciudad, País, Fecha de Nacimiento (en formato: 'Número' de 'Mes' del 'Año'),
        #         Carrera, Número de Teléfono, Correo,
        #         Entidad Donde Estudió (por ej: Universidad de O'Higgins) y Resumen del Postulante.
        #         Todo esto en formato JSON. No agregues más campos/claves de las que te pedí, sé exacto."""


        # prompt = """
        #         A continuación verás un currículum vitae. 
        #         Quiero que extraigas exactamente estos campos: 
        #           - Nombre
        #           - Ciudad
        #           - País
        #           - Fecha de Nacimiento
        #           - Carrera
        #           - Número de Teléfono
        #           - Correo
        #           - Entidad Donde Estudió
        #           - Resumen del Postulante
                
        #         Devuélvelos ÚNICAMENTE en formato JSON válido (sin texto adicional, sin códigos Markdown), 
        #         con las llaves en español correspondientes. 
                
        #         Currículum:
        #         """
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
          "Resumen del Postulante": "..."
        }
        
        No incluyas texto adicional, ni bloques de código. 
        Currículum:
        """



        uploaded_files = st.file_uploader(
            "Arrastra o haz clic para subir PDFs",
            type=["pdf"], 
            accept_multiple_files=True
        )

        # Botón para procesar PDFs
        if st.button("Procesar PDFs"):
            if uploaded_files and prompt:
                try:
                    all_dfs = []
                    with st.spinner("Procesando PDF(s)..."):
                        for pdf_file in uploaded_files:
                            pdf_text = read_file(pdf_file)
                            df = process_pdf(pdf_text, prompt)
                            all_dfs.append(df)
                            # Insertamos en Milvus
                            client.insert(pdf_file)

                        if len(all_dfs) > 0:
                            final_df = pd.concat(all_dfs, ignore_index=True)
                            st.success("¡Procesamiento exitoso!")
                            st.dataframe(final_df, use_container_width=True)
                            
                            # Insertar en la base de datos relacional
                            relational_client.insert_to_db(final_df)
                except Exception as e:
                    st.error(f"Error al procesar los PDF: {e}")
            else:
                st.warning("Por favor, sube al menos un archivo PDF antes de procesar.")

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
        user_input = st.text_input("Pregunta o consulta:", placeholder="Ejemplo: 'Busco un ingeniero en Chile'")

        if st.button("Enviar Consulta"):
            if user_input.strip():
                with st.spinner("Consultando..."):
                    r = client.question(user_input)
                    st.write("**Resultados de la búsqueda (hasta 5 coincidencias):**")
                    st.write(r)
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

        # Separador visual
        st.divider()

    
main()
