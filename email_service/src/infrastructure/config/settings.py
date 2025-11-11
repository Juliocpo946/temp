import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3003))
AMQP_URL = os.getenv("AMQP_URL")
EMAIL_QUEUE = os.getenv("EMAIL_QUEUE")
LOG_SERVICE_QUEUE = os.getenv("LOG_SERVICE_QUEUE", "logs")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME")