from typing import Any

from litestar.testing import TestClient
from pytest import fixture

from lessnews import app, check_valid_url, BAD_URL


@fixture(scope="module")
def client() -> TestClient[Any]:
    return TestClient(app)


def test_404(client: TestClient[Any]) -> None:
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.json() == {
        "error": "client error 404",
        "path": "/nonexistent",
        "status_code": 404,
    }


def test_preview_bad_query(client: TestClient[Any]) -> None:

    response = client.get("/preview?url=invalid_url")
    assert response.status_code == 200
    assert b"please check your input" in response.content


def test_check_valid_url_throws_exception() -> None:

    assert check_valid_url(1) == BAD_URL  # ty:ignore[invalid-argument-type]
