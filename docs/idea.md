# php-parser-py

## 1. Context

**Problem Statement**

Python-based static analysis tools for PHP require Abstract Syntax Tree (AST) representations that match the structure and semantics of nikic/PHP-Parser. Existing solutions either lack complete AST fidelity or require external PHP installations. This project provides a Python interface that generates AST structures fully consistent with PHP-Parser's node hierarchy, enabling seamless integration with PHP analysis toolchains while operating through an embedded static PHP binary.

**System Role**

php-parser-py serves as a Python-native AST provider that mirrors nikic/PHP-Parser's node structure and behavior, enabling Python applications to parse, traverse, modify, and regenerate PHP source code with full compatibility to PHP-Parser's object model.

**Data Flow**

- **Inputs:** PHP source code (string or file path)
- **Outputs:** AST Node Tree (PHP-Parser-consistent structure), PHP source code (regenerated)
- **Connections:** Python Application → php-parser-py → static-php-py → PHP-Parser PHAR → AST JSON → Python AST Nodes

**Scope Boundaries**

- **Owned:**
  - PHP source code to AST parsing (via PHP-Parser)
  - AST to PHP source code generation (via PrettyPrinter)
  - PHP-Parser-consistent AST node type hierarchy in Python
  - AST traversal with visitor pattern (NodeTraverser/NodeVisitor style)
  - cpg2py-compatible querier interface for AST access
  - PHP binary lifecycle through static-php-py

- **Not Owned:**
  - Control Flow Graph (CFG) construction
  - Data Flow Graph (DFG) construction
  - PHP code execution or runtime interpretation
  - PHP version detection or multi-version support beyond PHP-Parser 4.x
  - Code formatting or style enforcement beyond PrettyPrinter behavior

---

## 2. Concepts

**Conceptual Diagram**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           php-parser-py                                  │
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │  PHP Source  │────▶│  PHP Runner  │────▶│  AST Node Tree           │ │
│  │  (codes)     │     │  (static-php │     │  (PHP-Parser structure)  │ │
│  └──────────────┘     │   -py)       │     └──────────────────────────┘ │
│         ▲             └──────────────┘              │                    │
│         │                    │                      ▼                    │
│         │                    │              ┌──────────────────────────┐ │
│  ┌──────┴───────┐            │              │  NodeTraverser           │ │
│  │ PrettyPrinter│◀───────────┘◀─────────────│  + NodeVisitor           │ │
│  │ (AST→Code)   │                           └──────────────────────────┘ │
│  └──────────────┘                                    │                    │
│                                                      ▼                    │
│                                             ┌──────────────────────────┐ │
│                                             │  cpg2py Querier          │ │
│                                             │  Interface Adapter       │ │
│                                             └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        External Dependencies                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐ │
│  │ static-php-py  │  │ PHP-Parser     │  │ cpg2py                     │ │
│  │ (PHP Binary)   │  │ (PHAR 4.19.4)  │  │ (Traversal Interface)      │ │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

**Core Concepts**

**AST Node**

An AST Node is the fundamental building block of the syntax tree, directly corresponding to PHP-Parser's `PhpParser\Node` class hierarchy. Each node has a specific type (e.g., `Stmt_Function`, `Expr_Variable`, `Scalar_String`), sub-node attributes matching PHP-Parser's property definitions, and source location metadata. The Python node classes mirror PHP-Parser's naming conventions and attribute structures to ensure compatibility with PHP-Parser-based analysis tools.

**Node Type Hierarchy**

The Node Type Hierarchy organizes AST nodes into categories matching PHP-Parser's namespace structure. Primary categories include `Stmt` (statements like function declarations, class definitions, if/while blocks), `Expr` (expressions like function calls, binary operations, variable access), and `Scalar` (literal values like strings and numbers). Each specific node type (e.g., `Stmt_Class`, `Expr_MethodCall`) inherits from its category base class while maintaining PHP-Parser-compatible attribute names.

**Sub-Nodes and Attributes**

Sub-Nodes represent child AST elements within a parent node, such as `stmts` (statement list), `params` (parameter list), or `expr` (single expression). Attributes store metadata including `startLine`, `endLine`, `startFilePos`, `endFilePos`, and `comments`. The distinction between sub-nodes (structural children) and attributes (metadata) follows PHP-Parser's internal classification.

**NodeTraverser**

NodeTraverser implements the visitor pattern for systematic AST traversal. It walks the node tree in a defined order, invoking visitor callbacks at each node. The traverser supports multiple visitors, allowing composition of analysis or transformation passes. Its behavior mirrors PHP-Parser's `NodeTraverser` class, including control flow mechanisms for skipping subtrees or stopping traversal.

**NodeVisitor**

NodeVisitor defines the callback interface for AST traversal. It provides four hook points matching PHP-Parser's visitor interface: `beforeTraverse` (called before traversal begins), `enterNode` (called when entering a node), `leaveNode` (called after processing a node's children), and `afterTraverse` (called when traversal completes). Visitors can observe nodes for analysis or return modified/replacement nodes for transformation.

**PrettyPrinter**

PrettyPrinter converts an AST Node Tree back into valid PHP source code. It mirrors PHP-Parser's `PrettyPrinter\Standard` behavior, producing normalized code output. Format-preserving printing (maintaining original whitespace and formatting where possible) may be supported as an extended feature following PHP-Parser's format-preserving printer capabilities.

**PHP Runner**

PHP Runner abstracts the interaction with static-php-py and the embedded PHP-Parser PHAR. It manages subprocess communication, serialization of PHP code input, and deserialization of AST output (typically JSON format). The runner handles the lifecycle of PHP process invocations and provides a clean interface to the parsing and printing capabilities of PHP-Parser.

**Querier Interface Adapter**

The Querier Interface Adapter bridges PHP-Parser-style AST nodes with cpg2py's abstract querier interfaces (`AbcNodeQuerier`, `AbcEdgeQuerier`, `AbcGraphQuerier`). This allows users familiar with cpg2py to apply graph-style queries (like `children()`, `succ()`, `prev()`) to the PHP AST. The adapter wraps AST nodes without changing their PHP-Parser-consistent structure.

---

## 3. Contracts & Flow

**Data Contracts**

- **With static-php-py:**
  PHP Runner invokes the static PHP binary through static-php-py's API. Input consists of UTF-8 encoded PHP source code passed via subprocess stdin or temporary files. Output is JSON-serialized AST following PHP-Parser's JsonSerializer format.

- **With PHP-Parser PHAR:**
  The PHAR file (resources/php-parser-4.19.4.zip containing php-parser.phar) provides the parsing engine. Communication occurs through PHP script invocation that uses PHP-Parser's `ParserFactory`, `NodeDumper` or `JsonSerializer` for AST output, and `PrettyPrinter\Standard` for code regeneration.

- **With cpg2py:**
  AST Node classes can optionally implement cpg2py's `AbcNodeQuerier` interface methods. The Querier Interface Adapter provides `children()`, `parent()`, `succ()`, `prev()` methods wrapping the underlying AST structure. This enables cpg2py-style graph queries without altering the PHP-Parser-consistent node structure.

- **Node Structure Consistency Contract:**
  All Python AST Node classes maintain naming and attribute consistency with PHP-Parser's node classes. `Stmt\Function_` in PHP-Parser corresponds to `Stmt_Function` in Python. Node attributes like `name`, `params`, `stmts`, `returnType`, `attrGroups` preserve identical names and semantics.

**Internal Processing Flow**

1. **Parse Request** - User provides PHP source code string or file path to the parser interface.

2. **Runner Preparation** - PHP Runner prepares the PHP-Parser invocation script with serialization instructions.

3. **Binary Execution** - static-php-py launches the PHP process with the PHP-Parser PHAR and runner script.

4. **AST Parsing** - PHP-Parser's `ParserFactory` creates a parser instance and parses the source into PHP AST objects.

5. **JSON Serialization** - The PHP-side script serializes the AST to JSON format with full node type and attribute preservation.

6. **JSON Capture** - PHP Runner captures the JSON output from PHP process stdout.

7. **Node Construction** - Parser module deserializes JSON and instantiates corresponding Python AST Node objects with PHP-Parser-consistent types.

8. **Tree Assembly** - Individual nodes are linked into a complete AST Node Tree with parent-child relationships.

9. **Traversal (optional)** - User attaches NodeVisitor instances to NodeTraverser and executes traversal over the tree.

10. **Code Regeneration (optional)** - Modified or unmodified AST is serialized back to JSON and sent to PHP-Parser's PrettyPrinter via PHP Runner.

11. **Code Delivery** - Regenerated PHP source code is returned to the user as a string.

---

## 4. Scenarios

**Typical: Parse PHP File and Extract Function Names**

A security researcher needs to inventory all function definitions in a PHP application. They call `parse_file("target.php")` to obtain the AST Node Tree. Using NodeTraverser with a custom NodeVisitor, they implement `enterNode` to check for `Stmt_Function` type nodes, collecting the `name` attribute from each. The visitor accumulates function names during traversal, providing a complete list upon traversal completion.

**Typical: Rename Variable Across Codebase**

A developer wants to rename a variable `$oldName` to `$newName` throughout a file. They parse the source, then traverse with a transforming NodeVisitor. When `enterNode` encounters an `Expr_Variable` node with `name` matching "oldName", it returns a new node with the updated name. After traversal, they call the PrettyPrinter to generate the modified PHP source code.

**Boundary: Syntax Error Handling**

A user submits PHP code with a missing semicolon. PHP-Parser enters error recovery mode if configured, producing a partial AST with error nodes marking unparseable regions. The Python parser interface propagates error information including line number and error message. Users can inspect error nodes to understand parsing failures or handle the exception if strict parsing mode is enabled.

**Boundary: Large File Processing**

A user parses a PHP file exceeding 50,000 lines. The PHP process handles parsing with PHP-Parser's efficient implementation. JSON serialization may produce large output; the Python side deserializes and constructs nodes incrementally. Memory usage scales with AST size. Users processing extremely large codebases should consider file-by-file processing rather than loading all ASTs simultaneously.

**Interaction: Round-Trip Code Transformation**

An automated refactoring tool needs to add type hints to function parameters. The tool parses source code, traverses to find `Stmt_Function` nodes, examines each `Param` sub-node, and adds `type` attributes where missing. The modified AST passes through PrettyPrinter, producing valid PHP code with the new type hints. Parsing the regenerated code produces an AST structurally equivalent to the modified tree, confirming successful round-trip transformation.

**Interaction: cpg2py-Style AST Queries**

A vulnerability scanner uses cpg2py for multi-language analysis. When processing PHP, the scanner wraps the AST Node Tree with the Querier Interface Adapter. It uses `graph.node(id)` to access specific nodes, `children(node)` to navigate into sub-nodes, and filtering predicates to locate nodes of interest. The underlying nodes remain PHP-Parser-consistent, while the query interface provides familiar cpg2py semantics.

---

*For API specifications, implementation details, and code examples, see [design.md](design.md).*
