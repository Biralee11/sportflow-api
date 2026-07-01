def test_register_success(client):
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "TestPass1!",
        "first_name": "Test",
        "last_name": "User"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data

def test_register_duplicate_email(client):
    client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "TestPass1!",
        "first_name": "Test",
        "last_name": "User"
    })
    response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "TestPass1!",
        "first_name": "Test",
        "last_name": "User"
    })
    assert response.status_code == 400

def test_login_success(client):
    client.post("/auth/register", json={
        "email": "loginuser@example.com",
        "password": "TestPass1!",
        "first_name": "Test",
        "last_name": "User"
    })
    response = client.post("/auth/login", json={
        "email": "loginuser@example.com",
        "password": "TestPass1!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "TestPass1!",
        "first_name": "Test",
        "last_name": "User"
    })
    response = client.post("/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "WrongPassword1!"
    })
    assert response.status_code == 401