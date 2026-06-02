# -*- coding: utf-8 -*-
"""Dynamic library loading utilities for viscowave."""

from __future__ import annotations

import ctypes as ct
import logging
import os
import platform
from pathlib import Path
from typing import Sequence

__all__ = ["load_viscowave_lib", "load_relaxation_lib"]

_logger = logging.getLogger(__name__)


def _default_candidates(base: str) -> tuple[str, ...]:
    """
    Get default library filename candidates for the current platform.

    Args:
        base: Base name of the library (e.g., 'ViscoWave')

    Returns:
        Tuple of possible filenames to try, in order of preference

    Example:
        >>> _default_candidates('ViscoWave')
        ('ViscoWave_x64.dll', 'ViscoWave.dll')  # on Windows 64-bit
    """
    system = platform.system()

    if system == "Windows":
        arch = platform.architecture()[0]
        if arch == "64bit":
            return (f"{base}_x64.dll", f"{base}.dll")
        return (f"{base}.dll",)

    elif system == "Darwin":  # macOS
        return (f"{base}.dylib",)

    else:  # Linux and others
        return (f"{base}.so",)


def _add_windows_dll_dirs(dirs: Sequence[Path]) -> None:
    """
    Add directories to Windows DLL search path (Windows only).

    Args:
        dirs: List of directories to add to the search path
    """
    if platform.system() != "Windows":
        return

    for d in dirs:
        if d.exists() and d.is_dir():
            try:
                os.add_dll_directory(str(d))
                _logger.debug(f"Added DLL directory: {d}")
            except (OSError, AttributeError) as e:
                _logger.warning(f"Failed to add DLL directory {d}: {e}")


def _resolve_local(candidates: Sequence[str]) -> str | None:
    """
    Try to find library file in the package directory.

    Args:
        candidates: List of library filenames to search for

    Returns:
        Absolute path to the found library, or None if not found
    """
    here = Path(__file__).parent.resolve()
    _logger.debug(f"Searching for library in: {here}")

    for name in candidates:
        p = here / name
        if p.is_file():
            _logger.debug(f"Found library: {p}")
            return str(p)

    _logger.debug(f"Library not found in {here}. Tried: {candidates}")
    return None


def _load_lib(path: str | None, base: str) -> ct.CDLL:
    """
    Load a dynamic library with platform-specific handling.

    Args:
        path: Optional explicit path to library file
        base: Base name of library (e.g., 'ViscoWave')

    Returns:
        Loaded ctypes CDLL object

    Raises:
        OSError: If library cannot be loaded
        FileNotFoundError: If library file doesn't exist
    """
    from .exceptions import ViscoWaveLibraryNotFoundError

    candidates = _default_candidates(base)
    system_info = f"{platform.system()} {platform.machine()}"

    # Determine library path
    if path:
        lib_path = path
        _logger.debug(f"Using explicit library path: {lib_path}")
    else:
        lib_path = _resolve_local(candidates)
        if not lib_path:
            # Last resort: try system-wide search
            lib_path = candidates[0]
            _logger.warning(
                f"Library '{base}' not found in package directory, "
                f"trying system-wide search for '{lib_path}'"
            )

    # Add Windows DLL directories before loading
    if platform.system() == "Windows":
        package_dir = Path(__file__).parent.resolve()
        _add_windows_dll_dirs([package_dir])

    # Try to load the library
    try:
        _logger.info(f"Loading library: {lib_path}")
        lib = ct.CDLL(lib_path)
        _logger.info(f"Successfully loaded library: {base}")
        return lib

    except OSError as e:
        error_msg = str(e)
        search_paths = [str(Path(__file__).parent.resolve())]

        _logger.error(
            f"Failed to load library '{base}' from '{lib_path}': {error_msg}"
        )

        raise ViscoWaveLibraryNotFoundError(
            library_name=base,
            platform=system_info,
            search_paths=search_paths,
            original_error=e,
        ) from e


def load_viscowave_lib(path: str | None = None) -> ct.CDLL:
    """
    Load the ViscoWave native library.

    Args:
        path: Optional explicit path to library file.
              If None, searches in the package directory.

    Returns:
        Loaded ctypes CDLL object

    Raises:
        ViscoWaveLibraryNotFoundError: If library cannot be found or loaded

    Example:
        >>> lib = load_viscowave_lib()
        >>> # Or with explicit path:
        >>> lib = load_viscowave_lib('/custom/path/ViscoWave.dylib')
    """
    return _load_lib(path, "ViscoWave")


def load_relaxation_lib(path: str | None = None) -> ct.CDLL:
    """
    Load the Relaxation_Sig_to_Prony native library.

    Args:
        path: Optional explicit path to library file.
              If None, searches in the package directory.

    Returns:
        Loaded ctypes CDLL object

    Raises:
        ViscoWaveLibraryNotFoundError: If library cannot be found or loaded

    Example:
        >>> lib = load_relaxation_lib()
        >>> # Or with explicit path:
        >>> lib = load_relaxation_lib('/custom/path/Relaxation_Sig_to_Prony.dylib')
    """
    return _load_lib(path, "Relaxation_Sig_to_Prony")
