import google.generativeai as genai
import json
from typing import Optional
from datetime import datetime
from src.infrastructure.config.settings import (
    GEMINI_API_KEY,
    GEMINI_RATE_LIMIT_PER_MINUTE,
    GEMINI_TIMEOUT
)
from src.infrastructure.prompts.prompt_loader import LSMPromptLoader
from src.infrastructure.cache.redis_client import RedisClient


class GeminiClient:
    def __init__(self, redis_client: Optional[RedisClient] = None):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.lsm_prompt = LSMPromptLoader.load()
        self.redis_client = redis_client
        self._default_content = {
            "vibration": {
                "frustracion": "Respira profundo. Puedes hacerlo, intenta de nuevo con calma.",
                "desatencion": "Enfoca tu atencion en la actividad. Tu puedes lograrlo.",
                "cansancio_cognitivo": "Toma un momento para relajarte antes de continuar."
            },
            "instruction": {
                "frustracion": "Vamos paso a paso. Lee con calma las instrucciones y piensa en lo que ya sabes sobre el tema. Si necesitas ayuda, no dudes en pedirla.",
                "desatencion": "Concentrate en la actividad actual. Elimina distracciones y enfoca tu mente en el objetivo. Puedes lograrlo si te enfocas.",
                "cansancio_cognitivo": "Es normal sentirse cansado. Toma un breve descanso de 5 minutos y luego regresa con energia renovada."
            },
            "pause": {
                "frustracion": "Es momento de pausar. Alejate un momento, respira profundo y regresa cuando te sientas mejor.",
                "desatencion": "Toma una pausa corta. Estira tu cuerpo, descansa tus ojos y regresa enfocado.",
                "cansancio_cognitivo": "Tu mente necesita descanso. Toma una pausa de 10-15 minutos antes de continuar."
            }
        }

    def _check_rate_limit(self) -> bool:
        if not self.redis_client:
            return True
        current_count = self.redis_client.get_gemini_calls_count()
        return current_count < GEMINI_RATE_LIMIT_PER_MINUTE

    def _increment_rate_limit(self) -> None:
        if self.redis_client:
            self.redis_client.increment_gemini_calls()

    def _get_default_content(self, intervention_type: str, cognitive_event: str) -> str:
        type_defaults = self._default_content.get(intervention_type, self._default_content["instruction"])
        return type_defaults.get(cognitive_event, type_defaults.get("frustracion", "Continua con tu actividad."))

    def _get_cached_content(
        self,
        topic: str,
        intervention_type: str,
        cognitive_event: str
    ) -> Optional[str]:
        if not self.redis_client:
            return None
        return self.redis_client.get_generated_content(topic, intervention_type, cognitive_event)

    def _cache_content(
        self,
        topic: str,
        intervention_type: str,
        cognitive_event: str,
        content: str
    ) -> None:
        if self.redis_client:
            self.redis_client.set_generated_content(topic, intervention_type, cognitive_event, content)

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
        cached = self._get_cached_content(topic, intervention_type, cognitive_event)
        if cached:
            print(f"[GEMINI_CLIENT] [INFO] Usando contenido cacheado para: {topic[:30]}...")
            return cached

        if not self._check_rate_limit():
            print(f"[GEMINI_CLIENT] [WARNING] Rate limit alcanzado, usando contenido por defecto")
            return self._get_default_content(intervention_type, cognitive_event)

        try:
            self._increment_rate_limit()

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

            response = self.model.generate_content(
                prompt_text,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=200
                )
            )

            if response and response.text:
                content = response.text.strip()
                print(f"[GEMINI_CLIENT] [INFO] Contenido generado exitosamente")
                self._cache_content(topic, intervention_type, cognitive_event, content)
                return content

            print(f"[GEMINI_CLIENT] [WARNING] Respuesta vacia de Gemini, usando contenido por defecto")
            return self._get_default_content(intervention_type, cognitive_event)

        except Exception as e:
            print(f"[GEMINI_CLIENT] [ERROR] Error generando contenido con Gemini: {str(e)}")
            return self._get_default_content(intervention_type, cognitive_event)

    def _get_max_words(self, intervention_type: str) -> int:
        max_words_map = {
            'vibration': 30,
            'instruction': 60,
            'pause': 40
        }
        return max_words_map.get(intervention_type, 50)