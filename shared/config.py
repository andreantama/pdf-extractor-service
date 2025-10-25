import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Queue Names
    pdf_processing_queue: str = "pdf_processing_queue"
    result_queue: str = "pdf_result_queue"
    
    # Master App Configuration
    master_host: str = "0.0.0.0"
    master_port: int = 8000
    
    # Worker Configuration
    worker_concurrency: int = 4
    
    # File Upload Configuration
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    upload_dir: str = "uploads"
    temp_dir: str = "temp"
    
    # Processing Configuration
    pages_per_worker: int = 5  # Berapa halaman per worker
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()