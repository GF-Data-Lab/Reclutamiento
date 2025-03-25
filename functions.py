import requests
import os
import PyPDF2
import sqlalchemy
from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType, Collection,connections
import pandas as pd
from pymilvus import MilvusClient
# Asegúrate de que tienes importados los módulos que usas para:
#   - leer el PDF: read_file(pdf_path)
#   - generar embeddings: get_embed_from_text, EmbeddingAgent
#   - Agente para generar respuestas: Agent
#   - generar/generar ID actual: get_current_id

class Client:
    CLUSTER_ENDPOINT = "https://in03-1e156eb96457cf1.serverless.gcp-us-west1.cloud.zilliz.com"  # Ajusta tu endpoint si cambia
    TOKEN = "cc054aa36752b507d5faf3f9b16dbf0aaecd282899f4e27473a1e70498d54941e8f59ece91e52c1abbdfc1c126da876ee9a9af7e"  # Ajusta tu token

    def __init__(self):
        """
        Constructor de la clase, que crea la instancia de MilvusClient.
        """
        self.client = MilvusClient(
            uri=self.CLUSTER_ENDPOINT,
            token=self.TOKEN
        )

    def getClient(self):
        """
        Retorna la instancia de MilvusClient (por si quieres usar métodos de la librería).
        """
        return self.client

    def insert(self, pdf_path, RUN):
        """
        Lee un PDF, obtiene los embeddings en chunks y los inserta en la colección.
        Usa el campo 'RUN' para asociarlo al registro y 'text' para el texto original.
        """
        text = read_file(pdf_path)
        chunk_embeddings = get_embed_from_text(text, chunk_size=None)
        print(chunk_embeddings)

        # Ejemplo de un ID local para controlar tus resumes si lo necesitas
        resume_id = 0

        # Insertamos chunk por chunk en la colección 'resume_collection'
        for chunk in chunk_embeddings:
            print(chunk[0], chunk[1])
            _ = self.client.insert(
                collection_name='resume_collection',
                data={
                    "RUN": RUN,
                    "vector": chunk[0],
                    "text": chunk[1]
                }
            )

        print(f"Ingresado el CV '{pdf_path}' con {len(chunk_embeddings)} chunks (resume_id={resume_id}).")

    def question(self, question):
        """
        Recibe una pregunta, obtiene su embedding y hace un search en la colección 'resume_collection'.
        Luego, con cada resultado, arma un resumen a través de un agente (Agent).
        """
        embed_agent = EmbeddingAgent()
        print(embed_agent)

        # Obtenemos el embedding de la pregunta y hacemos un search en la colección
        search_res = self.client.search(
            collection_name="resume_collection",
            data=[embed_agent.get_embedding(question)[0]],
            limit=2,
            search_params={"metric_type": "COSINE", "params": {}},
            output_fields=["text"]
        )
        print(search_res)

        # Parseamos los resultados para quedarnos sólo con el texto
        search_res_list = [item['entity']['text'] for sublist in search_res for item in sublist]
        print(search_res_list)

        # Enviamos cada texto a un prompt/Agent para generar un resumen final
        search_res_modified = []
        for i in search_res_list:
            prompt = f"""Quiero que de este texto, hagas un resumen de lo mas importante:

                         '{i}'

                         Muestralo de manera ordenada y resumida que tu output sea solo texto, 
                         por favor sin comandos de saltos de linea ni nada. 
                         Quien verá este texto es una persona encargada de reclutamiento de personal, 
                         por lo que puedes hacer resumen de cada uno de los candidatos y ciertas recomendaciones.
                      """
            agent = Agent(prompt)
            agent_resp = agent.getResp()
            search_res_modified.append(agent_resp + "\n")

        # Unimos todo en un único string y lo devolvemos
        textos = "\n".join(search_res_modified)
        return textos

    def listAllRuns(self, collection_name="resume_collection"):
        """
        Retorna una lista con todos los valores únicos de RUN en la colección dada.
        """
        try:
            # Realiza la consulta para obtener el campo RUN de todos los registros
            results = self.client.query(
                collection_name=collection_name,
                filter="",limit=5,  # Consulta vacía => trae todos
                output_fields=["RUN"]
            )

            # Extrae los valores únicos de RUN
            runs = {r["RUN"] for r in results}
            return list(runs)

        except Exception as e:
            print(f"Error al obtener la lista de RUN: {e}")
            return []

    def deleteByRun(self, run_value, collection_name="resume_collection"):
        """
        Elimina todos los registros de la colección 'resume_collection' 
        cuyo campo RUN coincida con 'run_value'.
        """
        expr = f"RUN == '{run_value}'"  # Expresión para filtrar por RUN
        print(f"Eliminando registros con RUN='{run_value}'...")
        try:
            result = self.client.delete(
                collection_name=collection_name,
                filter=expr
            )
            print(f"Registros eliminados en Milvus con RUN='{run_value}': {result}")
        except Exception as e:
            print(f"Error al eliminar registros con RUN='{run_value}': {e}")



class RelationalClient():
    server = 'srvsql-prod-001.database.windows.net' #NBL22PF3NB901
    database = 'sqldb-prod-002' 
    username = 'ETLAnalytics'
    password = 'zuf63TCR7s2B' 
    #driver   = '{ODBC+Driver+17+for+SQL+Server}'
    driver   = 'ODBC Driver 17 for SQL Server'  
    port = '1433'
    try:
        engine2 = sqlalchemy.create_engine('mssql+pyodbc://'+username+':'+password+'@'+server+'/'+database+'?trusted_connection=no&driver=ODBC Driver 18 for SQL Server',fast_executemany=False)#,pool_reset_on_return=None,)
        #engine = sqlalchemy.create_engine('mssql+pyodbc://'+server+'/'+database+'?driver=ODBC Driver 17 for SQL Server')#,pool_reset_on_return=None,)
        conn = engine2.connect()
    except Exception as e:
        print(e)
    def insert_to_db(self,df):
        df.to_sql("STG_CANDIDATOS",con = self.engine2 ,if_exists = 'append',schema = 'API_RECLUTAMIENTO',  index = False)
    def getAllCandidates(self):
        query = "SELECT * FROM [API_RECLUTAMIENTO].[CANDIDATOS]"
        df = pd.read_sql(query, con=self.engine2)
        return df
    def executeSPCandidatos(self):
        with self.engine2.connect() as connection:
            result = connection.execute(sqlalchemy.text("EXEC [API_RECLUTAMIENTO].[MG_CANDIDATOS]"))
            connection.commit()
    def executeSPTruncate(self):
        with self.engine2.connect() as connection:
            result = connection.execute(sqlalchemy.text("EXEC [API_RECLUTAMIENTO].[TRUNCATE_AUX_TABLES]"))
            connection.commit()  
    def getInsertedCandidates(self):
        query = "SELECT * FROM [API_RECLUTAMIENTO].[CANDIDATOS_NUEVOS]"
        # Ejecuta la consulta y obtén el resultado en un DataFrame
        df = pd.read_sql_query(query, self.engine2)
        print(df)
        return df
    def getUpdatedCandidates(self):
        query = "SELECT * FROM [API_RECLUTAMIENTO].[CANDIDATOS_ACTUALIZADOS]"
        # Ejecuta la consulta y obtén el resultado en un DataFrame
        df = pd.read_sql_query(query, self.engine2)
        print(df)
        return df

        

class Agent:
    system_prompt = """you are an AI helpful assistant .
    """
    temperature = 0.2
    max_tokens = 2000
    top_p = 0.9

    def __init__(self, user_prompt=None):
        self.user_prompt = user_prompt
        self.tokens_used = 0

    def setUserPrompt(self, user_prompt):
        self.user_prompt = user_prompt

    def createPayload(self):
        # Payload para la request
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": self.system_prompt
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.user_prompt
                        }
                    ]
                }
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens
        }
        return payload

    def getResp(self):
        API_KEY = "6ivtI1Srm8xX4wO3WHUdNU7wBWF58zljz6ObGQAYcR3dzqKovKkvJQQJ99ALACHYHv6XJ3w3AAAAACOG4sBy"
        ENDPOINT = "https://manue-m55d5rek-eastus2.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"

        headers = {
            "Content-Type": "application/json",
            "api-key": API_KEY,
        }

        try:
            response = requests.post(ENDPOINT, headers=headers, json=self.createPayload())
            response.raise_for_status()
        except requests.RequestException as e:
            raise SystemExit(f"Failed to make the request. Error: {e}")

        self.tokens_used += int(response.json()['usage']['total_tokens'])
        return response.json()['choices'][0]['message']['content']

    def getTokens(self):
        return self.tokens_used


def read_file(file_path):
    """
    Lee un PDF y retorna todo su texto concatenado.
    """
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def get_embed_from_text(text, chunk_size=None):
    """
    Divide 'text' en trozos ('chunks') de longitud 'chunk_size'
    y obtiene el embedding para cada fragmento.
    """
    embed_agent = EmbeddingAgent()
    embed_list = []
    left_idx = 0
    text_len = len(text)
    if chunk_size == None:
      chunk_size = text_len
    while left_idx < text_len:
        end_idx = min(left_idx + chunk_size, text_len)
        fragment = text[left_idx:end_idx]
        # Obtenemos embedding del fragmento
        current_embed = embed_agent.get_embedding(fragment)
        embed_list.append(current_embed)
        left_idx += chunk_size
    return embed_list
def ingest_pdf(pdf_path, resume_id, chunk_size=1000):
    """
    Lee un PDF, obtiene los embeddings en chunks y los inserta en la colección
    con un resume_id específico (por ejemplo, 101, 102...).
    """
    text = read_file(pdf_path)
    chunk_embeddings = get_embed_from_text(text, chunk_size)
    # Insertamos en Milvus Lite: auto_id genera 'id' automáticamente,
    # nosotros sólo pasamos "resume_id" como campo extra.
    for chunk in chunk_embeddings:
      print(chunk[0], chunk[1])
      insert_result = client.insert(
          collection_name='resume_collection',
          data={"resume_id": resume_id, "vector": chunk[0],'text':chunk[1]}
      )
    print(f"Ingresado el CV {pdf_path} con {len(chunk_embeddings)} chunks (resume_id={resume_id}).")

class EmbeddingAgent:
    def get_embedding(self,fragment):
        API_KEY = "6ivtI1Srm8xX4wO3WHUdNU7wBWF58zljz6ObGQAYcR3dzqKovKkvJQQJ99ALACHYHv6XJ3w3AAAAACOG4sBy"
        headers = {
          "Content-Type": "application/json",
          "api-key": API_KEY,
        }
        ENDPOINT = "https://manue-m55d5rek-eastus2.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15"
        """
        Envía 'fragment' a tu API de embeddings y retorna el vector resultante.
        """
        payload = {'input': fragment}
        try:
            response = requests.post(ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            raise SystemExit(f"Failed to make the request. Error: {e}")

        return [response.json()['data'][0]['embedding'], fragment]  # Retorna una lista que contiene dos listas, la primera el vector de tamano R^3072 y la segunda el fragmento
    

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

def process_pdf(pdf_text, prompt, pdf_name):
    """
    Recibe el texto de un PDF y un prompt, llama a la clase Agent,
    interpreta la respuesta como JSON y la devuelve en un DataFrame.
    """
    user_prompt = prompt + f'{pdf_text}'
    agent = Agent(user_prompt)
    output = agent.getResp()

    output = limpiar_output(output)
    output = json.loads(output)
    output['Nombre Archivo']  = pdf_name

    # Creamos un DataFrame con una sola fila
    df = pd.DataFrame([output])
    return df

def load_pdf_to_vector_db(pdf):
    ingest_pdf(pdf, get_current_id(), chunk=None)