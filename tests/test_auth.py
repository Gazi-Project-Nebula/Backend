def test_create_user(client):
    response = client.post(
        "/users/",
        json={"username": "testuser", "password": "securepassword", "role": "voter"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert "id" in response.json()

def test_create_duplicate_user(client):
    user_data = {"username": "unique_user", "password": "password", "role": "voter"}
    client.post("/users/", json=user_data)
    # Try creating the same user again
    response = client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_login_and_get_token(client):
    # 1. Register
    client.post("/users/", json={"username": "auth_user", "password": "password123"})
    
    # 2. Login
    response = client.post(
        "/token",
        data={"username": "auth_user", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"