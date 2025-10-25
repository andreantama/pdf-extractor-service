import redis
import json
from typing import Any, Optional
from .config import settings
from .models import PageTask, TaskResult
from loguru import logger

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
            task_data = task.model_dump_json()
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
                task = PageTask.model_validate_json(task_data)
                logger.info(f"Task {task.task_id} retrieved from queue")
                return task
            return None
        except Exception as e:
            logger.error(f"Failed to get task from queue: {e}")
            return None
    
    def push_result(self, result: TaskResult) -> bool:
        """Push result to result queue"""
        try:
            result_data = result.model_dump_json()
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
                task_result = TaskResult.model_validate_json(result_data)
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
            self.redis_client.set(key, json.dumps(status_data), ex=3600)  # Expire in 1 hour
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
                return json.loads(status_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
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