"""PrettyPrinter class for PHP code generation."""

import logging

from php_parser_py._ast import AST
from php_parser_py._runner import Runner

logger = logging.getLogger(__name__)


class PrettyPrinter:
    """Converts AST to PHP code using PHP-Parser's PrettyPrinter.

    Reconstructs JSON from AST graph and invokes PHP-Parser to generate
    formatted PHP source code.

    Attributes:
        _runner: Runner instance for PHP-Parser invocation.
    """

    def __init__(self) -> None:
        """Initialize PrettyPrinter with Runner."""
        self._runner = Runner()

    def print(self, ast: AST) -> str:
        """Generate PHP code from AST.

        Args:
            ast: AST instance to convert to code.

        Returns:
            Generated PHP source code string.

        Raises:
            RunnerError: If PHP-Parser execution fails.
        """
        json_str = ast.to_json()
        return self._runner.print(json_str)
