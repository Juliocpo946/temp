import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "recommendation-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3006))

AMQP_URL = os.getenv("AMQP_URL")
MONITORING_EVENTS_QUEUE = os.getenv("MONITORING_EVENTS_QUEUE", "monitoring_events")
RECOMMENDATIONS_QUEUE = os.getenv("RECOMMENDATIONS_QUEUE", "recommendations")
LOG_SERVICE_QUEUE = os.getenv("LOG_SERVICE_QUEUE", "logs")

SESSION_SERVICE_URL = os.getenv("SESSION_SERVICE_URL")
CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL")
LOG_SERVICE_URL = os.getenv("LOG_SERVICE_URL")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", 10))
RABBITMQ_TIMEOUT = int(os.getenv("RABBITMQ_TIMEOUT", 5))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

CACHE_TTL = int(os.getenv("CACHE_TTL", 300))