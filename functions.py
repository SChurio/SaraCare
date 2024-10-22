import os
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()  


cliente = AzureChatOpenAI(
    azure_endpoint= os.getenv("AZURE_OPENAI_ENDPOINT"),  
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_ID"),  
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"), 
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"), 
    temperature=0.7  
)



def generate_prompt_without_retrieval_new(system_prompt, pregunta):
    """
    Genera una respuesta utilizando solo el LLM sin documentos recuperados.
    
    Args:
        system_prompt (str): El prompt del sistema para el asistente.
        pregunta (str): La pregunta que deseas hacer al LLM.
        cliente: La instancia del modelo de lenguaje (e.g., ChatOpenAI).
    
    Returns:
        dict: Respuesta generada por el modelo con la clave 'answer'.
    """

    prompt_without_context = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}"),
    ("human", "{input}"),
    ("assistant", "")
    ])

    # Crear el parser de salida
    output_parser = StrOutputParser()
    
    # Encadenar los runnables usando el operador pipe
    chain = prompt_without_context | cliente | output_parser
    
    # Ejecutar la cadena con la nueva pregunta
    response = chain.invoke({"system_prompt": system_prompt, "input": pregunta})
    
    return response