import logging
from pathlib import Path

from lessnews import app
from lessnews.config import Settings
from lessnews.cleanup import cleanup
import uvicorn

from huey import MemoryHuey, crontab  # type: ignore[import-untyped]

SETTINGS = Settings()
logging.basicConfig(level=logging.DEBUG if SETTINGS.debug else logging.INFO)
huey = MemoryHuey()


# Every hour at 27 minutes past the hour
@huey.periodic_task(crontab(minute=SETTINGS.cache_cron_minutes))  # type: ignore[misc]
def cleanup_task() -> None:
    cleanup(Path(SETTINGS.cache_path), SETTINGS.cache_max_hours)


def main() -> None:
    uvicorn.run(app, host=SETTINGS.host, port=SETTINGS.port)


if __name__ == "__main__":
    main()
