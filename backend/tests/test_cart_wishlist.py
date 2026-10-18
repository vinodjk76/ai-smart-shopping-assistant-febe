from models import Product


def _pid(app, sku):
    return Product.query.filter_by(sku=sku).first().id


def test_cart_totals_use_server_prices(app, client):
    a, b = _pid(app, "HP-001"), _pid(app, "AC-001")  # cheapest sample prices 1799 / 1799
    client.post("/api/cart/items", json={"product_id": a, "quantity": 2})
    r = client.post("/api/cart/items", json={"product_id": b, "quantity": 1,
                                             "price": 1, "unit_price": 1, "total": 1})
    assert r.status_code == 201
    cart = r.get_json()
    assert cart["total"] == 1799 * 3  # client-supplied prices ignored
    assert cart["item_count"] == 3
    line = next(i for i in cart["items"] if i["product_id"] == a)
    assert line["unit_price"] == 1799 and line["line_total"] == 3598


def test_cart_quantity_update_remove_and_persist(app, client):
    pid = _pid(app, "HP-001")
    item = client.post("/api/cart/items", json={"product_id": pid}).get_json()["items"][0]
    r = client.patch(f"/api/cart/items/{item['id']}", json={"quantity": 4})
    assert r.get_json()["total"] == 1799 * 4
    assert client.get("/api/cart").get_json()["item_count"] == 4  # persisted in DB
    r = client.delete(f"/api/cart/items/{item['id']}")
    assert r.get_json()["items"] == [] and r.get_json()["total"] == 0


def test_cart_adding_same_product_merges(app, client):
    pid = _pid(app, "HP-001")
    client.post("/api/cart/items", json={"product_id": pid, "quantity": 1})
    cart = client.post("/api/cart/items", json={"product_id": pid, "quantity": 2}).get_json()
    assert len(cart["items"]) == 1 and cart["items"][0]["quantity"] == 3


def test_cart_validation(app, client):
    pid = _pid(app, "HP-001")
    assert client.post("/api/cart/items", json={"product_id": pid, "quantity": 0}).status_code == 400
    assert client.post("/api/cart/items", json={"product_id": pid, "quantity": -1}).status_code == 400
    assert client.post("/api/cart/items", json={"product_id": pid, "quantity": 999}).status_code == 400
    assert client.post("/api/cart/items", json={"product_id": pid, "quantity": "x"}).status_code == 400
    assert client.post("/api/cart/items", json={"product_id": pid, "quantity": 1.5}).status_code == 400
    assert client.post("/api/cart/items", json={}).status_code == 400
    assert client.post("/api/cart/items", json={"product_id": 99999}).status_code == 404
    assert client.post("/api/cart/items", data="nope").status_code == 415
    item = client.post("/api/cart/items", json={"product_id": pid}).get_json()["items"][0]
    assert client.patch(f"/api/cart/items/{item['id']}", json={"quantity": 0}).status_code == 400
    assert client.patch("/api/cart/items/9999", json={"quantity": 1}).status_code == 404
    assert client.delete("/api/cart/items/9999").status_code == 404
    # total max per product enforced when merging
    assert client.post("/api/cart/items", json={"product_id": pid, "quantity": 10}).status_code == 400


def test_cart_rejects_out_of_stock(app, client):
    r = client.post("/api/cart/items", json={"product_id": _pid(app, "LP-003")})
    assert r.status_code == 409 and r.get_json()["error"]["code"] == "out_of_stock"


def test_wishlist_add_remove_persist(app, client):
    pid = _pid(app, "SM-001")
    r = client.post("/api/wishlist/items", json={"product_id": pid})
    assert r.status_code == 201 and r.get_json()["count"] == 1
    # adding again is idempotent
    r = client.post("/api/wishlist/items", json={"product_id": pid})
    assert r.status_code == 200 and r.get_json()["count"] == 1
    items = client.get("/api/wishlist").get_json()["items"]
    assert items[0]["product"]["id"] == pid
    r = client.delete(f"/api/wishlist/items/{items[0]['id']}")
    assert r.get_json()["count"] == 0
    assert client.delete("/api/wishlist/items/12345").status_code == 404


def test_wishlist_validation(client):
    assert client.post("/api/wishlist/items", json={"product_id": "abc"}).status_code == 400
    assert client.post("/api/wishlist/items", json={"product_id": 99999}).status_code == 404
    assert client.post("/api/wishlist/items", json=[1, 2]).status_code == 400
