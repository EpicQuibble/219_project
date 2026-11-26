"""Start SummitReady from the repository root; no installation required."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from summitready.server import main

if __name__ == "__main__":
    main()
