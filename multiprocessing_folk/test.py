import requests
import time
import json

BASE_URL = 'http://localhost:8000'

def print_separator(title):
    """Print a separator with a title for better test output readability"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)

def test_increment():
    """Test the increment endpoint"""
    print_separator("INCREMENT TEST")
    response = requests.get(f'{BASE_URL}/increment')
    assert response.status_code == 200
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Validate response structure
    assert "counter" in data, "Response missing 'counter' field"
    assert "processor" in data, "Response missing 'processor' field"
    assert "api_server" in data, "Response missing 'api_server' field"
    assert "task_id" in data, "Response missing 'task_id' field"
    
    # Return the counter value for chaining tests
    return data["counter"]

def test_decrement():
    """Test the decrement endpoint"""
    print_separator("DECREMENT TEST")
    response = requests.get(f'{BASE_URL}/decrement')
    assert response.status_code == 200
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Validate response structure
    assert "counter" in data, "Response missing 'counter' field"
    assert "processor" in data, "Response missing 'processor' field"
    assert "api_server" in data, "Response missing 'api_server' field"
    assert "task_id" in data, "Response missing 'task_id' field"
    
    # Return the counter value for chaining tests
    return data["counter"]

def test_get_counter():
    """Test the counter endpoint"""
    print_separator("GET COUNTER TEST")
    response = requests.get(f'{BASE_URL}/counter')
    assert response.status_code == 200
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Validate response structure
    assert "counter" in data, "Response missing 'counter' field"
    assert "processor" in data, "Response missing 'processor' field"
    assert "api_server" in data, "Response missing 'api_server' field"
    assert "task_id" in data, "Response missing 'task_id' field"
    
    # Return the counter value for chaining tests
    return data["counter"]

def test_counter_value():
    """Test the counter-value endpoint"""
    print_separator("COUNTER VALUE TEST")
    response = requests.get(f'{BASE_URL}/counter-value')
    assert response.status_code == 200
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Validate response structure
    assert "counter" in data, "Response missing 'counter' field"
    
    # Return the counter value for chaining tests
    return data["counter"]

def test_processor_info():
    """Test the processor-info endpoint"""
    print_separator("PROCESSOR INFO TEST")
    response = requests.get(f'{BASE_URL}/processor-info')
    assert response.status_code == 200
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Validate some expected fields
    assert "server_hostname" in data, "Response missing 'server_hostname' field"
    assert "server_pid" in data, "Response missing 'server_pid' field"
    assert "counter_value" in data, "Response missing 'counter_value' field"
    assert "worker_processes" in data, "Response missing 'worker_processes' field"
    
    return data

def test_counter_sequence():
    """Test a sequence of counter operations to verify correct behavior"""
    print_separator("COUNTER SEQUENCE TEST")
    
    # Get initial counter value
    initial = test_get_counter()
    print(f"Initial counter value: {initial}")
    
    # Increment twice
    inc1 = test_increment()
    print(f"After first increment: {inc1}")
    assert inc1 == initial + 1, f"Expected {initial + 1}, got {inc1}"
    
    inc2 = test_increment()
    print(f"After second increment: {inc2}")
    assert inc2 == inc1 + 1, f"Expected {inc1 + 1}, got {inc2}"
    
    # Decrement once
    dec1 = test_decrement()
    print(f"After decrement: {dec1}")
    assert dec1 == inc2 - 1, f"Expected {inc2 - 1}, got {dec1}"
    
    # Verify with counter-value endpoint
    val = test_counter_value()
    print(f"Counter value from counter-value endpoint: {val}")
    assert val == dec1, f"Expected {dec1}, got {val}"
    
    print("\nCounter sequence test passed!")

def test_response_times():
    """Test response times for different endpoints"""
    print_separator("RESPONSE TIME TEST")
    
    endpoints = ["increment", "counter", "counter-value", "processor-info"]
    results = {}
    
    for endpoint in endpoints:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/{endpoint}")
        elapsed = time.time() - start_time
        
        results[endpoint] = {
            "status_code": response.status_code,
            "time": elapsed
        }
        
        print(f"{endpoint}: {elapsed:.3f} seconds")
    
    # Decrement is expected to be slow due to the 3-second sleep
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/decrement")
    elapsed = time.time() - start_time
    results["decrement"] = {
        "status_code": response.status_code,
        "time": elapsed
    }
    print(f"decrement: {elapsed:.3f} seconds (expected to be ~3 seconds)")
    
    # Verify decrement takes at least 3 seconds
    assert elapsed >= 3.0, f"Decrement should take at least 3 seconds, took {elapsed:.3f}"
    
    return results

def test_error_handling():
    """Test error handling by making invalid requests"""
    print_separator("ERROR HANDLING TEST")
    
    # Test a non-existent endpoint
    response = requests.get(f"{BASE_URL}/nonexistent")
    print(f"Non-existent endpoint: {response.status_code}")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    # Test with an invalid HTTP method
    try:
        response = requests.post(f"{BASE_URL}/increment")
        print(f"Invalid HTTP method: {response.status_code}")
        # FastAPI may return different status codes depending on configuration
        assert response.status_code in [405, 404, 422], f"Expected error status, got {response.status_code}"
    except Exception as e:
        print(f"Exception with invalid HTTP method: {e}")

if __name__ == "__main__":
    print("\nStarting API tests...")
    
    try:
        # Basic endpoint tests
        test_get_counter()
        test_increment()
        test_decrement()
        test_counter_value()
        test_processor_info()
        
        # More complex tests
        test_counter_sequence()
        test_response_times()
        test_error_handling()
        
        print("\nAll tests completed successfully!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
