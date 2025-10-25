#!/bin/bash

# Script untuk testing PDF Extractor Service

BASE_URL="http://localhost:8000"

echo "🧪 Testing PDF Extractor Service..."
echo "=================================="

# Test 1: Health Check
echo "1. Testing health check..."
HEALTH_RESPONSE=$(curl -s $BASE_URL/health)
if [[ $? -eq 0 ]]; then
    echo "✅ Health check passed"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "❌ Health check failed"
    exit 1
fi

echo ""

# Test 2: Root endpoint
echo "2. Testing root endpoint..."
ROOT_RESPONSE=$(curl -s $BASE_URL/)
if [[ $? -eq 0 ]]; then
    echo "✅ Root endpoint working"
    echo "   Response: $ROOT_RESPONSE"
else
    echo "❌ Root endpoint failed"
fi

echo ""

# Test 3: Upload PDF (requires sample PDF)
echo "3. Testing PDF upload..."
if [[ -f "sample.pdf" ]]; then
    echo "   Uploading sample.pdf..."
    UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/upload-pdf" \
                     -H "Content-Type: multipart/form-data" \
                     -F "file=@sample.pdf")
    
    if [[ $? -eq 0 ]]; then
        echo "✅ PDF upload successful"
        echo "   Response: $UPLOAD_RESPONSE"
        
        # Extract job_id from response
        JOB_ID=$(echo $UPLOAD_RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        
        if [[ -n "$JOB_ID" ]]; then
            echo "   Job ID: $JOB_ID"
            
            # Test 4: Check job status
            echo ""
            echo "4. Testing job status check..."
            sleep 2  # Wait a bit
            STATUS_RESPONSE=$(curl -s "$BASE_URL/job-status/$JOB_ID")
            if [[ $? -eq 0 ]]; then
                echo "✅ Job status check successful"
                echo "   Response: $STATUS_RESPONSE"
            else
                echo "❌ Job status check failed"
            fi
            
            # Test 5: Wait for completion and get results
            echo ""
            echo "5. Waiting for job completion..."
            for i in {1..30}; do
                STATUS_RESPONSE=$(curl -s "$BASE_URL/job-status/$JOB_ID")
                STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
                
                echo "   Attempt $i/30 - Status: $STATUS"
                
                if [[ "$STATUS" == "completed" ]]; then
                    echo "✅ Job completed successfully!"
                    
                    # Get final results
                    echo ""
                    echo "6. Getting final results..."
                    RESULT_RESPONSE=$(curl -s "$BASE_URL/job-result/$JOB_ID")
                    if [[ $? -eq 0 ]]; then
                        echo "✅ Results retrieved successfully"
                        echo "   Results: $RESULT_RESPONSE"
                    else
                        echo "❌ Failed to get results"
                    fi
                    break
                elif [[ "$STATUS" == "failed" ]]; then
                    echo "❌ Job failed"
                    break
                fi
                
                sleep 3
            done
        fi
    else
        echo "❌ PDF upload failed"
    fi
else
    echo "⚠️  No sample.pdf found. Skipping upload test."
    echo "   To test upload, place a PDF file named 'sample.pdf' in this directory."
fi

echo ""
echo "🏁 Testing completed!"
echo ""
echo "📖 For more detailed testing, visit: $BASE_URL/docs"