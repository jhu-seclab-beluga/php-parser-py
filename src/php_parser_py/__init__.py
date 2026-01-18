"""
php-parser-py: Python wrapper for PHP-Parser using cpg2py.

This package provides a Python interface to PHP-Parser, enabling AST parsing
and manipulation of PHP code.
"""

from php_parser_py._resources import ensure_php_parser_extracted

# Ensure PHP-Parser is extracted on first import
ensure_php_parser_extracted()

# Public API will be imported here once implemented
# from php_parser_py.parser import parse, parse_file
# from php_parser_py.ast import AST
# from php_parser_py.node import Node
# from php_parser_py.edge import Edge

__version__ = "0.1.0"
__all__ = []  # Will be populated as modules are implemented
