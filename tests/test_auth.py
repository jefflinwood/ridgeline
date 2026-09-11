def test_protected_page_redirects_to_login(client):
    response = client.get("/orders/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_accepts_valid_credentials(client, login):
    response = login("STAFF@EXAMPLE.TEST")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    dashboard = client.get("/")
    assert dashboard.status_code == 200


def test_login_rejects_invalid_credentials(client, login):
    response = login("staff@example.test", "wrong-password")

    assert response.status_code == 200
    assert b"email and password don&#39;t match" in response.data


def test_customer_cannot_open_staff_customer_list(client, login):
    login("customer@example.test")

    response = client.get("/customers/")

    assert response.status_code == 403
