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

### Parse PHP Code (Without Project Structure)

```python
from php_parser_py import parse_code

# Parse PHP code into raw statement nodes
code = """<?php
function greet($name) {
    echo "Hello, $name!";
}
"""

nodes = parse_code(code)
# Returns list of Node instances (no project/file structure)

for node in nodes:
    print(f"Node type: {node.label}")
```

### Parse PHP File (With Project Structure)

```python
from php_parser_py import parse_file

# Parse a single file with project/file structure
ast = parse_file("example.php")

# Access project and file nodes
project = ast.project_node
files = ast.files()
print(f"Project has {len(files)} file(s)")

# Get file containing a specific node
stmt_node = ast.first_node(lambda n: n.label == "Stmt_Function")
file_node = ast.get_file(stmt_node.id)
print(f"Function is in file: {file_node.get_property('filePath')}")
```

### Parse Multiple Files (Project Structure)

```python
from php_parser_py import parse_project

# Parse multiple files into a single AST
ast = parse_project(["file1.php", "file2.php", "file3.php"])

# Access all files
for file_node in ast.files():
    print(f"File: {file_node.get_property('filePath')}")
    # Get statements in this file
    for stmt in ast.children(file_node):
        print(f"  Statement: {stmt.label}")

# Access project and file paths
ast = parse_project(["file1.php", "subdir/file2.php"])
project = ast.project_node
print(f"Project root: {project.get_property('path')}")

for file_node in ast.files():
    print(f"File relative path: {file_node.get_property('path')}")
    print(f"File absolute path: {file_node.get_property('filePath')}")
```

### Traverse AST

```python
from php_parser_py import parse_file

ast = parse_file("example.php")

# Find all echo statements
for echo in ast.nodes(lambda n: n.label == "Stmt_Echo"):
    print(f"Echo at line {echo.get_property('startLine')}")

# Get children of a node (via PARENT_OF edges)
for child in ast.succ(some_node):
    print(f"Child type: {child.label}")

# Get all descendants
for descendant in ast.descendants(some_node):
    print(f"Descendant: {descendant.label}")

# Get file containing a node
stmt_node = ast.first_node(lambda n: n.label == "Stmt_Function")
file_node = ast.get_file(stmt_node.id)
if file_node:
    print(f"Function is in: {file_node.get_property('filePath')}")

# Access project structure
project = ast.project_node
files = ast.files()
for file_node in files:
    print(f"File: {file_node.get_property('filePath')}")
```

### Generate PHP Code

```python
from php_parser_py import parse_file, parse_project, PrettyPrinter

# Parse single file
ast = parse_file("example.php")

# Generate code (returns dict mapping file paths to code)
printer = PrettyPrinter()
generated = printer.print(ast)
for file_path, code in generated.items():
    print(f"File: {file_path}")
    print(code)

# Parse multiple files
ast = parse_project(["file1.php", "file2.php"])

# Generate code for all files
generated = printer.print(ast)
# Returns: {"file1.php": "...", "file2.php": "..."}
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

- **`parse_code(code: str) -> list[Node]`**: Parse PHP code string into raw statement nodes (no project/file structure)
- **`parse(code: str) -> AST`**: Parse PHP code string and return AST with project/file structure (backward compatibility)
- **`parse_file(path: str) -> AST`**: Parse a single PHP file and return AST with project/file structure
- **`parse_project(paths: list[str]) -> AST`**: Parse multiple PHP files into a single AST with project structure

### Classes

- **`AST`**: Represents the complete AST as a graph
  - `node(id)`: Get node by ID
  - `nodes(predicate)`: Iterate nodes matching predicate
  - `first_node(predicate)`: Get first matching node
  - `succ(node, predicate)`: Get successor nodes (children via PARENT_OF edges)
  - `prev(node, predicate)`: Get predecessor nodes (parents via PARENT_OF edges)
  - `descendants(node, predicate)`: Get all descendants via BFS
  - `ancestors(node, predicate)`: Get all ancestors via BFS
  - `root_node`: Property returning the root/project node
  - `project_node`: Property returning the project node (alias for root_node)
  - `files()`: Get all file nodes in the project
  - `get_file(node_id)`: Get the file node containing the given node
  - `to_json()`: Reconstruct PHP-Parser JSON

- **`Node`**: Wraps a single AST node
  - `id`: Node identifier
  - `label`: Node type (e.g., "Stmt_Function")
  - `node_type`: Alias for label (PHP-Parser node type)
  - `properties`: All node properties
  - `get_property(*names)`: Get property value

- **`Parser`**: Parses PHP code
  - `__init__(php_binary_path=None, php_binary_url=None)`: Initialize parser
    - `php_binary_path`: Optional path to local PHP binary
    - `php_binary_url`: Optional URL to download PHP binary from
  - `parse_code(code)`: Parse code string into list of nodes
  - `parse(code)`: Parse code string into AST (backward compatibility)
  - `parse_file(path)`: Parse file into AST with project/file structure
  - `parse_project(paths)`: Parse multiple files into AST with project structure

- **`PrettyPrinter`**: Generates PHP code
  - `__init__(php_binary_path=None, php_binary_url=None)`: Initialize printer
    - `php_binary_path`: Optional path to local PHP binary
    - `php_binary_url`: Optional URL to download PHP binary from
  - `print(ast) -> dict[str, str]`: Generate code from AST, returns dictionary mapping file paths to generated code
    - Returns: `{file_path: code_string, ...}` for each file in the AST
    - If AST has no file structure, returns `{"": code_string}`

### Exceptions

- **`ParseError`**: Raised when PHP-Parser reports syntax error
- **`RunnerError`**: Raised when PHP execution fails

## AST Structure

The library supports three parsing modes:

1. **Code Parsing** (`parse_code`): Returns flat list of statement nodes
   - Node IDs: `node_1`, `node_2`, ...
   - No project/file structure

2. **File Parsing** (`parse_file`): Creates project → file → statements hierarchy
   - Project node: `"project"` (fixed ID)
   - File node: 8-character hex hash (e.g., `"a1b2c3d4"`)
   - Statement nodes: `{hex}_1`, `{hex}_2`, ...

3. **Project Parsing** (`parse_project`): Creates project → multiple files → statements hierarchy
   - Single project node: `"project"` (fixed ID)
   - Multiple file nodes: Each with unique hex hash
   - Statement nodes: Prefixed with their file's hash

## Architecture

The library follows a delegation-based architecture:

1. **PHP-Parser** handles all parsing and code generation
2. **cpg2py Storage** stores the AST as a graph
3. **Python classes** provide convenient access to the graph

This design ensures:
- No need to maintain PHP node type definitions in Python
- Automatic compatibility with PHP-Parser updates
- Full access to PHP-Parser's features
- Support for multi-file project analysis with merge capabilities

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
