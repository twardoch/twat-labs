#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "fire",
# ]
# ///
# this_file: needs2.py

"""
A focused module that provides QtNetwork-based download functionality with
a synchronous Python interface. Handles HTTP redirects automatically.
"""

## TODO:
## Mac uv is at https://astral.sh/uv/install.sh but on Windows to install it, users need to do:
## powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
## and we need to find a Python-compatible way of doing the above
## The code is also pretty messy, should be refactored for clarity and itemization

import importlib
import importlib.util
import logging
import os
import platform
import shutil
import site
import subprocess
import sys
from functools import lru_cache, wraps
from pathlib import Path
from typing import Callable, List, Optional, Tuple

###############################
## PATH PROVIDERS & ENVIRONMENT FUNCTIONS
###############################
"""
Functions related to system path management including:
- Custom path provider registration
- System-specific path discovery
- PATH environment manipulation
"""

# Type for path provider functions
PathProvider = Callable[[], List[str]]

# Registry for custom path providers
_path_providers: List[PathProvider] = []

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG, format="%(levelname)s: %(message)s", stream=sys.stdout
)


def _get_fontlab_site_packages() -> Path | None:
    """
    Get the FontLab site-packages directory path if FontLab is available.

    This function attempts to locate the FontLab-specific site-packages directory
    by using FontLab's data path and the current Python version. This is needed
    because FontLab maintains its own Python environment.

    Returns:
        Path: Path to FontLab's site-packages directory if found and in sys.path
        None: If FontLab is not available or the path is not in sys.path
    """
    try:
        import fontlab

        # Get FontLab data path
        fontlab_path = Path(fontlab.flPreferences.instance().dataPath)

        # Get current Python version (major.minor)
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        # Construct the full path
        site_packages_path = fontlab_path / "python" / python_version / "site-packages"

        # Only return the path if it's actually in sys.path
        return site_packages_path if str(site_packages_path) in sys.path else None

    except ImportError:
        return None


def get_site_packages_path() -> Path:
    # Get FontLab site-packages if available, otherwise fall back to user site-packages
    return _get_fontlab_site_packages() or Path(site.getusersitepackages())


# Constant for the UV package installation target.
# FIXME: Update UV_INSTALL_TARGET as needed for environments other than FontLab.
UV_INSTALL_TARGET = Path(
    os.environ.get(
        "UV_INSTALL_TARGET",
        str(get_site_packages_path()),
    )
)


def register_path_provider(provider: PathProvider) -> None:
    """Register a custom path provider function."""
    _path_providers.append(provider)
    clear_path_cache()  # Invalidate cache when providers change


####################################
## XDG PATH MANAGEMENT
####################################
def get_xdg_paths() -> List[str]:
    """Get XDG specification paths for common tool installations."""
    paths = []

    # XDG_BIN_HOME
    xdg_bin = os.environ.get("XDG_BIN_HOME")
    if xdg_bin:
        paths.append(xdg_bin)

    # XDG_DATA_HOME/../bin
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        data_parent_bin = Path(xdg_data).parent / "bin"
        paths.append(str(data_parent_bin))

    # Default ~/.local/bin if XDG vars not set
    local_bin = Path.home() / ".local" / "bin"
    if local_bin.exists() and str(local_bin) not in paths:
        paths.append(str(local_bin))

    return paths


####################################
## SYSTEM-SPECIFIC PATH DISCOVERY
####################################
def get_system_specific_paths() -> List[str]:
    """Get OS-specific executable paths."""
    system = platform.system()
    paths = []

    if system == "Darwin":  # macOS
        paths.extend(
            [
                "/usr/local/bin",  # Homebrew (Intel)
                "/usr/local/sbin",
                "/opt/homebrew/bin",  # Homebrew (Apple Silicon)
                "/opt/homebrew/sbin",
                "/usr/bin",
                "/usr/sbin",
                "/bin",
                "/sbin",
                "/Library/Apple/usr/bin",
                "/Applications/Xcode.app/Contents/Developer/usr/bin",
            ]
        )
    elif system == "Windows":
        win_dir = os.environ.get("SystemRoot", r"C:\Windows")
        paths.extend(
            [
                str(
                    Path(os.path.expanduser("~"))
                    / "AppData"
                    / "Local"
                    / "Microsoft"
                    / "WindowsApps"
                ),
                os.path.join(win_dir, "System32"),
                win_dir,
                os.path.join(win_dir, "System32", "Wbem"),
                os.path.join(win_dir, "System32", "WindowsPowerShell", "v1.0"),
                r"C:\Program Files\PowerShell\7",
                r"C:\ProgramData\chocolatey\bin",
            ]
        )
    else:  # Linux and others
        paths.extend(
            [
                "/usr/local/bin",
                "/usr/local/sbin",
                "/usr/bin",
                "/usr/sbin",
                "/bin",
                "/sbin",
            ]
        )

        # Add snap paths if they exist
        snap_bin = "/snap/bin"
        if os.path.exists(snap_bin):
            paths.append(snap_bin)

    return paths


###############################
## UTILITY FUNCTIONS
###############################
"""
Core utilities for system interaction including:
- Executable verification
- Enhanced which implementation
- Data type conversion
"""


####################################
## EXECUTABLE SECURITY
####################################
def verify_executable(path: str) -> Tuple[bool, str]:
    """Validate executable safety and permissions."""
    if not os.path.exists(path):
        return False, "File does not exist"

    if not os.path.isfile(path):
        return False, "Not a regular file"

    # Check if path is writable by others on Unix-like systems
    if platform.system() != "Windows":
        mode = os.stat(path).st_mode
        if mode & 0o002:  # World-writable
            return False, "File is world-writable"

    # On Windows, we could add additional checks like:
    # - Digital signature verification
    # - Known paths validation
    # But for now we'll keep it simple

    return True, "OK"


####################################
## DATA CONVERSION
####################################
def bin_or_str(data: bytes, mode: int = 0) -> bytes | str:
    """Convert bytes to string based on decoding mode."""
    match mode:
        case 1:
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data
        case 2:
            return data.decode("utf-8")
        case _:
            return data


###############################
## URL DOWNLOAD FUNCTIONS
###############################
"""
Network utilities for HTTP content retrieval with:
- QtNetwork implementation (priority)
- urllib fallback implementation
"""


####################################
## CORE DOWNLOAD MECHANISMS
####################################
@lru_cache(maxsize=20)
def download_url_qt(
    url: str,
    mode: int = 1,
    max_redir: int = 5,
) -> bytes | str:
    """
    Fetch URL with redirect handling. Returns bytes/str based on mode.

    Args:
        url: HTTP/HTTPS URL to download from
        max_redir: Maximum number of redirects to follow (default: 5)
        mode: 0 for raw bytes, 1 for string or bytes, 2 for string

    Returns:
        bytes | str: Downloaded content

    Raises:
        RuntimeError: For network errors, too many redirects, or invalid responses
    """
    from PythonQt import QtNetwork
    from PythonQt.QtCore import QEventLoop, QUrl

    loop, nam = QEventLoop(), QtNetwork.QNetworkAccessManager()
    current_url, redir_count = QUrl(url), 0

    while redir_count <= max_redir:
        reply = nam.get(QtNetwork.QNetworkRequest(current_url))
        reply.finished.connect(loop.quit)
        loop.exec_()

        if (
            sc := reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute)
        ) in {301, 302, 303, 307, 308}:
            if (
                redir_url := reply.attribute(
                    QtNetwork.QNetworkRequest.RedirectionTargetAttribute
                )
            ).isValid():
                current_url, redir_count = (
                    reply.url().resolved(redir_url),
                    redir_count + 1,
                )
                reply.deleteLater()
                continue
            reply.deleteLater()
            raise RuntimeError(f"Invalid redirect (HTTP {sc})")

        if reply.error() == QtNetwork.QNetworkReply.NoError:
            data = bin_or_str(reply.readAll().data(), mode)
            reply.deleteLater()
            return data

        err = f"{reply.errorString()} (HTTP {sc})"
        reply.deleteLater()
        raise RuntimeError(f"Download failed: {err}")

    raise RuntimeError(f"Max redirects exceeded ({max_redir})")


@lru_cache(maxsize=20)
def download_url_py(
    url: str,
    mode: int = 1,
    max_redir: int = 5,
) -> bytes | str:
    """
    Fetch URL with redirect handling using urllib. Returns bytes/str based on mode.

    Args:
        url: HTTP/HTTPS URL to download from
        max_redir: Maximum number of redirects to follow (default: 5)
        mode: 0 for raw bytes, 1 for string or bytes, 2 for string

    Returns:
        bytes | str: Downloaded content

    Raises:
        RuntimeError: For network errors, too many redirects, or invalid responses
    """
    import urllib.error
    import urllib.request

    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "Python-urllib/3.x")]

    try:
        with opener.open(url) as response:
            data = response.read()
            return bin_or_str(data, mode)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Download failed: HTTP {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Download failed: {str(e.reason)}")
    except Exception as e:
        raise RuntimeError(f"Download failed: {str(e)}")


@lru_cache(maxsize=20)
def download_url(
    url: str,
    mode: int = 1,
    max_redir: int = 5,
) -> bytes | str:
    try:
        pass

        return download_url_qt(url, mode, max_redir)
    except Exception as e:
        return download_url_py(url, mode, max_redir)


###############################
## UV INSTALLATION HELPERS
###############################
"""
UV package manager lifecycle management:
- Installation routines
- Binary location
- Dependency verification
"""


####################################
## INSTALLATION TARGET CONFIG
####################################
# Configurable via UV_INSTALL_TARGET environment variable
UV_INSTALL_TARGET = Path(
    os.environ.get(
        "UV_INSTALL_TARGET",
        str(
            Path.home()
            / "Library/Application Support/FontLab/FontLab 8/python/3.11/site-packages"
        ),
    )
)


####################################
## PIP MANAGEMENT
####################################
@lru_cache(maxsize=20)
def which_pip() -> Path | None:
    try:
        pass

        pip_cli = which("pip")
        if pip_cli:
            pip_cli = Path(pip_cli)
            if pip_cli.exists():
                return pip_cli
    except ImportError:
        pass

    try:
        pip_cli = which("pip")
        if pip_cli:
            pip_cli = Path(pip_cli)
            if pip_cli.exists():
                return pip_cli
    except Exception as e:
        pass
    try:
        import ensurepip

        ensurepip.bootstrap()
        importlib.import_module("pip")
        pip_cli = which("pip")
        if pip_cli:
            pip_cli = Path(pip_cli)
            if pip_cli.exists():
                return pip_cli
    except Exception as e:
        logging.warning(f"Error ensuring pip: {str(e)}")
    return None


###############################
## DECORATORS & MAIN FUNCTION
###############################
"""
Application entry points and dependency management decorators:
- needs(): Auto-install decorator
- main(): CLI entry point
"""


def needs(mods: List[str]) -> Callable:
    """Decorator to auto-install missing dependencies using uv."""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            missing = [m for m in mods if not importlib.util.find_spec(m)]
            if missing:
                uv_cli = which_uv()
                if uv_cli:
                    print(f"Installing {', '.join(missing)} via {uv_cli}")
                    subprocess.run(
                        [
                            str(uv_cli),
                            "pip",
                            "install",
                            "--python",
                            sys.executable,
                            # "--target",
                            # str(UV_INSTALL_TARGET),
                            *missing,
                        ],
                        check=True,
                    )
                # Force import newly installed packages
                for mod in missing:
                    importlib.import_module(mod)
            return f(*args, **kwargs)

        return wrapper

    return decorator


@needs(["fire", "pydantic"])
def main():
    import fire

    print(fire)


if __name__ == "__main__":
    main()


####################################
## EXECUTABLE SECURITY
####################################
@lru_cache(maxsize=20)
def which(
    cmd: str,
    mode: int = os.F_OK | os.X_OK,
    path: Optional[str] = None,
    verify: bool = True,
) -> Path | None:
    """
    Enhanced version of shutil.which that searches an extended set of paths.

    Args:
        cmd: The command to search for
        mode: The mode to use when checking if a file is executable
        path: Optional path string to use instead of building one
        verify: Whether to perform security verification

    Returns:
        Path | None: Full path to the command if found, None otherwise
    """
    if path is None:
        path = build_extended_path()

    result = shutil.which(cmd, mode=mode, path=path)

    if result and verify:
        is_safe, reason = verify_executable(result)
        if not is_safe:
            if os.environ.get("CLIFIND_DEBUG"):
                print(f"Warning: Found {cmd} at {result} but {reason}", file=sys.stderr)
            return None

    if result:
        result_path = Path(result)
        if result_path.exists():
            return result_path
    return None


@lru_cache(maxsize=20)
def build_extended_path() -> str:
    """
    Build a comprehensive PATH string combining:
    1. Current PATH
    2. XDG specification paths
    3. System-specific paths
    4. Default Python paths
    5. Custom provider paths

    Returns:
        str: os.pathsep-separated path string
    """
    # Start with current PATH
    current_path = os.environ.get("PATH", "").split(os.pathsep)

    # Collect all potential paths
    all_paths = []
    all_paths.extend(current_path)
    all_paths.extend(get_xdg_paths())
    all_paths.extend(get_system_specific_paths())
    all_paths.extend(os.defpath.split(os.pathsep))

    # Add paths from custom providers
    for provider in _path_providers:
        try:
            all_paths.extend(provider())
        except Exception as e:
            if os.environ.get("CLIFIND_DEBUG"):
                print(
                    f"Warning: Path provider {provider.__name__} failed: {e}",
                    file=sys.stderr,
                )

    # Remove empty strings and duplicates while preserving order
    seen = set()
    unique_paths = []
    for path in all_paths:
        if path and path not in seen and os.path.isdir(path):
            seen.add(path)
            unique_paths.append(path)

    return os.pathsep.join(unique_paths)


def clear_path_cache() -> None:
    """Clear the cached PATH. Call this if environment variables change."""
    build_extended_path.cache_clear()
