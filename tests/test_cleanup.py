import os
from tempfile import TemporaryDirectory
from pathlib import Path

from lessnews.cleanup import cleanup


def test_cleanup() -> None:
    tempdir = TemporaryDirectory()
    url = "https://example.com/news/article"
    filename = f"{tempdir.name}/12345.result"
    with open(filename, "w") as f:
        f.write(url)

    # set the file modification time to 2 hours ago
    mod_time = os.path.getmtime(filename) - (2 * 3600)
    os.utime(filename, (mod_time, mod_time))

    cleanup(Path(tempdir.name), cache_max_hours=0)
    assert not os.path.exists(filename)
