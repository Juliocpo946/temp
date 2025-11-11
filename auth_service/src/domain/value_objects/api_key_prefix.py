class ApiKeyPrefix:
    @staticmethod
    def generate(platform: str, environment: str) -> str:
        return f"pk_{platform}_{environment}_"
    
    @staticmethod
    def parse(key_value: str) -> dict:
        parts = key_value.split('_')
        if len(parts) >= 3:
            return {
                'platform': parts[1],
                'environment': parts[2]
            }
        return {}