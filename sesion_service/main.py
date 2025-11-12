from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from src.infrastructure.persistence.database import engine, Base
from src.infrastructure.config.settings import SERVICE_PORT
from src.presentation.routes.session_routes import router
from src.infrastructure.jobs.session_expiration_job import SessionExpirationJob

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    job = SessionExpirationJob()
    scheduler.add_job(job.mark_paused_sessions, 'interval', seconds=30)
    scheduler.add_job(job.mark_expired_sessions, 'interval', seconds=3600)
    scheduler.start()
    
    yield
    
    scheduler.shutdown()

app = FastAPI(
    title="Session Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "session-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)