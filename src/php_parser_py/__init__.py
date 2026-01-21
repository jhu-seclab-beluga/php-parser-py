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
from php_parser_py._node import Node
from php_parser_py._edge import Edge
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


def parse(code: str) -> AST:
    """Parse PHP code string into an AST (backward compatibility).

    This is a convenience function that creates a temporary project/file structure.
    For code-only parsing without project structure, use parse_code() instead.

    Args:
        code: PHP source code string.

    Returns:
        AST instance with project -> file -> statements hierarchy.

    Raises:
        ParseError: If PHP-Parser reports syntax error.
    """
    # Create a temporary file-like structure for backward compatibility
    import tempfile
    from pathlib import Path
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        return parse_file(temp_path)
    finally:
        Path(temp_path).unlink()


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


def parse_project(paths: list[str], project_path: str | None = None) -> AST:
    """Parse multiple PHP files into an AST.

    Creates a project node and multiple file nodes. Each file node
    contains statements from its corresponding file.

    Args:
        paths: List of file path strings.
        project_path: Optional project root path. If not provided, computed as common parent.

    Returns:
        AST instance with project -> files -> statements hierarchy.

    Raises:
        ParseError: If any file has syntax errors.
        FileNotFoundError: If any file does not exist.
    """
    parser = Parser()
    return parser.parse_project(paths, project_path=project_path)


__version__ = "0.1.0"
__all__ = [
    "AST",
    "Node",
    "Edge",
    "Parser",
    "PrettyPrinter",
    "ParseError",
    "RunnerError",
    "parse_code",
    "parse_file",
    "parse_project",
]
