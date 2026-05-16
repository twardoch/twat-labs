# this_file: src/twat_labs/__main__.py
"""Fire CLI entry point for twat-labs."""

from __future__ import annotations

import importlib
import pkgutil
import sys

import fire

from twat_labs.__version__ import __version__


def _version() -> str:
    """Print the installed twat-labs version."""
    return __version__


def _info() -> dict:
    """Show package info for twat-labs.

    Returns:
        Dict with package name, version, and description.
    """
    return {
        "package": "twat-labs",
        "version": __version__,
        "description": "Experimental lab/demo modules for the twat ecosystem.",
        "note": (
            "twat-labs is a sandbox for experimental features. "
            "Add demo modules under src/twat_labs/ and register them via the 'experiments' command."
        ),
    }


def _experiments() -> dict:
    """List available demo/experiment modules in twat_labs.

    Returns:
        Dict mapping module names to their docstrings (or a note if none found).
    """
    _twat_labs_pkg = sys.modules.get("twat_labs") or importlib.import_module("twat_labs")
    results: dict[str, str] = {}
    pkg_path = getattr(_twat_labs_pkg, "__path__", [])
    for mod_info in pkgutil.iter_modules(pkg_path):
        if mod_info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"twat_labs.{mod_info.name}")
            results[mod_info.name] = (mod.__doc__ or "").strip().splitlines()[0] if mod.__doc__ else "(no docstring)"
        except Exception as exc:
            results[mod_info.name] = f"(import error: {exc})"

    if not results:
        results["_note"] = "No experiment modules found. Add .py files under src/twat_labs/ to register them here."
    return results


COMMANDS: dict[str, object] = {
    "version": _version,
    "info": _info,
    "experiments": _experiments,
}


def cmd_version() -> None:
    """Entry point: twat-labs-version."""
    fire.Fire(_version, name="twat-labs-version")


def cmd_info() -> None:
    """Entry point: twat-labs-info."""
    fire.Fire(_info, name="twat-labs-info")


def cmd_experiments() -> None:
    """Entry point: twat-labs-experiments."""
    fire.Fire(_experiments, name="twat-labs-experiments")


def main() -> None:
    """Fire CLI dispatcher for twat-labs."""
    fire.Fire(COMMANDS, name="twat-labs")


if __name__ == "__main__":
    main()
