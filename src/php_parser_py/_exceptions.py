"""Exception classes for php-parser-py."""


class ParseError(Exception):
    """Raised when PHP-Parser reports a syntax error.

    Attributes:
        message: Error message from PHP-Parser.
        line: Line number where the error occurred, if available.
    """

    def __init__(self, message: str, line: int | None = None) -> None:
        """Initialize ParseError.

        Args:
            message: Error message from PHP-Parser.
            line: Line number where the error occurred, if available.
        """
        super().__init__(message)
        self.message = message
        self.line = line


class RunnerError(Exception):
    """Raised when PHP process execution fails.

    Attributes:
        message: Error message describing the failure.
        stderr: Standard error output from the PHP process.
        exit_code: Exit code returned by the PHP process.
    """

    def __init__(self, message: str, stderr: str = "", exit_code: int = 1) -> None:
        """Initialize RunnerError.

        Args:
            message: Error message describing the failure.
            stderr: Standard error output from the PHP process.
            exit_code: Exit code returned by the PHP process.
        """
        super().__init__(message)
        self.message = message
        self.stderr = stderr
        self.exit_code = exit_code
