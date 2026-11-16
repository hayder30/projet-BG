def _move(client, headers, product_id, type_, qty, reason=""):
    return client.post(
        "/api/stock/movements",
        headers=headers,
        json={"product_id": product_id, "type": type_, "quantity": qty, "reason": reason},
    )


def test_stock_in(client, staff_headers, product):
    res = _move(client, staff_headers, product["id"], "in", 5, "Delivery")
    assert res.status_code == 201
    assert res.json()["quantity_after"] == 15
    assert res.json()["username"] == "staff"


def test_stock_out(client, staff_headers, product):
    res = _move(client, staff_headers, product["id"], "out", 4, "Sale")
    assert res.status_code == 201
    assert res.json()["quantity_after"] == 6


def test_cannot_remove_more_than_available(client, staff_headers, admin_headers, product):
    res = _move(client, staff_headers, product["id"], "out", 999)
    assert res.status_code == 400
    # stock unchanged
    assert client.get(f"/api/products/{product['id']}", headers=admin_headers).json()["quantity"] == 10


def test_adjust_sets_exact_quantity(client, staff_headers, product):
    res = _move(client, staff_headers, product["id"], "adjust", 7, "Inventory count")
    assert res.json()["quantity_after"] == 7


def test_unknown_product(client, staff_headers):
    assert _move(client, staff_headers, 12345, "in", 1).status_code == 404


def test_invalid_type_rejected(client, staff_headers, product):
    assert _move(client, staff_headers, product["id"], "teleport", 1).status_code == 422


def test_movement_history(client, staff_headers, product):
    _move(client, staff_headers, product["id"], "in", 1)
    _move(client, staff_headers, product["id"], "out", 2)
    res = client.get(f"/api/stock/movements?product_id={product['id']}", headers=staff_headers)
    assert len(res.json()) == 3  # initial + 2


def test_low_stock_flag_and_filter(client, staff_headers, admin_headers, product):
    _move(client, staff_headers, product["id"], "out", 8)  # 10 -> 2, threshold is 3
    res = client.get("/api/products?low_stock=true", headers=admin_headers)
    assert len(res.json()) == 1
    assert res.json()[0]["is_low_stock"] is True


def test_dashboard(client, staff_headers, product):
    res = client.get("/api/dashboard", headers=staff_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_products"] == 1
    assert data["total_units"] == 10
    assert data["stock_value_cost"] == 250.0
    assert data["stock_value_retail"] == 500.0
    assert data["low_stock_count"] == 0
    assert data["out_of_stock_count"] == 0


def test_dashboard_out_of_stock(client, staff_headers, product):
    _move(client, staff_headers, product["id"], "out", 10)
    data = client.get("/api/dashboard", headers=staff_headers).json()
    assert data["out_of_stock_count"] == 1
    assert data["low_stock_count"] == 1
