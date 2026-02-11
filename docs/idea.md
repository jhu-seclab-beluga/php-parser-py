# php-parser-py

## 1. Context

**Problem Statement**

Python-based static analysis tools for PHP require Abstract Syntax Tree representations that integrate with graph-based analysis frameworks. Existing solutions either lack complete AST fidelity or require external PHP installations. This project bridges PHP-Parser's native capabilities with cpg2py's graph framework, enabling Python tools to work with PHP ASTs while delegating all parsing and code generation to PHP-Parser.

**System Role**

php-parser-py serves as a thin wrapper that bridges PHP-Parser's JSON serialization with cpg2py's graph structure, maximizing reuse of PHP-Parser's native functionality.

**Data Flow**

- **Inputs:** PHP Source Code
- **Outputs:** PHPASTGraph, PHP Source Code (regenerated)
- **Connections:** PHP Source → PHP-Parser → AST JSON → PHPASTGraph → AST JSON → PHP-Parser → PHP Source

**Scope Boundaries**

- **Owned:**
  - PHP-Parser invocation for parsing and code generation
  - AST JSON to cpg2py Storage mapping
  - PHPASTNode and PHPASTGraph extending cpg2py interfaces

- **Not Owned:**
  - Node type definitions (from PHP-Parser)
  - AST validation (by PHP-Parser)
  - Code formatting (by PHP-Parser PrettyPrinter)
  - Parsing logic reimplementation

---

## 2. Concepts

**Conceptual Diagram**

```
┌─────────────────────────────────────────────────────────────────┐
│                        php-parser-py                             │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ PHP Source   │───▶│ PHP Runner   │───▶│ AST JSON         │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│         ▲                   │                    │               │
│         │                   │                    ▼               │
│         │                   │            ┌──────────────────┐   │
│         │                   │            │ PHPASTGraph      │   │
│         │                   │            │ (cpg2py Storage) │   │
│         │                   │            └──────────────────┘   │
│         │                   │                    │               │
│         │                   ▼                    ▼               │
│  ┌──────┴───────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ PHP Source   │◀───│ PHP Runner   │◀───│ AST JSON         │   │
│  │ (regenerated)│    │              │    │ (reconstructed)  │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Dependencies                        │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │ static-php-py  │  │ PHP-Parser     │  │ cpg2py             │ │
│  │ (PHP Runtime)  │  │ (Parsing)      │  │ (Graph Framework)  │ │
│  └────────────────┘  └────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Core Concepts**

- **PHP Source Code**
  - **Definition:** The input PHP code provided as a string or file path for parsing. It represents the raw textual form of PHP programs before AST transformation.
  - **Scope:** Includes any valid PHP syntax supported by PHP-Parser. Excludes binary files or non-PHP content.
  - **Relationships:** Transformed into AST JSON by PHP Runner, regenerated from PHPASTGraph via PHP Runner.

- **AST JSON**
  - **Definition:** PHP-Parser's native JSON representation of the Abstract Syntax Tree. This format captures complete structural and metadata information including node types, child relationships, and source locations.
  - **Scope:** Includes all node types and attributes defined by PHP-Parser. This project does not define or interpret the JSON schema.
  - **Relationships:** Produced by PHP-Parser during parsing, consumed by PHP-Parser during code generation, stored in PHPASTGraph as cpg2py Storage.

- **PHPASTNode**
  - **Definition:** A graph node extending cpg2py's AbcNodeQuerier that wraps a single AST JSON node or synthetic node (Project/File). It provides dynamic property access to all JSON fields without hardcoded field definitions, and typed access to position attributes.
  - **Scope:** Includes all properties from the original JSON node, plus synthesized properties for Project/File nodes (absolutePath, relativePath, position attributes). Excludes type-specific behavior or validation.
  - **Relationships:** Contained within PHPASTGraph, linked to other nodes via PARENT_OF edges, accessed via cpg2py traversal methods (succ, prev, ancestors, descendants).

- **PHPASTGraph**
  - **Definition:** A graph structure extending cpg2py's AbcGraphQuerier that stores the complete AST including synthetic Project and File structural nodes. It uses cpg2py's Storage for node and edge management, representing parent-child relationships as PARENT_OF typed edges with field metadata.
  - **Scope:** Includes all AST nodes (from PHP-Parser and synthetic nodes), their relationships, and project/file organization. Provides cpg2py-compatible traversal methods for graph analysis.
  - **Relationships:** Contains PHPASTNode instances, constructed from AST JSON with added synthetic nodes, reconstructs AST JSON for code generation.

- **PHP Runner**
  - **Definition:** The component that manages communication with PHP-Parser via static-php-py. It invokes PHP-Parser for parsing and code generation, handling input/output serialization.
  - **Scope:** Includes process lifecycle and data exchange. Excludes parsing or printing logic implementation.
  - **Relationships:** Uses static-php-py for PHP execution, receives PHP Source Code and AST JSON, produces AST JSON and PHP Source Code.

- **Storage**
  - **Definition:** cpg2py's internal data structure for holding nodes, edges, and their properties. It provides the foundation for graph traversal and query operations.
  - **Scope:** Includes node/edge storage and property management. Inherited from cpg2py without modification.
  - **Relationships:** Used by PHPASTGraph, populated from AST JSON, reconstructed to AST JSON.

---

## 3. Contracts & Flow

**Data Contracts**

- **With PHP-Parser:** All data exchange uses PHP-Parser's native JSON format. The JSON schema is defined by PHP-Parser and preserved without interpretation or modification by this project.

- **With cpg2py:** PHPASTNode extends AbcNodeQuerier, PHPASTGraph extends AbcGraphQuerier. All traversal methods are inherited from cpg2py. Storage holds AST data with PARENT_OF edges representing nesting.

- **With static-php-py:** PHP Runner uses static-php-py to invoke PHP-Parser. Input and output pass through process stdin/stdout as text.

**Internal Processing Flow**

1. **Parse Input** - User provides PHP Source Code to the parsing interface.

2. **PHP Invocation** - PHP Runner invokes PHP-Parser to parse the code and serialize the AST to JSON format.

3. **JSON Capture** - PHP Runner captures the AST JSON output.

4. **Storage Population** - The JSON is walked recursively, creating nodes and PARENT_OF edges in cpg2py Storage.

5. **Graph Creation** - PHPASTGraph is instantiated with the populated Storage.

6. **Traversal** - User traverses the graph using cpg2py's inherited methods.

7. **JSON Reconstruction** - For code generation, Storage is walked to reconstruct the original JSON structure.

8. **Code Generation** - PHP Runner invokes PHP-Parser to decode JSON and generate PHP Source Code.

9. **Output Delivery** - Regenerated PHP Source Code is returned to the user.

---

## 4. Scenarios

- **Typical:** A security researcher parses a PHP file and queries for all function definitions using cpg2py's traversal methods. They filter nodes by the node_type property to find specific node types, then access node properties to extract function names and position information. All type information comes from PHP-Parser's JSON or synthetic node markers.

- **Typical:** A developer extracts all variable assignments from a codebase. They traverse the graph using descendants method, filter by node_type, and collect property values. The dynamic property access works for any node type without predefined schemas.

- **Boundary:** A user provides PHP code with syntax errors. PHP-Parser reports errors during parsing, and PHP Runner propagates the error information to the user. No partial AST is produced; error handling follows PHP-Parser's behavior.

- **Boundary:** PHP-Parser is updated with new node types. Since this project has no hardcoded type definitions, new types appear automatically in the node_type property. All properties remain accessible via dynamic property access without code changes.

- **Interaction:** A refactoring tool modifies property values in the graph and position information (File node's endLine), then regenerates code. The JSON reconstruction preserves all structural relationships and position attributes. PHP-Parser's code generator produces valid PHP reflecting the modifications.

- **Interaction:** A multi-language analyzer combines PHP ASTs with other language graphs in a cpg2py pipeline. PHPASTGraph is fully compatible with cpg2py's interface, enabling unified traversal and analysis across languages. Project and File nodes can be queried like any other graph nodes.

---

*For technical specifications, see [design.md](design.md).*
