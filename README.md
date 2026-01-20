# php-parser-py

Python wrapper for PHP-Parser using cpg2py's graph framework.

## Overview

`php-parser-py` provides a Python interface to [PHP-Parser](https://github.com/nikic/PHP-Parser), enabling Abstract Syntax Tree (AST) parsing and manipulation of PHP code. The library integrates with [cpg2py](https://github.com/jhu-seclab/cpg2py)'s graph framework for powerful graph-based code analysis.

## Features

- **Native PHP-Parser Integration**: Delegates all parsing and code generation to PHP-Parser for maximum compatibility
- **Zero-Configuration PHP**: Bundled PHP binaries via static-php-py - no system PHP installation required
- **Graph-Based Analysis**: Uses cpg2py's graph framework for AST traversal and querying
- **Dynamic Node Types**: No hardcoded PHP node types - all types come from PHP-Parser's JSON output
- **Lossless Round-Trip**: Parse → Modify → Generate code with full fidelity
- **Cross-Platform Support**: Pre-built PHP 8.4 binaries for Linux (x86_64/aarch64), macOS (x86_64/arm64), and Windows (x64)

## Installation

```bash
pip install php-parser-py
```

**Note**: Platform-specific wheels include pre-built PHP 8.4 binaries. No separate PHP installation required!

## Quick Start

### Parse PHP Code

```python
from php_parser_py import parse

# Parse PHP code
code = """<?php
function greet($name) {
    echo "Hello, $name!";
}
"""

ast = parse(code)

# Query nodes by type
for func in ast.nodes(lambda n: n.label == "Stmt_Function"):
    name = func.get_property("name")
    print(f"Found function: {name}")
```

### Parse PHP File

```python
from php_parser_py import parse_file

ast = parse_file("example.php")
```

### Traverse AST

```python
# Find all echo statements
for echo in ast.nodes(lambda n: n.label == "Stmt_Echo"):
    print(f"Echo at line {echo.get_property('startLine')}")

# Get children of a node
for child in ast.children(some_node):
    print(f"Child type: {child.label}")

# Get all descendants
for descendant in ast.descendants(some_node):
    print(f"Descendant: {descendant.label}")
```

### Generate PHP Code

```python
from php_parser_py import parse, PrettyPrinter

# Parse code
ast = parse("<?php echo 'hello';")

# Modify AST (example: change properties)
# ... modify nodes as needed ...

# Generate code
printer = PrettyPrinter()
generated_code = printer.print(ast)
print(generated_code)
```

## Advanced Usage

### Custom PHP Binary

If you need to use a specific PHP version or custom binary:

```python
from php_parser_py import Parser
from pathlib import Path

# Use local PHP binary
parser = Parser(php_binary_path=Path("/usr/local/bin/php"))
ast = parser.parse("<?php echo 'hello';")

# Or download from remote URL
parser = Parser(php_binary_url="https://example.com/php-8.4.zip")
ast = parser.parse("<?php echo 'hello';")
```

## API Reference

### Main Functions

- **`parse(code: str) -> AST`**: Parse PHP code string and return AST
- **`parse_file(path: str) -> AST`**: Parse PHP file and return AST

### Classes

- **`AST`**: Represents the complete AST as a graph
  - `node(id)`: Get node by ID
  - `nodes(predicate)`: Iterate nodes matching predicate
  - `first_node(predicate)`: Get first matching node
  - `children(node)`: Get child nodes
  - `descendants(node)`: Get all descendants
  - `to_json()`: Reconstruct PHP-Parser JSON

- **`Node`**: Wraps a single AST node
  - `id`: Node identifier
  - `label`: Node type (e.g., "Stmt_Function")
  - `properties`: All node properties
  - `get_property(*names)`: Get property value

- **`Parser`**: Parses PHP code
  - `__init__(php_binary_path=None, php_binary_url=None)`: Initialize parser
    - `php_binary_path`: Optional path to local PHP binary
    - `php_binary_url`: Optional URL to download PHP binary from
  - `parse(code, prefix="")`: Parse code string
    - `prefix`: Optional prefix for node IDs (useful for multi-file parsing)
  - `parse_file(path, prefix=None)`: Parse file
    - `prefix`: Optional prefix (auto-generated from file path if not provided)

- **`PrettyPrinter`**: Generates PHP code
  - `__init__(php_binary_path=None, php_binary_url=None)`: Initialize printer
    - `php_binary_path`: Optional path to local PHP binary
    - `php_binary_url`: Optional URL to download PHP binary from
  - `print(ast)`: Generate code from AST

### Exceptions

- **`ParseError`**: Raised when PHP-Parser reports syntax error
- **`RunnerError`**: Raised when PHP execution fails

## Architecture

The library follows a delegation-based architecture:

1. **PHP-Parser** handles all parsing and code generation
2. **cpg2py Storage** stores the AST as a graph
3. **Python classes** provide convenient access to the graph

This design ensures:
- No need to maintain PHP node type definitions in Python
- Automatic compatibility with PHP-Parser updates
- Full access to PHP-Parser's features

## Requirements

- Python >= 3.11
- cpg2py
- static-php-py (bundled PHP binaries)

## License

MIT License - see LICENSE file for details.

## Documentation

For detailed design documentation, see:
- [Design Document](docs/design.md)
- [Idea Document](docs/idea.md)
- [API Demo](docs/api_demo.ipynb)
