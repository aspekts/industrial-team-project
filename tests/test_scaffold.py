"""Scaffold smoke test — verifies the project structure is intact.

Real tests will live in tests/parsers/, tests/cleaning/, tests/analysis/,
and tests/ml/ as those modules are built out in Sprints 1-2.
"""

from pathlib import Path


def test_src_dirs_exist():
    root = Path(__file__).parent.parent / "src"
    for d in ("parsers", "cleaning", "analysis", "ml", "dashboard"):
        assert (root / d).exists(), f"Expected src/{d}/ to exist"


def test_data_dirs_exist():
    root = Path(__file__).parent.parent
    for d in ("data/synthetic", "data/raw", "data/clean"):
        assert (root / d).exists(), f"Expected {d}/ to exist"


def test_docs_dir_exists():
    docs = Path(__file__).parent.parent / "docs"
    assert docs.exists(), "docs/ directory is missing"
