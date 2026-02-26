# cpg2py Graph API

**Source**: Verified against `cpg2py` library and `php-parser-py` implementation.

## Core Concepts

php-parser-py uses `cpg2py` for AST storage and querying.
- **Node**: A JSON object from PHP-Parser (extends `AbcNodeQuerier`).
- **Edge**: `PARENT_OF` relationship (extends `AbcEdgeQuerier`).

> [!CAUTION]
> **Do NOT use direct storage interfaces** (e.g., `ast._storage`, `storage.add_node`, `storage.set_node_prop`, `storage.add_edge`).
> Always use the high-level API methods described below. Direct storage access is an implementation detail and may change without notice.

## Querying Methods

All querying methods support **Flow Style** programming (functional predicates) and return **Generators** for lazy evaluation.

| Method | Description | Return Type |
|--------|-------------|-------------|
| `ast.nodes(pred=None)`| Iterate nodes, optionally filtering by `pred(node) -> bool` | `Generator[Node]` |
| `ast.first_node(pred)`| Find first node where `pred(node)` is True | `Node` \| `None` |
| `ast.succ(n)` | Get **children** (outgoing edges) | `Generator[Node]` |
| `ast.prev(n)` | Get **parents** (incoming edges) | `Generator[Node]` |
| `ast.node(id)` | Get single node by ID (raises `KeyError` if missing) | `Node` |

## Property Management

Use `set_property` / `set_properties` to modify node attributes. **Never** write to storage directly.

| Method | Usage | Description |
|--------|-------|-------------|
| `set_property` | `node.set_property("analyzed", True)` | Set single property |
| `set_properties` | `node.set_properties({"a": 1, "b": 2})` | Set multiple properties |
| `get_property` | `node.get_property("key", default)` | Get with fallback |

> [!IMPORTANT]
> Always use `node.set_property(key, value)` or `node.set_properties(dict)` to update node values.
> For structural changes (adding/removing nodes and edges), use the `Modifier` class:
> ```python
> from php_parser_py import Modifier
> modifier = Modifier(ast)
> new_node = modifier.add_node("new_id", "Stmt_Break")
> modifier.add_edge("parent_id", "new_id", field="stmts", index=0)
> ```

## Flow Style Patterns (Recommended)

### 1. Filtering Nodes
Use lazy generators with lambda predicates.

```python
# Find all Function nodes (lazy generator)
functions = ast.nodes(lambda n: n.node_type == "Stmt_Function")

# Find first Class node
cls = ast.first_node(lambda n: n.node_type == "Stmt_Class")
```

### 2. Finding Children (Functional)
Common pattern: Start with all children, filter down to what you need.

```python
# 1. Start with all children (Generator)
children = ast.succ(func)

# 2. Filter by Node Type (Generator)
params = (c for c in children if c.node_type == "Param")
```

### 3. Get Child by Field Name
**Critical**: Use edge fields, not node properties, for structural children.

```python
# 1. Start with all children
children = ast.succ(node)

# 2. Define Filter
is_name_field = lambda c: ast.edge(node.id, c.id, "PARENT_OF").get("field") == "name"

# 3. Filter children
name_nodes = (c for c in children if is_name_field(c))

# 4. Take the first result (or None)
child_name = next(name_nodes, None)
```

### 4. Get Indexed Children (Arrays)
For fields like `stmts`, `params`, `args`.

```python
# 1. Start with all children
children = ast.succ(node)

# 2. Define Filter
is_stmt_field = lambda c: ast.edge(node.id, c.id, "PARENT_OF").get("field") == "stmts"

# 3. Filter children
stmts_nodes = [c for c in children if is_stmt_field(c)]

# 4. Sort by edge index (edge property "index" is None when not an array element)
get_index = lambda c: (e := ast.edge(node.id, c.id, "PARENT_OF")).get("index") if e.get("index") is not None else 999
stmts = sorted(stmts_nodes, key=get_index)
```

### 5. Setting Node Values

```python
# Set a single property
node.set_property("analyzed", True)

# Set multiple properties at once
node.set_properties({"status": "complete", "confidence": 0.95})

# Read back
status = node.get_property("status", "unknown")
```

## Project Structure

| Helper | Description |
|--------|-------------|
| `ast.project_node` | Root node (ID: `project`) |
| `ast.files()` | List of all `File` nodes |
| `ast.get_file(node_id)` | Get `File` node containing specific node |
