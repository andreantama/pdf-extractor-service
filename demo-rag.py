#!/usr/bin/env python3
"""
Demo sederhana untuk knowledge aggregation endpoint
Pastikan service sudah running dengan: ./run-local.sh
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def demo_knowledge_endpoint():
    """Demo penggunaan knowledge endpoint"""
    
    print("🧠 Demo Knowledge Aggregation untuk RAG")
    print("=" * 50)
    
    # Check service health
    try:
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code == 200:
            print("✅ Service is running")
        else:
            print("❌ Service not responding properly")
            return
    except:
        print("❌ Service not running. Please start with: ./run-local.sh")
        return
    
    print("\n📋 Available endpoints for RAG:")
    print(f"   Health: {BASE_URL}/health")
    print(f"   Upload: {BASE_URL}/upload-pdf")
    print(f"   Status: {BASE_URL}/job-status/{{job_id}}")
    print(f"   Result: {BASE_URL}/job-result/{{job_id}}")
    print(f"   🧠 Knowledge: {BASE_URL}/job-knowledge/{{job_id}}")
    
    print("\n💡 Knowledge endpoint benefits for RAG:")
    print("   ✓ Clean and normalized text")
    print("   ✓ Combined text + table + OCR content")
    print("   ✓ Page-level attribution available")
    print("   ✓ Full document aggregation")
    print("   ✓ Optimized for LLM consumption")
    
    print("\n🔧 Usage example:")
    usage_example = '''
    # 1. Upload PDF
    response = requests.post(f"{BASE_URL}/upload-pdf", files={'file': pdf_file})
    job_id = response.json()['job_id']
    
    # 2. Wait for completion
    while True:
        status = requests.get(f"{BASE_URL}/job-status/{job_id}")
        if status.json()['status'] == 'completed':
            break
        time.sleep(2)
    
    # 3. Get knowledge for RAG
    knowledge = requests.get(f"{BASE_URL}/job-knowledge/{job_id}")
    rag_text = knowledge.json()['full_document_knowledge']
    
    # 4. Feed to RAG model
    # llm_response = your_rag_model.generate(query, context=rag_text)
    '''
    print(usage_example)
    
    print("\n📚 Testing:")
    print("   Run: python3 test-knowledge.py")
    print("   Or:  python3 rag-knowledge-example.py")

if __name__ == "__main__":
    demo_knowledge_endpoint()