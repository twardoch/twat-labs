"""twat labs plugin"""

from __future__ import annotations

import runpy

from twat_labs.__version__ import __version__


def main() -> None:
    """CLI entry point for twat-labs."""
    runpy.run_module("twat_labs.__main__", run_name="__main__", alter_sys=True)


__all__ = ["__version__", "main"]
