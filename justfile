[private]
default:
    just --list


check: lint test type

lint:
    uv run ruff check lessnews tests

test:
    uv run pytest

type:
    uv run ty check

docker_build:
    docker build -t ghcr.io/yaleman/lessnews:latest .

docker_run: docker_build
    docker run -p 8001:8001 \
        --platform linux/$(uname -m) \
        --mount "type=bind,src=$(pwd)/cache/,dst=/cache" \
        ghcr.io/yaleman/lessnews:latest

coverage:
    uv run coverage run --source=lessnews --omit="lessnews/__main__.py" -m pytest
    uv run coveralls
    @echo "Coverage report should be at https://coveralls.io/github/yaleman/lessnews?branch=$(git branch --show-current)"