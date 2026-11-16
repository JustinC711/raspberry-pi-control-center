
"""Install the astronomy data required by the dashboard."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from skyfield.api import Loader

BASE_DIR = Path(__file__).resolve().parent.parent
DESTINATION = BASE_DIR / "de421.bsp"


def main():
    # Leave existing astronomy data untouched.
    if DESTINATION.exists():
        print(f"Astronomy data already exists: {DESTINATION}")
        return

    print("Downloading astronomy data from NASA JPL...")

    try:
        # Download into a temporary directory.
        with TemporaryDirectory(dir=BASE_DIR) as temporary_dir:
            loader = Loader(temporary_dir)
            planets = loader("de421.bsp")

            # Verify that Skyfield can read the data.
            if not planets.segments:
                raise ValueError("Astronomy data contains no segments")

            temporary_file = Path(temporary_dir) / "de421.bsp"

            # Atomically install the file without overwriting
            # any existing astronomy data.
            os.link(temporary_file, DESTINATION)

        print(f"Astronomy data installed: {DESTINATION}")

    except FileExistsError:
        print("Astronomy data already exists; leaving it unchanged.")

    except Exception as error:
        print(f"Astronomy installation failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
