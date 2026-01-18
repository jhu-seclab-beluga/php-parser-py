"""
php-parser-py: Python wrapper for PHP-Parser using cpg2py.

This package provides a Python interface to PHP-Parser, enabling AST parsing
and manipulation of PHP code.
"""

from php_parser_py._parser import Parser as _Parser
from php_parser_py._printer import PrettyPrinter as _PrettyPrinter
from php_parser_py._resources import ensure_php_parser_extracted

# Ensure PHP-Parser is extracted on first import
ensure_php_parser_extracted()

# Import and expose public classes directly
from php_parser_py._ast import AST
from php_parser_py.exceptions import ParseError, RunnerError


class Parser(_Parser):
    """Parses PHP source code using PHP-Parser.

    Invokes PHP-Parser to parse PHP code and converts the resulting JSON
    to cpg2py Storage format for graph-based analysis.
    """


class PrettyPrinter(_PrettyPrinter):
    """Converts AST to PHP code using PHP-Parser's PrettyPrinter.

    Reconstructs JSON from AST graph and invokes PHP-Parser to generate
    formatted PHP source code.
    """


def parse(code: str) -> AST:
    """Parse PHP code and return AST.

    Convenience function that creates a Parser instance and parses the code.

    Args:
        code: PHP source code string.

    Returns:
        AST instance containing parsed code structure.

    Raises:
        ParseError: If PHP-Parser reports syntax error.
    """
    parser = Parser()
    return parser.parse(code)


def parse_file(path: str) -> AST:
    """Read and parse PHP file.

    Convenience function that creates a Parser instance and parses the file.

    Args:
        path: File path string.

    Returns:
        AST instance containing parsed code structure.

    Raises:
        ParseError: If PHP-Parser reports syntax error.
        FileNotFoundError: If file does not exist.
    """
    parser = Parser()
    return parser.parse_file(path)


__version__ = "0.1.0"
__all__ = [
    "AST",
    "Parser",
    "PrettyPrinter",
    "ParseError",
    "RunnerError",
    "parse",
    "parse_file",
]
