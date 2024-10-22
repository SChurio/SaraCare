import streamlit as st
import functions as fu
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Cosmos DB Configuración

DATABASE_NAME = os.getenv("DATABASE_NAME")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

#print(CONTAINER_NAME)


client = CosmosClient(url=os.environ["COSMOS_URI"], credential= os.environ["COSMOS_KEY"]) 
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)


#databases = client.list_databases()
#for db in databases:
#    print(db['id'])



print(container)