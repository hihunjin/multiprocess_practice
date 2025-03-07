from multiprocessing.managers import BaseManager
import multiprocessing

class SharedDictManager:
    def __init__(self):
        self.shared_dict = {}
        
    def get_counter(self):
        return self.shared_dict.get("counter", 0)
        
    def increment_counter(self):
        if "counter" not in self.shared_dict:
            self.shared_dict["counter"] = 0
        self.shared_dict["counter"] += 1
        return self.shared_dict["counter"]

class MyManager(BaseManager):
    pass

if __name__ == "__main__":
    # Create an instance of our shared dictionary manager
    shared_dict_manager = SharedDictManager()

    # Register methods to access the shared dictionary
    MyManager.register('get_shared_dict_manager', callable=lambda: shared_dict_manager)

    # Start manager server on a specific port and auth key
    manager = MyManager(address=('127.0.0.1', 50000), authkey=b'secret')
    server = manager.get_server()
    print("Manager server started on port 50000...")
    server.serve_forever()
