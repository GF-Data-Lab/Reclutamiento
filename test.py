import pymilvus
from pymilvus import MilvusClient, DataType

# Connect using a MilvusClient object
 
CLUSTER_ENDPOINT="https://in03-1e156eb96457cf1.serverless.gcp-us-west1.cloud.zilliz.com" # Set your cluster endpoint
TOKEN="cc054aa36752b507d5faf3f9b16dbf0aaecd282899f4e27473a1e70498d54941e8f59ece91e52c1abbdfc1c126da876ee9a9af7e" # Set your token
 
client = MilvusClient(
    uri = CLUSTER_ENDPOINT, # Cluster endpoint obtained from the console
    token = TOKEN, # API key or a colon-separated cluster username and password,
)

collection_name="resume_collection"
try:
    client.drop_collection(collection_name)
    print(f"La colección '{collection_name}' ha sido eliminada por completo.")
    # Aquí podrías recrearla si lo necesitas...
    # self.client.create_collection(collection_name, fields=...)
except Exception as e:
    print(f"No se pudo eliminar la colección '{collection_name}': {e}")

client.create_collection(
    collection_name="resume_collection",
    dimension=3072,             # Dimensión del vector
    primary_field="id",        # Campo primario
    vector_field="embedding",   # Campo para el vector
    metric_type="COSINE",       # O "IP", según tu métrica de similitud
    auto_id=True,              # Desactivamos auto_id para usar RUN como string
    other_fields=[
        ("RUN", DataType.VARCHAR, 50)
      # Campo adicional para almacenar el texto, si es necesario
    ],
    description="Colección de currículums con RUN como campo primario de tipo string."
)


print(client.describe_collection("resume_collection"))