import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "api-gateway")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3000))
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
LOG_SERVICE_URL = os.getenv("LOG_SERVICE_URL")
AMQP_URL = os.getenv("AMQP_URL")
LOG_SERVICE_QUEUE = os.getenv("LOG_SERVICE_QUEUE", "logs")
REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN")