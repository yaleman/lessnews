[private]
default:
    just --list


check: lint test mypy

lint:
    uv run ruff check lessnews tests

test:
    uv run pytest

mypy:
    uv run mypy --strict lessnews tests

docker_build:
    docker buildx build --load -t ghcr.io/yaleman/lessnews:latest .

docker_run: docker_build
    docker run -p 8001:8001 \
        --mount "type=bind,src=$(pwd)/cache/,dst=/cache" \
        ghcr.io/yaleman/lessnews:latest

coverage:
    uv run coverage run --source=lessnews --omit="lessnews/__main__.py" -m pytest
    uv run coveralls
    @echo "Coverage report should be at https://coveralls.io/github/yaleman/lessnews?branch=$(git branch --show-current)"