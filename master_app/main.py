from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from pathlib import Path
import PyPDF2
from typing import List
import asyncio
from datetime import datetime
import time

# Import shared modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.config import settings
from shared.models import (
    PDFUploadResponse, PDFProcessingResult, JobStatus, TaskStatus,
    PageTask, TaskResult
)
from shared.redis_queue import redis_queue
from loguru import logger

# Configure logging
logger.add("logs/master_app.log", rotation="500 MB", level=settings.log_level)

app = FastAPI(
    title="PDF Extractor Master Service",
    description="Master service untuk PDF extraction dengan worker pattern",
    version="1.0.0"
)

# Global storage untuk job status
jobs_storage = {}

@app.on_event("startup")
async def startup_event():
    """Initialize master app"""
    # Create necessary directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.temp_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Test Redis connection
    if not redis_queue.ping():
        logger.error("Failed to connect to Redis")
        raise Exception("Redis connection failed")
    
    logger.info("Master app started successfully")
    
    # Start background task untuk mengumpulkan hasil
    asyncio.create_task(collect_results_background())

async def collect_results_background():
    """Background task untuk mengumpulkan hasil dari worker"""
    logger.info("Starting result collection background task")
    
    while True:
        try:
            # Get result from queue dengan timeout pendek
            result = redis_queue.get_result(timeout=1)
            if result:
                await process_worker_result(result)
            else:
                # Jika tidak ada result, tunggu sebentar
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in result collection: {e}")
            await asyncio.sleep(1)

async def process_worker_result(result: TaskResult):
    """Process hasil dari worker"""
    job_id = result.job_id
    
    # Update job status
    job_status = redis_queue.get_job_status(job_id)
    if not job_status:
        logger.warning(f"Job status not found for job_id: {job_id}")
        return
    
    job = JobStatus(**job_status)
    
    # Add hasil dari worker
    job.results.extend(result.page_results)
    job.completed_pages += len(result.page_results)
    
    # Check if semua halaman sudah selesai
    if job.completed_pages >= job.total_pages:
        job.status = TaskStatus.COMPLETED
        job.completed_at = datetime.now()
        logger.info(f"Job {job_id} completed successfully")
    
    # Update job status di Redis
    redis_queue.set_job_status(job_id, job.model_dump())
    
    # Store in memory untuk quick access
    jobs_storage[job_id] = job

def get_pdf_page_count(file_path: str) -> int:
    """Get jumlah halaman dari PDF"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages)
    except Exception as e:
        logger.error(f"Error getting page count: {e}")
        raise HTTPException(status_code=400, detail="Invalid PDF file")

def split_pages_for_workers(total_pages: int, pages_per_worker: int = None) -> List[List[int]]:
    """Split halaman untuk workers"""
    if pages_per_worker is None:
        pages_per_worker = settings.pages_per_worker
    
    page_groups = []
    for i in range(0, total_pages, pages_per_worker):
        end_page = min(i + pages_per_worker, total_pages)
        page_numbers = list(range(i + 1, end_page + 1))  # PDF pages are 1-indexed
        page_groups.append(page_numbers)
    
    return page_groups

@app.post("/upload-pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload PDF dan mulai processing"""
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if file.size > settings.max_file_size:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_path = os.path.join(settings.upload_dir, f"{job_id}.pdf")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get total pages
        total_pages = get_pdf_page_count(file_path)
        
        # Create job status
        job_status = JobStatus(
            job_id=job_id,
            status=TaskStatus.PENDING,
            total_pages=total_pages
        )
        
        # Store job status
        redis_queue.set_job_status(job_id, job_status.model_dump())
        jobs_storage[job_id] = job_status
        
        # Start processing in background
        background_tasks.add_task(process_pdf_async, job_id, file_path, total_pages)
        
        logger.info(f"PDF uploaded successfully: job_id={job_id}, pages={total_pages}")
        
        return PDFUploadResponse(
            job_id=job_id,
            total_pages=total_pages,
            status=TaskStatus.PENDING,
            message=f"PDF uploaded successfully. Processing {total_pages} pages."
        )
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

async def process_pdf_async(job_id: str, file_path: str, total_pages: int):
    """Process PDF secara async"""
    try:
        # Update job status to processing
        job_status = jobs_storage[job_id]
        job_status.status = TaskStatus.PROCESSING
        redis_queue.set_job_status(job_id, job_status.model_dump())
        
        # Split pages untuk workers
        page_groups = split_pages_for_workers(total_pages)
        
        logger.info(f"Splitting {total_pages} pages into {len(page_groups)} tasks for job {job_id}")
        
        # Send tasks ke workers
        for i, page_numbers in enumerate(page_groups):
            task = PageTask(
                task_id=f"{job_id}_{i}",
                job_id=job_id,
                page_numbers=page_numbers,
                pdf_path=file_path
            )
            
            success = redis_queue.push_task(task)
            if not success:
                logger.error(f"Failed to push task {task.task_id}")
            else:
                logger.info(f"Task {task.task_id} sent to workers for pages {page_numbers}")
        
    except Exception as e:
        logger.error(f"Error processing PDF async: {e}")
        # Update job status to failed
        job_status = jobs_storage.get(job_id)
        if job_status:
            job_status.status = TaskStatus.FAILED
            redis_queue.set_job_status(job_id, job_status.model_dump())

@app.get("/job-status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status dari job"""
    
    # Try memory first
    if job_id in jobs_storage:
        return jobs_storage[job_id]
    
    # Try Redis
    job_status_data = redis_queue.get_job_status(job_id)
    if job_status_data:
        job_status = JobStatus(**job_status_data)
        jobs_storage[job_id] = job_status  # Cache in memory
        return job_status
    
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/job-result/{job_id}", response_model=PDFProcessingResult)
async def get_job_result(job_id: str):
    """Get hasil lengkap dari job"""
    
    job_status = await get_job_status(job_id)
    
    if job_status.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Job not yet completed")
    
    # Sort hasil berdasarkan page number
    sorted_results = sorted(job_status.results, key=lambda x: x.page_number)
    
    processing_time = 0
    if job_status.completed_at and job_status.created_at:
        processing_time = (job_status.completed_at - job_status.created_at).total_seconds()
    
    return PDFProcessingResult(
        job_id=job_id,
        status=job_status.status,
        total_pages=job_status.total_pages,
        completed_pages=job_status.completed_pages,
        failed_pages=job_status.failed_pages,
        processing_time=processing_time,
        results=sorted_results,
        created_at=job_status.created_at,
        completed_at=job_status.completed_at
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = redis_queue.ping()
    
    return {
        "status": "healthy" if redis_status else "unhealthy",
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "PDF Extractor Master Service",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.master_host,
        port=settings.master_port,
        reload=False,
        log_level=settings.log_level.lower()
    )