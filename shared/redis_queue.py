import redis
import json
from datetime import datetime
from typing import Any, Optional
from .config import settings
from .models import PageTask, TaskResult
from loguru import logger

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder untuk handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class RedisQueue:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
    
    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    def push_task(self, task: PageTask) -> bool:
        """Push task to processing queue"""
        try:
            # Use custom encoder untuk handle datetime
            task_data = json.dumps(task.model_dump(), cls=DateTimeEncoder)
            self.redis_client.lpush(settings.pdf_processing_queue, task_data)
            logger.info(f"Task {task.task_id} pushed to queue")
            return True
        except Exception as e:
            logger.error(f"Failed to push task {task.task_id}: {e}")
            return False
    
    def get_task(self, timeout: int = 10) -> Optional[PageTask]:
        """Get task from processing queue (blocking)"""
        try:
            result = self.redis_client.brpop(settings.pdf_processing_queue, timeout=timeout)
            if result:
                _, task_data = result
                # Parse JSON and handle datetime
                parsed_data = json.loads(task_data)
                parsed_data = self._parse_datetime_fields(parsed_data)
                task = PageTask(**parsed_data)
                logger.info(f"Task {task.task_id} retrieved from queue")
                return task
            return None
        except Exception as e:
            logger.error(f"Failed to get task from queue: {e}")
            return None
    
    def push_result(self, result: TaskResult) -> bool:
        """Push result to result queue"""
        try:
            # Use custom encoder untuk handle datetime
            result_data = json.dumps(result.model_dump(), cls=DateTimeEncoder)
            self.redis_client.lpush(settings.result_queue, result_data)
            logger.info(f"Result for task {result.task_id} pushed to result queue")
            return True
        except Exception as e:
            logger.error(f"Failed to push result for task {result.task_id}: {e}")
            return False
    
    def get_result(self, timeout: int = 1) -> Optional[TaskResult]:
        """Get result from result queue (blocking)"""
        try:
            result = self.redis_client.brpop(settings.result_queue, timeout=timeout)
            if result:
                _, result_data = result
                # Parse JSON and handle datetime
                parsed_data = json.loads(result_data)
                parsed_data = self._parse_datetime_fields(parsed_data)
                task_result = TaskResult(**parsed_data)
                logger.info(f"Result for task {task_result.task_id} retrieved from result queue")
                return task_result
            return None
        except Exception as e:
            logger.error(f"Failed to get result from queue: {e}")
            return None
    
    def set_job_status(self, job_id: str, status_data: dict) -> bool:
        """Store job status in Redis"""
        try:
            key = f"job_status:{job_id}"
            # Use custom encoder untuk handle datetime
            json_data = json.dumps(status_data, cls=DateTimeEncoder)
            self.redis_client.set(key, json_data, ex=3600)  # Expire in 1 hour
            logger.debug(f"Job status saved for {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set job status for {job_id}: {e}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get job status from Redis"""
        try:
            key = f"job_status:{job_id}"
            status_data = self.redis_client.get(key)
            if status_data:
                parsed_data = json.loads(status_data)
                # Convert datetime strings back to datetime objects
                parsed_data = self._parse_datetime_fields(parsed_data)
                return parsed_data
            return None
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    def _parse_datetime_fields(self, data: dict) -> dict:
        """Parse datetime string fields back to datetime objects"""
        datetime_fields = ['created_at', 'completed_at']
        
        for field in datetime_fields:
            if field in data and data[field] is not None:
                try:
                    if isinstance(data[field], str):
                        data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse datetime field {field}: {e}")
                    # Keep as string if parsing fails
                    pass
        
        return data
    
    def delete_job_status(self, job_id: str) -> bool:
        """Delete job status from Redis"""
        try:
            key = f"job_status:{job_id}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete job status for {job_id}: {e}")
            return False

# Global Redis queue instance
redis_queue = RedisQueue()