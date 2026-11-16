def test_create_and_get_product(client, admin_headers, product):
    assert product["is_low_stock"] is False
    res = client.get(f"/api/products/{product['id']}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["sku"] == "BG-001"


def test_initial_stock_creates_movement(client, admin_headers, product):
    res = client.get("/api/stock/movements", headers=admin_headers)
    assert len(res.json()) == 1
    assert res.json()[0]["reason"] == "Initial stock"


def test_duplicate_sku_rejected(client, admin_headers, product):
    res = client.post(
        "/api/products", headers=admin_headers, json={"sku": "BG-001", "name": "Other", "price": 10}
    )
    assert res.status_code == 409


def test_negative_price_rejected(client, admin_headers):
    res = client.post(
        "/api/products", headers=admin_headers, json={"sku": "X", "name": "Bad", "price": -5}
    )
    assert res.status_code == 422


def test_staff_cannot_create_product(client, staff_headers):
    res = client.post(
        "/api/products", headers=staff_headers, json={"sku": "S1", "name": "Nope", "price": 10}
    )
    assert res.status_code == 403


def test_staff_can_read_products(client, staff_headers, product):
    res = client.get("/api/products", headers=staff_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_update_product(client, admin_headers, product):
    res = client.put(
        f"/api/products/{product['id']}", headers=admin_headers, json={"price": 60.5}
    )
    assert res.status_code == 200
    assert res.json()["price"] == 60.5
    assert res.json()["name"] == "Glow Serum"  # untouched


def test_search_products(client, admin_headers, product):
    assert len(client.get("/api/products?q=glow", headers=admin_headers).json()) == 1
    assert len(client.get("/api/products?q=nothing", headers=admin_headers).json()) == 0
    assert len(client.get("/api/products?q=bg-001", headers=admin_headers).json()) == 1


def test_unknown_category_rejected(client, admin_headers):
    res = client.post(
        "/api/products",
        headers=admin_headers,
        json={"sku": "C1", "name": "Cat test", "price": 10, "category_id": 999},
    )
    assert res.status_code == 400


def test_category_with_products_cannot_be_deleted(client, admin_headers):
    cat = client.post("/api/categories", headers=admin_headers, json={"name": "Skincare"}).json()
    client.post(
        "/api/products",
        headers=admin_headers,
        json={"sku": "C2", "name": "In cat", "price": 10, "category_id": cat["id"]},
    )
    res = client.delete(f"/api/categories/{cat['id']}", headers=admin_headers)
    assert res.status_code == 400


def test_delete_product(client, admin_headers, product):
    assert client.delete(f"/api/products/{product['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/products/{product['id']}", headers=admin_headers).status_code == 404


def test_supplier_crud(client, admin_headers):
    res = client.post("/api/suppliers", headers=admin_headers, json={"name": "Glow Supplies"})
    assert res.status_code == 201
    assert len(client.get("/api/suppliers", headers=admin_headers).json()) == 1
    assert client.delete(f"/api/suppliers/{res.json()['id']}", headers=admin_headers).status_code == 204
