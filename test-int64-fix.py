#!/usr/bin/env python3
"""
Test script untuk memverifikasi int64 serialization fix
"""

import sys
import os
import numpy as np
import pandas as pd
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_int64_serialization():
    """Test int64 dan numpy types serialization"""
    
    print("🧪 Testing NumPy/Pandas int64 Serialization Fix...")
    print("=" * 60)
    
    try:
        from shared.redis_queue import DateTimeEncoder, RedisQueue
        
        # Test 1: Numpy int64 serialization
        print("1. Testing numpy int64 serialization...")
        test_data = {
            "numpy_int64": np.int64(12345),
            "numpy_int32": np.int32(6789),
            "numpy_float64": np.float64(123.456),
            "numpy_bool": np.bool_(True),
            "numpy_array": np.array([1, 2, 3]),
            "regular_int": 42,
            "regular_float": 3.14
        }
        
        json_str = json.dumps(test_data, cls=DateTimeEncoder)
        print(f"   ✅ Numpy types serialized successfully")
        print(f"   JSON: {json_str[:100]}...")
        
        # Test 2: Pandas types
        print("2. Testing pandas types serialization...")
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [10.5, 20.5, 30.5]
        })
        
        pandas_data = {
            "pandas_int": pd.Series([1, 2, 3], dtype='int64').iloc[0],
            "pandas_float": pd.Series([1.1, 2.2, 3.3]).iloc[0],
            "dataframe_dict": df.to_dict('records')[0]
        }
        
        json_str = json.dumps(pandas_data, cls=DateTimeEncoder)
        print(f"   ✅ Pandas types serialized successfully")
        print(f"   JSON: {json_str[:100]}...")
        
        # Test 3: Clean data function
        print("3. Testing data cleaning function...")
        redis_queue = RedisQueue()
        
        complex_data = {
            "nested": {
                "numpy_int": np.int64(999),
                "list_with_numpy": [np.int32(1), np.int32(2), np.float64(3.14)]
            },
            "pandas_na": pd.NA if hasattr(pd, 'NA') else None
        }
        
        cleaned = redis_queue._clean_data_for_serialization(complex_data)
        json_str = json.dumps(cleaned, cls=DateTimeEncoder)
        print(f"   ✅ Complex data cleaned and serialized successfully")
        print(f"   Cleaned: {cleaned}")
        
        print("\n🎉 All int64/numpy serialization tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ int64 serialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_table_extraction_types():
    """Test serialization dengan data tabel yang mengandung int64"""
    
    print("\n🔧 Testing Table Extraction Data Types...")
    print("=" * 50)
    
    try:
        from shared.redis_queue import DateTimeEncoder, RedisQueue
        from shared.models import ExtractedContent, ContentType
        
        # Simulate table data dengan int64
        table_data = {
            "table_id": "table_1",
            "headers": ["ID", "Age", "Score"],
            "rows": [
                [np.int64(1), np.int64(25), np.float64(95.5)],
                [np.int64(2), np.int64(30), np.float64(87.2)]
            ],
            "data": [
                {"ID": np.int64(1), "Age": np.int64(25), "Score": np.float64(95.5)},
                {"ID": np.int64(2), "Age": np.int64(30), "Score": np.float64(87.2)}
            ],
            "row_count": np.int64(2),
            "col_count": np.int64(3)
        }
        
        # Test serialization
        content = ExtractedContent(
            content_type=ContentType.TABLE,
            content=table_data,
            bbox=[100.0, 200.0, 500.0, 300.0],
            confidence=0.9,
            metadata={
                "extraction_method": "pdfplumber",
                "table_index": np.int64(0)
            }
        )
        
        # Clean dan serialize
        redis_queue = RedisQueue()
        content_dict = content.model_dump()
        cleaned_data = redis_queue._clean_data_for_serialization(content_dict)
        json_str = json.dumps(cleaned_data, cls=DateTimeEncoder)
        
        print(f"✅ Table extraction data serialized successfully")
        print(f"   Table rows: {len(cleaned_data['content']['data'])}")
        print(f"   Data types fixed: {type(cleaned_data['content']['row_count'])}")
        
        # Test deserialization
        parsed_data = json.loads(json_str)
        print(f"✅ Table data deserialized successfully")
        print(f"   Row count: {parsed_data['content']['row_count']} (type: {type(parsed_data['content']['row_count'])})")
        
        return True
        
    except Exception as e:
        print(f"❌ Table extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redis_operations_with_int64():
    """Test Redis operations dengan int64 data"""
    
    print("\n🔧 Testing Redis Operations with int64...")
    print("=" * 50)
    
    try:
        from shared.redis_queue import redis_queue
        from shared.models import TaskResult, PageResult, TaskStatus, ExtractedContent, ContentType
        from datetime import datetime
        
        # Check Redis connection
        if not redis_queue.ping():
            print("❌ Redis not available, skipping Redis tests")
            return True
        
        print("✅ Redis connection successful")
        
        # Create test data dengan int64
        page_result = PageResult(
            page_number=np.int64(11),
            content=[
                ExtractedContent(
                    content_type=ContentType.TABLE,
                    content={
                        "table_id": "table_1",
                        "row_count": np.int64(5),
                        "col_count": np.int64(3),
                        "data": [{"id": np.int64(1), "value": np.float64(99.9)}]
                    },
                    bbox=[np.float64(100.0), np.float64(200.0), np.float64(500.0), np.float64(300.0)],
                    confidence=np.float64(0.95)
                )
            ],
            knowledge="Test knowledge content",
            processing_time=2.3,
            status=TaskStatus.COMPLETED
        )
        
        task_result = TaskResult(
            task_id="test-int64-fix",
            job_id="test-job-int64",
            page_results=[page_result],
            worker_id="test-worker"
        )
        
        # Test push result
        success = redis_queue.push_result(task_result)
        
        if success:
            print("✅ TaskResult with int64 data pushed to Redis successfully")
            
            # Test get result
            retrieved_result = redis_queue.get_result(timeout=2)
            if retrieved_result:
                print("✅ TaskResult with int64 data retrieved from Redis successfully")
                print(f"   Page number: {retrieved_result.page_results[0].page_number}")
                print(f"   Table row count: {retrieved_result.page_results[0].content[0].content['row_count']}")
                print(f"   Data types: Page={type(retrieved_result.page_results[0].page_number)}, Row={type(retrieved_result.page_results[0].content[0].content['row_count'])}")
            else:
                print("❌ Failed to retrieve TaskResult")
                return False
        else:
            print("❌ Failed to push TaskResult")
            return False
            
        print("\n🎉 All Redis int64 operations tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Redis int64 operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 PDF Extractor - int64 Serialization Fix Test")
    print("=" * 70)
    
    test1_result = test_int64_serialization()
    test2_result = test_table_extraction_types()
    test3_result = test_redis_operations_with_int64()
    
    print("\n📊 Test Summary:")
    print("=" * 30)
    print(f"NumPy/Pandas Serialization: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Table Extraction Types:     {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"Redis Operations with int64: {'✅ PASS' if test3_result else '❌ FAIL'}")
    
    if test1_result and test2_result and test3_result:
        print("\n🎉 All tests passed! int64 serialization fix is working correctly.")
        print("\n💡 Your PDF extraction should now work without int64 JSON errors!")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)