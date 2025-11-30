import google.generativeai as genai
import json
from typing import Optional
from datetime import datetime
from src.infrastructure.config.settings import GEMINI_API_KEY
from src.infrastructure.prompts.prompt_loader import LSMPromptLoader


class GeminiClient:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.lsm_prompt = LSMPromptLoader.load()

    async def generate_content(
        self,
        tipo_intervencion: str,
        tema: str,
        subtema: Optional[str],
        tipo_actividad: Optional[str],
        titulo: Optional[str],
        objetivo: Optional[str],
        evento_cognitivo: str,
        precision: float
    ) -> Optional[str]:
        try:
            max_words = self._get_max_words(tipo_intervencion)

            json_prompt = {
                "schema": "education_lsm_v1",
                "meta": {
                    "context": "Generacion de recomendaciones educativas LSM para ninos sordos",
                    "guidelines": self.lsm_prompt.get("notas_para_ia", [])
                },
                "input": {
                    "tema": tema,
                    "subtema": subtema,
                    "tipo_actividad": tipo_actividad,
                    "titulo": titulo,
                    "objetivo": objetivo,
                    "tipo_intervencion": tipo_intervencion,
                    "estado_estudiante": evento_cognitivo,
                    "precision_actual": precision,
                    "max_palabras": max_words
                },
                "output_requirements": {
                    "tipo": "recomendacion",
                    "max_palabras": max_words,
                    "debe_cumplir": [
                        "Usar reglas fundamentales de LSM del contexto",
                        "Ser motivador y accesible para el estudiante",
                        "Adaptarse al estado emocional del estudiante",
                        "Ser breve y directo"
                    ]
                }
            }

            prompt_text = f"""Basandote en este esquema JSON, genera una recomendacion educativa LSM:

{json.dumps(json_prompt, ensure_ascii=False, indent=2)}

Contexto de reglas LSM:
{json.dumps(self.lsm_prompt.get("estructura_basica", {}), ensure_ascii=False, indent=2)}

Genera SOLO el contenido recomendado, sin explicaciones adicionales."""

            response = self.model.generate_content(prompt_text)
            return response.text if response else None

        except Exception:
            self._log_error("Error generando contenido con Gemini")
            return None

    def _get_max_words(self, tipo_intervencion: str) -> int:
        max_words_map = {
            'vibration': 30,
            'instruction': 60,
            'pause': 40
        }
        return max_words_map.get(tipo_intervencion, 50)

    def _log_error(self, message: str) -> None:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [GEMINI_CLIENT] [ERROR] {message}")