import pytest
from backend.app import app, in_memory_storage

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    in_memory_storage.clear()
    with app.test_client() as client:
        yield client

def test_add_order_api_success(client):
    order_data = {
        "order_id": "API001", "item_name": "API Laptop", "quantity": 1, "customer_id": "APICUST001"
    }
    response = client.post('/api/orders', json=order_data)
    assert response.status_code == 201
    assert response.json['order_id'] == "API001"

def test_get_order_api_success(client):
    client.post('/api/orders', json={
        "order_id": "GET001", "item_name": "Test Item", "quantity": 1, "customer_id": "C1"
    })
    response = client.get('/api/orders/GET001')
    assert response.status_code == 200
    assert response.json['order_id'] == "GET001"

def test_get_order_api_not_found(client):
    response = client.get('/api/orders/NONEXISTENT')
    assert response.status_code == 404

def test_update_order_status_api_success(client):
    client.post('/api/orders', json={
        "order_id": "UPDATE001", "item_name": "Test Item", "quantity": 1, "customer_id": "C1"
    })
    response = client.put('/api/orders/UPDATE001/status', json={"new_status": "shipped"})
    assert response.status_code == 200
    assert response.json['status'] == "shipped"

def test_list_all_orders_api_with_data(client):
    client.post('/api/orders', json={"order_id": "LST001", "item_name": "Item A", "quantity": 1, "customer_id": "C1"})
    client.post('/api/orders', json={"order_id": "LST002", "item_name": "Item B", "quantity": 2, "customer_id": "C2"})
    response = client.get('/api/orders')
    assert response.status_code == 200
    assert len(response.json) == 2

def test_list_orders_by_status_api_matching(client):
    client.post('/api/orders', json={"order_id": "S001", "item_name": "A", "quantity": 1, "customer_id": "C1", "status": "pending"})
    client.post('/api/orders', json={"order_id": "S002", "item_name": "B", "quantity": 2, "customer_id": "C2", "status": "shipped"})
    response = client.get('/api/orders?status=pending')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['order_id'] == "S001"


# --- Error handling ---

def test_unknown_api_route_returns_json_404(client):
    response = client.get('/api/nope')
    assert response.status_code == 404
    assert "error" in response.json

def test_wrong_method_returns_json_405(client):
    response = client.patch('/api/orders')
    assert response.status_code == 405
    assert "error" in response.json

def test_add_order_duplicate_returns_409(client):
    order = {"order_id": "DUP1", "item_name": "A", "quantity": 1, "customer_id": "C1"}
    client.post('/api/orders', json=order)
    response = client.post('/api/orders', json=order)
    assert response.status_code == 409
    assert "already exists" in response.json["error"]

def test_add_order_missing_field_returns_400(client):
    response = client.post('/api/orders', json={"order_id": "X"})
    assert response.status_code == 400
    assert "error" in response.json

def test_update_status_invalid_returns_400(client):
    client.post('/api/orders', json={"order_id": "U1", "item_name": "A", "quantity": 1, "customer_id": "C1"})
    response = client.put('/api/orders/U1/status', json={"new_status": "teleported"})
    assert response.status_code == 400

def test_update_status_non_existent_returns_404(client):
    response = client.put('/api/orders/NOPE/status', json={"new_status": "shipped"})
    assert response.status_code == 404

# --- Filter by customer ---

def _seed(client):
    client.post('/api/orders', json={"order_id": "F1", "item_name": "A", "quantity": 1, "customer_id": "C123", "status": "pending"})
    client.post('/api/orders', json={"order_id": "F2", "item_name": "B", "quantity": 1, "customer_id": "C123", "status": "shipped"})
    client.post('/api/orders', json={"order_id": "F3", "item_name": "C", "quantity": 1, "customer_id": "C999", "status": "pending"})

def test_list_orders_by_customer(client):
    _seed(client)
    response = client.get('/api/orders?customer_id=C123')
    assert response.status_code == 200
    assert {o["order_id"] for o in response.json} == {"F1", "F2"}

def test_list_orders_by_customer_and_status(client):
    _seed(client)
    response = client.get('/api/orders?customer_id=C123&status=pending')
    assert response.status_code == 200
    assert [o["order_id"] for o in response.json] == ["F1"]

def test_list_orders_invalid_status_returns_400(client):
    response = client.get('/api/orders?status=teleported')
    assert response.status_code == 400

# --- Delete ---

def test_delete_order_success(client):
    client.post('/api/orders', json={"order_id": "D1", "item_name": "A", "quantity": 1, "customer_id": "C1"})
    response = client.delete('/api/orders/D1')
    assert response.status_code == 204
    assert response.data == b""
    assert client.get('/api/orders/D1').status_code == 404

def test_delete_order_not_found(client):
    response = client.delete('/api/orders/NOPE')
    assert response.status_code == 404
    assert "error" in response.json
