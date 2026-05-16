# this_file: tests/test_cli.py
"""CLI tests for twat-labs."""

from __future__ import annotations

import subprocess
import sys


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "twat_labs", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_exits_zero() -> None:
    """twat-labs --help exits 0 and prints output (Fire writes help to stderr)."""
    r = _run("--help")
    assert r.returncode == 0
    out = r.stdout + r.stderr
    assert out.strip()


def test_version_exits_zero() -> None:
    """twat-labs version prints a semver string."""
    r = _run("version")
    assert r.returncode == 0
    assert r.stdout.strip()


def test_version_looks_like_semver() -> None:
    """Version string contains at least one dot."""
    r = _run("version")
    assert "." in r.stdout


def test_info_exits_zero() -> None:
    """twat-labs info exits 0."""
    r = _run("info")
    assert r.returncode == 0
    assert "twat-labs" in r.stdout


def test_info_help() -> None:
    """twat-labs info --help exits 0."""
    r = _run("info", "--help")
    assert r.returncode == 0


def test_experiments_exits_zero() -> None:
    """twat-labs experiments exits 0."""
    r = _run("experiments")
    assert r.returncode == 0


def test_experiments_help() -> None:
    """twat-labs experiments --help exits 0."""
    r = _run("experiments", "--help")
    assert r.returncode == 0
