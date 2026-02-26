# php-parser-py

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/jhu-seclab-beluga/php-parser-py)

Python wrapper for [nikic/PHP-Parser](https://github.com/nikic/PHP-Parser) built on the [cpg2py](https://github.com/samhsu-dev/cpg2py) graph framework.

- **Automated**: Uses [static-php-py](https://github.com/jhu-seclab-beluga/static-php-py) binaries (no local PHP required).
- **Graph-Based**: AST nodes are stored in a queryable graph database.
- **Accurate**: Full support for PHP-Parser 4.19.4 AST structure.

## Quick Start
```bash
pip install php-parser-py
```

```python
from php_parser_py import parse_file, Modifier

# 1. Parse
ast = parse_file("src/User.php")

# 2. Query
functions = ast.nodes(lambda n: n.node_type == "Stmt_Function")
for func in functions:
    print(f"Function: {func['namespacedName']}")
    params = [c for c in ast.succ(func) if c.node_type == "Param"]

# 3. Modify properties
func.set_property("analyzed", True)

# 4. Modify structure
modifier = Modifier(ast)
modifier.add_node("new_1", "Stmt_Break")
modifier.add_edge("parent_id", "new_1", field="stmts", index=0)
modifier.remove_node("obsolete_node_id")
```

## Documentation

- **[Architecture & Design](docs/design.md)**
  Internal architecture, class specifications, and design rationale.

- **[AST Structure Reference](docs/libs/php_parser_ast.md)**  
  Complete table of all node types, subnodes (children), and properties.

- **[cpg2py Graph API](docs/libs/cpg2py.md)**  
  Querying (`nodes`, `succ`, `prev`)

## Requirements
- Python ≥ 3.11
- (Optional) Custom PHP binary can be configured via `Parser` constructor.
