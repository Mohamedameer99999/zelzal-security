import logging
from celery import Celery
from app.core.config import Config

logger = logging.getLogger(__name__)

celery_app = Celery(
    'ai_task_manager',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(bind=True, max_retries=3)
def send_notification(self, user_email, message):
    try:
        logger.info(f'Notification to {user_email}: {message}')
        return {'status': 'sent', 'to': user_email, 'message': message}
    except Exception as e:
        logger.error(f'Failed to send notification to {user_email}: {e}')
        raise self.retry(exc=e, countdown=60)
