from celery import Celery
from datetime import datetime, timedelta
from database import documents_collection
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
app = Celery('tasks', broker='amqp://localhost:5672//')

@app.task
def cleanup_old_documents():
    """Clean up documents older than 30 days at the end of each month."""
    try:
        today = datetime.now()
        if today.day == 1:  
            cutoff_date = today - timedelta(days=30)
            
            # Delete documents older than 30 days
            result = documents_collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old documents")
            return f"Successfully cleaned up {result.deleted_count} documents"
        return "Not the end of the month, skipping cleanup"
    except Exception as e:
        logger.error(f"Error during document cleanup: {str(e)}")
        return f"Error during cleanup: {str(e)}"

app.conf.beat_schedule = {
    'cleanup-documents': {
        'task': 'tasks.cleanup_old_documents',
        'schedule': timedelta(days=1),
    },
} 