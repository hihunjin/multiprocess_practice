from fastapi import FastAPI
from multiprocessing.managers import BaseManager

class MyManager(BaseManager):
    pass

# Register the method to get the shared dictionary manager
MyManager.register('get_shared_dict_manager')

def get_manager():
    # Connect to the running manager server
    m = MyManager(address=('127.0.0.1', 50000), authkey=b'secret')
    m.connect()
    return m

app = FastAPI()

@app.get("/increment")
def increment():
    manager = get_manager()
    shared_dict_manager = manager.get_shared_dict_manager()
    
    # Increment counter using the manager's method
    new_value = shared_dict_manager.increment_counter()
    
    # Return updated counter value
    return {"counter": new_value}

@app.get("/decrement")
def decrement():
    manager = get_manager()
    shared_dict_manager = manager.get_shared_dict_manager()
    
    # Decrement counter using the manager's method (includes 3-second pause)
    new_value = shared_dict_manager.decrement_counter()
    
    # Return updated counter value
    return {"counter": new_value}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
