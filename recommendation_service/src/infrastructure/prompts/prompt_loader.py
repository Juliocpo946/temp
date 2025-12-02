import json
import os
from typing import Dict, Any


class LSMPromptLoader:
    _cached_prompt = None

    @classmethod
    def load(cls) -> Dict[str, Any]:
        if cls._cached_prompt is not None:
            return cls._cached_prompt

        # CORRECCION: Nombre de archivo ajustado a lo que realmente existe en la carpeta
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "prompts",
            "lsm_grammar.json"
        )

        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                cls._cached_prompt = json.load(f)
                print(f"[PROMPT_LOADER] [INFO] Prompt LSM cargado exitosamente")
        except FileNotFoundError:
            print(f"[PROMPT_LOADER] [WARNING] Archivo de prompt no encontrado en {prompt_path}, usando valores por defecto")
            cls._cached_prompt = {
                "estructura_basica": {},
                "notas_para_ia": [],
                "reglas_fundamentales": []
            }

        return cls._cached_prompt