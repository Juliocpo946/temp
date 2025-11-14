import google.generativeai as genai
from typing import Optional
from datetime import datetime
import json
from src.infrastructure.config.settings import GEMINI_API_KEY
from src.infrastructure.prompts.lsm_grammar_prompt_loader import LSMPromptLoader

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.lsm_prompt = LSMPromptLoader.load()

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
            
            json_prompt = {
                "schema": "education_lsm_v1",
                "meta": {
                    "context": "Generación de recomendaciones educativas LSM para niños sordos",
                    "guidelines": self.lsm_prompt.get("notas_para_ia", [])
                },
                "input": {
                    "tema_actividad": title,
                    "hint_visual_conceptual": hint,
                    "objetivo_educativo": objective,
                    "tipo_actividad": activity_type,
                    "tipo_contenido": recommendation_type,
                    "estado_estudiante": evento,
                    "precision_actual": precision,
                    "max_palabras": max_words
                },
                "output_requirements": {
                    "tipo": "recomendacion_especifica",
                    "max_palabras": max_words,
                    "debe_cumplir": [
                        "Usar reglas fundamentales de LSM del contexto",
                        "Integrar el hint proporcionado de forma pedagógica",
                        "Alinearse con el objetivo educativo",
                        "Ser motivador y accesible para el estudiante"
                    ]
                }
            }
            
            prompt_text = f"""Basándote en este esquema JSON, genera una recomendación educativa LSM:

{json.dumps(json_prompt, ensure_ascii=False, indent=2)}

Contexto de reglas LSM:
{json.dumps(self.lsm_prompt.get("estructura_basica", {}), ensure_ascii=False, indent=2)}

Genera SOLO el contenido recomendado, sin explicaciones adicionales."""

            response = self.model.generate_content(prompt_text)
            return response.text if response else None
            
        except Exception:
            print(f"[{self._timestamp()}] [GEMINI] [ERROR] Error generando contenido específico")
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
            
            json_prompt = {
                "schema": "education_lsm_v1",
                "meta": {
                    "context": "Generación de recomendaciones educativas genéricas LSM",
                    "guidelines": self.lsm_prompt.get("notas_para_ia", [])
                },
                "input": {
                    "tipo_actividad": activity_type,
                    "tipo_contenido": recommendation_type,
                    "estado_estudiante": evento,
                    "precision_actual": precision,
                    "max_palabras": max_words
                },
                "output_requirements": {
                    "tipo": "recomendacion_generica",
                    "max_palabras": max_words,
                    "debe_cumplir": [
                        "Ser universal y reutilizable",
                        "Aplicable a diferentes contextos de aprendizaje",
                        "Motivador y accesible",
                        "Alineado con principios pedagógicos LSM"
                    ]
                }
            }
            
            prompt_text = f"""Basándote en este esquema JSON, genera una recomendación educativa LSM genérica:

{json.dumps(json_prompt, ensure_ascii=False, indent=2)}

Reglas fundamentales de LSM:
{json.dumps(self.lsm_prompt.get("reglas_fundamentales", []), ensure_ascii=False, indent=2)}

Genera SOLO el contenido recomendado, sin explicaciones adicionales."""

            response = self.model.generate_content(prompt_text)
            return response.text if response else None
            
        except Exception:
            print(f"[{self._timestamp()}] [GEMINI] [ERROR] Error generando contenido genérico")
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

    @staticmethod
    def _timestamp() -> str:
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')