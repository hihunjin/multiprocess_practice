import requests
import time
import concurrent.futures
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

def timestamp():
    """Return current timestamp for logging"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def make_request(endpoint, request_id):
    """Make a request to the specified endpoint and return the result"""
    start_time = time.time()
    print(f"[{timestamp()}] Request {request_id} to {endpoint} started")
    
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"[{timestamp()}] Request {request_id} to {endpoint} completed in {elapsed:.2f}s - Result: {json.dumps(result)}")
            return {
                "request_id": request_id,
                "endpoint": endpoint,
                "status": "success",
                "elapsed": elapsed,
                "result": result
            }
        else:
            print(f"[{timestamp()}] Request {request_id} to {endpoint} failed with status {response.status_code} in {elapsed:.2f}s")
            return {
                "request_id": request_id,
                "endpoint": endpoint,
                "status": "error",
                "elapsed": elapsed,
                "status_code": response.status_code,
                "error": response.text
            }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[{timestamp()}] Request {request_id} to {endpoint} exception: {str(e)} in {elapsed:.2f}s")
        return {
            "request_id": request_id,
            "endpoint": endpoint,
            "status": "exception",
            "elapsed": elapsed,
            "error": str(e)
        }

def run_concurrent_test(endpoint, num_requests, max_workers=10):
    """Run multiple requests concurrently and collect results"""
    print(f"[{timestamp()}] Starting concurrent test with {num_requests} requests to {endpoint} using {max_workers} workers")
    
    # Create a list of request IDs
    request_ids = [f"{i+1}" for i in range(num_requests)]
    
    # Use ThreadPoolExecutor to run requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all requests
        future_to_id = {
            executor.submit(make_request, endpoint, request_id): request_id
            for request_id in request_ids
        }
        
        # Collect results as they complete
        results = []
        for future in concurrent.futures.as_completed(future_to_id):
            request_id = future_to_id[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"[{timestamp()}] Error processing result for request {request_id}: {str(e)}")
                results.append({
                    "request_id": request_id,
                    "status": "processing_error",
                    "error": str(e)
                })
    
    # Sort results by request ID
    results.sort(key=lambda x: int(x["request_id"]))
    
    # Calculate statistics
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    exceptions = [r for r in results if r["status"] == "exception"]
    
    if successful:
        avg_time = sum(r["elapsed"] for r in successful) / len(successful)
        min_time = min(r["elapsed"] for r in successful)
        max_time = max(r["elapsed"] for r in successful)
    else:
        avg_time = min_time = max_time = 0
    
    # Print summary
    print(f"\n[{timestamp()}] Test Summary:")
    print(f"  Total Requests: {num_requests}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Exceptions: {len(exceptions)}")
    print(f"  Average Response Time: {avg_time:.2f}s")
    print(f"  Min Response Time: {min_time:.2f}s")
    print(f"  Max Response Time: {max_time:.2f}s")
    
    # Check if we got different worker processes
    if successful:
        workers = set()
        for r in successful:
            if "processor" in r["result"]:
                workers.add(r["result"]["processor"])
        
        print(f"  Unique Worker Processes: {len(workers)}")
        print(f"  Workers: {', '.join(workers)}")
    
    return results

def test_increment_concurrent(num_requests=10, max_workers=10):
    """Run concurrent increment requests"""
    print(f"\n[{timestamp()}] === Testing Concurrent Increment Requests ===")
    return run_concurrent_test("increment", num_requests, max_workers)

def test_decrement_concurrent(num_requests=5, max_workers=5):
    """Run concurrent decrement requests"""
    print(f"\n[{timestamp()}] === Testing Concurrent Decrement Requests ===")
    return run_concurrent_test("decrement", num_requests, max_workers)

def test_get_counter_concurrent(num_requests=20, max_workers=20):
    """Run concurrent get counter requests"""
    print(f"\n[{timestamp()}] === Testing Concurrent Get Counter Requests ===")
    return run_concurrent_test("counter", num_requests, max_workers)

def test_mixed_concurrent(num_each=5, max_workers=15):
    """Run a mix of different request types concurrently"""
    print(f"\n[{timestamp()}] === Testing Mixed Concurrent Requests ===")
    
    # Create a list of (endpoint, request_id) tuples
    _requests = []
    for i in range(num_each):
        _requests.append(("increment", f"inc-{i+1}"))
        _requests.append(("decrement", f"dec-{i+1}"))
        _requests.append(("counter", f"get-{i+1}"))
    
    print(f"[{timestamp()}] Starting mixed test with {len(_requests)} total _requests using {max_workers} workers")
    
    # Use ThreadPoolExecutor to run _requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all _requests
        future_to_req = {
            executor.submit(make_request, endpoint, request_id): (endpoint, request_id)
            for endpoint, request_id in _requests
        }
        
        # Collect results as they complete
        results = []
        for future in concurrent.futures.as_completed(future_to_req):
            endpoint, request_id = future_to_req[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"[{timestamp()}] Error processing result for {endpoint} request {request_id}: {str(e)}")
                results.append({
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "status": "processing_error",
                    "error": str(e)
                })
    
    # Calculate statistics by endpoint
    endpoints = set(r["endpoint"] for r in results)
    
    print(f"\n[{timestamp()}] Test Summary by Endpoint:")
    for endpoint in endpoints:
        endpoint_results = [r for r in results if r["endpoint"] == endpoint]
        successful = [r for r in endpoint_results if r["status"] == "success"]
        
        if successful:
            avg_time = sum(r["elapsed"] for r in successful) / len(successful)
            print(f"  {endpoint.capitalize()}: {len(successful)} successful, avg time {avg_time:.2f}s")
    
    # Check final counter value
    try:
        response = requests.get(f"{BASE_URL}/counter-value")
        if response.status_code == 200:
            final_counter = response.json()["counter"]
            print(f"  Final Counter Value: {final_counter}")
    except Exception as e:
        print(f"  Error getting final counter value: {str(e)}")
    
    return results

def test_processor_info():
    """Get processor info to see which workers handled requests"""
    print(f"\n[{timestamp()}] === Getting Processor Info ===")
    
    try:
        response = requests.get(f"{BASE_URL}/processor-info")
        if response.status_code == 200:
            info = response.json()
            print(f"Processor Info: {json.dumps(info, indent=2)}")
            return info
        else:
            print(f"Error getting processor info: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception getting processor info: {str(e)}")
        return None

if __name__ == "__main__":
    print(f"[{timestamp()}] Starting concurrent tests...")
    
    # First, get the initial counter value
    try:
        response = requests.get(f"{BASE_URL}/counter")
        if response.status_code == 200:
            initial_counter = response.json()["counter"]
            print(f"Initial Counter Value: {initial_counter}")
    except Exception as e:
        print(f"Error getting initial counter value: {str(e)}")
        initial_counter = None
    
    # Run the tests
    test_get_counter_concurrent(num_requests=10, max_workers=10)
    test_increment_concurrent(num_requests=5, max_workers=5)
    test_decrement_concurrent(num_requests=3, max_workers=3)
    test_mixed_concurrent(num_each=3, max_workers=9)
    
    # Get processor info at the end
    test_processor_info()
    
    print(f"[{timestamp()}] All tests completed.") 