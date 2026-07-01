def test_customer_cannot_create_product(client):
    client.post("/auth/register", json={
        "email": "customer@example.com",
        "password": "TestPass1!",
        "first_name": "Test",
        "last_name": "Customer"
    })
    login_response = client.post("/auth/login", json={
        "email": "customer@example.com",
        "password": "TestPass1!"
    })
    token = login_response.json()["access_token"]
    
    response = client.post("/products/", 
        json={
            "name": "Test Product",
            "description": "Test description",
            "price": 99.99,
            "category": "Test"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403