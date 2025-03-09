# multiprocess_practice

## Description

This is a simple example of how to use multiprocessing in Python.

## How to run

1. Start the manager server:

```bash
python manager_server.py
```

2. Start the API server:

```bash
python app.py
```

3. Run the concurrent test:

```bash
python concurrent_test.py
```

4. Run the test:

```bash
python test.py
```


## Notes

- The manager server is a simple server that allows the API server to communicate with the worker processes.
- The API server is a simple server that allows the user to communicate with the manager server.
- The test is a simple test that allows the user to test the API server.
- The test.py file is a simple test that allows the user to test the API server.
- The concurrent_test.py file is a simple test that allows the user to test the API server in a concurrent manner.


## TODO

- Add a test that allows the user to test the API server in a concurrent manner.
  - If query too much too fast, the error on [app.py](app.py#L130-L133)
  - Need to fix it.
