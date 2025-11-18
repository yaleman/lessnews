# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LessNews is a web service that fixes news article links to point to the original source. It's built with Litestar (async web framework) and uses aiohttp for HTTP requests.

## Development Commands

### Running checks (lint + test + mypy)

```bash
just check
```

### Individual commands

```bash
# Linting
just lint

# Testing
just test

# Type checking
just mypy

# Formatting
uv run ruff fmt lessnews tests
```

### Running single tests

```bash
uv run pytest tests/test_loads.py::test_root
```

### Running the application

```bash
uv run lessnews
```

The server runs on <http://127.0.0.1:8001>

## Architecture

### Core Components

- **lessnews/**init**.py** - Main application module containing:
  - Litestar app initialization
  - Route handlers (`/`, `/styles.css`, `/fix`)
  - URL caching and link extraction logic
  - Exception handlers for HTTP and validation errors

- **lessnews/config.py** - Pydantic settings using environment variables with `LESSNEWS_` prefix:
  - `debug`: Enable debug logging
  - `cache_path`: Directory for caching fetched URLs (default: `./cache`)
  - `cache_cron_minutes`: How often to clean up the cache
  - `cache_max_hours`: How old a cached file can be in hours

- **lessnews/models.py** - Pydantic models:
  - `CachedResult`: Represents cached URL content with is_result flag

### URL Processing Flow

1. Client hits `/fix?url=<target_url>`
2. `cache_url()` checks for cached content by URL hash (SHA256)
   - Checks for `.result` file (processed result)
   - Checks for `.html` file (raw cached content)
   - If not cached, fetches URL with aiohttp and caches as `.html`
3. `fixlink()` parses HTML looking for `<span class="click-here">Click here</span>` to extract the real URL from the href
4. Returns redirect to the extracted URL

Alternatively `/preview?url=<url>` shows a preview.

### Caching Strategy

- URLs are hashed (SHA256) and stored in `cache/` directory
- Two types of cached files:
  - `{hash}.html` - Raw fetched content
  - `{hash}.result` - Processed result (extracted URL)
- `load_file()` uses LRU cache (maxsize=32) for static files

### Static Files

Static content served from `lessnews/static/`:

- `index.html` - Homepage
- `styles.css` - CSS styles

## Testing

Uses Litestar's TestClient for HTTP endpoint testing. Test fixtures are defined in test files using pytest's @fixture decorator.

## Configuration

Environment variables:

- `LESSNEWS_DEBUG` - Set to enable debug logging
- `LESSNEWS_CACHE_PATH` - Override cache directory path
