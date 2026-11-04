"""Paths to the repository's data, for tests that read files."""

import os
from pathlib import Path

#   Shared test data paths; individual tests live beside their source modules.
REPO = str(Path(__file__).resolve().parents[2])
DOCS_EXAMPLES = os.path.join(REPO, "docs", "examples")
GAMES = os.path.join(REPO, "data", "games")
