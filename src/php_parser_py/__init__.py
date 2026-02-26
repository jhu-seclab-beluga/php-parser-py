"""
php-parser-py: Python wrapper for PHP-Parser using cpg2py.

This package provides a Python interface to PHP-Parser, enabling AST parsing
and manipulation of PHP code.
"""

from pathlib import Path
from typing import Callable

from ._resources import ensure_php_parser_extracted

# Ensure PHP-Parser is extracted on first import
ensure_php_parser_extracted()

# Import and expose public classes directly
from ._ast import AST
from ._edge import Edge
from ._exceptions import NodeNotInFileError, ParseError, RunnerError
from ._modifier import Modifier
from ._node import Node
from ._parser import Parser
from ._printer import PrettyPrinter


def parse_code(code: str) -> list[Node]:
    """Parse PHP code string into a list of top-level statement nodes.

    Does not create project or file nodes. Returns raw statement nodes.

    Args:
        code: PHP source code string.

    Returns:
        List of Node instances representing top-level statements.

    Raises:
        ParseError: If PHP-Parser reports syntax error.
    """
    parser = Parser()
    return parser.parse_code(code)


def parse_file(path: str) -> AST:
    """Read and parse a single PHP file into an AST.

    Creates a project node and a file node. The file node contains
    all statements from the file.

    Args:
        path: File path string.

    Returns:
        AST instance with project -> file -> statements hierarchy.

    Raises:
        ParseError: If PHP-Parser reports syntax error.
        FileNotFoundError: If file does not exist.
    """
    parser = Parser()
    return parser.parse_file(path)


def _default_file_filter(path: Path) -> bool:
    return path.suffix == ".php"


def parse_project(
    project_path: str,
    file_filter: Callable[[Path], bool] | None = None,
) -> AST:
    """Parse all PHP files in a project directory into an AST.

    Recursively traverses the project directory to find all PHP files,
    then parses them into a single AST with project and file nodes.

    Args:
        project_path: Project root directory path.
        file_filter: Function to filter files. Takes a Path and returns
            True if the file should be parsed. Defaults to .php suffix.

    Returns:
        AST instance with project -> files -> statements hierarchy.

    Raises:
        ParseError: If any file has syntax errors.
        FileNotFoundError: If project directory does not exist.
        ValueError: If project_path is not a directory.
    """
    if file_filter is None:
        file_filter = _default_file_filter
    parser = Parser()
    return parser.parse_project(project_path, file_filter=file_filter)


__version__ = "0.1.0"
__all__ = [
    "AST",
    "Edge",
    "Modifier",
    "Node",
    "Parser",
    "PrettyPrinter",
    "ParseError",
    "RunnerError",
    "NodeNotInFileError",
    "parse_code",
    "parse_file",
    "parse_project",
]
