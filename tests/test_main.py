from fastapi.testclient import TestClient
import pytest

from src.main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    # L'endpoint racine redirige vers la doc Swagger, donc on vérifie le HTML
    assert "Swagger UI" in response.text or "swagger-ui" in response.text
    
def test_read_prompt():
    response = client.get("/prompt")
    assert response.status_code == 404
    assert response.json() != {"msg": "Hello", "response": ""}

def test_noread_prompt():
    response = client.get("/prompt")
    assert response.status_code == 404
    assert response.json() != {"msg": "Hola", "response": ""}


# calculator.py
class Calculator:
    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b



@pytest.fixture
def calculator():
    return Calculator()


def test_add_positive_numbers(calculator):
    result = calculator.add(2, 3)
    assert result == 5


def test_add_negative_numbers(calculator):
    result = calculator.add(-1, -4)
    assert result == -5


def test_add_zero(calculator):
    result = calculator.add(10, 0)
    assert result == 10


def test_divide_valid_numbers(calculator):
    result = calculator.divide(10, 2)
    assert result == 5.0


def test_divide_by_zero(calculator):
    with pytest.raises(ValueError, match="Division by zero is not allowed"):
        calculator.divide(10, 0)


def test_divide_negative_numbers(calculator):
    result = calculator.divide(-10, 2)
    assert result == -5.0
