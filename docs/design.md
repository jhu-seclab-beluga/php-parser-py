# php-parser-py Design Document

## Design Overview

**Classes**: `PHPASTNode`, `PHPASTEdge`, `PHPASTGraph`, `Parser`, `PrettyPrinter`, `PHPRunner`

**Relationships**: 
- `PHPASTNode` extends cpg2py's `AbcNodeQuerier`
- `PHPASTEdge` extends cpg2py's `AbcEdgeQuerier`
- `PHPASTGraph` extends cpg2py's `AbcGraphQuerier`
- `Parser` uses `PHPRunner` to invoke PHP-Parser parse + JsonSerializer
- `PrettyPrinter` uses `PHPRunner` to invoke PHP-Parser JsonDecoder + PrettyPrinter
- All classes use cpg2py's `Storage` for node/edge management

**Inherited from cpg2py**: `AbcNodeQuerier`, `AbcEdgeQuerier`, `AbcGraphQuerier`, `Storage`

**Exceptions**: `ParseError`, `PHPRunnerError`

**Design Principle**: Maximize delegation to PHP-Parser. No hardcoded node types. All AST operations use PHP-Parser's native JSON format.

---

## Class Specifications

### PHPASTNode Class

- **Responsibility**: Wraps a single AST node stored in cpg2py Storage, providing dynamic property access to PHP-Parser's JSON fields.

- **Inherits**: `cpg2py.AbcNodeQuerier`

- **[__init__(self, storage: Storage, nid: str) -> None]**
  - **Behavior**: Initializes node querier with storage reference and node ID
  - **Input**: cpg2py Storage instance, node ID string
  - **Raises**: Exception if node ID not found in storage

- **[@property id -> str]**
  - **Behavior**: Returns the node identifier
  - **Output**: Node ID string

- **[@property label -> str | None]**
  - **Behavior**: Returns `nodeType` from stored JSON (e.g., "Stmt_Function", "Expr_Variable")
  - **Output**: Node type string or None
  - **Note**: This is the PHP-Parser class name, not hardcoded in Python

- **[@property properties -> dict | None]**
  - **Behavior**: Returns all stored properties (the complete JSON object for this node)
  - **Output**: Dictionary of all properties

- **[get_property(*prop_names: str) -> Any | None]** (inherited)
  - **Behavior**: Returns first non-None property value from given names
  - **Input**: One or more property name strings
  - **Output**: Property value or None
  - **Note**: Use for accessing any JSON field dynamically

- **Example Usage**:
```python
# Dynamic property access - no hardcoded field names
node = graph.first_node(lambda n: n.label == "Stmt_Function")
name_prop = node.get_property("name")  # Returns Identifier node or dict
line = node.get_property("startLine", "lineno")  # Try multiple names
```

---

### PHPASTEdge Class

- **Responsibility**: Represents an edge between AST nodes, extending cpg2py's `AbcEdgeQuerier`.

- **Inherits**: `cpg2py.AbcEdgeQuerier`

- **Properties** (inherited):
  - `edge_id: tuple[str, str, str]` - (from_id, to_id, edge_type)
  - `from_nid: str` - Source node ID
  - `to_nid: str` - Target node ID

- **[@property type -> str]**
  - **Behavior**: Returns edge type (e.g., "PARENT_OF")
  - **Output**: Edge type string

- **[@property index -> int | None]**
  - **Behavior**: Returns array index for ordered child relationships
  - **Output**: Integer index or None

---

### PHPASTGraph Class

- **Responsibility**: Represents the complete AST as a graph, storing PHP-Parser's JSON structure in cpg2py Storage.

- **Inherits**: `cpg2py.AbcGraphQuerier`

- **[__init__(self, storage: Storage, root_node_id: str = "node_0") -> None]**
  - **Behavior**: Initializes graph with populated storage and root node ID
  - **Input**: cpg2py Storage containing AST nodes and edges, optional root node ID
  - **Note**: For project structures, root_node_id is typically `"project"`

- **[node(whose_id_is: str) -> PHPASTNode | None]** (implements abstract)
  - **Behavior**: Returns node wrapper by ID
  - **Input**: Node ID string
  - **Output**: PHPASTNode instance or None

- **[edge(fid: str, tid: str, eid: str) -> PHPASTEdge | None]** (implements abstract)
  - **Behavior**: Returns edge wrapper by ID tuple
  - **Input**: From ID, To ID, Edge type
  - **Output**: PHPASTEdge instance or None


- **[project_node() -> PHPASTNode | None]**
  - **Behavior**: Alias for root_node, returns project node
  - **Output**: Project Node instance or None

- **[file_nodes() -> list[PHPASTNode]]**
  - **Behavior**: Returns all file nodes in the project
  - **Output**: List of File Node instances, sorted by file path
  - **Note**: Only works for ASTs with project structure (created via parse_file or parse_project)

- **[get_file(node_id: str) -> PHPASTNode | None]**
  - **Behavior**: Gets the file node containing the given node by traversing upward via PARENT_OF edges
  - **Input**: Node ID string
  - **Output**: File Node instance containing the node, or None if:
    - Node ID doesn't exist
    - Node is the project node (project doesn't belong to a file)
    - Node is not under any file node
  - **Note**: If the node itself is a File node, returns it

- **[to_json() -> str]**
  - **Behavior**: Reconstructs PHP-Parser JSON from Storage for code generation
  - **Output**: JSON string compatible with PHP-Parser's JsonDecoder
  - **Note**: Traverses PARENT_OF edges to rebuild nested structure, excludes virtual project/file nodes for PrettyPrinter compatibility

- **Inherited Traversal Methods** (from AbcGraphQuerier):
  - `nodes(predicate)` → iterate all nodes matching condition
  - `first_node(predicate)` → get first matching node
  - `edges(predicate)` → iterate all edges matching condition
  - `succ(node, predicate)` → successor nodes (children via PARENT_OF edges)
  - `prev(node, predicate)` → predecessor nodes (parents via PARENT_OF edges)
  - `descendants(node, predicate)` → all descendants via BFS
  - `ancestors(node, predicate)` → all ancestors via BFS

- **Example Usage**:
```python
# Query by node type (from PHP-Parser JSON, not hardcoded)
for func in graph.nodes(lambda n: n.label == "Stmt_Function"):
    print(func.get_property("name"))

# Traverse children
for child in graph.children(some_node):
    print(child.label)

# Reconstruct JSON for printing
json_str = graph.to_json()
```

---

### Parser Class

- **Responsibility**: Parses PHP source code by invoking PHP-Parser, returning AST or list of nodes.

- **Properties**:
  - `_runner: PHPRunner` - PHP binary execution handler

- **[__init__(self, php: PHP | None = None) -> None]**
  - **Behavior**: Initializes parser with Runner
  - **Input**: Optional `static_php_py.PHP` instance
  - **Note**: If `php` is not provided, defaults to `PHP.builtin()`

- **[parse(code: str) -> AST]**
  - **Behavior**: Parses PHP code via PHP-Parser, creates temporary file structure for backward compatibility
  - **Input**: PHP source code string
  - **Output**: AST instance with project -> file -> statements hierarchy
  - **Raises**: `ParseError` if PHP-Parser reports syntax error
  - **Note**: For code-only parsing without project structure, use `parse_code()` instead

- **[parse_code(code: str) -> list[Node]]**
  - **Behavior**: Parses PHP code string into raw statement nodes without project/file structure
  - **Input**: PHP source code string
  - **Output**: List of Node instances representing top-level statements
  - **Raises**: `ParseError` if PHP-Parser reports syntax error
  - **Node IDs**: Simple `node_1`, `node_2`, ... format (no prefix)

- **[parse_file(path: str) -> AST]**
  - **Behavior**: Parses a single PHP file, creates project and file nodes
  - **Input**: File path string
  - **Output**: AST instance with project -> file -> statements hierarchy
  - **Raises**: `ParseError`, `FileNotFoundError`
  - **Structure**: 
    - Project node (ID: `"project"`, fixed)
      - `path` property: File's directory (project root)
    - File node (ID: 8-character hex hash of file path)
      - `path` property: Relative path from project root (filename)
      - `filePath` property: Absolute file path
    - Statement nodes (IDs: `{hex}_1`, `{hex}_2`, ...)

- **[parse_project(project_path: str, file_filter: Callable[[Path], bool] = lambda p: p.suffix == '.php') -> AST]**
  - **Behavior**: Recursively traverses project directory to find all PHP files, then parses them into a single AST with project structure
  - **Input**: 
    - `project_path`: Project root directory path string
    - `file_filter`: Function to filter files. Takes a `Path` and returns `True` if the file should be parsed. Defaults to `lambda p: p.suffix == '.php'`
  - **Output**: AST instance with project -> multiple files -> statements hierarchy
  - **Raises**: `ParseError` if any file has syntax errors, `FileNotFoundError` if project directory does not exist, `ValueError` if project_path is not a directory
  - **File Discovery**: 
    - Recursively finds all files using `Path.rglob("*")`
    - Filters files using `file_filter` function (default: `lambda p: p.suffix == '.php'`)
    - Only processes files that pass the filter and are regular files
  - **Structure**: 
    - Single project node (ID: `"project"`, fixed)
      - `path` property: Project root directory (absolute path)
    - Multiple file nodes (each with unique hex hash ID)
      - `path` property: Relative path from project root
      - `filePath` property: Absolute file path
    - Statement nodes within each file (prefixed with file hash)

- **[_json_to_storage(json_data: list | dict) -> Storage]** (internal)
  - **Behavior**: Converts PHP-Parser JSON to cpg2py Storage
  - **Input**: Parsed JSON data (list of statements or single node)
  - **Output**: Populated Storage instance
  - **Algorithm**:
    1. Generate unique ID for each node object with `nodeType`
    2. Store all JSON fields as node properties
    3. Create PARENT_OF edges for nested nodes
    4. Store array index in edge properties for ordered children

---

### PrettyPrinter Class

- **Responsibility**: Converts AST to PHP code by invoking PHP-Parser's PrettyPrinter for each file.

- **Properties**:
  - `_runner: PHPRunner` - PHP binary execution handler

- **[__init__(self, php: PHP | None = None) -> None]**
  - **Behavior**: Initializes PrettyPrinter with Runner
  - **Input**: Optional `static_php_py.PHP` instance
  - **Note**: If `php` is not provided, defaults to `PHP.builtin()`

- **[print(ast: AST) -> dict[str, str]]**
  - **Behavior**: Reconstructs JSON from AST for each file, invokes PHP-Parser to generate code
  - **Input**: AST instance (may contain multiple files)
  - **Output**: Dictionary mapping file paths to PHP source code strings
    - Keys: File paths (from file node's `filePath` property) or file hash if path unavailable
    - Values: Generated PHP source code for that file
    - If AST has no file structure, returns single entry with key `""` (empty string)
  - **Raises**: `PHPRunnerError` if PHP-Parser fails
  - **Note**: Each file is processed separately, allowing independent code generation
  - **PHP Script Used**:
    ```php
    <?php
    require 'vendor/autoload.php';
    use PhpParser\JsonDecoder;
    use PhpParser\PrettyPrinter;
    
    $json = file_get_contents('php://stdin');
    $decoder = new JsonDecoder();
    $stmts = $decoder->decode($json);
    $printer = new PrettyPrinter\Standard();
    echo $printer->prettyPrintFile($stmts);
    ```

---

### PHPRunner Class

- **Responsibility**: Manages PHP-Parser invocation via static-php-py.

- **Properties**:
- **Properties**:
  - `_php: PHP` - PHP binary wrapper

- **[__init__(self, php: PHP | None = None) -> None]**
  - **Behavior**: Initializes Runner with PHP binary wrapper
  - **Input**: Optional `static_php_py.PHP` instance
  - **Note**: If `php` is not provided, defaults to `PHP.builtin()`

- **[execute(script: str, stdin: str) -> str]**
  - **Behavior**: Executes PHP script with stdin input, returns stdout
  - **Input**: PHP script content, stdin data
  - **Output**: stdout content
  - **Raises**: `PHPRunnerError` if non-zero exit code

- **[parse(code: str) -> dict]**
  - **Behavior**: Invokes PHP-Parser parse + JsonSerializer
  - **Input**: PHP source code
  - **Output**: Parsed JSON as dict
  - **Raises**: `ParseError` if syntax error (extracted from PHP-Parser output)

- **[print(ast_json: str) -> str]**
  - **Behavior**: Invokes PHP-Parser JsonDecoder + PrettyPrinter
  - **Input**: AST JSON string
  - **Output**: PHP source code
  - **Raises**: `PHPRunnerError` if fails

---

## Module-Level Functions

**[parse_code(code: str) -> list[Node]]**
- **Responsibility**: Parse PHP code string into raw statement nodes without project/file structure
- **Example**:
```python
from php_parser_py import parse_code
nodes = parse_code("<?php function foo() {}")
# Returns list of Node instances
```

**[parse(code: str) -> AST]**
- **Responsibility**: Convenience function to parse PHP code (backward compatibility)
- **Note**: Creates temporary file structure, use `parse_code()` for code-only parsing
- **Example**:
```python
from php_parser_py import parse
ast = parse("<?php echo 'hello';")
```

**[parse_file(path: str) -> AST]**
- **Responsibility**: Convenience function to parse a single PHP file with project structure
- **Example**:
```python
from php_parser_py import parse_file
ast = parse_file("example.php")
files = ast.file_nodes()
```

**[parse_project(project_path: str, file_filter: Callable[[Path], bool] = lambda p: p.suffix == '.php') -> AST]**
- **Responsibility**: Convenience function to parse all PHP files in a project directory into a single AST
- **Example**:
```python
from php_parser_py import parse_project
from pathlib import Path

# Default: only .php files
ast = parse_project("/path/to/project")
files = ast.file_nodes()  # Returns all file nodes found recursively

# Custom filter: include .php and .phtml files
ast = parse_project(
    "/path/to/project",
    file_filter=lambda p: p.suffix in ['.php', '.phtml']
)
```

---

## AST Structure

The library supports three parsing modes with different AST structures:

### 1. Code Parsing (`parse_code`)
- **Structure**: Flat list of statement nodes
- **Node IDs**: `node_1`, `node_2`, `node_3`, ...
- **Use Case**: Code analysis without file/project context

### 2. File Parsing (`parse_file`)
- **Structure**: Project → File → Statements
- **Node IDs**:
  - Project: `"project"` (fixed)
  - File: 8-character hex hash (e.g., `"a1b2c3d4"`)
  - Statements: `{hex}_1`, `{hex}_2`, `{hex}_3`, ...
- **Use Case**: Single file analysis with file context

### 3. Project Parsing (`parse_project`)
- **Structure**: Project → Multiple Files → Statements
- **Node IDs**:
  - Project: `"project"` (fixed)
  - Files: Unique 8-character hex hash per file
  - Statements: `{hex}_1`, `{hex}_2`, ... (prefixed with file hash)
- **Use Case**: Multi-file project analysis

## JSON-to-Storage Mapping

PHP-Parser's JSON structure is mapped to cpg2py Storage mechanically:

**Input JSON Example**:
```json
[{
  "nodeType": "Stmt_Function",
  "attributes": { "startLine": 1, "endLine": 3 },
  "name": { "nodeType": "Identifier", "name": "foo", "attributes": {} },
  "params": [],
  "stmts": [
    { "nodeType": "Stmt_Return", "expr": null, "attributes": { "startLine": 2 } }
  ],
  "returnType": null
}]
```

**Storage Mapping** (for `parse_code`):

| Node ID | Properties |
|---------|------------|
| `node_1` | `{nodeType: "Stmt_Function", startLine: 1, endLine: 3, ...}` |
| `node_2` | `{nodeType: "Identifier", name: "foo"}` |
| `node_3` | `{nodeType: "Stmt_Return", startLine: 2}` |

**Storage Mapping** (for `parse_file`):

| Node ID | Properties |
|---------|------------|
| `project` | `{nodeType: "Project", label: "Project"}` |
| `a1b2c3d4` | `{nodeType: "File", label: "File", filePath: "/path/to/file.php"}` |
| `a1b2c3d4_1` | `{nodeType: "Stmt_Function", startLine: 1, ...}` |
| `a1b2c3d4_2` | `{nodeType: "Identifier", name: "foo"}` |

| Edge (from, to, type) | Properties |
|-----------------------|------------|
| `(project, a1b2c3d4, PARENT_OF)` | `{field: "files"}` |
| `(a1b2c3d4, a1b2c3d4_1, PARENT_OF)` | `{field: "stmts", index: 0}` |
| `(a1b2c3d4_1, a1b2c3d4_2, PARENT_OF)` | `{field: "name"}` |

**Mapping Rules**:
1. Each object with `nodeType` → new node with unique ID
2. `nodeType` value → `label` property (alias)
3. `attributes` fields → flattened to node properties
4. Scalar fields (`name: "foo"`) → direct properties
5. Object fields (nested node) → PARENT_OF edge + field name in edge properties
6. Array fields → PARENT_OF edges with `index` property for ordering
7. Null fields → not stored (or stored as explicit null)
8. Project/File nodes are virtual nodes not present in PHP-Parser JSON

---

## Storage-to-JSON Reconstruction

For code generation, Storage is converted back to PHP-Parser's exact JSON format:

**Algorithm**:
1. Find root nodes (no incoming PARENT_OF edges)
2. For each node, reconstruct JSON object:
   - Set `nodeType` from `label` property
   - Reconstruct `attributes` dict from line/column properties
   - For each outgoing PARENT_OF edge:
     - Get field name from edge `field` property
     - If edge has `index`, collect into array at that index
     - Recursively reconstruct child node
3. Return array of root nodes (for statement lists)

**Output Fidelity**: The reconstructed JSON is structurally identical to the original PHP-Parser output, enabling lossless round-trip.

---

## Exception Classes

**ParseError**: Raised when PHP-Parser reports syntax error.
- Properties: `message: str`, `line: int | None`
- Source: Extracted from PHP-Parser's error output

**PHPRunnerError**: Raised when PHP process execution fails.
- Properties: `message: str`, `stderr: str`, `exit_code: int`

---

## Module Structure

```
php_parser_py/
├── __init__.py              # Public API: parse, parse_file
├── graph.py                 # PHPASTGraph (extends AbcGraphQuerier)
├── node.py                  # PHPASTNode (extends AbcNodeQuerier)
├── edge.py                  # PHPASTEdge (extends AbcEdgeQuerier)
├── parser.py                # Parser class with JSON-to-Storage mapping
├── printer.py               # PrettyPrinter class with Storage-to-JSON
├── runner.py                # PHPRunner class for PHP-Parser invocation
├── exceptions.py            # ParseError, PHPRunnerError
└── scripts/
    ├── parse.php            # PHP script for parsing
    └── print.php            # PHP script for code generation
```

---

## PHP Scripts

### parse.php

```php
<?php
// Bundled with PHP-Parser PHAR
require_once __DIR__ . '/php-parser.phar';

use PhpParser\ParserFactory;
use PhpParser\JsonSerializer;
use PhpParser\ErrorHandler\Collecting;

$code = file_get_contents('php://stdin');
$errorHandler = new Collecting();
$parser = (new ParserFactory())->createForNewestSupportedVersion();

try {
    $stmts = $parser->parse($code, $errorHandler);
    if ($errorHandler->hasErrors()) {
        $errors = array_map(fn($e) => [
            'message' => $e->getMessage(),
            'line' => $e->getStartLine()
        ], $errorHandler->getErrors());
        echo json_encode(['errors' => $errors]);
        exit(1);
    }
    $serializer = new JsonSerializer();
    echo $serializer->serialize($stmts);
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
    exit(1);
}
```

### print.php

```php
<?php
require_once __DIR__ . '/php-parser.phar';

use PhpParser\JsonDecoder;
use PhpParser\PrettyPrinter;

$json = file_get_contents('php://stdin');

try {
    $decoder = new JsonDecoder();
    $stmts = $decoder->decode($json);
    $printer = new PrettyPrinter\Standard();
    echo $printer->prettyPrintFile($stmts);
} catch (Exception $e) {
    fwrite(STDERR, $e->getMessage());
    exit(1);
}
```

---

## Design Rationale

**Why Delegate to PHP-Parser?**
- Eliminates need to maintain node type definitions in Python
- Automatic compatibility with PHP-Parser updates
- Leverages PHP-Parser's battle-tested parsing and printing
- Reduces codebase size and maintenance burden

**Why Store Complete JSON?**
- Enables lossless round-trip (parse → modify → print)
- No information loss from schema interpretation
- Future-proof for new PHP-Parser features

**Why cpg2py Storage?**
- Provides graph traversal infrastructure
- Enables integration with multi-language analysis pipelines
- Familiar API for cpg2py users
