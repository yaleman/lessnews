from litestar.params import QueryParameter
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Annotated
import os.path
from hashlib import sha256
from urllib.parse import urlparse
from importlib import metadata
from aiohttp import ClientSession
from aiohttp.client_exceptions import InvalidUrlClientError

from litestar import Litestar, MediaType, get, Response
from litestar.connection import Request
from litestar.exceptions import HTTPException
from litestar.logging import LoggingConfig
from litestar.response import Redirect

from .config import Settings
from .models import CachedResult, FixedLink

SETTINGS = Settings()
STATIC_PATH = Path(__file__).parent / "static"
CACHE_DIR = Path(SETTINGS.cache_path)
VALID_URLS_CONTAIN = ["apple.news"]
URL_PATTERN = r"^http[s]*:\/\/.+"

APP_VERSION = metadata.version("lessnews")
USERAGENT = f"LessNews/{APP_VERSION}"


@lru_cache(maxsize=32)
def load_file(file_path: Path) -> str:
    """loads a static file"""
    filepath = Path(os.path.join(STATIC_PATH, file_path))
    if not filepath.exists():
        raise FileNotFoundError(f"Static file not found: {filepath}")
    return filepath.read_text(encoding="utf-8")


def inject_url(index_html: str, url: Optional[str]) -> str:
    if url is not None:
        index_html = index_html.replace(
            "<!--LINK_INPUT-->",
            f'<input type="text" name="url" placeholder="Fix your link..." value="{url}" required>',
        )
    else:
        index_html = index_html.replace(
            "<!--LINK_INPUT-->",
            '<input type="text" name="url" placeholder="Fix your link..." required>',
        )
    return index_html


@get("/", media_type=MediaType.HTML, cache=True)
async def root(
    url: Annotated[Optional[str], QueryParameter()] = None,
    error: Annotated[Optional[str], QueryParameter(read_only=True)] = None,
) -> str:
    index_html = load_file("index.html")
    index_html = inject_url(index_html, url)
    if error is not None:
        index_html = index_html.replace(
            "<!--ERROR-->", f'<div class="error">{error}</div>'
        )
    return index_html


@get("/styles.css", media_type=MediaType.CSS, cache=True)
async def styles() -> str:
    return load_file("styles.css")


@get("/script.js", media_type="application/js", cache=True)
async def script() -> str:
    return load_file("script.js")


class Responses(Enum):
    INVALID_URL = "Invalid URL, please check your input!"
    INVALID_SCHEME = "Invalid URL scheme, only http and https are supported."
    UNSUPPORTED_URL = (
        "The provided URL is not supported. Please provide an Apple News link."
    )


BAD_URL = CachedResult(
    is_result=False,
    is_error=True,
    content=Responses.INVALID_URL.value,
)


def check_valid_url(url: str) -> Optional[CachedResult]:
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return BAD_URL
    except Exception:
        return BAD_URL
    if parsed_url.scheme not in ("http", "https"):
        return CachedResult(
            is_result=False,
            is_error=True,
            content=Responses.INVALID_SCHEME.value,
        )
    if not any(valid in parsed_url.netloc for valid in VALID_URLS_CONTAIN):
        return CachedResult(
            is_result=False,
            is_error=True,
            content=Responses.UNSUPPORTED_URL.value,
        )
    return None


def url_hash(url: str) -> str:
    return sha256(url.encode("utf-8")).hexdigest()


def cache_result_path(url: str) -> Path:
    return CACHE_DIR / f"{url_hash(url)}.result"


def cache_html_path(url: str) -> Path:
    return CACHE_DIR / f"{url_hash(url)}.html"


async def cache_url(url: str) -> CachedResult:

    cached_result = cache_result_path(url)
    if cached_result.exists():
        return CachedResult(
            is_result=True,
            content="",
            fixed_link=FixedLink.model_validate_json(
                cached_result.read_text(encoding="utf-8")
            ),
            is_error=False,
        )
    if cache_html_path(url).exists():
        return CachedResult(
            is_result=False,
            content=cache_html_path(url).read_text(encoding="utf-8"),
            is_error=False,
        )

    valid_check = check_valid_url(url)
    if valid_check is not None:
        return valid_check

    async with ClientSession() as session:
        session.headers.add("User-Agent", USERAGENT)
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    cache_html_path(url).write_text(content, encoding="utf-8")
                    return CachedResult(
                        is_result=False, content=content, is_error=False
                    )
                print(f"Failed to fetch URL: {url=} {response.status=}")
                return CachedResult(
                    is_result=False,
                    is_error=True,
                    content="Failed to fetch the URL, please try again later.",
                )
        except InvalidUrlClientError:
            return CachedResult(
                is_result=False,
                is_error=True,
                content="Invalid URL, please check your input!",
            )
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return CachedResult(
                is_result=False,
                is_error=True,
                content="Failed to fetch the URL, please try again later.",
            )


async def fixlink(url: str) -> FixedLink:
    cached = await cache_url(url)

    if cached.is_error:
        return FixedLink(
            is_error=True,
            url=None,
            redirect=Redirect(
                path="/", query_params={"url": url, "error": str(cached.content)}
            ),
        )
    if cached.fixed_link is not None:
        return cached.fixed_link
    # apple news link
    for line in str(cached.content).splitlines():
        if '<span class="click-here">Click here</span>' in line:
            start = line.find('href="') + 6
            end = line.find('"', start)
            fixed_url = line[start:end]

            res = FixedLink(url=fixed_url, is_error=False, redirect=None)
            cache_result_path(url).write_text(res.model_dump_json(), encoding="utf-8")
            return res
    return FixedLink(
        url=None,
        is_error=True,
        redirect=Redirect(
            path="/",
            query_params={
                "url": url,
                "error": "Could not find a fixable/supported link.",
            },
        ),
    )


@get("/preview", media_type=MediaType.HTML, cache=True)
async def preview(
    url: Annotated[
        str,
        QueryParameter(read_only=True, description="The URL to preview"),
    ] = "",
    error: Annotated[Optional[str], QueryParameter()] = None,
) -> str | Redirect:
    index_html = load_file("index.html")
    if not url.strip():
        index_html = index_html.replace(
            "<!--PREVIEW-->", "<p>No URL provided for preview.</p>"
        )

    if error is not None:
        index_html = index_html.replace(
            "<!--ERROR-->", f'<div class="error">{error}</div>'
        )
    index_html = inject_url(index_html, url)
    fixed_link = await fixlink(url)
    if fixed_link is None:
        return index_html.replace("<!--PREVIEW-->", "<p>Could not fix the link.</p>")
    if fixed_link.is_error:
        if fixed_link.redirect is not None:
            return fixed_link.redirect
        return index_html.replace(
            "<!--PREVIEW-->",
            "<div class='error'>Error occurred while fixing the link.</div>",
        )
    if fixed_link.url is not None:
        preview_content = f'<div class="preview">This is the fixed link: <a href="{fixed_link.url}">{fixed_link.url}</a></div>'
    else:
        preview_content = "<p>No fixed link available.</p>"
    return index_html.replace("<!--PREVIEW-->", preview_content)


@get("/fix")
async def fix(url: Annotated[Optional[str], QueryParameter()] = None) -> Redirect:
    if url is None or not url.strip():
        return Redirect(path="/")
    fixed_link = await fixlink(url)
    if fixed_link.url is None and fixed_link.redirect is not None:
        return fixed_link.redirect
    if fixed_link.is_error:
        if fixed_link.redirect is not None:
            return fixed_link.redirect
        return Redirect(
            path="/",
            query_params={"url": url, "error": "Error occurred while fixing the link."},
        )
    print("Fixed link:", fixed_link)
    if fixed_link.url is None:
        return Redirect(
            path="/",
            query_params={
                "url": url,
                "error": "Could not find a fixable/supported link.",
            },
        )
    return Redirect(path=fixed_link.url)


def app_exception_handler(
    request: Request[Any, Any, Any], exc: HTTPException
) -> Response[Any]:
    if exc.status_code < 500:
        return Response(
            content={
                "error": f"client error {exc.status_code}",
                "path": request.url.path,
                "status_code": exc.status_code,
            },
            status_code=exc.status_code,
        )
    return Response(
        content={
            "error": "server error",
            "path": request.url.path,
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
        status_code=500,
    )


logging_config = LoggingConfig(
    root={
        "level": "DEBUG" if SETTINGS.debug else "INFO",
        "handlers": ["queue_listener"],
    },
    formatters={
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
    },
    log_exceptions="always",
)


app = Litestar(
    logging_config=logging_config,
    exception_handlers={HTTPException: app_exception_handler},  # ty:ignore[invalid-argument-type]
    route_handlers=[fix, root, styles, script, preview],
)
__all__ = ["app"]
