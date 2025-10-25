from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uuid
from datetime import datetime

class ContentType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PageTask(BaseModel):
    task_id: str
    job_id: str
    page_numbers: List[int]
    pdf_path: str
    created_at: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ExtractedContent(BaseModel):
    content_type: ContentType
    content: Union[str, Dict[str, Any]]  # Text string atau table data atau image info
    bbox: Optional[List[float]] = None  # Bounding box [x1, y1, x2, y2]
    confidence: Optional[float] = None  # Confidence score untuk OCR
    metadata: Optional[Dict[str, Any]] = None

class PageResult(BaseModel):
    page_number: int
    content: List[ExtractedContent]
    knowledge: str = ""  # 🆕 Aggregated text content for RAG
    processing_time: float
    status: TaskStatus
    error_message: Optional[str] = None

class TaskResult(BaseModel):
    task_id: str
    job_id: str
    page_results: List[PageResult]
    worker_id: str
    completed_at: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class JobStatus(BaseModel):
    job_id: str
    status: TaskStatus
    total_pages: int
    completed_pages: int = 0
    failed_pages: int = 0
    created_at: datetime = datetime.now()
    completed_at: Optional[datetime] = None
    results: List[PageResult] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PDFUploadResponse(BaseModel):
    job_id: str
    total_pages: int
    status: TaskStatus
    message: str

class PDFProcessingResult(BaseModel):
    job_id: str
    status: TaskStatus
    total_pages: int
    completed_pages: int
    failed_pages: int
    processing_time: float
    results: List[PageResult]
    full_document_knowledge: str = ""  # 🆕 Complete document knowledge
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    def aggregate_knowledge(self) -> str:
        """Aggregate knowledge from all pages into full document knowledge"""
        knowledge_parts = []
        
        for page_result in sorted(self.results, key=lambda x: x.page_number):
            if page_result.knowledge.strip():
                knowledge_parts.append(f"Page {page_result.page_number}:\n{page_result.knowledge}")
        
        self.full_document_knowledge = "\n\n".join(knowledge_parts)
        return self.full_document_knowledge