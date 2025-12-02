import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "payment-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3005))

# MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "host.docker.internal") # Default para Mac
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "payment_service")

# IMPORTANTE: Codificar la contraseña para que caracteres como ".." o "@" no rompan la URL
encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# RabbitMQ
AMQP_URL = os.getenv("AMQP_URL")
PAYMENT_EVENTS_QUEUE = os.getenv("PAYMENT_EVENTS_QUEUE", "payment_events")
LOG_SERVICE_QUEUE = os.getenv("LOG_SERVICE_QUEUE", "logs")

# MercadoPago
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
APP_CREATION_PRICE_MXN = int(os.getenv("APP_CREATION_PRICE_MXN", 20))
MP_WEBHOOK_URL = os.getenv("MP_WEBHOOK_URL")