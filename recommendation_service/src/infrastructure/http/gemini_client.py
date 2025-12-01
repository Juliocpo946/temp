import google.generativeai as genai
import json
from typing import Optional
from src.infrastructure.config.settings import (
    GEMINI_API_KEY,
    GEMINI_RATE_LIMIT_PER_MINUTE
)
from src.infrastructure.prompts.prompt_loader import LSMPromptLoader
from src.infrastructure.cache.redis_client import RedisClient


class GeminiClient:
    def __init__(self, redis_client: Optional[RedisClient] = None):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.lsm_prompt = LSMPromptLoader.load()
        self.redis_client = redis_client

    def _check_rate_limit(self) -> bool:
        if not self.redis_client:
            return True
        current_count = self.redis_client.get_gemini_calls_count()
        return current_count < GEMINI_RATE_LIMIT_PER_MINUTE

    def _increment_rate_limit(self) -> None:
        if self.redis_client:
            self.redis_client.increment_gemini_calls()

    def _get_cached_content(
        self,
        topic: str,
        subtopic: Optional[str],
        cognitive_event: str
    ) -> Optional[str]:
        if not self.redis_client:
            return None
        cache_key = f"{topic}:{subtopic or 'none'}:{cognitive_event}"
        return self.redis_client.get_generated_content(topic, "instruction", cognitive_event)

    def _cache_content(
        self,
        topic: str,
        subtopic: Optional[str],
        cognitive_event: str,
        content: str
    ) -> None:
        if self.redis_client:
            self.redis_client.set_generated_content(topic, "instruction", cognitive_event, content)

    def generate_instruction(
        self,
        topic: str,
        subtopic: Optional[str],
        activity_type: Optional[str],
        title: Optional[str],
        objective: Optional[str],
        cognitive_event: str,
        precision: float
    ) -> Optional[str]:
        cached = self._get_cached_content(topic, subtopic, cognitive_event)
        if cached:
            print(f"[GEMINI_CLIENT] [INFO] Usando contenido cacheado para: {topic[:30]}...")
            return cached

        if not self._check_rate_limit():
            print(f"[GEMINI_CLIENT] [WARNING] Rate limit alcanzado")
            return None

        try:
            self._increment_rate_limit()

            prompt_text = f"""Eres un asistente educativo para ninos sordos. Genera UNA instruccion de ayuda.

REGLAS OBLIGATORIAS:
1. Maximo 10-15 palabras
2. Usar gramatica LSM (Lengua de Senas Mexicana):
   - Sin articulos (el, la, un, una)
   - Sin preposiciones (de, en, con, para)
   - Verbos sin conjugar
   - Orden: Sujeto + Objeto + Verbo
3. Incluir 1 emoji relevante al tema
4. Tono positivo y motivador
5. DEBE ser especifico sobre el tema de la actividad

CONTEXTO DE LA ACTIVIDAD:
- Tema: {topic}
- Subtema: {subtopic or 'No especificado'}
- Tipo: {activity_type or 'Leccion'}
- Titulo: {title or topic}
- Objetivo: {objective or 'Aprender sobre ' + topic}

ESTADO DEL ESTUDIANTE:
- Evento cognitivo: {cognitive_event}
- Precision: {precision}

EJEMPLOS DE FORMATO CORRECTO:
- Tema "Fracciones": "Denominador igual primero. Sumar arriba 🔢"
- Tema "Lectura patito feo": "Patito diferente. Historia bonita, seguir 🦆"
- Tema "Colores": "Rojo azul amarillo. Mezclar colores nuevos 🎨"

Genera SOLO la instruccion, sin explicaciones:"""

            response = self.model.generate_content(
                prompt_text,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=50
                )
            )

            if response and response.text:
                content = response.text.strip()
                content = content.replace('"', '').replace("'", "")
                
                if len(content) > 100:
                    content = content[:100]

                print(f"[GEMINI_CLIENT] [INFO] Instruccion generada: {content}")
                self._cache_content(topic, subtopic, cognitive_event, content)
                return content

            print(f"[GEMINI_CLIENT] [WARNING] Respuesta vacia de Gemini")
            return None

        except Exception as e:
            print(f"[GEMINI_CLIENT] [ERROR] Error generando contenido: {str(e)}")
            return None