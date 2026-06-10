from typing import Any

from litestar.testing import TestClient
import pytest
from pytest import fixture, raises

from lessnews import (
    app,
    load_file,
    check_valid_url,
    Responses,
    cache_result_path,
    cache_html_path,
    cache_url,
)
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


def test_testlink(client: TestClient[Any]) -> None:
    response = client.get("/fix?url=testfile", follow_redirects=False)
    assert response.status_code == 302
    assert "https://example.com" in response.headers.get("location", "")

    response = client.get("/preview?url=testfile", follow_redirects=False)
    assert response.status_code == 200
    assert b"https://example.com" in response.content

    response = client.get("/preview?url=testfile&error=lol", follow_redirects=False)
    assert response.status_code == 200
    assert b"lol" in response.content

    response = client.get("/preview?url=", follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid URL" in response.content

    response = client.get("/fix?url=", follow_redirects=True)
    assert response.status_code == 200


def test_cached_result(client: TestClient[Any]) -> None:
    url = "https://apple.news/A5vHgPPmQSvuIxPjeXLTdGQ"  # WWDC 2026, from https://developer.apple.com/documentation/applenewsformat/supportedurls

    cache_result_path(url).unlink(missing_ok=True)  # Ensure cache is clear before test
    cache_html_path(url).unlink(missing_ok=True)
    response = client.get(f"/fix?url={url}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("location", "") == "http://www.apple.com"
    assert cache_result_path(url).exists()

    cache_result_path(url).unlink(missing_ok=True)  # Ensure cache is clear before test
    response = client.get(f"/fix?url={url}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("location", "") == "http://www.apple.com"


@pytest.mark.asyncio
async def test_failed_result() -> None:
    res = await cache_url(
        "https://apple.news/thisisnotavalidurl"
    )  # Invalid Apple News URL, should fail
    assert res == CachedResult(
        is_result=False,
        is_error=True,
        content="Failed to fetch the URL, please try again later.",
    )
