import time


def test_login_responds_under_2s(client):
    client.post(
        "/api/auth/register",
        json={"email": "perf-login@dyp.com", "password": "secret123"},
    )

    start = time.monotonic()
    response = client.post(
        "/api/auth/login",
        json={"email": "perf-login@dyp.com", "password": "secret123"},
    )
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert elapsed < 2.0


def test_register_responds_under_2s(client):
    start = time.monotonic()
    response = client.post(
        "/api/auth/register",
        json={"email": "perf-register@dyp.com", "password": "secret123"},
    )
    elapsed = time.monotonic() - start

    assert response.status_code == 201
    assert elapsed < 2.0
