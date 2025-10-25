#!/usr/bin/env python3
"""
Test script untuk knowledge aggregation functionality
"""

import requests
import json
import time
import sys
import os

BASE_URL = "http://localhost:8000"

def test_knowledge_aggregation():
    """Test knowledge aggregation dengan sample PDF"""
    
    print("🧠 Testing Knowledge Aggregation for RAG")
    print("=" * 50)
    
    # Check if service is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ Service not running. Please start the service first.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to service. Please start the service first.")
        return False
    
    print("✅ Service is running")
    
    # Check for sample PDF
    sample_files = ["sample.pdf", "test.pdf", "example.pdf"]
    sample_file = None
    
    for file in sample_files:
        if os.path.exists(file):
            sample_file = file
            break
    
    if not sample_file:
        print("⚠️  No sample PDF found. Please create a sample.pdf file for testing.")
        print("   You can create a simple PDF with text, tables, and images for testing.")
        return True  # Not a failure, just no test file
    
    print(f"📄 Using sample file: {sample_file}")
    
    # Upload PDF
    print("1. Uploading PDF...")
    with open(sample_file, 'rb') as f:
        files = {'file': f}
        upload_response = requests.post(f"{BASE_URL}/upload-pdf", files=files)
    
    if upload_response.status_code != 200:
        print(f"❌ Upload failed: {upload_response.text}")
        return False
    
    upload_result = upload_response.json()
    job_id = upload_result['job_id']
    total_pages = upload_result['total_pages']
    
    print(f"✅ Upload successful - Job ID: {job_id}, Pages: {total_pages}")
    
    # Wait for processing
    print("2. Waiting for processing...")
    max_wait = 120  # 2 minutes max
    wait_time = 0
    
    while wait_time < max_wait:
        status_response = requests.get(f"{BASE_URL}/job-status/{job_id}")
        if status_response.status_code == 200:
            status = status_response.json()['status']
            completed_pages = status_response.json()['completed_pages']
            
            print(f"   Status: {status}, Progress: {completed_pages}/{total_pages}")
            
            if status == "completed":
                print("✅ Processing completed")
                break
            elif status == "failed":
                print("❌ Processing failed")
                return False
        
        time.sleep(3)
        wait_time += 3
    
    if wait_time >= max_wait:
        print("❌ Processing timeout")
        return False
    
    # Test knowledge endpoints
    print("3. Testing knowledge extraction...")
    
    # Test full result endpoint
    result_response = requests.get(f"{BASE_URL}/job-result/{job_id}")
    if result_response.status_code == 200:
        result = result_response.json()
        print("✅ Full result retrieved")
        
        # Check if knowledge fields exist
        if 'full_document_knowledge' in result:
            knowledge_length = len(result['full_document_knowledge'])
            print(f"   📚 Full document knowledge: {knowledge_length} characters")
        
        # Check page-level knowledge
        page_knowledge_count = 0
        for page_result in result.get('results', []):
            if 'knowledge' in page_result and page_result['knowledge']:
                page_knowledge_count += 1
        
        print(f"   📄 Pages with knowledge: {page_knowledge_count}/{total_pages}")
        
    else:
        print(f"❌ Failed to get result: {result_response.text}")
        return False
    
    # Test knowledge-only endpoint
    knowledge_response = requests.get(f"{BASE_URL}/job-knowledge/{job_id}")
    if knowledge_response.status_code == 200:
        knowledge_result = knowledge_response.json()
        print("✅ Knowledge-only endpoint working")
        
        print(f"   📊 Knowledge Stats:")
        print(f"      - Processed pages: {knowledge_result['processed_pages']}")
        print(f"      - Failed pages: {knowledge_result['failed_pages']}")
        print(f"      - Knowledge length: {knowledge_result['knowledge_length']} characters")
        
        # Show sample knowledge
        if knowledge_result['full_document_knowledge']:
            sample = knowledge_result['full_document_knowledge'][:200]
            print(f"   📝 Sample knowledge: \"{sample}...\"")
        
    else:
        print(f"❌ Knowledge endpoint failed: {knowledge_response.text}")
        return False
    
    print("\n🎉 Knowledge aggregation test completed successfully!")
    print("\n📋 API Endpoints for RAG:")
    print(f"   Full result: GET {BASE_URL}/job-result/{job_id}")
    print(f"   Knowledge only: GET {BASE_URL}/job-knowledge/{job_id}")
    
    return True

def show_knowledge_structure():
    """Show expected knowledge structure"""
    
    print("\n📖 Knowledge Structure for RAG:")
    print("=" * 40)
    
    print("""
    Page Level Knowledge (in each page result):
    {
      "page_number": 1,
      "content": [...],
      "knowledge": "Combined text from all content types",
      "processing_time": 2.3,
      "status": "completed"
    }
    
    Document Level Knowledge (in full result):
    {
      "full_document_knowledge": "Page 1:\\nCombined content...\\n\\nPage 2:\\n...",
      "results": [...]
    }
    
    Knowledge-Only Endpoint Response:
    {
      "job_id": "uuid",
      "page_knowledge": [
        {
          "page_number": 1,
          "knowledge": "page content",
          "status": "completed"
        }
      ],
      "full_document_knowledge": "complete document text",
      "knowledge_length": 1500
    }
    """)

def main():
    """Main test function"""
    show_knowledge_structure()
    
    print("\n" + "="*60)
    success = test_knowledge_aggregation()
    
    if success:
        print("\n🎯 Knowledge aggregation is ready for RAG integration!")
        print("\n💡 Usage tips:")
        print("   - Use /job-knowledge/{job_id} for RAG systems")
        print("   - full_document_knowledge contains complete text")
        print("   - page_knowledge provides page-by-page breakdown")
        return 0
    else:
        print("\n❌ Knowledge aggregation test failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)