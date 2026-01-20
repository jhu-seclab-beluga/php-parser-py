"""Parser class for PHP code parsing."""

import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

from cpg2py import Storage

from php_parser_py._ast import AST
from php_parser_py._runner import Runner
from php_parser_py.exceptions import ParseError, RunnerError

logger = logging.getLogger(__name__)


class Parser:
    """Parses PHP source code using PHP-Parser.

    Invokes PHP-Parser to parse PHP code and converts the resulting JSON
    to cpg2py Storage format for graph-based analysis.

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
        self._node_counter = 0

    def parse(self, code: str, prefix: str = "") -> AST:
        """Parse PHP code into an AST.

        Args:
            code: PHP source code to parse.
            prefix: Optional prefix for node IDs. Useful for distinguishing
                   nodes from different files when merging multiple ASTs.

        Returns:
            AST instance containing parsed code.

        Raises:
            ParseError: If code has syntax errors.
            RunnerError: If PHP execution fails.
        """
        # Reset node counter for each parse
        self._node_counter = 0
        self._node_id_prefix = prefix
        
        try:
            json_data = self._runner.parse(code)
        except RunnerError as e:
            # Check if it's a parse error
            if "Syntax error" in str(e):
                raise ParseError("Syntax error in PHP code", line=1) from e
            raise
        
        storage = self._json_to_storage(json_data)
        return AST(storage)

    def parse_file(self, path: str, prefix: str | None = None) -> AST:
        """Read and parse PHP file.

        Args:
            path: File path string.
            prefix: Optional prefix for node IDs. If not provided,
                   uses a hash of the file path (first 6 chars).

        Returns:
            AST instance containing parsed code structure.

        Raises:
            ParseError: If PHP-Parser reports syntax error.
            FileNotFoundError: If file does not exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Use file path hash as default prefix if none provided
        if prefix is None:
            # Generate a short hash from the file path
            path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:6]
            prefix = path_hash

        code = file_path.read_text(encoding="utf-8")
        return self.parse(code, prefix=prefix)

    def _json_to_storage(self, json_data: Any) -> Storage:
        """Convert PHP-Parser JSON to cpg2py Storage.

        Args:
            json_data: JSON data from PHP-Parser.

        Returns:
            Storage instance containing the AST graph.
        """
        storage = Storage()

        # Handle both single node and array of nodes
        if isinstance(json_data, list):
            for item in json_data:
                self._process_node(storage, item, None, None, None)
        else:
            self._process_node(storage, json_data, None, None, None)

        return storage

    def _process_node(
        self,
        storage: Storage,
        node_data: Any,
        parent_id: str | None,
        field_name: str | None,
        index: int | None,
    ) -> str | None:
        """Process a single node and its children recursively.

        Args:
            storage: Storage to populate.
            node_data: JSON node data.
            parent_id: Parent node ID if this is a child.
            field_name: Field name in parent if this is a child.
            index: Array index if this is an array element.

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
        node_id = f"node_{self._node_counter}"
        self._node_counter += 1

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
                    # Array of scalars (strings, numbers, etc.) - save as property
                    properties[key] = value
            else:
                # Scalar property
                properties[key] = value

        # Add node to storage (cpg2py API: add_node takes only nid)
        storage.add_node(node_id)
        # Set properties separately
        if properties:
            storage.set_node_props(node_id, properties)

        # Create edge from parent if applicable
        if parent_id is not None and field_name is not None:
            edge_props = {"field": field_name}
            if index is not None:
                edge_props["index"] = index
            # add_edge takes edge_id as a tuple
            edge_id = (parent_id, node_id, "PARENT_OF")
            storage.add_edge(edge_id)
            if edge_props:
                storage.set_edge_props(edge_id, edge_props)

        # Process child fields (only object arrays now)
        for field_name, field_value in child_fields:
            if isinstance(field_value, list):
                # Array of child objects
                for idx, item in enumerate(field_value):
                    self._process_node(storage, item, node_id, field_name, idx)
            else:
                # Single child object
                self._process_node(storage, field_value, node_id, field_name, None)

        return node_id
