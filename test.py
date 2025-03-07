import requests

def test_increment():
    response = requests.get('http://localhost:8000/increment')
    assert response.status_code == 200
    print("test_increment:", response.json())
    # assert response.json()["counter"] == 1

def test_decrement():
    response = requests.get('http://localhost:8000/decrement')
    assert response.status_code == 200
    print("test_decrement:", response.json())
    # assert response.json()["counter"] == 0

if __name__ == "__main__":
    test_increment()
    test_increment()
    test_increment()
    test_decrement()
    test_increment()
    test_decrement()
    test_decrement()
