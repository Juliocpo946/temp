import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "cognitive-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3005))
SESSION_SERVICE_URL = os.getenv("SESSION_SERVICE_URL")