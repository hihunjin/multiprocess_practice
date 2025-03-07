from multiprocessing.managers import SyncManager
import multiprocessing
import time
import os
import sys
import traceback
import socket
import queue

# Set up debug printing
def debug_print(message):
    print(f"[DEBUG] {time.strftime('%H:%M:%S')} - {message}", flush=True)

# Get hostname for processor identification
hostname = socket.gethostname()
process_id = os.getpid()
debug_print(f"Starting manager_server.py on {hostname} with PID {process_id}")

# Create a manager to share objects between processes
manager = multiprocessing.Manager()
# Create shared queues using the manager
task_queue = manager.Queue()
result_queue = manager.Queue()
debug_print(f"Created manager queues: task_queue={type(task_queue)}, result_queue={type(result_queue)}")

# Create a shared counter using multiprocessing.Value
counter = multiprocessing.Value('i', 0)
debug_print("Created shared counter with initial value 0")

# Track processor information
processor_info = manager.dict()
processor_info['workers'] = manager.list()

# Define functions to get the queues
def get_task_queue():
    caller_id = f"{hostname}:{os.getpid()}"
    debug_print(f"get_task_queue called by {caller_id}")
    return task_queue

def get_result_queue():
    caller_id = f"{hostname}:{os.getpid()}"
    debug_print(f"get_result_queue called by {caller_id}")
    return result_queue

def get_processor_info():
    caller_id = f"{hostname}:{os.getpid()}"
    debug_print(f"get_processor_info called by {caller_id}")
    return processor_info

def update_processor_info(key, value):
    caller_id = f"{hostname}:{os.getpid()}"
    debug_print(f"update_processor_info called by {caller_id}: {key}={value}")
    processor_info[key] = value
    return True

class SharedDictManager:
    def __init__(self):
        self.process_id = os.getpid()
        debug_print(f"SharedDictManager initialized in process {self.process_id}")
        
    def get_counter(self):
        caller_id = f"{hostname}:{self.process_id}"
        debug_print(f"get_counter called in process {caller_id}")
        with counter.get_lock():
            value = counter.value
            debug_print(f"Current counter value: {value}")
            return value, caller_id
        
    def increment_counter(self):
        caller_id = f"{hostname}:{self.process_id}"
        debug_print(f"increment_counter called in process {caller_id}")
        with counter.get_lock():
            counter.value += 1
            debug_print(f"Incremented counter to {counter.value}")
            processor_info['last_increment'] = caller_id
            return counter.value, caller_id
        
    def decrement_counter(self):
        caller_id = f"{hostname}:{self.process_id}"
        debug_print(f"decrement_counter called in process {caller_id}")
        with counter.get_lock():
            debug_print(f"Sleeping for 3 seconds in process {caller_id}")
            time.sleep(3)
            
            if counter.value > 0:
                counter.value -= 1
                debug_print(f"Decremented counter to {counter.value}")
            else:
                debug_print(f"Counter already at 0, not decrementing")
                
            processor_info['last_decrement'] = caller_id
            return counter.value, caller_id

def worker_process(worker_id):
    """Worker process function that processes tasks from the queue"""
    process_id = os.getpid()
    worker_name = f"{hostname}:{process_id} (Worker {worker_id})"
    debug_print(f"Worker process {worker_name} started")
    
    # Add this worker to the processor info
    processor_info['workers'].append(worker_name)
    
    shared_dict_manager = SharedDictManager()
    debug_print(f"Worker process {worker_name} created SharedDictManager")
    
    # Check if queues are empty at start
    try:
        debug_print(f"Worker {worker_name} task queue size at start: {task_queue.qsize()}")
    except Exception as e:
        debug_print(f"Worker {worker_name} can't get task queue size: {e}")
    
    while True:
        try:
            debug_print(f"Worker {worker_name} waiting for task...")
            # Get a task from the queue with a timeout to allow for debugging
            try:
                debug_print(f"Worker {worker_name} about to call task_queue.get(block=True, timeout=1)")
                task = task_queue.get(block=True, timeout=1)
                debug_print(f"Worker {worker_name} got task: {task}")
            except queue.Empty:
                # This is expected when the queue is empty
                debug_print(f"Worker {worker_name} task queue is empty, continuing...")
                continue
            except Exception as e:
                debug_print(f"Worker {worker_name} error in task_queue.get(): {e}")
                debug_print(traceback.format_exc())
                time.sleep(1)  # Wait a bit before retrying
                continue
            
            try:
                task_id, task_type = task
                debug_print(f"Worker {worker_name} processing task_id={task_id}, type={task_type}")
                processor_info[f'task_{task_id}'] = worker_name
                
                if task_type == "increment":
                    result, processor = shared_dict_manager.increment_counter()
                elif task_type == "decrement":
                    result, processor = shared_dict_manager.decrement_counter()
                elif task_type == "get":
                    result, processor = shared_dict_manager.get_counter()
                else:
                    debug_print(f"Worker {worker_name} received unknown task type: {task_type}")
                    result = None
                    processor = worker_name
                    
                # Put the result back in the result queue with the task ID
                debug_print(f"Worker {worker_name} putting result in queue: task_id={task_id}, result={result}")
                result_queue.put((task_id, result, processor))
                debug_print(f"Worker {worker_name} finished processing task {task_id}")
                
                # Check result queue size after putting result
                try:
                    debug_print(f"Worker {worker_name} result queue size after put: {result_queue.qsize()}")
                except Exception as e:
                    debug_print(f"Worker {worker_name} can't get result queue size: {e}")
                
            except Exception as e:
                debug_print(f"Worker {worker_name} error processing task: {e}")
                debug_print(traceback.format_exc())
        except Exception as e:
            debug_print(f"Error in worker process {worker_name} main loop: {e}")
            debug_print(traceback.format_exc())
            time.sleep(1)  # Wait a bit before continuing

class MyManager(SyncManager):
    pass

if __name__ == "__main__":
    debug_print("Entering main block")
    
    # Register the queues and processor info with the manager
    debug_print("Registering queues with manager")
    MyManager.register('get_task_queue', callable=get_task_queue)
    MyManager.register('get_result_queue', callable=get_result_queue)
    MyManager.register('get_processor_info', callable=get_processor_info)
    MyManager.register('update_processor_info', callable=update_processor_info)
    
    # Create the manager server
    debug_print("Creating manager server on port 50000")
    server_manager = MyManager(address=('127.0.0.1', 50000), authkey=b'secret')
    
    try:
        debug_print("Starting manager server")
        server_manager.start()
        debug_print("Manager server started successfully")
    except Exception as e:
        debug_print(f"Error starting manager: {e}")
        debug_print(traceback.format_exc())
        sys.exit(1)
    
    # Number of worker processes
    num_workers = 3
    debug_print(f"Creating {num_workers} worker processes")
    
    # Create and start worker processes
    processes = []
    for i in range(num_workers):
        try:
            debug_print(f"Creating worker process {i}")
            p = multiprocessing.Process(target=worker_process, args=(i,))
            p.daemon = True  # Set as daemon so they exit when the main process exits
            debug_print(f"Starting worker process {i}")
            p.start()
            processes.append(p)
            debug_print(f"Started worker process {i} with PID {p.pid}")
        except Exception as e:
            debug_print(f"Error creating worker process {i}: {e}")
            debug_print(traceback.format_exc())
    
    debug_print("All worker processes started")
    debug_print("Manager server running on port 50000...")
    
    # Keep the main process running
    try:
        debug_print("Entering main loop")
        while True:
            # Periodically check queue sizes
            try:
                debug_print(f"Main process task queue size: {task_queue.qsize()}")
                debug_print(f"Main process result queue size: {result_queue.qsize()}")
            except Exception as e:
                debug_print(f"Main process can't get queue sizes: {e}")
            
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        debug_print("Received KeyboardInterrupt, shutting down...")
        server_manager.shutdown()
        debug_print("Manager shutdown complete")