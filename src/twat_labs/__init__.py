# this_file: src/twat_labs/__init__.py
"""twat-labs: experimental sandbox plugin for the twat ecosystem.

This package is a proving ground for new features, utilities, and integrations
that are under development or evaluation before potential inclusion in the core
``twat`` package or other specialised ``twat-*`` plugins.

Public API
----------
__version__ : str
    The installed package version (derived from git tags via hatch-vcs).
main : callable
    Fire-based CLI dispatcher (also exposed as the ``twat-labs`` console script).

Role in twat ecosystem
-----------------------
``twat-labs`` registers itself as a plugin under the ``twat.plugins`` entry-point
group with the key ``labs``.  When ``twat`` loads its plugin registry it will
discover this package and surface its commands alongside those of other plugins.
"""

from __future__ import annotations

import runpy

from twat_labs.__version__ import __version__


def main() -> None:
    """CLI entry point for twat-labs (delegates to Fire dispatcher)."""
    runpy.run_module("twat_labs.__main__", run_name="__main__", alter_sys=True)


__all__ = ["__version__", "main"]
