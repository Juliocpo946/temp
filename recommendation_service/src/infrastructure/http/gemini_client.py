import google.generativeai as genai
from typing import Optional, Dict, Any
from src.infrastructure.config.settings import GEMINI_API_KEY

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    async def generate_specific_content(
        self,
        recommendation_type: str,
        title: str,
        hint: str,
        objective: str,
        activity_type: str,
        evento: str,
        precision: float
    ) -> Optional[str]:
        try:
            max_words = self._get_max_words(recommendation_type)
            
            prompt = f"""Eres experto en educación LSM para niños sordos.
            
Tema de actividad: {title}
Hint visual/conceptual: {hint}
Objetivo educativo: {objective}
Tipo de actividad: {activity_type}
Tipo de contenido requerido: {recommendation_type}
Estado del estudiante: {evento}
Precisión actual: {precision}

Genera un {recommendation_type} específico para este tema.
Usa el hint proporcionado de manera integral.
Máximo {max_words} palabras.
Solo texto, sin explicaciones adicionales."""

            response = self.model.generate_content(prompt)
            return response.text if response else None
            
        except Exception as e:
            print(f"[ERROR] Error generating content with Gemini: {str(e)}")
            return None

    async def generate_generic_content(
        self,
        recommendation_type: str,
        activity_type: str,
        evento: str,
        precision: float
    ) -> Optional[str]:
        try:
            max_words = self._get_max_words(recommendation_type)
            
            prompt = f"""Eres experto en educación LSM para niños sordos.
            
Tipo de actividad: {activity_type}
Tipo de contenido requerido: {recommendation_type}
Estado del estudiante: {evento}
Precisión actual: {precision}

Genera un {recommendation_type} genérico y aplicable.
Máximo {max_words} palabras.
Solo texto, sin explicaciones adicionales."""

            response = self.model.generate_content(prompt)
            return response.text if response else None
            
        except Exception as e:
            print(f"[ERROR] Error generating generic content with Gemini: {str(e)}")
            return None

    @staticmethod
    def _get_max_words(recommendation_type: str) -> int:
        max_words_map = {
            'instruccion': 60,
            'motivacion': 40,
            'pausa': 35,
            'distraccion': 50
        }
        return max_words_map.get(recommendation_type, 50)