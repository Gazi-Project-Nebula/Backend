def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "securepassword"}
    )
    assert response.status_code == 201
    # Register endpoint returns no body

def test_register_duplicate_user(client):
    user_data = {"username": "unique_user", "password": "password"}
    client.post("/api/auth/register", json=user_data)
    # Try creating the same user again
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_login_api(client):
    # 1. Register
    client.post("/api/auth/register", json={"username": "auth_user", "password": "password123"})
    
    # 2. Login (New Endpoint)
    response = client.post(
        "/api/auth/login",
        json={"username": "auth_user", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "auth_user"
    assert "role" in data
    assert "id" in data

def test_get_token_for_admin_actions(client):
    # 1. Register
    client.post("/api/auth/register", json={"username": "token_user", "password": "password123"})
    
    # 2. Get Token (OAuth2 endpoint still needed for Authorization headers in other tests)
    response = client.post(
        "/token",
        data={"username": "token_user", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"