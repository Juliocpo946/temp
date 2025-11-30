import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "recommendation-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3006))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "recommendation_service")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

AMQP_URL = os.getenv("AMQP_URL")
MONITORING_EVENTS_QUEUE = os.getenv("MONITORING_EVENTS_QUEUE", "monitoring_events")
RECOMMENDATIONS_QUEUE = os.getenv("RECOMMENDATIONS_QUEUE", "recommendations")
ACTIVITY_DETAILS_REQUEST_QUEUE = os.getenv("ACTIVITY_DETAILS_REQUEST_QUEUE", "activity_details_request")
ACTIVITY_DETAILS_RESPONSE_QUEUE = os.getenv("ACTIVITY_DETAILS_RESPONSE_QUEUE", "activity_details_response")
LOG_SERVICE_QUEUE = os.getenv("LOG_SERVICE_QUEUE", "logs")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", 10))
RABBITMQ_TIMEOUT = int(os.getenv("RABBITMQ_TIMEOUT", 5))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
CACHE_TTL = int(os.getenv("CACHE_TTL", 300))