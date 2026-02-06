# php-parser-py

Python wrapper for [nikic/PHP-Parser](https://github.com/nikic/PHP-Parser) built on the [cpg2py](https://github.com/jhu-seclab/cpg2py) graph framework.

- **Automated**: Uses [static-php-cli](https://github.com/static-php-cli/static-php-cli) binaries (no local PHP required).
- **Graph-Based**: AST nodes are stored in a queryable graph database.
- **Accurate**: Full support for PHP-Parser 4.19.4 AST structure.

## Quick Start
```bash
pip install php-parser-py
```

```python
from php_parser_py import parse_file, parse_project

# 1. Parse
ast = parse_file("src/User.php")
# ast = parse_project("src/")

# 2. Traverse
files = ast.file_nodes()

# Find specific nodes
functions = ast.nodes(lambda n: n.node_type == "Stmt_Function")

# Get properties (scalars)
for func in functions:
    print(f"Function: {func['namespacedName']}")

# Get child nodes (structure)
for func in functions:
    # Use helper method or traverse edges
    params = [c for c in ast.succ(func) if c.node_type == "Param"]
```

## Documentation

- **[Architecture & Design](docs/design.md)**
  Detailed design documentation covering internal architecture, class specifications, and design rationale.

- **[AST Structure Reference](docs/libs/php_parser_ast.md)**  
  Complete table of all node types, subnodes (children), and properties. Verified against PHP-Parser source.

- **[Graph Traversal Guide](docs/libs/cpg2py_traversal.md)**  
  How to navigate the graph (`succ`, `prev`), access properties, and modify the graph (`set_property`).

## Requirements
- Python ≥ 3.11
- (Optional) Custom PHP binary can be configured via `Parser` constructor.
