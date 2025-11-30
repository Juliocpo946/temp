import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "monitoring-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3008))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "monitoring_service")

AMQP_URL = os.getenv("AMQP_URL")
MONITORING_EVENTS_QUEUE = os.getenv("MONITORING_EVENTS_QUEUE", "monitoring_events")
LOG_SERVICE_QUEUE = os.getenv("LOG_SERVICE_QUEUE", "logs")
ACTIVITY_EVENTS_QUEUE = os.getenv("ACTIVITY_EVENTS_QUEUE", "activity_events")
MONITORING_WEBSOCKET_EVENTS_QUEUE = os.getenv("MONITORING_WEBSOCKET_EVENTS_QUEUE", "monitoring_websocket_events")

MODEL_PATH = os.getenv("MODEL_PATH", "models/intervention_model.keras")
SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", 30))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))

COOLDOWN_VIBRATION_SECONDS = int(os.getenv("COOLDOWN_VIBRATION_SECONDS", 30))
COOLDOWN_INSTRUCTION_SECONDS = int(os.getenv("COOLDOWN_INSTRUCTION_SECONDS", 60))
COOLDOWN_PAUSE_SECONDS = int(os.getenv("COOLDOWN_PAUSE_SECONDS", 180))

RESULT_EVALUATION_DELAY_SECONDS = int(os.getenv("RESULT_EVALUATION_DELAY_SECONDS", 45))
NEGATIVE_SAMPLE_RATE = float(os.getenv("NEGATIVE_SAMPLE_RATE", 0.05))

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"