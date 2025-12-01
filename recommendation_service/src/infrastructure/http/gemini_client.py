import google.generativeai as genai
import time
from typing import Optional, Dict, Any
from datetime import datetime
from src.infrastructure.config.settings import (
    GEMINI_API_KEY,
    GEMINI_RATE_LIMIT_PER_MINUTE,
    GEMINI_TIMEOUT
)
from src.infrastructure.prompts.prompt_loader import LSMPromptLoader
from src.infrastructure.cache.redis_client import RedisClient


class CircuitBreaker:
    STATE_CLOSED = "closed"
    STATE_OPEN = "open"
    STATE_HALF_OPEN = "half_open"

    def __init__(self, redis_client: Optional[RedisClient], service_name: str, 
                 failure_threshold: int = 5, recovery_timeout: int = 60):
        self.redis_client = redis_client
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._local_state = {
            "state": self.STATE_CLOSED,
            "failures": 0,
            "last_failure_time": None,
            "successes_in_half_open": 0
        }

    def _get_state(self) -> Dict[str, Any]:
        if self.redis_client:
            state = self.redis_client.get_circuit_breaker_state(self.service_name)
            if state:
                return state
        return self._local_state

    def _set_state(self, state: Dict[str, Any]) -> None:
        self._local_state = state
        if self.redis_client:
            self.redis_client.set_circuit_breaker_state(self.service_name, state)

    def can_execute(self) -> bool:
        state = self._get_state()
        current_state = state.get("state", self.STATE_CLOSED)

        if current_state == self.STATE_CLOSED:
            return True

        if current_state == self.STATE_OPEN:
            last_failure = state.get("last_failure_time")
            if last_failure:
                elapsed = time.time() - last_failure
                if elapsed >= self.recovery_timeout:
                    state["state"] = self.STATE_HALF_OPEN
                    state["successes_in_half_open"] = 0
                    self._set_state(state)
                    print(f"[CIRCUIT_BREAKER] [INFO] {self.service_name} pasando a HALF_OPEN")
                    return True
            return False

        if current_state == self.STATE_HALF_OPEN:
            return True

        return False

    def record_success(self) -> None:
        state = self._get_state()
        current_state = state.get("state", self.STATE_CLOSED)

        if current_state == self.STATE_HALF_OPEN:
            state["successes_in_half_open"] = state.get("successes_in_half_open", 0) + 1
            if state["successes_in_half_open"] >= 3:
                state["state"] = self.STATE_CLOSED
                state["failures"] = 0
                print(f"[CIRCUIT_BREAKER] [INFO] {self.service_name} recuperado, pasando a CLOSED")
            self._set_state(state)
        elif current_state == self.STATE_CLOSED:
            state["failures"] = max(0, state.get("failures", 0) - 1)
            self._set_state(state)

    def record_failure(self) -> None:
        state = self._get_state()
        current_state = state.get("state", self.STATE_CLOSED)

        state["failures"] = state.get("failures", 0) + 1
        state["last_failure_time"] = time.time()

        if current_state == self.STATE_HALF_OPEN:
            state["state"] = self.STATE_OPEN
            print(f"[CIRCUIT_BREAKER] [INFO] {self.service_name} fallo en HALF_OPEN, volviendo a OPEN")
        elif state["failures"] >= self.failure_threshold:
            state["state"] = self.STATE_OPEN
            print(f"[CIRCUIT_BREAKER] [WARNING] {self.service_name} abierto despues de {state['failures']} fallos")

        self._set_state(state)

    def is_open(self) -> bool:
        state = self._get_state()
        return state.get("state") == self.STATE_OPEN


class GeminiClient:
    def __init__(self, redis_client: Optional[RedisClient] = None):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.lsm_prompt = LSMPromptLoader.load()
        self.redis_client = redis_client
        self.circuit_breaker = CircuitBreaker(redis_client, "gemini", failure_threshold=5, recovery_timeout=60)

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

        if not self.circuit_breaker.can_execute():
            print(f"[GEMINI_CLIENT] [WARNING] Circuit breaker abierto, usando fallback")
            return None

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
- Tema "Fracciones": "Denominador igual primero. Sumar arriba"
- Tema "Lectura patito feo": "Patito diferente. Historia bonita, seguir"
- Tema "Colores": "Rojo azul amarillo. Mezclar colores nuevos"

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
                self.circuit_breaker.record_success()
                return content

            print(f"[GEMINI_CLIENT] [WARNING] Respuesta vacia de Gemini")
            self.circuit_breaker.record_failure()
            return None

        except Exception as e:
            print(f"[GEMINI_CLIENT] [ERROR] Error generando contenido: {str(e)}")
            self.circuit_breaker.record_failure()
            return None