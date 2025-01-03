from functions import Client
client = Client()
client.empty_collection()

import pymilvus
from pymilvus import MilvusClient, DataType

# Connect using a MilvusClient object
 
CLUSTER_ENDPOINT="https://in03-1e156eb96457cf1.serverless.gcp-us-west1.cloud.zilliz.com" # Set your cluster endpoint
TOKEN="cc054aa36752b507d5faf3f9b16dbf0aaecd282899f4e27473a1e70498d54941e8f59ece91e52c1abbdfc1c126da876ee9a9af7e" # Set your token
 
client = MilvusClient(
    uri = CLUSTER_ENDPOINT, # Cluster endpoint obtained from the console
    token = TOKEN, # API key or a colon-separated cluster username and password,
)
 
client.create_collection(
    collection_name="resume_collection",
    dimension=3072,            # Dimensión del vector
    primary_field="id",        # Campo primario
    vector_field="embedding",  # Campo para el vector
    metric_type="COSINE",          # O "IP", según tu métrica de similitud
    auto_id=True,              # Autoincremental para 'id'
    # Lista de otros campos (nombre, tipo)

    other_fields=[("resume_id", DataType.INT64)],
    description="Colección de currículums con ID autoincremental."
)