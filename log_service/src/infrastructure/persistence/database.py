from mongoengine import connect
from src.infrastructure.config.settings import MONGO_URL, MONGODB_DATABASE

def connect_db():
    try:
        connect(MONGODB_DATABASE, host=MONGO_URL)
        print(f"Conectado a MongoDB: {MONGODB_DATABASE}")
    except Exception as e:
        print(f"Error al conectar con MongoDB: {str(e)}")
        raise

def disconnect_db():
    from mongoengine import disconnect
    disconnect()