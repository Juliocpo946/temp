from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.application.dtos.api_key_dto import ApiKeyDTO


class GetApplicationApiKeysUseCase:
    def __init__(self, api_key_repo: ApiKeyRepository):
        self.api_key_repo = api_key_repo

    def execute(self, application_id: str) -> dict:
        api_keys = self.api_key_repo.get_by_application_id(application_id)

        keys_dtos = []
        for key in api_keys:

            dto = ApiKeyDTO(
                id=str(key.id),
                key_value="********************",
                company_id=str(key.company_id),
                application_id=str(key.application_id),
                created_at=key.created_at,
                expires_at=key.expires_at,
                is_active=key.is_active
            )
            keys_dtos.append(dto.to_dict())

        # Ordenamos por fecha de creación (más recientes primero)
        keys_dtos.sort(key=lambda x: x['created_at'], reverse=True)

        return {
            'api_keys': keys_dtos,
            'total': len(keys_dtos)
        }