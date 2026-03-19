from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "job_tracker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email_processor"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "poll-imap-accounts": {
        "task": "app.tasks.email_processor.poll_all_imap_accounts",
        "schedule": settings.IMAP_POLL_INTERVAL_MINUTES * 60,  # seconds
    },
}
