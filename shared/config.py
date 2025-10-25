import os
from pathlib import Path
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
    
    # 🔧 Path configuration dengan absolute path
    @property
    def project_root(self) -> Path:
        """Get project root directory"""
        current_file = Path(__file__).resolve()
        return current_file.parent.parent  # ../shared/../ = project root
    
    @property
    def upload_dir(self) -> str:
        """Upload directory path (absolute)"""
        upload_path = self.project_root / "uploads"
        upload_path.mkdir(exist_ok=True)  # Create if not exists
        return str(upload_path)
    
    @property
    def temp_dir(self) -> str:
        """Temp directory path (absolute)"""
        temp_path = self.project_root / "temp"
        temp_path.mkdir(exist_ok=True)  # Create if not exists
        return str(temp_path)
    
    @property
    def logs_dir(self) -> str:
        """Logs directory path (absolute)"""
        logs_path = self.project_root / "logs"
        logs_path.mkdir(exist_ok=True)  # Create if not exists
        return str(logs_path)
    
    # Processing Configuration
    pages_per_worker: int = 5  # Berapa halaman per worker
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()