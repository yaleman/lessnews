from typing import Any

from litestar.testing import TestClient
from pytest import fixture, raises

from lessnews import app, load_file, check_valid_url, Responses
from lessnews.models import CachedResult


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


def test_static(client: TestClient[Any]) -> None:
    for file in ["/styles.css", "/script.js"]:
        response = client.get(file)
        assert response.status_code == 200


def test_redirect(client: TestClient[Any]) -> None:
    response = client.get("/fix?url=testfile", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("location") == "https://example.com"


def test_load_file() -> None:
    with raises(FileNotFoundError):
        load_file("nonexistentfile.txt")


def test_valid_url() -> None:
    for url, expected in [
        (
            "http://example.com",
            CachedResult(
                is_result=False,
                is_error=True,
                content=Responses.UNSUPPORTED_URL.value,
            ),
        ),
        ("https://apple.news/foo", None),
        (
            "ftp://example.com",
            CachedResult(
                is_result=False,
                is_error=True,
                content=Responses.INVALID_SCHEME.value,
            ),
        ),
        (
            "example.com",
            CachedResult(
                is_result=False,
                is_error=True,
                content=Responses.INVALID_URL.value,
            ),
        ),
        (
            "",
            CachedResult(
                is_result=False,
                is_error=True,
                content=Responses.INVALID_URL.value,
            ),
        ),
    ]:
        assert check_valid_url(url) == expected, f"Failed for URL: '{url}'"
