# -*- coding: utf-8 -*-
"""Custom exceptions for the viscowave package."""

from __future__ import annotations


class ViscoWaveError(RuntimeError):
    """
    Base exception for all viscowave-related errors.

    This is raised when a library call returns a non-zero error code,
    indicating a computational or runtime error in the underlying C++ library.

    Attributes:
        func: Name of the function that failed
        code: Error code returned by the library (0 = success, non-zero = error)
        message: Descriptive error message

    Example:
        >>> try:
        ...     model.compute(invalid_params)
        ... except ViscoWaveError as e:
        ...     print(f"Error in {e.func}: code {e.code}")
    """

    def __init__(self, func: str, code: int, message: str | None = None):
        """
        Initialize ViscoWaveError.

        Args:
            func: Name of the function that failed
            code: Error code from the library
            message: Optional custom error message
        """
        self.func = func
        self.code = int(code)
        if message is None:
            message = f"{func} failed with error code {code}"
        super().__init__(message)


class ViscoWaveLibraryNotFoundError(ImportError):
    """
    Raised when the required native library cannot be found or loaded.

    This typically occurs when:
    - The library file is missing from the package
    - The library architecture doesn't match the Python interpreter
    - Required system dependencies are missing

    Attributes:
        library_name: Name of the library that couldn't be loaded
        platform: Operating system and architecture information
        search_paths: List of paths where the library was searched for

    Example:
        >>> try:
        ...     from viscowave.api import ViscoWaveModel
        ... except ViscoWaveLibraryNotFoundError as e:
        ...     print(f"Library {e.library_name} not found")
        ...     print(f"Searched in: {e.search_paths}")
    """

    def __init__(
        self,
        library_name: str,
        platform: str | None = None,
        search_paths: list[str] | None = None,
        original_error: Exception | None = None,
    ):
        """
        Initialize ViscoWaveLibraryNotFoundError.

        Args:
            library_name: Name of the library that couldn't be loaded
            platform: Platform information (optional)
            search_paths: Paths where library was searched (optional)
            original_error: The underlying exception (optional)
        """
        self.library_name = library_name
        self.platform = platform
        self.search_paths = search_paths or []
        self.original_error = original_error

        message = f"Failed to load library '{library_name}'"
        if platform:
            message += f" on {platform}"
        if search_paths:
            message += f"\nSearched in: {', '.join(search_paths)}"
        if original_error:
            message += f"\nUnderlying error: {original_error}"

        super().__init__(message)


class ViscoWaveInputError(ValueError):
    """
    Raised when input parameters are invalid or incompatible.

    This is raised for parameter validation errors before calling
    the underlying library, helping catch issues early with clear
    error messages.

    Example:
        >>> try:
        ...     model.compute(sigmoid=np.array([1, 2]))  # Wrong shape
        ... except ViscoWaveInputError as e:
        ...     print(f"Invalid input: {e}")
    """

    pass


class ViscoWaveConfigError(RuntimeError):
    """
    Raised when there's a configuration or setup error.

    This includes issues like:
    - Incompatible parameter combinations
    - Missing required configuration
    - Invalid model state

    Example:
        >>> try:
        ...     model.compute(num_ve_layer=2, sigmoid=single_sigmoid)
        ... except ViscoWaveConfigError as e:
        ...     print(f"Configuration error: {e}")
    """

    pass


__all__ = [
    "ViscoWaveError",
    "ViscoWaveLibraryNotFoundError",
    "ViscoWaveInputError",
    "ViscoWaveConfigError",
]
