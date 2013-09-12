from ai import settings

from notification.engine import send_all

from celery.task import task
from celery.utils.log import get_task_logger
celery_logger = get_task_logger(__name__) 

import logging
logger = logging.getLogger(__name__)

@task
def emit_notices():
    celery_logger.info("Emitting notices ...")
    send_all()
