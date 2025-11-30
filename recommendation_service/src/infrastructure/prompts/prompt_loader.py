import json
import os
from typing import Dict, Any


class LSMPromptLoader:
    _cached_prompt = None

    @classmethod
    def load(cls) -> Dict[str, Any]:
        if cls._cached_prompt is not None:
            return cls._cached_prompt

        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "prompts",
            "lsm-grammar-prompt.json"
        )

        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                cls._cached_prompt = json.load(f)
        except FileNotFoundError:
            cls._cached_prompt = {
                "estructura_basica": {},
                "notas_para_ia": [],
                "reglas_fundamentales": []
            }

        return cls._cached_prompt