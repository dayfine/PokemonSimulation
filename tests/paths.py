"""Paths to the repository's data, for tests that read files."""

import os

#   The repository root: the parent of tests.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_EXAMPLES = os.path.join(REPO, "docs", "examples")
GAMES = os.path.join(REPO, "data", "games")
