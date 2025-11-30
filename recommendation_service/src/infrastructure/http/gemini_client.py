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

    def generate_content(
        self,
        intervention_type: str,
        topic: str,
        subtopic: Optional[str],
        activity_type: Optional[str],
        title: Optional[str],
        objective: Optional[str],
        cognitive_event: str,
        precision: float
    ) -> Optional[str]:
        try:
            max_words = self._get_max_words(intervention_type)

            json_prompt = {
                "schema": "education_lsm_v1",
                "meta": {
                    "context": "Generacion de recomendaciones educativas LSM para ninos sordos",
                    "guidelines": self.lsm_prompt.get("notas_para_ia", [])
                },
                "input": {
                    "topic": topic,
                    "subtopic": subtopic,
                    "activity_type": activity_type,
                    "title": title,
                    "objective": objective,
                    "intervention_type": intervention_type,
                    "student_state": cognitive_event,
                    "current_precision": precision,
                    "max_words": max_words
                },
                "output_requirements": {
                    "type": "recommendation",
                    "max_words": max_words,
                    "must_comply": [
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
            
            if response:
                print(f"[GEMINI_CLIENT] [INFO] Contenido generado exitosamente")
                return response.text
            return None

        except Exception as e:
            print(f"[GEMINI_CLIENT] [ERROR] Error generando contenido con Gemini: {str(e)}")
            return None

    def _get_max_words(self, intervention_type: str) -> int:
        max_words_map = {
            'vibration': 30,
            'instruction': 60,
            'pause': 40
        }
        return max_words_map.get(intervention_type, 50)