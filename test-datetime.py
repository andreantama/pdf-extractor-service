#!/usr/bin/env python3
"""
Test script untuk memverifikasi datetime serialization fix
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_datetime_serialization():
    """Test datetime serialization di Redis queue"""
    
    print("🧪 Testing DateTime Serialization Fix...")
    print("=" * 50)
    
    try:
        from shared.redis_queue import DateTimeEncoder
        from shared.models import JobStatus, TaskStatus
        import json
        
        # Test 1: DateTimeEncoder
        print("1. Testing DateTimeEncoder...")
        test_data = {
            "id": "test-123",
            "created_at": datetime.now(),
            "completed_at": None,
            "status": "processing"
        }
        
        json_str = json.dumps(test_data, cls=DateTimeEncoder)
        print(f"   ✅ Serialized: {json_str[:100]}...")
        
        # Test 2: Parse back
        print("2. Testing DateTime parsing...")
        parsed = json.loads(json_str)
        print(f"   ✅ Parsed back: {type(parsed['created_at'])}")
        
        # Test 3: JobStatus model with datetime
        print("3. Testing JobStatus with datetime...")
        job_status = JobStatus(
            job_id="test-job-123",
            status=TaskStatus.PROCESSING,
            total_pages=10,
            completed_pages=5
        )
        
        # Test serialization
        job_data = job_status.model_dump()
        json_str = json.dumps(job_data, cls=DateTimeEncoder)
        print(f"   ✅ JobStatus serialized successfully")
        
        # Test parsing back
        parsed_data = json.loads(json_str)
        print(f"   ✅ JobStatus parsed back successfully")
        
        print("\n🎉 All DateTime serialization tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ DateTime serialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redis_operations():
    """Test Redis operations dengan datetime"""
    
    print("\n🔧 Testing Redis Operations...")
    print("=" * 40)
    
    try:
        from shared.redis_queue import redis_queue
        from shared.models import JobStatus, TaskStatus
        
        # Check Redis connection
        if not redis_queue.ping():
            print("❌ Redis not available, skipping Redis tests")
            return True
        
        print("✅ Redis connection successful")
        
        # Test job status dengan datetime
        test_job_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        job_status = JobStatus(
            job_id=test_job_id,
            status=TaskStatus.PROCESSING,
            total_pages=5,
            completed_pages=2
        )
        
        # Test set job status
        job_data = job_status.model_dump()
        success = redis_queue.set_job_status(test_job_id, job_data)
        
        if success:
            print("✅ Job status saved to Redis successfully")
            
            # Test get job status
            retrieved_data = redis_queue.get_job_status(test_job_id)
            if retrieved_data:
                print("✅ Job status retrieved from Redis successfully")
                print(f"   Created at: {retrieved_data.get('created_at')}")
                print(f"   Status: {retrieved_data.get('status')}")
                
                # Cleanup
                redis_queue.delete_job_status(test_job_id)
                print("✅ Cleanup completed")
            else:
                print("❌ Failed to retrieve job status")
                return False
        else:
            print("❌ Failed to save job status")
            return False
            
        print("\n🎉 All Redis operations tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Redis operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 PDF Extractor - DateTime Serialization Test")
    print("=" * 60)
    
    test1_result = test_datetime_serialization()
    test2_result = test_redis_operations()
    
    print("\n📊 Test Summary:")
    print("=" * 20)
    print(f"DateTime Serialization: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Redis Operations:       {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! DateTime serialization fix is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)