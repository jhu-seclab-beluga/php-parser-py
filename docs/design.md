# php-parser-py Design Document

## Design Overview

**Classes**: `Node`, `Edge`, `AST`, `Parser`, `PrettyPrinter`, `Runner`

**Relationships**: 
- `Node` extends cpg2py's `AbcNodeQuerier`
- `Edge` extends cpg2py's `AbcEdgeQuerier`
- `AST` extends cpg2py's `AbcGraphQuerier`
- `Parser` uses `Runner` to invoke PHP-Parser parse + JsonSerializer
- `PrettyPrinter` uses `Runner` to invoke PHP-Parser JsonDecoder + PrettyPrinter
- All classes use cpg2py's `Storage` for node/edge management

**Inherited from cpg2py**: `AbcNodeQuerier`, `AbcEdgeQuerier`, `AbcGraphQuerier`, `Storage`

**Exceptions**: `ParseError`, `RunnerError`

**Design Principle**: Maximize delegation to PHP-Parser. No hardcoded node types. All AST operations use PHP-Parser's native JSON format.

---

## Class Specifications

### Node Class

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

### Edge Class

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

### AST Class

- **Responsibility**: Represents the complete AST as a graph, storing PHP-Parser's JSON structure in cpg2py Storage.

- **Inherits**: `cpg2py.AbcGraphQuerier`

- **[__init__(self, storage: Storage) -> None]**
  - **Behavior**: Initializes graph with populated storage
  - **Input**: cpg2py Storage containing AST nodes and edges

- **[node(whose_id_is: str) -> Node | None]** (implements abstract)
  - **Behavior**: Returns node wrapper by ID
  - **Input**: Node ID string
  - **Output**: Node instance or None

- **[edge(fid: str, tid: str, eid: str) -> Edge | None]** (implements abstract)
  - **Behavior**: Returns edge wrapper by ID tuple
  - **Input**: From ID, To ID, Edge type
  - **Output**: Edge instance or None

- **[to_json() -> str]**
  - **Behavior**: Reconstructs PHP-Parser JSON from Storage for code generation
  - **Output**: JSON string compatible with PHP-Parser's JsonDecoder
  - **Note**: Traverses PARENT_OF edges to rebuild nested structure

- **Inherited Traversal Methods** (from AbcGraphQuerier):
  - `nodes(predicate)` → iterate all nodes matching condition
  - `first_node(predicate)` → get first matching node
  - `edges(predicate)` → iterate all edges matching condition
  - `succ(node, predicate)` → successor nodes
  - `prev(node, predicate)` → predecessor nodes
  - `children(node, predicate)` → child nodes via PARENT_OF
  - `parent(node, predicate)` → parent nodes via PARENT_OF
  - `descendants(node, predicate)` → all descendants via BFS
  - `ancestors(node, predicate)` → all ancestors via BFS

- **Example Usage**:
```python
# Query by node type (from PHP-Parser JSON, not hardcoded)
for func in ast.nodes(lambda n: n.label == "Stmt_Function"):
    print(func.get_property("name"))

# Traverse children
for child in ast.children(some_node):
    print(child.label)

# Reconstruct JSON for printing
json_str = ast.to_json()
```

---

### Parser Class

- **Responsibility**: Parses PHP source code by invoking PHP-Parser, returning AST.

- **Properties**:
  - `_runner: Runner` - PHP binary execution handler
  - `_node_counter: int` - Counter for generating unique node IDs
  - `_node_id_prefix: str` - Optional prefix for node IDs

- **[__init__(self, php_binary_path: Optional[Path] = None, php_binary_url: Optional[str] = None) -> None]**
  - **Behavior**: Initializes Parser with Runner and optional PHP binary configuration
  - **Input**: 
    - `php_binary_path`: Optional path to local PHP binary
    - `php_binary_url`: Optional URL to download PHP binary from
  - **Note**: If no PHP binary is specified, uses bundled PHP from static-php-py

- **[parse(code: str, prefix: str = "") -> AST]**
  - **Behavior**: Parses PHP code via PHP-Parser, populates cpg2py Storage from JSON
  - **Input**: 
    - `code`: PHP source code string
    - `prefix`: Optional prefix for node IDs (useful for multi-file parsing)
  - **Output**: AST instance
  - **Raises**: `ParseError` if PHP-Parser reports syntax error
  - **PHP Script Used**:
    ```php
    <?php
    require 'vendor/autoload.php';
    use PhpParser\ParserFactory;
    use PhpParser\JsonSerializer;
    
    $code = file_get_contents('php://stdin');
    $parser = (new ParserFactory())->createForNewestSupportedVersion();
    $stmts = $parser->parse($code);
    $serializer = new JsonSerializer();
    echo $serializer->serialize($stmts);
    ```

- **[parse_file(path: str, node_id_prefix: str | None = None) -> AST]**
  - **Behavior**: Reads file and parses content with optional node ID prefix
  - **Input**: File path string, optional node ID prefix (defaults to hash of file path)
  - **Output**: AST instance
  - **Raises**: `ParseError`, `FileNotFoundError`

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

- **Responsibility**: Converts AST to PHP code by invoking PHP-Parser's PrettyPrinter.

- **Properties**:
  - `_runner: Runner` - PHP binary execution handler

- **[__init__(self, php_binary_path: Optional[Path] = None, php_binary_url: Optional[str] = None) -> None]**
  - **Behavior**: Initializes PrettyPrinter with Runner and optional PHP binary configuration
  - **Input**:
    - `php_binary_path`: Optional path to local PHP binary
    - `php_binary_url`: Optional URL to download PHP binary from
  - **Note**: If no PHP binary is specified, uses bundled PHP from static-php-py

- **[print(ast: AST) -> str]**
  - **Behavior**: Reconstructs JSON from AST, invokes PHP-Parser to generate code
  - **Input**: AST instance
  - **Output**: PHP source code string
  - **Raises**: `RunnerError` if PHP-Parser fails
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

### Runner Class

- **Responsibility**: Manages PHP-Parser invocation via static-php-py.

- **Properties**:
  - `_php_binary: Path` - Path to PHP binary (from static-php-py or custom)
  - `_vendor_dir: Path` - Path to directory containing extracted PHP-Parser PHAR

- **[__init__(self, php_binary_path: Optional[Path] = None, php_binary_url: Optional[str] = None) -> None]**
  - **Behavior**: Initializes Runner with PHP binary from static-php-py or custom source
  - **Input**:
    - `php_binary_path`: Optional path to local PHP binary
    - `php_binary_url`: Optional URL to download PHP binary from
  - **Priority**: custom path > custom URL > built-in binary from static-php-py
  - **Raises**: `RunnerError` if PHP binary cannot be obtained

- **[execute(script: str, stdin: str) -> str]**
  - **Behavior**: Executes PHP script with stdin input, returns stdout
  - **Input**: PHP script content, stdin data
  - **Output**: stdout content
  - **Raises**: `RunnerError` if non-zero exit code

- **[parse(code: str) -> dict]**
  - **Behavior**: Invokes PHP-Parser parse + JsonSerializer
  - **Input**: PHP source code
  - **Output**: Parsed JSON as dict
  - **Raises**: `ParseError` if syntax error (extracted from PHP-Parser output)

- **[_build_parse_script(self) -> str]** (internal)
  - **Behavior**: Generates inline PHP script for parsing
  - **Output**: PHP script string for execution via `php -r`
  - **Note**: Script uses PHP-Parser's ParserFactory and JsonSerializer

- **[_build_print_script(self) -> str]** (internal)
  - **Behavior**: Generates inline PHP script for code generation
  - **Output**: PHP script string for execution via `php -r`
  - **Note**: Script uses PHP-Parser's JsonDecoder and PrettyPrinter

---

## Resource Management

### Runtime Extraction

PHP-Parser is distributed as a compressed zip file (`resources/php-parser-4.19.4.zip`) and automatically extracted on first import:

1. **Package Installation**: When users run `pip install php-parser-py`, the wheel includes the compressed PHP-Parser zip file
2. **First Import**: On `import php_parser_py`, the package checks if PHP-Parser has been extracted
3. **Extraction**: If not found, extracts `php-parser.phar` to `php_parser_py/vendor/` directory
4. **Caching**: Creates `.extracted` marker file with zip hash to prevent re-extraction
5. **Subsequent Imports**: Fast path checks marker file and skips extraction

### _resources Module

- **[ensure_php_parser_extracted() -> Path]**
  - **Behavior**: Ensures PHP-Parser is extracted and ready to use
  - **Thread-safe**: Uses threading lock to prevent concurrent extraction
  - **Hash verification**: Compares zip file hash with marker to detect updates
  - **Output**: Path to vendor directory containing PHP-Parser
  - **Raises**: `FileNotFoundError` if zip not found, `RuntimeError` if extraction fails

- **[get_php_parser_path() -> Path | None]**
  - **Behavior**: Returns path to extracted PHP-Parser directory
  - **Output**: Path to PHP-Parser or None if not extracted

---

## Module-Level Functions

**[parse(code: str) -> AST]**
- **Responsibility**: Convenience function to parse PHP code
- **Example**:
```python
from php_parser_py import parse
ast = parse("<?php echo 'hello';")
```

**[parse_file(path: str) -> AST]**
- **Responsibility**: Convenience function to parse PHP file

---

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

**Storage Mapping**:

| Node ID | Properties |
|---------|------------|
| `node_0` | `{nodeType: "Stmt_Function", startLine: 1, endLine: 3, ...}` |
| `node_1` | `{nodeType: "Identifier", name: "foo"}` |
| `node_2` | `{nodeType: "Stmt_Return", startLine: 2}` |

| Edge (from, to, type) | Properties |
|-----------------------|------------|
| `(node_0, node_1, PARENT_OF)` | `{field: "name"}` |
| `(node_0, node_2, PARENT_OF)` | `{field: "stmts", index: 0}` |

**Mapping Rules**:
1. Each object with `nodeType` → new node with unique ID
2. `nodeType` value → `label` property (alias)
3. `attributes` fields → flattened to node properties
4. Scalar fields (`name: "foo"`) → direct properties
5. Object fields (nested node) → PARENT_OF edge + field name in edge properties
6. Array fields → PARENT_OF edges with `index` property for ordering
7. Null fields → not stored (or stored as explicit null)

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

**RunnerError**: Raised when PHP process execution fails.
- Properties: `message: str`, `stderr: str`, `exit_code: int`

---

## Module Structure

```
php_parser_py/
├── src/
│   └── php_parser_py/
│       ├── __init__.py          # Public API: parse, parse_file
│       ├── _resources.py        # Resource extraction and management
│       ├── _ast.py              # AST (extends AbcGraphQuerier)
│       ├── _node.py             # Node (extends AbcNodeQuerier)
│       ├── _edge.py             # Edge (extends AbcEdgeQuerier)
│       ├── _parser.py           # Parser class with JSON-to-Storage mapping
│       ├── _printer.py          # PrettyPrinter class with Storage-to-JSON
│       ├── _runner.py           # Runner class for PHP-Parser invocation
│       ├── exceptions.py        # ParseError, RunnerError
│       ├── resources/
│       │   └── php-parser-4.19.4.zip  # Bundled PHP-Parser (extracted at runtime)
│       └── vendor/              # Created at runtime (gitignored)
│           ├── .extracted       # Marker file with zip hash
│           ├── php-parser.phar  # Extracted PHP-Parser PHAR
│           └── LICENSE.txt      # PHP-Parser license
├── docs/
│   ├── design.md
│   └── idea.md
└── pyproject.toml
```

---

## Inline PHP Scripts

PHP scripts are generated inline by Runner methods and executed via `php -r`:

### Parse Script (generated by _build_parse_script)

```php
error_reporting(E_ALL & ~E_DEPRECATED);
require_once 'phar://{phar_path}/vendor/autoload.php';

use PhpParser\ParserFactory;
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
    // PHP-Parser nodes implement JsonSerializable
    echo json_encode($stmts);
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
    exit(1);
}
```

### Print Script (generated by _build_print_script)

```php
error_reporting(E_ALL & ~E_DEPRECATED);
require_once 'phar://{phar_path}/vendor/autoload.php';

use PhpParser\JsonDecoder;
use PhpParser\PrettyPrinter\Standard;

$json = file_get_contents('php://stdin');

try {
    $decoder = new JsonDecoder();
    $stmts = $decoder->decode($json);
    $printer = new Standard();
    echo $printer->prettyPrintFile($stmts);
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
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

**Why static-php-py?**
- Zero-configuration installation - no system PHP required
- Cross-platform support with pre-built binaries
- Flexible - supports custom PHP binaries when needed
- Self-contained distribution
