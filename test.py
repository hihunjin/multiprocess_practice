import requests

def test_increment():
    response = requests.get('http://localhost:8000/increment')
    assert response.status_code == 200
    print(response.json())
    # assert response.json()["counter"] == 1

if __name__ == "__main__":
    test_increment()
