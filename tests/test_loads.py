from typing import Any

from litestar.testing import TestClient
from pytest import fixture, raises

from lessnews import app, load_file


@fixture(scope="module")
def client() -> TestClient[Any]:
    return TestClient(app)


def test_root(client: TestClient[Any]) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to LessNews" in response.text

    response = client.get("/fix?url=example.com")
    assert response.status_code == 200
    assert b"example.com" in response.content
    assert "error=Invalid" in str(response.url)


def test_redirect(client: TestClient[Any]) -> None:
    response = client.get("/fix?url=testfile", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("location") == "https://example.com"


def test_load_file() -> None:
    with raises(FileNotFoundError):
        load_file("nonexistentfile.txt")
