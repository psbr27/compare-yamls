"""Custom exception classes for YAML merging operations."""


class YamlMergeError(Exception):
    """Base exception class for YAML merge operations."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class ConfigurationError(YamlMergeError):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Configuration error: {message}", exit_code=2)


class FileError(YamlMergeError):
    """Exception raised for file-related errors."""

    def __init__(self, message: str) -> None:
        super().__init__(f"File error: {message}", exit_code=3)


class YamlSyntaxError(YamlMergeError):
    """Exception raised for YAML syntax errors."""

    def __init__(self, message: str, file_path: str = "") -> None:
        if file_path:
            full_message = f"YAML syntax error in {file_path}: {message}"
        else:
            full_message = f"YAML syntax error: {message}"
        super().__init__(full_message, exit_code=4)


class ValidationError(YamlMergeError):
    """Exception raised for validation errors."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Validation error: {message}", exit_code=5)


class FilePermissionError(YamlMergeError):
    """Exception raised for permission-related errors."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Permission error: {message}", exit_code=6)
