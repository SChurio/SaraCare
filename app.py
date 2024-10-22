import streamlit as st
import functions as fu
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Cosmos DB Configuración
COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

client = CosmosClient(COSMOS_URI, COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

# Inicialización de session_state
if 'new_id' not in st.session_state:
    st.session_state['new_id'] = 1
if 'identification' not in st.session_state:
    st.session_state['identification'] = None
if 'step' not in st.session_state:
    st.session_state['step'] = 0  # Paso 0 por defecto
# Inicializar 'id' en session_state para evitar errores
if 'id' not in st.session_state:
    st.session_state['id'] = None

# Función para avanzar al siguiente paso
def next_step():
    st.session_state.step += 1

# Función para generar un ID progresivo
def get_next_id():
    try:
        # Query para obtener todos los valores de ID
        query = "SELECT VALUE c.id FROM c"
        id_results = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        # Convertir todos los IDs a enteros, ignorando aquellos que no puedan convertirse
        numeric_ids = [int(id) for id in id_results if id.isdigit()]

        if numeric_ids:
            # Incrementa el ID más alto en 1
            return str(max(numeric_ids) + 1)
        else:
            return "1"  # Si no hay documentos o ningún ID es numérico, empieza en "1"
    except exceptions.CosmosResourceNotFoundError:
        # En caso de que no haya registros o ocurra un error con la consulta
        st.error("No se encontraron documentos en la base de datos.")
        return "1"  # Empieza desde el ID "1" si no existen documentos





# CSS to style buttons
st.markdown(
    """
    <style>
    .stButton button {
        display: block;
        margin: 0 auto;
        background-color: #28a745;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
    }
    .stButton button:hover {
        background-color: #218838;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# Step 0: Welcome screen with registration button
if st.session_state.step == 0:
    # Center the image and welcome message
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(' ')
    with col2:
        st.image("Sara.png")
    with col3:
        st.write(' ')

    st.markdown("""
        <h1 style='text-align: center;'>🩺 Bienvenidos a SaraCare AI: Triage Inteligente 👨‍⚕️</h1>
        <p style='text-align: center;'>
            SaraCare AI es una herramienta de triage médico inteligente que recopila tus datos personales, de salud y síntomas para generar una recomendación médica basada en IA. 
            Con nuestra ayuda, puedes obtener un análisis rápido y preciso de tu estado de salud y agendar una cita con un especialista si es necesario.
        </p>
    """, unsafe_allow_html=True)


    if st.button("Iniciar Registro"):
        next_step()

# Paso 1: Verificar si el paciente existe y crear un nuevo registro si es necesario
if st.session_state.step == 1:
    st.markdown("<h2 style='color: #ff6347;'>👤 Paso 1: Ingresar Número de Identificación</h2>", unsafe_allow_html=True)
    identification = st.text_input("🔑 Ingresa tu número de identificación")
    
    if st.button("Verificar Identificación"):
        if identification:
            try:
                # Verificar si el paciente ya existe en la base de datos
                query = f"SELECT * FROM c WHERE c.identification = '{identification}'"
                items = list(container.query_items(query=query, enable_cross_partition_query=True))

                if items:
                    user_item = items[0]
                    st.success(f"Paciente {user_item['name']} encontrado.")
                    
                    # Asignar un nuevo ID para crear un registro nuevo aunque el paciente ya exista
                    st.session_state['new_id'] = get_next_id()

                    # Crear un nuevo registro para el paciente existente con el nuevo ID
                    new_user_data = {
                        "id": str(st.session_state['new_id']),  # Nuevo ID
                        "identification": user_item['identification'],
                        "name": user_item['name'],
                        "age": user_item['age'],
                        "sex": user_item['sex']
                    }

                    # Insertar el nuevo registro en la base de datos
                    container.create_item(new_user_data)
                    st.success(f"🎉 Nuevo registro creado para {user_item['name']} con ID: {st.session_state['new_id']}.")

                    # Pasar al paso 3 para ingresar datos de salud
                    st.session_state.step = 3

                else:
                    # Si no se encuentra el paciente, pasar al paso de crear un nuevo registro
                    raise exceptions.CosmosResourceNotFoundError

            except exceptions.CosmosResourceNotFoundError:
                # Si no se encuentra el paciente, crear un nuevo registro
                st.error("Paciente no encontrado. Creando un nuevo registro.")
                st.session_state['identification'] = identification
                st.session_state['new_id'] = get_next_id()  # Obtener el nuevo ID
                st.session_state.step = 2  # Pasar al paso de entrada de datos básicos


# Paso 2: Ingresar Datos Básicos si no existe el paciente o si se quiere crear un nuevo registro
if st.session_state.step == 2:
    st.markdown(f"<h2 style='color: #ff6347;'>👤 Paso 2: Ingresar Datos Básicos (Nuevo ID: {st.session_state['new_id']})</h2>", unsafe_allow_html=True)
    
    with st.expander("Formulario de Datos Básicos"):
        with st.form(key="basic_form"):
            # Los valores estarán prellenados si el paciente existía, de lo contrario estarán vacíos
            name = st.text_input("📝 Nombre", value=st.session_state.get('name', ''))
            age = st.number_input("📅 Edad", min_value=0, max_value=120, value=st.session_state.get('age', 0))
            sex = st.selectbox("⚥ Sexo", ["Masculino", "Femenino", "Otro"], index=["Masculino", "Femenino", "Otro"].index(st.session_state.get('sex', "Masculino")))
            submit_basic = st.form_submit_button("Enviar Datos Básicos")
        
        if submit_basic:
            if name and age and sex:
                user_data = {
                    "id": str(st.session_state['new_id']),  # Usar el nuevo ID generado
                    "identification": st.session_state['identification'],  # Guardar la identificación ingresada
                    "name": name,
                    "age": age,
                    "sex": sex
                }
                try:
                    # Crear un nuevo registro en Cosmos DB con el nuevo ID
                    container.create_item(user_data)
                    st.success(f"🎉 Datos básicos guardados correctamente con ID: {st.session_state['new_id']}.")
                    st.session_state.step = 3  # Avanzar al paso de salud después de guardar los datos
                except exceptions.CosmosResourceExistsError:
                    st.error("⚠️ El usuario ya existe.")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {e}")
            else:
                st.error("⚠️ Por favor completa todos los campos.")


# Paso 3: Ingresar Datos de Salud
if st.session_state.step == 3:
    st.markdown("<h2 style='color: #ff6347;'>🏥 Paso 3: Ingresar Datos de Salud</h2>", unsafe_allow_html=True)
    
    with st.expander("Formulario de Salud"):
        with st.form(key="health_form"):
            injury = st.selectbox("🏃‍♂️ ¿Has tenido alguna lesión?", ["Sí", "No"])
            smoking = st.selectbox("🚬 ¿Fumas?", ["Sí", "No"])
            allergies = st.selectbox("🌿 ¿Tienes alergias?", ["Sí", "No"])
            obesity = st.selectbox("⚖️ ¿Padeces obesidad?", ["Sí", "No"])
            hypertension = st.selectbox("❤️‍🩹 ¿Tienes hipertensión?", ["Sí", "No"])
            submit_health = st.form_submit_button("Enviar Datos de Salud")
        
        if submit_health:
            health_data = {
                "injury": injury,
                "smoking": smoking,
                "allergies": allergies,
                "obesity": obesity,
                "hypertension": hypertension
            }

            try:
                # Retrieve user data and update it with health information
                id = str(st.session_state['new_id'])
                user_item = container.read_item(item=id, partition_key=id)
                user_item.update(health_data)
                container.upsert_item(user_item)
                st.success("🎉 Datos de salud guardados correctamente.")
                st.session_state.step = 4  # Move to the symptoms form step
            except exceptions.CosmosResourceNotFoundError:
                st.error("⚠️ No se encontró el registro para esta identificación.")



# Paso 4: Ingresar Síntomas
if st.session_state.step == 4:
    st.markdown("<h2 style='color: #ff6347;'>🤒 Paso 4: Ingresar Síntomas</h2>", unsafe_allow_html=True)
    
    with st.expander("Formulario de Síntomas"):
        with st.form(key="symptoms_form"):
            symptoms = st.text_area("📝 Describe tus síntomas")
            submit_symptoms = st.form_submit_button("Enviar Síntomas")
        
        if submit_symptoms:
            if symptoms:
                try:
                    # Recuperar el identificador y los datos del usuario
                    id = st.session_state['new_id']
                    user_item = container.read_item(item=id, partition_key=id)
                    
                    # Agregar los síntomas a los datos del usuario
                    user_item['symptoms'] = symptoms
                    
                    # Actualizar o insertar los datos en la base de datos
                    container.upsert_item(user_item)
                    st.success("🎉 Síntomas guardados correctamente.")
                    
                    # Avanzar al siguiente paso
                    st.session_state.step = 5
                except exceptions.CosmosResourceNotFoundError:
                    st.error("⚠️ No se encontró el registro para esta identificación.")
                except Exception as e:
                    st.error(f"⚠️ Ocurrió un error inesperado: {e}")
            else:
                st.error("⚠️ Por favor ingresa tus síntomas.")


# Paso 5: Resultado del Triage
if st.session_state.step == 5:
    st.markdown("<h2 style='color: #ff6347;'>📊 Paso 5: Resultado del Triage generado por IA</h2>", unsafe_allow_html=True)
    
    if st.button("🔍 Obtener resultado del Triage"):
        try:
            # Usar 'new_id' como el identificador único
            identification = str(st.session_state['new_id'])
            user_item = container.read_item(item=identification, partition_key=identification)
            
            # Verificar que los datos necesarios están presentes
            if all(key in user_item for key in ['name', 'age', 'symptoms', 'injury', 'smoking', 'allergies', 'obesity', 'hypertension']):
                system_prompt = "Eres un sistema experto en triage médico. Proporciona el nivel de urgencia basado en los siguientes datos del paciente."
                pregunta = (f"Paciente {user_item['name']}, edad {user_item['age']}, "
                            f"Síntomas: {user_item['symptoms']}, Lesión: {user_item['injury']}, "
                            f"Fuma: {user_item['smoking']}, Alergias: {user_item['allergies']}, "
                            f"Obesidad: {user_item['obesity']}, Hipertensión: {user_item['hypertension']}.")

                # Generar la respuesta de la IA
                response = fu.generate_prompt_without_retrieval_new(system_prompt, pregunta)

                # Mostrar el resultado del triage
                st.markdown("<h3 style='color: green;'>✅ Resultado del Triage:</h3>", unsafe_allow_html=True)
                st.write(response)

                # Guardar la respuesta de la IA en la base de datos
                user_item['triage_result'] = response
                container.upsert_item(user_item)
                
                st.session_state.step = 6
            else:
                st.error("⚠️ Los datos del paciente están incompletos.")
        
        except exceptions.CosmosResourceNotFoundError:
            st.error("⚠️ No se encontraron los datos del usuario.")
        except Exception as e:
            st.error(f"⚠️ Error al generar el triage: {e}")

# Paso 5: Agendar Cita
if st.session_state.step == 6:
    st.markdown("<h2 style='color: #ff6347;'>📅 Paso 5: Generar una Cita con un Especialista</h2>", unsafe_allow_html=True)
    
    if st.button("📅 Agendar Cita"):
        bookings_url = "https://outlook.office365.com/owa/calendar/SaraHelp@procalidad.com/bookings/"
        st.markdown(f"[Haz clic aquí para agendar una cita]({bookings_url})")

    st.button("🔄 Reiniciar", on_click=lambda: st.session_state.update(step=0))