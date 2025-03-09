import requests
import time
import concurrent.futures
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

# Base URL for the Ray Serve application
BASE_URL = "http://127.0.0.1:8000"

def timestamp():
    """Return current timestamp for logging"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def test_predict(x):
    """Test the predict endpoint with a given input value"""
    start_time = time.time()
    url = f"{BASE_URL}/predict/{x}"
    
    print(f"[{timestamp()}] Testing predict with x={x}")
    response = requests.get(url)
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"[{timestamp()}] Predict result: {json.dumps(result)}, time: {elapsed:.3f}s")
        return {
            "status": "success",
            "input": x,
            "result": result,
            "elapsed": elapsed
        }
    else:
        print(f"[{timestamp()}] Predict failed: {response.status_code}, time: {elapsed:.3f}s")
        return {
            "status": "error",
            "input": x,
            "status_code": response.status_code,
            "elapsed": elapsed
        }

def test_state():
    """Test the state endpoint to get the current counter value"""
    start_time = time.time()
    url = f"{BASE_URL}/state"
    
    print(f"[{timestamp()}] Testing state endpoint")
    response = requests.get(url)
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"[{timestamp()}] State result: {json.dumps(result)}, time: {elapsed:.3f}s")
        return {
            "status": "success",
            "result": result,
            "elapsed": elapsed
        }
    else:
        print(f"[{timestamp()}] State request failed: {response.status_code}, time: {elapsed:.3f}s")
        return {
            "status": "error",
            "status_code": response.status_code,
            "elapsed": elapsed
        }

def run_sequential_tests(num_tests=10):
    """Run a series of sequential tests with increasing input values"""
    print("\n" + "=" * 50)
    print(f"Running {num_tests} sequential predict tests")
    print("=" * 50)
    
    results = []
    for i in range(num_tests):
        # Use i+1 as the input value
        result = test_predict(i + 1)
        results.append(result)
        
        # Check the state after each predict
        state = test_state()
        
        # Small delay between tests
        time.sleep(0.5)
    
    return results

def run_concurrent_tests(num_tests=10, max_workers=5):
    """Run concurrent predict tests to test Ray's parallel processing"""
    print("\n" + "=" * 50)
    print(f"Running {num_tests} concurrent predict tests with {max_workers} workers")
    print("=" * 50)
    
    # Create a list of input values
    inputs = list(range(1, num_tests + 1))
    
    # Use ThreadPoolExecutor to run requests concurrently
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all predict requests
        future_to_input = {executor.submit(test_predict, x): x for x in inputs}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_input):
            input_val = future_to_input[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"[{timestamp()}] Error processing result for input {input_val}: {str(e)}")
                results.append({
                    "status": "exception",
                    "input": input_val,
                    "error": str(e)
                })
    
    # Check the final state after all concurrent requests
    state = test_state()
    
    return results

def test_gpu_scaling(max_size=1000, steps=5):
    """Test how the GPU computation scales with different input values"""
    print("\n" + "=" * 50)
    print(f"Testing GPU scaling with inputs from 1 to {max_size}")
    print("=" * 50)
    
    sizes = np.linspace(1, max_size, steps, dtype=int)
    results = []
    
    for size in sizes:
        result = test_predict(int(size))
        results.append(result)
        time.sleep(1)  # Give the GPU a moment to cool down
    
    return results

def plot_results(results, title, filename):
    """Plot the results of the tests"""
    # Extract data for successful requests
    successful = [r for r in results if r["status"] == "success"]
    
    if not successful:
        print(f"No successful results to plot for {title}")
        return
    
    # For predict tests, plot input vs. elapsed time
    if "input" in successful[0]:
        inputs = [r["input"] for r in successful]
        times = [r["elapsed"] for r in successful]
        counter_vals = [r["result"]["shared_counter"] for r in successful]
        
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot input vs. time
        ax1.plot(inputs, times, 'o-', color='blue')
        ax1.set_xlabel('Input Value')
        ax1.set_ylabel('Response Time (s)')
        ax1.set_title(f'{title} - Input vs. Response Time')
        ax1.grid(True)
        
        # Plot counter progression
        ax2.plot(inputs, counter_vals, 'o-', color='green')
        ax2.set_xlabel('Input Value')
        ax2.set_ylabel('Shared Counter Value')
        ax2.set_title('Shared Counter Progression')
        ax2.grid(True)
        
    # For state tests, just plot the counter value over time
    else:
        times = [r["elapsed"] for r in successful]
        counter_vals = [r["result"]["shared_counter"] for r in successful]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(range(len(counter_vals)), counter_vals, 'o-', color='green')
        ax.set_xlabel('Request Number')
        ax.set_ylabel('Shared Counter Value')
        ax.set_title(f'{title} - Shared Counter Value')
        ax.grid(True)
    
    plt.tight_layout()
    
    # Create plots directory if it doesn't exist
    os.makedirs("plots", exist_ok=True)
    
    # Save the plot
    plt.savefig(f"plots/{filename}.png")
    print(f"Plot saved to plots/{filename}.png")
    plt.close()

def run_all_tests():
    """Run all tests and plot the results"""
    # Make sure the plots directory exists
    os.makedirs("plots", exist_ok=True)
    
    # Test 1: Sequential predict tests
    seq_results = run_sequential_tests(num_tests=10)
    plot_results(seq_results, "Sequential Predict Tests", "sequential_predict")
    
    # Test 2: Concurrent predict tests
    conc_results = run_concurrent_tests(num_tests=20, max_workers=10)
    plot_results(conc_results, "Concurrent Predict Tests", "concurrent_predict")
    
    # Test 3: GPU scaling test
    scaling_results = test_gpu_scaling(max_size=1000, steps=10)
    plot_results(scaling_results, "GPU Scaling Test", "gpu_scaling")
    
    # Test 4: Final state check
    final_state = test_state()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print(f"Final shared counter value: {final_state['result']['shared_counter']}")
    print("=" * 50)

if __name__ == "__main__":
    print(f"[{timestamp()}] Starting Ray Serve tests...")
    
    try:
        # First, check if the service is running
        try:
            response = requests.get(f"{BASE_URL}/state")
            if response.status_code == 200:
                print(f"[{timestamp()}] Ray Serve is running. Initial state: {response.json()}")
            else:
                print(f"[{timestamp()}] Ray Serve returned status code {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"[{timestamp()}] ERROR: Could not connect to Ray Serve at {BASE_URL}")
            print("Make sure serve_app.py is running before running tests.")
            exit(1)
        
        # Run all tests
        run_all_tests()
        
    except KeyboardInterrupt:
        print(f"[{timestamp()}] Tests interrupted by user")
    except Exception as e:
        print(f"[{timestamp()}] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
