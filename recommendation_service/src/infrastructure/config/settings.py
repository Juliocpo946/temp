import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "recommendation-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3006))

AMQP_URL = os.getenv("AMQP_URL")
MONITORING_EVENTS_QUEUE = os.getenv("MONITORING_EVENTS_QUEUE", "monitoring_events")
RECOMMENDATIONS_QUEUE = os.getenv("RECOMMENDATIONS_QUEUE", "recommendations")

SESSION_SERVICE_URL = os.getenv("SESSION_SERVICE_URL")

DATABASE_URL = os.getenv("DATABASE_URL")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", 10))