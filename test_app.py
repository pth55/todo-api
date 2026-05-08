import pytest
from app import app, todos

@pytest.fixture(autouse=True)
def reset_todos():
    """Reset in-memory store before each test."""
    todos.clear()
    todos.extend([
        {"id": 1, "title": "Buy groceries", "done": False},
        {"id": 2, "title": "Read a book",   "done": False},
    ])
    import app as app_module
    app_module.next_id = 3
    yield

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_get_all_todos(client):
    res = client.get("/todos")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 2

def test_add_todo(client):
    res = client.post("/todos", json={"title": "Write tests"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "Write tests"
    assert data["done"] is False
    assert "id" in data

def test_add_todo_missing_title(client):
    res = client.post("/todos", json={})
    assert res.status_code == 400
    assert "error" in res.get_json()
