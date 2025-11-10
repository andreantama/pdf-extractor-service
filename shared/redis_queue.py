import redis
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Any, Optional
from .config import settings
from .models import PageTask, TaskResult
from loguru import logger

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder untuk handle datetime objects dan numpy/pandas types"""
    def default(self, obj):
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle numpy integers
        if isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64)):
            return int(obj)
        
        # Handle numpy floats
        if isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
            return float(obj)
        
        # Handle numpy booleans
        if isinstance(obj, np.bool_):
            return bool(obj)
        
        # Handle numpy arrays
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        
        # Handle pandas nullable integers
        if isinstance(obj, pd._libs.missing.NAType):
            return None
        
        # Handle pandas integers and floats
        if hasattr(obj, 'dtype') and hasattr(obj, 'item'):
            # Convert pandas scalars to native Python types
            try:
                return obj.item()
            except (ValueError, TypeError):
                pass
        
        # Handle general pandas types
        if hasattr(pd, 'api') and hasattr(pd.api, 'types'):
            if pd.api.types.is_integer_dtype(type(obj)):
                return int(obj)
            elif pd.api.types.is_float_dtype(type(obj)):
                return float(obj)
            elif pd.api.types.is_bool_dtype(type(obj)):
                return bool(obj)
        
        # Fallback: try to convert to basic Python types
        if hasattr(obj, '__int__'):
            try:
                return int(obj)
            except (ValueError, TypeError, OverflowError):
                pass
        
        if hasattr(obj, '__float__'):
            try:
                return float(obj)
            except (ValueError, TypeError, OverflowError):
                pass
        
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
    
    def _clean_data_for_serialization(self, data: Any) -> Any:
        """Clean data untuk memastikan bisa di-serialize ke JSON"""
        if isinstance(data, dict):
            return {key: self._clean_data_for_serialization(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._clean_data_for_serialization(item) for item in data]
        elif isinstance(data, (np.integer, np.int8, np.int16, np.int32, np.int64)):
            return int(data)
        elif isinstance(data, (np.floating, np.float16, np.float32, np.float64)):
            return float(data)
        elif isinstance(data, np.bool_):
            return bool(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif hasattr(data, 'dtype') and hasattr(data, 'item'):
            # Handle pandas scalars
            try:
                return data.item()
            except (ValueError, TypeError):
                return str(data)
        elif pd.isna(data) or (hasattr(pd, '_libs') and isinstance(data, pd._libs.missing.NAType)):
            return None
        else:
            return data
    
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
            # Clean data dan use custom encoder untuk handle datetime dan numpy types
            task_data_dict = task.model_dump()
            cleaned_data = self._clean_data_for_serialization(task_data_dict)
            task_data = json.dumps(cleaned_data, cls=DateTimeEncoder)
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
            # Clean data dan use custom encoder untuk handle datetime dan numpy types
            result_data_dict = result.model_dump()
            cleaned_data = self._clean_data_for_serialization(result_data_dict)
            result_data = json.dumps(cleaned_data, cls=DateTimeEncoder)
            self.redis_client.lpush(settings.result_queue, result_data)
            logger.info(f"Result for task {result.task_id} pushed to result queue")
            return True
        except Exception as e:
            logger.error(f"Failed to push result for task {result.task_id}: {e}")
            # Log additional debug info
            logger.debug(f"Result data type: {type(result)}")
            if hasattr(result, 'page_results') and result.page_results:
                logger.debug(f"Page results count: {len(result.page_results)}")
                for i, page_result in enumerate(result.page_results[:2]):  # Log first 2 pages
                    logger.debug(f"Page {i+1} content count: {len(page_result.content) if page_result.content else 0}")
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
            # Clean data dan use custom encoder untuk handle datetime dan numpy types
            cleaned_data = self._clean_data_for_serialization(status_data)
            json_data = json.dumps(cleaned_data, cls=DateTimeEncoder)
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