import os
import time
import uuid
import signal
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
import cv2
import numpy as np
from PIL import Image
import pytesseract
import easyocr
import io
import json
from datetime import datetime

# Import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.config import settings
from shared.models import (
    PageTask, TaskResult, PageResult, ExtractedContent, 
    ContentType, TaskStatus
)
from shared.redis_queue import redis_queue
from loguru import logger

# Configure logging
logger.add(os.path.join(settings.logs_dir, "worker_app.log"), rotation="500 MB", level=settings.log_level)

class PDFExtractor:
    def __init__(self):
        self.worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        self.easyocr_reader = easyocr.Reader(['en', 'id'])  # English dan Indonesian
        
    def extract_text_content(self, page) -> List[ExtractedContent]:
        """Extract text content dari halaman"""
        text_contents = []
        
        try:
            # Extract text blocks dengan posisi
            text_blocks = page.get_text("dict")
            
            for block in text_blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text and len(text) > 2:  # Filter text pendek
                                bbox = span["bbox"]  # [x0, y0, x1, y1]
                                
                                content = ExtractedContent(
                                    content_type=ContentType.TEXT,
                                    content=text,
                                    bbox=list(bbox),
                                    confidence=1.0,  # Native text memiliki confidence tinggi
                                    metadata={
                                        "font": span.get("font", ""),
                                        "size": span.get("size", 0),
                                        "flags": span.get("flags", 0)
                                    }
                                )
                                text_contents.append(content)
                                
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            
        return text_contents
    
    def extract_table_content(self, pdf_path: str, page_number: int) -> List[ExtractedContent]:
        """Extract table content dari halaman"""
        table_contents = []
        
        try:
            # Gunakan pdfplumber untuk table extraction
            with pdfplumber.open(pdf_path) as pdf:
                if page_number <= len(pdf.pages):
                    page = pdf.pages[page_number - 1]  # pdfplumber menggunakan 0-indexed
                    
                    # Find tables
                    tables = page.find_tables()
                    
                    for i, table in enumerate(tables):
                        try:
                            # Extract table data
                            table_data = table.extract()
                            if table_data and len(table_data) > 1:  # Minimal header + 1 row
                                
                                # Convert ke format yang lebih mudah dibaca
                                df = pd.DataFrame(table_data[1:], columns=table_data[0])
                                table_dict = df.to_dict('records')
                                
                                # Get table bounds
                                bbox = table.bbox  # [x0, y0, x1, y1]
                                
                                content = ExtractedContent(
                                    content_type=ContentType.TABLE,
                                    content={
                                        "table_id": f"table_{i+1}",
                                        "headers": table_data[0],
                                        "rows": table_data[1:],
                                        "data": table_dict,
                                        "row_count": len(table_data) - 1,
                                        "col_count": len(table_data[0]) if table_data[0] else 0
                                    },
                                    bbox=list(bbox),
                                    confidence=0.9,
                                    metadata={
                                        "extraction_method": "pdfplumber",
                                        "table_index": i
                                    }
                                )
                                table_contents.append(content)
                                
                        except Exception as e:
                            logger.error(f"Error processing table {i}: {e}")
                            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            
        return table_contents
    
    def extract_image_content(self, page) -> List[ExtractedContent]:
        """Extract images dan text dari images"""
        image_contents = []
        
        try:
            # Get images dari halaman
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        # Convert ke PIL Image
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Get image bounds (approximate)
                        img_rect = page.get_image_rects(img)[0] if page.get_image_rects(img) else None
                        bbox = list(img_rect) if img_rect else None
                        
                        # Convert ke numpy array untuk OCR
                        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                        
                        # OCR dengan EasyOCR
                        ocr_results = self.easyocr_reader.readtext(cv_image)
                        
                        extracted_text = []
                        total_confidence = 0
                        
                        for (box, text, confidence) in ocr_results:
                            if confidence > 0.5 and len(text.strip()) > 2:
                                extracted_text.append({
                                    "text": text.strip(),
                                    "confidence": confidence,
                                    "bbox": box
                                })
                                total_confidence += confidence
                        
                        avg_confidence = total_confidence / len(ocr_results) if ocr_results else 0
                        
                        # Save image info
                        content = ExtractedContent(
                            content_type=ContentType.IMAGE,
                            content={
                                "image_id": f"image_{img_index+1}",
                                "width": pix.width,
                                "height": pix.height,
                                "extracted_text": extracted_text,
                                "text_summary": " ".join([item["text"] for item in extracted_text]),
                                "has_text": len(extracted_text) > 0
                            },
                            bbox=bbox,
                            confidence=avg_confidence,
                            metadata={
                                "extraction_method": "easyocr",
                                "image_index": img_index,
                                "total_text_elements": len(extracted_text)
                            }
                        )
                        image_contents.append(content)
                    
                    pix = None  # Cleanup
                    
                except Exception as e:
                    logger.error(f"Error processing image {img_index}: {e}")
                    
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            
        return image_contents
    
    def aggregate_knowledge_from_content(self, content_list: List[ExtractedContent]) -> str:
        """Aggregate all extracted content into a single knowledge string for RAG"""
        knowledge_parts = []
        
        # Group content by type for better organization
        text_parts = []
        table_parts = []
        image_parts = []
        
        for content in content_list:
            if content.content_type == ContentType.TEXT:
                if isinstance(content.content, str) and content.content.strip():
                    text_parts.append(content.content.strip())
                    
            elif content.content_type == ContentType.TABLE:
                if isinstance(content.content, dict):
                    table_data = content.content
                    
                    # Extract table as readable text
                    if "headers" in table_data and "rows" in table_data:
                        headers = table_data["headers"]
                        rows = table_data["rows"]
                        
                        # Format table as text
                        table_text = f"Table: {table_data.get('table_id', 'Unknown')}\n"
                        if headers:
                            table_text += " | ".join(str(h) for h in headers) + "\n"
                            table_text += "-" * (len(" | ".join(str(h) for h in headers))) + "\n"
                            
                        for row in rows:
                            if row:
                                table_text += " | ".join(str(cell) for cell in row) + "\n"
                                
                        table_parts.append(table_text.strip())
                        
            elif content.content_type == ContentType.IMAGE:
                if isinstance(content.content, dict):
                    image_data = content.content
                    
                    # Extract text from image OCR results
                    if "text_summary" in image_data and image_data["text_summary"]:
                        image_text = f"Image {image_data.get('image_id', 'Unknown')} Text: {image_data['text_summary']}"
                        image_parts.append(image_text)
                        
                    # Also include detailed extracted text if available
                    elif "extracted_text" in image_data and image_data["extracted_text"]:
                        extracted_texts = []
                        for text_item in image_data["extracted_text"]:
                            if isinstance(text_item, dict) and "text" in text_item:
                                extracted_texts.append(text_item["text"])
                        
                        if extracted_texts:
                            image_text = f"Image {image_data.get('image_id', 'Unknown')} Text: {' '.join(extracted_texts)}"
                            image_parts.append(image_text)
        
        # Combine all parts with clear separation
        if text_parts:
            knowledge_parts.append("TEXT CONTENT:\n" + "\n".join(text_parts))
            
        if table_parts:
            knowledge_parts.append("TABLE CONTENT:\n" + "\n\n".join(table_parts))
            
        if image_parts:
            knowledge_parts.append("IMAGE TEXT CONTENT:\n" + "\n".join(image_parts))
        
        # Join all parts
        knowledge = "\n\n".join(knowledge_parts)
        
        # Clean up and normalize text
        knowledge = self._clean_knowledge_text(knowledge)
        
        return knowledge
    
    def _clean_knowledge_text(self, text: str) -> str:
        """Clean and normalize knowledge text"""
        import re
        
        # Remove extra whitespaces and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove very short fragments (likely noise)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 2:  # Keep lines with more than 2 characters
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def process_page(self, pdf_path: str, page_number: int) -> PageResult:
        """Process single page dan extract semua content"""
        start_time = time.time()
        
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            page = doc[page_number - 1]  # Convert to 0-indexed
            
            all_content = []
            
            # Extract text content
            text_content = self.extract_text_content(page)
            all_content.extend(text_content)
            logger.info(f"Extracted {len(text_content)} text elements from page {page_number}")
            
            # Extract table content
            table_content = self.extract_table_content(pdf_path, page_number)
            all_content.extend(table_content)
            logger.info(f"Extracted {len(table_content)} tables from page {page_number}")
            
            # Extract image content
            image_content = self.extract_image_content(page)
            all_content.extend(image_content)
            logger.info(f"Extracted {len(image_content)} images from page {page_number}")
            
            doc.close()
            
            # 🤖 Aggregate knowledge for RAG
            knowledge = self.aggregate_knowledge_from_content(all_content)
            logger.info(f"Generated {len(knowledge)} characters of knowledge for page {page_number}")
            
            processing_time = time.time() - start_time
            
            return PageResult(
                page_number=page_number,
                content=all_content,
                knowledge=knowledge,  # 🆕 New aggregated knowledge field
                processing_time=processing_time,
                status=TaskStatus.COMPLETED
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing page {page_number}: {e}")
            
            return PageResult(
                page_number=page_number,
                content=[],
                knowledge="",  # 🆕 Empty knowledge for failed pages
                processing_time=processing_time,
                status=TaskStatus.FAILED,
                error_message=str(e)
            )
    
    def process_task(self, task: PageTask) -> TaskResult:
        """Process task dari queue"""
        logger.info(f"Processing task {task.task_id} for pages {task.page_numbers}")
        
        page_results = []
        
        for page_number in task.page_numbers:
            try:
                page_result = self.process_page(task.pdf_path, page_number)
                page_results.append(page_result)
                logger.info(f"Completed page {page_number} in {page_result.processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Failed to process page {page_number}: {e}")
                # Add failed result
                page_results.append(PageResult(
                    page_number=page_number,
                    content=[],
                    processing_time=0,
                    status=TaskStatus.FAILED,
                    error_message=str(e)
                ))
        
        return TaskResult(
            task_id=task.task_id,
            job_id=task.job_id,
            page_results=page_results,
            worker_id=self.worker_id
        )

class PDFWorker:
    def __init__(self):
        self.extractor = PDFExtractor()
        self.running = True
        
        # Setup signal handlers untuk graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def run(self):
        """Main worker loop"""
        logger.info(f"Worker {self.extractor.worker_id} started")
        
        # Create logs directory using absolute path
        os.makedirs(settings.logs_dir, exist_ok=True)
        
        # Log path information
        logger.info(f"Using logs directory: {settings.logs_dir}")
        
        # Test Redis connection
        if not redis_queue.ping():
            logger.error("Cannot connect to Redis, exiting...")
            sys.exit(1)
        
        while self.running:
            try:
                # Get task dari queue
                task = redis_queue.get_task(timeout=5)
                
                if task:
                    logger.info(f"Received task {task.task_id}")
                    
                    # Process task
                    result = self.extractor.process_task(task)
                    
                    # Send result back
                    success = redis_queue.push_result(result)
                    if success:
                        logger.info(f"Result sent for task {task.task_id}")
                    else:
                        logger.error(f"Failed to send result for task {task.task_id}")
                        
                else:
                    # No task available, continue loop
                    pass
                    
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)  # Wait before retrying
        
        logger.info(f"Worker {self.extractor.worker_id} stopped")

if __name__ == "__main__":
    worker = PDFWorker()
    worker.run()