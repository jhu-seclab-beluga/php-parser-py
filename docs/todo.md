# php-parser-py TODO

This document tracks the implementation tasks for the php-parser-py project according to the [design specification](design.md).

## Phase 1: Core Infrastructure

### Exception Classes
- [ ] Create `src/php_parser_py/exceptions.py`
  - [ ] Implement `ParseError` exception
    - [ ] Add `message: str` property
    - [ ] Add `line: int | None` property
  - [ ] Implement `RunnerError` exception
    - [ ] Add `message: str` property
    - [ ] Add `stderr: str` property
    - [ ] Add `exit_code: int` property

### Node and Edge Classes
- [ ] Create `src/php_parser_py/node.py`
  - [ ] Implement `Node` class extending `cpg2py.AbcNodeQuerier`
    - [ ] Implement `__init__(storage, nid)` method
    - [ ] Implement `id` property
    - [ ] Implement `label` property (returns `nodeType`)
    - [ ] Implement `properties` property
    - [ ] Inherit `get_property(*prop_names)` from parent

- [ ] Create `src/php_parser_py/edge.py`
  - [ ] Implement `Edge` class extending `cpg2py.AbcEdgeQuerier`
    - [ ] Implement `type` property
    - [ ] Implement `index` property for array ordering

### AST Graph Class
- [ ] Create `src/php_parser_py/ast.py`
  - [ ] Implement `AST` class extending `cpg2py.AbcGraphQuerier`
    - [ ] Implement `__init__(storage)` method
    - [ ] Implement `node(whose_id_is)` method
    - [ ] Implement `edge(fid, tid, eid)` method
    - [ ] Implement `to_json()` method for Storage-to-JSON reconstruction
      - [ ] Find root nodes (no incoming PARENT_OF edges)
      - [ ] Recursively reconstruct nested JSON structure
      - [ ] Preserve array ordering using edge index property
      - [ ] Reconstruct `attributes` dict from node properties

## Phase 2: PHP-Parser Integration

### Runner Class
- [ ] Create `src/php_parser_py/runner.py`
  - [ ] Implement `Runner` class
    - [ ] Add `_php_binary: Path` property (from static-php-py)
    - [ ] Add `_phar_path: Path` property
    - [ ] Implement `__init__()` method
      - [ ] Initialize PHP binary path from static-php-py
      - [ ] Initialize PHP-Parser PHAR path from resources
    - [ ] Implement `execute(script, stdin)` method
      - [ ] Execute PHP script with subprocess
      - [ ] Capture stdout/stderr
      - [ ] Raise `RunnerError` on non-zero exit
    - [ ] Implement `parse(code)` method
      - [ ] Invoke parse.php script
      - [ ] Parse JSON output
      - [ ] Extract and raise `ParseError` if syntax errors
    - [ ] Implement `print(ast_json)` method
      - [ ] Invoke print.php script
      - [ ] Return generated PHP code

### Parser Class
- [ ] Create `src/php_parser_py/parser.py`
  - [ ] Implement `Parser` class
    - [ ] Add `_runner: Runner` property
    - [ ] Implement `__init__()` method
    - [ ] Implement `parse(code)` method
      - [ ] Call `_runner.parse(code)`
      - [ ] Convert JSON to Storage via `_json_to_storage()`
      - [ ] Return `AST` instance
    - [ ] Implement `parse_file(path)` method
      - [ ] Read file content
      - [ ] Call `parse(code)`
    - [ ] Implement `_json_to_storage(json_data)` internal method
      - [ ] Generate unique IDs for each node with `nodeType`
      - [ ] Store all JSON fields as node properties
      - [ ] Flatten `attributes` to node properties
      - [ ] Create PARENT_OF edges for nested nodes
      - [ ] Store field names in edge properties
      - [ ] Store array indices in edge properties for ordering

### PrettyPrinter Class
- [ ] Create `src/php_parser_py/printer.py`
  - [ ] Implement `PrettyPrinter` class
    - [ ] Add `_runner: Runner` property
    - [ ] Implement `__init__()` method
    - [ ] Implement `print(ast)` method
      - [ ] Call `ast.to_json()` to reconstruct JSON
      - [ ] Call `_runner.print(json_str)`
      - [ ] Return generated PHP code

## Phase 3: PHP Scripts

### Parse Script
- [ ] Create `src/php_parser_py/scripts/parse.php`
  - [ ] Require PHP-Parser PHAR
  - [ ] Read code from stdin
  - [ ] Create ParserFactory for newest PHP version
  - [ ] Use Collecting error handler
  - [ ] Parse code and handle errors
  - [ ] Serialize AST to JSON using JsonSerializer
  - [ ] Output JSON to stdout
  - [ ] Output errors as JSON on failure

### Print Script
- [ ] Create `src/php_parser_py/scripts/print.php`
  - [ ] Require PHP-Parser PHAR
  - [ ] Read JSON from stdin
  - [ ] Create JsonDecoder
  - [ ] Decode JSON to AST
  - [ ] Create PrettyPrinter\Standard
  - [ ] Generate PHP code using prettyPrintFile
  - [ ] Output code to stdout
  - [ ] Handle exceptions and output to stderr

## Phase 4: Public API & Integration

### Module Initialization
- [ ] Update `src/php_parser_py/__init__.py`
  - [ ] Import all public classes
  - [ ] Implement `parse(code)` convenience function
  - [ ] Implement `parse_file(path)` convenience function
  - [ ] Define `__all__` for public API
  - [ ] Call `ensure_php_parser_extracted()` on module import

### Dependencies
- [ ] Update `pyproject.toml`
  - [ ] Add `cpg2py` dependency
  - [ ] Add `static-php-py` dependency
  - [ ] Verify Python version requirement (>=3.11)
  - [ ] Ensure resource files are included in package

### Directory Structure
- [ ] Create `src/php_parser_py/scripts/` directory
- [ ] Create `src/php_parser_py/vendor/` directory (gitignored)
- [ ] Verify `src/php_parser_py/resources/` contains PHP-Parser zip

## Phase 5: Testing & Validation

### Basic Functionality Tests
- [ ] Test parsing simple PHP code
  - [ ] Parse "<?php echo 'hello';"
  - [ ] Verify AST structure
  - [ ] Check node types and properties
- [ ] Test parsing PHP file
  - [ ] Create test PHP file
  - [ ] Parse using `parse_file()`
  - [ ] Verify AST correctness
- [ ] Test code generation
  - [ ] Parse PHP code
  - [ ] Regenerate code using PrettyPrinter
  - [ ] Verify output is valid PHP
- [ ] Test round-trip (parse → modify → print)
  - [ ] Parse code
  - [ ] Modify AST properties
  - [ ] Regenerate code
  - [ ] Verify modifications are reflected

### Error Handling Tests
- [ ] Test syntax error handling
  - [ ] Parse invalid PHP code
  - [ ] Verify `ParseError` is raised
  - [ ] Check error message and line number
- [ ] Test runner error handling
  - [ ] Simulate PHP execution failure
  - [ ] Verify `RunnerError` is raised

### Graph Traversal Tests
- [ ] Test node traversal
  - [ ] Use `nodes()` to iterate all nodes
  - [ ] Use `first_node()` to find specific node
  - [ ] Filter by label (node type)
- [ ] Test edge traversal
  - [ ] Use `children()` to get child nodes
  - [ ] Use `parent()` to get parent nodes
  - [ ] Use `descendants()` for recursive traversal
  - [ ] Verify edge ordering via index property

## Phase 6: Documentation & Examples

### README
- [ ] Update `README.md`
  - [ ] Add project description
  - [ ] Add installation instructions
  - [ ] Add basic usage examples
  - [ ] Add API reference links
  - [ ] Add license information

### Examples
- [ ] Create `examples/` directory
  - [ ] Create basic parsing example
  - [ ] Create graph traversal example
  - [ ] Create code modification example
  - [ ] Create error handling example

### Documentation
- [ ] Verify `docs/design.md` is up to date
- [ ] Verify `docs/idea.md` is up to date
- [ ] Add inline code documentation (docstrings)
  - [ ] Document all public classes
  - [ ] Document all public methods
  - [ ] Add type hints throughout

## Phase 7: Polish & Release

### Code Quality
- [ ] Add type hints to all functions
- [ ] Add docstrings to all public APIs
- [ ] Format code with black/ruff
- [ ] Run linter and fix issues
- [ ] Add .gitignore entries for vendor/

### Package Distribution
- [ ] Build wheel package
- [ ] Test installation from wheel
- [ ] Verify resource extraction works
- [ ] Test on clean environment
- [ ] Prepare for PyPI release (if applicable)

---

## Notes

- All implementations must follow the design specification in `docs/design.md`
- No hardcoded PHP node types - all types come from PHP-Parser JSON
- All AST operations delegate to PHP-Parser
- Use cpg2py's Storage for all graph operations
- Maintain lossless round-trip capability (parse → modify → print)
