from typing import Any

from litestar.testing import TestClient
from lessnews import app
from pytest import fixture


@fixture(scope="module")
def client() -> TestClient[Any]:
    return TestClient(app)


def test_root(client: TestClient[Any]) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to LessNews" in response.text


def test_redirect(client: TestClient[Any]) -> None:
    response = client.get("/fix?url=testfile", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("location") == "https://example.com"
