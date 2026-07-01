def test_insufficient_stock(client, admin_token):
    # Create a product
    product_response = client.post("/products/", 
        json={
            "name": "Test Trainer",
            "description": "A test trainer",
            "price": 99.99,
            "category": "Footwear"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    product_id = product_response.json()["id"]

    # Create inventory with only 2 items
    client.post("/inventory/",
        json={"product_id": product_id, "size": "9", "quantity": 2},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Register and login customer
    client.post("/auth/register", json={
        "email": "customer@test.com",
        "password": "TestPass1!",
        "first_name": "Test",
        "last_name": "Customer"
    })
    login = client.post("/auth/login", json={
        "email": "customer@test.com",
        "password": "TestPass1!"
    })
    customer_token = login.json()["access_token"]

    # Add 5 items to cart (more than available)
    client.post("/cart/",
        json={"product_id": product_id, "size": "9", "quantity": 5},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    # Try to place order, should fail with 409
    response = client.post("/orders/",
        json={"payment_method": "card"},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert response.status_code == 409

def test_successful_checkout_decrements_stock(client, admin_token):
    # Admin creates a product
    product_response = client.post("/products/",
        json={
            "name": "Running Shoe",
            "description": "A great shoe",
            "price": 79.99,
            "category": "Footwear"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    product_id = product_response.json()["id"]

    # Admin creates inventory with quantity 10
    client.post("/inventory/",
        json={"product_id": product_id, "size": "9", "quantity": 10},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Register and login a customer
    client.post("/auth/register", json={
        "email": "buyer@test.com",
        "password": "TestPass1!",
        "first_name": "Test",
        "last_name": "Buyer"
    })
    login = client.post("/auth/login", json={
        "email": "buyer@test.com",
        "password": "TestPass1!"
    })
    customer_token = login.json()["access_token"]

    # Add 3 items to cart
    client.post("/cart/",
        json={"product_id": product_id, "size": "9", "quantity": 3},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    # Place the order
    order_response = client.post("/orders/",
        json={"payment_method": "card"},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert order_response.status_code == 200

    # Check inventory dropped from 10 to 7
    inventory_response = client.get(f"/inventory/product/{product_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert inventory_response.json()[0]["quantity"] == 7