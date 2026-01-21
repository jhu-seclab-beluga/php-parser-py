"""Parser class for PHP code parsing."""

import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

from cpg2py import Storage

from php_parser_py._ast import AST
from php_parser_py._node import Node
from php_parser_py._runner import Runner
from php_parser_py.exceptions import ParseError, RunnerError

logger = logging.getLogger(__name__)


class Parser:
    """Parses PHP source code using PHP-Parser.

    Provides three parsing methods:
    - parse_code: Parse code string, returns list of top-level statement nodes
    - parse_file: Parse single file, returns AST with project and file nodes
    - parse_project: Parse multiple files, returns AST with project and multiple file nodes

    Attributes:
        _runner: Runner instance for PHP-Parser invocation.
    """

    def __init__(
        self,
        php_binary_path: Optional[Path] = None,
        php_binary_url: Optional[str] = None,
    ) -> None:
        """Initialize Parser with Runner.
        
        Args:
            php_binary_path: Optional path to local PHP binary.
            php_binary_url: Optional URL to download PHP binary from.
        """
        self._runner = Runner(
            php_binary_path=php_binary_path,
            php_binary_url=php_binary_url,
        )

    def parse(self, code: str) -> AST:
        """Parse PHP code string into an AST (backward compatibility).

        Creates a temporary project/file structure. For code-only parsing
        without project structure, use parse_code() instead.

        Args:
            code: PHP source code string.

        Returns:
            AST instance with project -> file -> statements hierarchy.

        Raises:
            ParseError: If code has syntax errors.
            RunnerError: If PHP execution fails.
        """
        import tempfile
        from pathlib import Path
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            return self.parse_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def parse_code(self, code: str) -> list[Node]:
        """Parse PHP code string into a list of top-level statement nodes.

        Does not create project or file nodes. Returns raw statement nodes
        that can be used for analysis or inserted into other AST structures.

        Args:
            code: PHP source code to parse.

        Returns:
            List of Node instances representing top-level statements.

        Raises:
            ParseError: If code has syntax errors.
            RunnerError: If PHP execution fails.
        """
        try:
            json_data = self._runner.parse(code)
        except RunnerError as e:
            if "Syntax error" in str(e):
                raise ParseError("Syntax error in PHP code", line=1) from e
            raise
        
        # Normalize to list
        if not isinstance(json_data, list):
            json_data = [json_data]

        # Create temporary storage to convert JSON to nodes
        storage = Storage()
        node_ids = []
        node_counter = [1]  # Use list to allow mutation in recursive calls

        for item in json_data:
            node_id = self._process_node(storage, item, None, None, None, node_counter, "")
            if node_id:
                node_ids.append(node_id)

        # Return Node instances
        return [Node(storage, nid) for nid in node_ids]

    def parse_file(self, path: str) -> AST:
        """Parse a single PHP file into an AST with project and file nodes.

        Creates a project node (ID: "project") and a file node (ID: hex hash of path).
        File node contains all statements from the file.
        Project path is set to the file's directory.

        Args:
            path: File path string.

        Returns:
            AST instance with project -> file -> statements hierarchy.

        Raises:
            ParseError: If PHP-Parser reports syntax error.
            FileNotFoundError: If file does not exist.
        """
        file_path = Path(path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Project path is the file's directory
        project_path = file_path.parent

        # Generate file hash (hex)
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]

        code = file_path.read_text(encoding="utf-8")
        
        try:
            json_data = self._runner.parse(code)
        except RunnerError as e:
            if "Syntax error" in str(e):
                raise ParseError("Syntax error in PHP code", line=1) from e
            raise

        # Normalize json_data to list
        if not isinstance(json_data, list):
            json_data = [json_data]

        storage = self._create_project_structure(
            [(file_path, json_data)], 
            [(file_path, file_hash)],
            project_path=project_path
        )
        return AST(storage, root_node_id="project")

    def parse_project(self, paths: list[str], project_path: str | None = None) -> AST:
        """Parse multiple PHP files into an AST with project and file nodes.

        Creates a project node (ID: "project") and multiple file nodes.
        Each file node has ID based on its path hash.
        Project path is the common parent directory of all files, or the provided project_path.

        Args:
            paths: List of file path strings.
            project_path: Optional project root path. If not provided, computed as common parent.

        Returns:
            AST instance with project -> files -> statements hierarchy.

        Raises:
            ParseError: If any file has syntax errors.
            FileNotFoundError: If any file does not exist.
        """
        file_infos = []
        resolved_paths = []
        for path in paths:
            file_path = Path(path).resolve()
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
            file_infos.append((file_path, file_hash))
            resolved_paths.append(file_path)

        # Determine project path
        if project_path:
            project_path = Path(project_path).resolve()
        else:
            # Compute common parent directory
            if len(resolved_paths) == 1:
                project_path = resolved_paths[0].parent
            else:
                # Find common parent
                common_parts = None
                for file_path in resolved_paths:
                    parts = file_path.parts
                    if common_parts is None:
                        common_parts = parts
                    else:
                        # Find common prefix
                        min_len = min(len(common_parts), len(parts))
                        common_parts = [p for i, p in enumerate(common_parts[:min_len]) if parts[i] == p]
                if common_parts:
                    project_path = Path(*common_parts)
                else:
                    # Fallback to first file's parent
                    project_path = resolved_paths[0].parent

        # Parse all files
        all_json_data = []
        for file_path, _ in file_infos:
            code = file_path.read_text(encoding="utf-8")
            try:
                json_data = self._runner.parse(code)
                if not isinstance(json_data, list):
                    json_data = [json_data]
                all_json_data.append((file_path, json_data))
            except RunnerError as e:
                if "Syntax error" in str(e):
                    raise ParseError(f"Syntax error in {file_path}", line=1) from e
                raise

        storage = self._create_project_structure(all_json_data, file_infos, project_path=project_path)
        return AST(storage, root_node_id="project")

    def _create_project_structure(
        self,
        files_data: list[tuple[Path, Any]],
        file_infos: list[tuple[Path, str]],
        project_path: Path
    ) -> Storage:
        """Create AST structure with project -> files -> statements hierarchy.

        Args:
            files_data: List of (file_path, json_data) tuples.
            file_infos: List of (file_path, file_hash) tuples.
            project_path: Project root directory path.

        Returns:
            Storage instance with complete project structure.
        """
        storage = Storage()

        # Create project node (fixed ID: "project")
        project_id = "project"
        storage.add_node(project_id)
        storage.set_node_props(project_id, {
            "nodeType": "Project",
            "label": "Project",
            "path": str(project_path)
        })

        # Create file nodes and process their statements
        for (file_path, file_hash), (_, json_data) in zip(file_infos, files_data):
            # Calculate relative path from project root
            try:
                relative_path = file_path.relative_to(project_path)
            except ValueError:
                # If file is not under project_path, use filename
                relative_path = file_path.name

            # Create file node (ID: hex hash)
            file_id = file_hash
            storage.add_node(file_id)
            storage.set_node_props(file_id, {
                "nodeType": "File",
                "label": "File",
                "filePath": str(file_path),  # Absolute path
                "path": str(relative_path)   # Relative path from project root
            })

            # Link file to project
            edge_id = (project_id, file_id, "PARENT_OF")
            storage.add_edge(edge_id)
            storage.set_edge_props(edge_id, {"field": "files"})

            # Process statements in file (node IDs: {hex}_1, {hex}_2, ...)
            node_counter = [1]
            if not isinstance(json_data, list):
                json_data = [json_data]

            for idx, item in enumerate(json_data):
                self._process_node(
                    storage, item, file_id, "stmts", idx, node_counter, file_hash
                )

        return storage

    def _process_node(
        self,
        storage: Storage,
        node_data: Any,
        parent_id: str | None,
        field_name: str | None,
        index: int | None,
        node_counter: list[int],
        prefix: str
    ) -> str | None:
        """Process a single node and its children recursively.

        Args:
            storage: Storage to populate.
            node_data: JSON node data.
            parent_id: Parent node ID if this is a child.
            field_name: Field name in parent if this is a child.
            index: Array index if this is an array element.
            node_counter: Mutable list with single int counter for generating node IDs.
            prefix: Prefix for node IDs (file hash for file nodes, empty for code nodes).

        Returns:
            Node ID if a node was created, None otherwise.
        """
        if node_data is None:
            return None

        if not isinstance(node_data, dict):
            return None

        # Only create nodes for objects with nodeType
        if "nodeType" not in node_data:
            return None

        # Generate unique node ID
        current_counter = node_counter[0]
        if prefix:
            node_id = f"{prefix}_{current_counter}"
        else:
            node_id = f"node_{current_counter}"
        node_counter[0] += 1

        # Collect node properties
        properties: dict[str, Any] = {}
        child_fields: list[tuple[str, Any]] = []

        for key, value in node_data.items():
            if key == "attributes":
                # Flatten attributes to node properties
                if isinstance(value, dict):
                    properties.update(value)
            elif isinstance(value, dict):
                # Nested object - will create child node
                child_fields.append((key, value))
            elif isinstance(value, list):
                # Check if it's an array of objects or scalars
                if value and isinstance(value[0], dict):
                    # Array of objects - create child nodes
                    child_fields.append((key, value))
                else:
                    # Array of scalars - save as property
                    properties[key] = value
            else:
                # Scalar property
                properties[key] = value

        # Add node to storage
        storage.add_node(node_id)
        if properties:
            storage.set_node_props(node_id, properties)

        # Create edge from parent if applicable
        if parent_id is not None and field_name is not None:
            edge_props = {"field": field_name}
            if index is not None:
                edge_props["index"] = index
            edge_id = (parent_id, node_id, "PARENT_OF")
            storage.add_edge(edge_id)
            if edge_props:
                storage.set_edge_props(edge_id, edge_props)

        # Process child fields recursively
        for field_name, field_value in child_fields:
            if isinstance(field_value, list):
                # Array of child objects
                for idx, item in enumerate(field_value):
                    self._process_node(
                        storage, item, node_id, field_name, idx, node_counter, prefix
                    )
            else:
                # Single child object
                self._process_node(
                    storage, field_value, node_id, field_name, None, node_counter, prefix
                )

        return node_id
