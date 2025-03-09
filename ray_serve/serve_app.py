import ray
from ray import serve
from fastapi import FastAPI
import torch

# ---------------------------------
# 1) Define a Ray actor for SHARED STATE
# ---------------------------------
@ray.remote
class SharedState:
    """
    A simple actor that holds state accessible by all replicas.
    Here, we store a counter that can be incremented.
    """
    def __init__(self):
        self.counter = 0

    def increment(self):
        self.counter += 1
        return self.counter

    def get_count(self):
        return self.counter

# ---------------------------------
# 2) Define a Ray Serve deployment for GPU WORKERS
# ---------------------------------
app = FastAPI()

@serve.deployment(
    num_replicas=2,
    ray_actor_options={"num_gpus": 1}
)
@serve.ingress(app)
class GPUTask:
    def __init__(self, shared_state_actor):
        self.shared_state = shared_state_actor
        self.device = "cuda"
        self.model_tensor = torch.randn((1000, 1000), device=self.device)
        print(f"GPUTask replica initialized on {self.device}.")

    @app.get("/predict/{x}")
    async def predict(self, x: int):
        """
        Perform a dummy GPU computation with x, then increment the shared counter.
        """
        # Dummy GPU work
        x_t = torch.full((1000, 1000), float(x), device=self.device)
        result = x_t * self.model_tensor
        sum_val = float(result.sum().item())  # bring scalar back to CPU

        # Increment the shared counter (IPC via Ray)
        new_count_future = self.shared_state.increment.remote()
        new_count = await new_count_future  # fetch the updated counter value

        return {
            "input": x,
            "gpu_sum": sum_val,
            "shared_counter": new_count
        }

    @app.get("/state")
    async def get_state(self):
        """
        Query the shared counter without doing GPU work.
        """
        count = await self.shared_state.get_count.remote()
        return {"shared_counter": count}

# ---------------------------------
# 3) Main: Initialize Ray, start Serve, bind + run
# ---------------------------------
if __name__ == "__main__":
    ray.init()
    serve.start()

    # Create the shared state actor
    shared_state = SharedState.remote()

    # Bind the GPUTask deployment to your constructor argument
    gpu_app = GPUTask.bind(shared_state)

    # Run the app on the Ray cluster
    serve.run(gpu_app)

    print("Ray Serve is running with 2 GPU replicas. Try:")
    print("  curl http://127.0.0.1:8000/predict/5")
    print("  curl http://127.0.0.1:8000/state")
