from enum import Enum

class SessionStatus(str, Enum):
    ACTIVA = "activa"
    PAUSADA = "pausada"
    PAUSADA_AUTOMATICAMENTE = "pausada_automaticamente"
    EXPIRADA = "expirada"
    FINALIZADA = "finalizada"