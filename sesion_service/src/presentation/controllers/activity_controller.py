from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.activity_log_repository_impl import ActivityLogRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.pause_activity import PauseActivityUseCase
from src.application.use_cases.resume_activity import ResumeActivityUseCase
from src.application.use_cases.complete_activity import CompleteActivityUseCase
from src.application.use_cases.abandon_activity import AbandonActivityUseCase
from src.presentation.schemas.activity_schema import ActivityCompleteSchema

router = APIRouter()
rabbitmq_client = RabbitMQClient()

@router.post("/{activity_uuid}/pause")
def pause_activity(activity_uuid: str, db: Session = Depends(get_db)):
    try:
        activity_log_repo = ActivityLogRepositoryImpl(db)
        use_case = PauseActivityUseCase(activity_log_repo, rabbitmq_client)
        result = use_case.execute(activity_uuid)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{activity_uuid}/resume")
def resume_activity(activity_uuid: str, db: Session = Depends(get_db)):
    try:
        activity_log_repo = ActivityLogRepositoryImpl(db)
        use_case = ResumeActivityUseCase(activity_log_repo, rabbitmq_client)
        result = use_case.execute(activity_uuid)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{activity_uuid}/complete")
def complete_activity(activity_uuid: str, activity_data: ActivityCompleteSchema, db: Session = Depends(get_db)):
    try:
        activity_log_repo = ActivityLogRepositoryImpl(db)
        use_case = CompleteActivityUseCase(activity_log_repo, rabbitmq_client)
        result = use_case.execute(activity_uuid, activity_data.feedback)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{activity_uuid}/abandon")
def abandon_activity(activity_uuid: str, db: Session = Depends(get_db)):
    try:
        activity_log_repo = ActivityLogRepositoryImpl(db)
        use_case = AbandonActivityUseCase(activity_log_repo, rabbitmq_client)
        result = use_case.execute(activity_uuid)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{activity_uuid}")
def get_activity(activity_uuid: str, db: Session = Depends(get_db)):
    try:
        activity_log_repo = ActivityLogRepositoryImpl(db)
        activity = activity_log_repo.get_by_uuid(activity_uuid)
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actividad no encontrada")
        
        return {
            'activity_uuid': str(activity.activity_uuid),
            'session_id': str(activity.session_id),
            'external_activity_id': activity.external_activity_id,
            'status': activity.status,
            'started_at': activity.started_at.isoformat(),
            'paused_at': activity.paused_at.isoformat() if activity.paused_at else None,
            'resumed_at': activity.resumed_at.isoformat() if activity.resumed_at else None,
            'completed_at': activity.completed_at.isoformat() if activity.completed_at else None,
            'pause_count': activity.pause_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))