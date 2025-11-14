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
            os.path.dirname(__file__),
            "lsm-grammar-prompt.json"
        )
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            cls._cached_prompt = json.load(f)
        
        return cls._cached_prompt