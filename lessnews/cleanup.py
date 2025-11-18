from datetime import datetime, UTC
from pathlib import Path
import sys


def cleanup(dir: Path, cache_max_hours: int = 168) -> None:
    print(f"Running cleanup on {dir}...", file=sys.stderr)
    now = datetime.now(UTC).timestamp()

    for file in dir.rglob("*"):
        # get the age of the file
        if (
            "d37b9395c2baf168f977ce9ff9ec007d7270fc84cbf1549324bfc8dfc34333a9.html"
            in str(file)
        ):
            # skip the test file
            continue
        if file.is_file():
            age = (now - file.stat().st_mtime) / (3600)
            if age > cache_max_hours:
                print(f"Deleting {file} (age: {age:.2f} hours)")
                file.unlink()
