from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.cosmos import CosmosClient, exceptions
from typing import Optional
import uvicorn
from functions import generate_prompt_without_retrieval_new
import os
from fastapi.responses import RedirectResponse

from dotenv import load_dotenv

load_dotenv()  

app = FastAPI()

COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

client = CosmosClient(COSMOS_URI, COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)


print(client)
print(database)
print(container)
# Modelo para los datos del usuario
class UserData(BaseModel):
    name: str
    identification: str
    age: int
    sex: str

# Modelo para las respuestas del formulario de salud
class HealthForm(BaseModel):
    injury: Optional[str]
    smoking: Optional[str]
    allergies: Optional[str]
    obesity: Optional[str]
    hypertension: Optional[str]

class SymptomsForm(BaseModel):
    symptoms: str

app = FastAPI()


# Variable global para guardar los datos del usuario y del formulario temporalmente
user_data = {}

@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Endpoint de bienvenida
@app.get("/chatbot/")
async def start_chat():
    return {"message": "¡Hola! Bienvenido al chatbot. Por favor, dime tu nombre, edad y tu número de identificación."}

# Endpoint para capturar los datos básicos del usuario
@app.post("/chatbot/")
async def capture_data(user_data_request: UserData):

    # Guardamos los datos básicos en la variable global
    user_data['name'] = user_data_request.name
    user_data['identification'] = user_data_request.identification
    user_data['age'] = user_data_request.age
    user_data['sex'] = user_data_request.sex
    
    # Guardamos en Cosmos DB
    user = {
        "id": user_data['identification'],
        "name": user_data['name'],
        "identification": user_data['identification'],
        "age": user_data['age'],
        "sex": user_data['sex']
    }

    try:
        container.create_item(user)
        return {"message": f"Tus datos han sido guardados exitosamente, {user_data['name']}. Ahora, por favor, proporciona los datos clínicos."}
    except exceptions.CosmosResourceExistsError:
        raise HTTPException(status_code=400, detail="El usuario ya existe. Intenta con otra identificación.")

  
# Endpoint para capturar los datos clínicos del usuario
@app.post("/health_form/")
async def capture_health_data(health_form: HealthForm):
    if not user_data:
        raise HTTPException(status_code=400, detail="Primero debes ingresar los datos básicos del usuario.")
    
    health_data = {
        "injury": health_form.injury,
        "smoking": health_form.smoking,
        "allergies": health_form.allergies,
        "obesity": health_form.obesity,
        "hypertension": health_form.hypertension
    }
    try:
        identification = user_data["identification"]
        user_item = container.read_item(item=identification, partition_key=identification)
        user_item.update(health_data)  # Actualizar con los nuevos datos de salud
        container.upsert_item(user_item)  # Upsert actualiza el registro existente
        return {"message": f"Datos de salud guardados correctamente para {user_data['name']}. Ahora, proporciona tus síntomas."}
    except exceptions.CosmosResourceNotFoundError:
        return {"message": "No se encontró el registro para esta identificación."}

@app.post("/symptoms/")
async def capture_symptoms(symptoms_form: SymptomsForm):
    if not user_data:
        raise HTTPException(status_code=400, detail="Primero debes ingresar los datos básicos del usuario.")
    
    try:
        identification = user_data['identification']
        user_item = container.read_item(item=identification, partition_key=identification)
        user_item['symptoms'] = symptoms_form.symptoms  # Actualizar con los síntomas
        container.upsert_item(user_item)  # Upsert para guardar los cambios
        return {"message": "Síntomas guardados correctamente."}
    except exceptions.CosmosResourceNotFoundError:
        return {"message": "No se encontró el registro para esta identificación."}


# Endpoint para realizar el triage con todos los datos del usuario
@app.get("/triage/")
async def get_triage():
    try:
        # Buscar el registro del usuario basado en su identificación
        identification = user_data['identification']
        user_item = container.read_item(item=identification, partition_key=identification)
        
        # Extraer todos los datos necesarios
        name = user_item.get("name", "Usuario")
        age = user_item.get("age", "No disponible")
        sex = user_item.get("sex", "No disponible")
        injury = user_item.get("injury", "No disponible")
        smoking = user_item.get("smoking", "No disponible")
        allergies = user_item.get("allergies", "No disponible")
        obesity = user_item.get("obesity", "No disponible")
        hypertension = user_item.get("hypertension", "No disponible")
        symptoms = user_item.get("symptoms", "No hay síntomas registrados")

        # Crear el prompt para el modelo de IA basado en los datos del usuario
        # Crear el prompt para el modelo de IA basado en los datos del usuario
        system_prompt = "Eres un sistema experto en triage médico. Proporciona el nivel de urgencia basado en los siguientes datos del paciente."
        pregunta = (f"Paciente {name}, edad {age}, sexo {sex}. "
                    f"Síntomas: {symptoms}. Datos clínicos: Lesión: {injury}, "
                    f"Fuma: {smoking}, Alergias: {allergies}, Obesidad: {obesity}, "
                    f"Hipertensión: {hypertension}.")
        
        # Llamar a la función para generar el triage usando Langchain y OpenAI
        response = generate_prompt_without_retrieval_new(system_prompt, pregunta)
        
        return {
            "message": "Triage completado.",
            "user": {
                "name": name,
                "age": age,
                "sex": sex,
                "injury": injury,
                "smoking": smoking,
                "allergies": allergies,
                "obesity": obesity,
                "hypertension": hypertension,
                "symptoms": symptoms
            },
            "triage_result": response
        }

    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="No se encontraron los datos del usuario con esta identificación.")


@app.get("/schedule-appointment/")
async def schedule_appointment():
    # URL de Microsoft Bookings
    bookings_url = "https://outlook.office365.com/owa/calendar/SaraHelp@procalidad.com/bookings/"
    return RedirectResponse(url=bookings_url)


if __name__ == "__main__":
    uvicorn.run(app)
