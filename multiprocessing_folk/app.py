from fastapi import FastAPI, HTTPException
from multiprocessing.managers import SyncManager
import time
import uuid
import traceback
import socket
import os
import queue
import json

# Set up debug printing
def debug_print(message):
    print(f"[APP DEBUG] {time.strftime('%H:%M:%S')} - {message}", flush=True)

# Get hostname and process ID for processor identification
hostname = socket.gethostname()
process_id = os.getpid()
debug_print(f"Starting app.py on {hostname} with PID {process_id}")

class MyManager(SyncManager):
    pass

# Register the queues and processor info with the manager
debug_print("Registering with manager")
MyManager.register('get_task_queue')
MyManager.register('get_result_queue')
MyManager.register('get_processor_info')
MyManager.register('get_processor_info_dict')
MyManager.register('get_processor_info_as_string')  # Register the new method
MyManager.register('update_processor_info')

def get_manager():
    debug_print(f"get_manager called by {hostname}:{process_id}")
    # Connect to the manager server
    try:
        debug_print("Connecting to manager server at 127.0.0.1:50000")
        m = MyManager(address=('127.0.0.1', 50000), authkey=b'secret')
        m.connect()
        debug_print("Connected to manager server successfully")
        return m
    except Exception as e:
        debug_print(f"Error connecting to manager: {e}")
        debug_print(traceback.format_exc())
        raise

app = FastAPI()

def process_task(task_type, timeout=10):
    """Helper function to process a task and wait for the result with timeout"""
    api_server = f"{hostname}:{process_id}"
    debug_print(f"process_task called with task_type={task_type}, timeout={timeout} by {api_server}")
    
    # Get the manager and queues
    try:
        manager = get_manager()
        debug_print("Got manager")
        
        task_queue = manager.get_task_queue()
        debug_print(f"Got task queue: {type(task_queue)}")
        
        result_queue = manager.get_result_queue()
        debug_print(f"Got result queue: {type(result_queue)}")
        
        processor_info = manager.get_processor_info()
        debug_print(f"Got processor info: {processor_info}")
    except Exception as e:
        debug_print(f"Error getting manager resources: {e}")
        debug_print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error connecting to task manager: {str(e)}")
    
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    debug_print(f"Generated task_id={task_id}")
    
    # Put the task in the queue with its ID
    try:
        debug_print(f"Putting task in queue: task_id={task_id}, type={task_type}")
        task_queue.put((task_id, task_type))
        debug_print("Task put in queue successfully")
        
        # Record which API server submitted this task
        try:
            # Use the update_processor_info method instead of direct assignment
            manager.update_processor_info(f'api_server_{task_id}', api_server)
            debug_print(f"Updated processor info with api_server_{task_id}={api_server}")
        except Exception as e:
            debug_print(f"Warning: Could not update processor info: {e}")
        
        # Debug: Check queue size if possible
        try:
            debug_print(f"Task queue size: {task_queue.qsize()}")
        except Exception as e:
            debug_print(f"Cannot get queue size: {e}")
    except Exception as e:
        debug_print(f"Error putting task in queue: {e}")
        debug_print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error submitting task: {str(e)}")
    
    # Wait for the result with timeout
    debug_print(f"Waiting for result with timeout={timeout}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check if there's a result
        try:
            # Try to get a result with a timeout
            debug_print("Checking for result...")
            try:
                debug_print("About to call result_queue.get(timeout=0.5)")
                result_data = result_queue.get(timeout=0.5)
                
                # Unpack the result data
                if len(result_data) == 3:
                    result_id, result, processor = result_data
                else:
                    result_id, result = result_data
                    processor = "unknown"
                    
                debug_print(f"Got result: result_id={result_id}, result={result}, processor={processor}")
                
                # If this is our result, return it
                if result_id == task_id:
                    debug_print(f"Result matches our task_id, returning result={result}")
                    return {
                        "counter": result,
                        "processor": processor,
                        "api_server": api_server,
                        "task_id": task_id
                    }
                else:
                    debug_print(f"Result is for a different task (expected {task_id}, got {result_id}), continuing to wait")
                    # Put the result back for another process to pick up
                    result_queue.put(result_data)
            except queue.Empty:
                # No result yet
                elapsed = time.time() - start_time
                debug_print(f"Queue Empty exception, waited {elapsed:.1f}s so far")
            except Exception as e:
                # Error getting result
                elapsed = time.time() - start_time
                debug_print(f"Error in result_queue.get(): {e}, waited {elapsed:.1f}s so far")
                debug_print(f"Exception type: {type(e)}")
                debug_print(traceback.format_exc())
        except Exception as e:
            debug_print(f"Error in result loop: {e}")
            debug_print(traceback.format_exc())
            
        # Small sleep to prevent CPU spinning
        time.sleep(0.1)
        
    # If we get here, we timed out
    debug_print(f"Timed out waiting for result after {timeout}s")
    raise HTTPException(status_code=504, detail="Task processing timed out")

@app.get("/increment")
def increment():
    debug_print(f"increment endpoint called on {hostname}:{process_id}")
    result = process_task("increment")
    debug_print(f"increment returning result={result}")
    return result

@app.get("/decrement") 
def decrement():
    debug_print(f"decrement endpoint called on {hostname}:{process_id}")
    result = process_task("decrement")
    debug_print(f"decrement returning result={result}")
    return result

@app.get("/counter")
def get_counter():
    debug_print(f"counter endpoint called on {hostname}:{process_id}")
    result = process_task("get")
    debug_print(f"counter returning result={result}")
    return result

@app.get("/processor-info")
def get_processor_info():
    debug_print(f"processor-info endpoint called on {hostname}:{process_id}")
    try:
        # Get the manager
        manager = get_manager()
        
        # Use the method that returns a simple string
        try:
            # Get the proxy object
            proxy_obj = manager.get_processor_info_as_string()
            debug_print(f"Got proxy object: {type(proxy_obj)}")
            
            # Convert proxy to string - this is the critical step
            if hasattr(proxy_obj, '_getvalue'):
                # If it has _getvalue method, use it
                json_str = proxy_obj._getvalue()
                debug_print(f"Got value using _getvalue(): {type(json_str)}")
            else:
                # Otherwise try direct string conversion
                json_str = str(proxy_obj)
                debug_print(f"Converted to string using str(): {type(json_str)}")
            
            # Make sure it's a valid JSON string
            if not json_str.startswith('{') and not json_str.startswith('['):
                debug_print(f"Warning: Not a valid JSON string: {json_str[:100]}")
                # Create a simple fallback dictionary
                info_dict = {
                    "error": "Invalid JSON string from server",
                    "raw_value": json_str[:100] + "..." if len(json_str) > 100 else json_str
                }
            else:
                # Parse the JSON string
                info_dict = json.loads(json_str)
                debug_print(f"Successfully parsed JSON string into dictionary with {len(info_dict)} keys")
        except Exception as e:
            debug_print(f"Error getting or parsing processor info: {e}")
            debug_print(traceback.format_exc())
            info_dict = {"error": f"Could not get processor info: {str(e)}"}
        
        # Add current API server info
        info_dict["current_api_server"] = f"{hostname}:{process_id}"
        
        return info_dict
    except Exception as e:
        debug_print(f"Error in get_processor_info: {e}")
        debug_print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error getting processor info: {str(e)}")

@app.get("/counter-value")
def get_counter_value():
    """Simple endpoint that returns just the counter value as an integer"""
    debug_print(f"counter-value endpoint called on {hostname}:{process_id}")
    try:
        # Use the same process_task function that the /counter endpoint uses
        # This ensures we get the actual counter value from a worker process
        result = process_task("get")
        
        # Extract just the counter value
        counter_value = result.get("counter", 0)
        debug_print(f"Got counter value: {counter_value}")
        
        # Return just the counter value in a simple format
        return {"counter": counter_value}
    except HTTPException as e:
        # If we got a timeout or other HTTP exception, return 0 with an error
        debug_print(f"HTTP error in get_counter_value: {e.detail}")
        return {"counter": 0, "error": e.detail}
    except Exception as e:
        # For any other error, also return 0 with the error message
        debug_print(f"Error in get_counter_value: {e}")
        debug_print(traceback.format_exc())
        return {"counter": 0, "error": str(e)}

if __name__ == "__main__":
    debug_print("Starting FastAPI server")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
