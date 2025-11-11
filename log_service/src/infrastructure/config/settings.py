import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "log_service")
SERVICE_NAME = os.getenv("SERVICE_NAME", "log-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3002))
AMQP_URL = os.getenv("AMQP_URL")
LOG_QUEUE = os.getenv("LOG_QUEUE", "logs")