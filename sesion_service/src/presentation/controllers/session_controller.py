from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.session_repository_impl import SessionRepositoryImpl
from src.infrastructure.persistence.repositories.activity_log_repository_impl import ActivityLogRepositoryImpl
from src.infrastructure.persistence.repositories.analysis_config_repository_impl import AnalysisConfigRepositoryImpl
from src.infrastructure.persistence.repositories.external_activity_repository_impl import ExternalActivityRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.create_session import CreateSessionUseCase
from src.application.use_cases.get_session import GetSessionUseCase
from src.application.use_cases.finalize_session import FinalizeSessionUseCase
from src.application.use_cases.start_activity import StartActivityUseCase
from src.application.use_cases.update_config import UpdateConfigUseCase
from src.presentation.schemas.session_schema import SessionCreateSchema, SessionResponseSchema
from src.presentation.schemas.activity_schema import ActivityStartSchema
from src.presentation.schemas.config_schema import ConfigUpdateSchema

router = APIRouter()
rabbitmq_client = RabbitMQClient()

@router.post("/", response_model=SessionResponseSchema)
def create_session(
    session_data: SessionCreateSchema,
    db: Session = Depends(get_db),
    x_company_id: str = Header(None, alias="X-Company-ID")
):
    try:
        if not x_company_id:
            raise HTTPException(status_code=401, detail="X-Company-ID header missing")

        session_repo = SessionRepositoryImpl(db)
        config_repo = AnalysisConfigRepositoryImpl(db)
        use_case = CreateSessionUseCase(session_repo, config_repo, rabbitmq_client)
        result = use_case.execute(
            session_data.user_id,
            x_company_id,
            session_data.disability_type,
            session_data.cognitive_analysis_enabled
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Error creando sesion: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    try:
        session_repo = SessionRepositoryImpl(db)
        activity_log_repo = ActivityLogRepositoryImpl(db)
        use_case = GetSessionUseCase(session_repo, activity_log_repo, rabbitmq_client)
        result = use_case.execute(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{session_id}")
def finalize_session(session_id: str, db: Session = Depends(get_db)):
    try:
        session_repo = SessionRepositoryImpl(db)
        activity_log_repo = ActivityLogRepositoryImpl(db)
        use_case = FinalizeSessionUseCase(session_repo, activity_log_repo, rabbitmq_client)
        result = use_case.execute(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{session_id}/activity/start")
def start_activity(session_id: str, activity_data: ActivityStartSchema, db: Session = Depends(get_db)):
    try:
        session_repo = SessionRepositoryImpl(db)
        activity_log_repo = ActivityLogRepositoryImpl(db)
        external_activity_repo = ExternalActivityRepositoryImpl(db)
        use_case = StartActivityUseCase(session_repo, activity_log_repo, external_activity_repo, rabbitmq_client)
        result = use_case.execute(
            session_id,
            activity_data.external_activity_id,
            activity_data.title,
            activity_data.subtitle,
            activity_data.content,
            activity_data.activity_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{session_id}/config")
def update_config(session_id: str, config_data: ConfigUpdateSchema, db: Session = Depends(get_db)):
    try:
        config_repo = AnalysisConfigRepositoryImpl(db)
        use_case = UpdateConfigUseCase(config_repo, rabbitmq_client)
        result = use_case.execute(
            session_id,
            config_data.cognitive_analysis_enabled,
            config_data.text_notifications,
            config_data.video_suggestions,
            config_data.vibration_alerts,
            config_data.pause_suggestions
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))