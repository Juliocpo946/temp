import google.generativeai as genai
import os
from src.infrastructure.config.settings import GEMINI_API_KEY

# Configurar
genai.configure(api_key=GEMINI_API_KEY)

print("--- Modelos Disponibles ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Nombre: {m.name}")
except Exception as e:
    print(f"Error listando modelos: {e}")