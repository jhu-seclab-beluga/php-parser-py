"""Parser class for PHP code parsing."""

import logging
from pathlib import Path
from typing import Any

from cpg2py import Storage

from php_parser_py._ast import AST
from php_parser_py._runner import Runner
from php_parser_py.exceptions import ParseError

logger = logging.getLogger(__name__)


class Parser:
    """Parses PHP source code using PHP-Parser.

    Invokes PHP-Parser to parse PHP code and converts the resulting JSON
    to cpg2py Storage format for graph-based analysis.

    Attributes:
        _runner: Runner instance for PHP-Parser invocation.
    """

    def __init__(self) -> None:
        """Initialize Parser with Runner."""
        self._runner = Runner()
        self._node_counter = 0

    def parse(self, code: str) -> AST:
        """Parse PHP code and return AST.

        Args:
            code: PHP source code string.

        Returns:
            AST instance containing parsed code structure.

        Raises:
            ParseError: If PHP-Parser reports syntax error.
        """
        json_data = self._runner.parse(code)
        storage = self._json_to_storage(json_data)
        return AST(storage)

    def parse_file(self, path: str) -> AST:
        """Read and parse PHP file.

        Args:
            path: File path string.

        Returns:
            AST instance containing parsed code structure.

        Raises:
            ParseError: If PHP-Parser reports syntax error.
            FileNotFoundError: If file does not exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        code = file_path.read_text(encoding="utf-8")
        return self.parse(code)

    def _json_to_storage(self, json_data: list | dict) -> Storage:
        """Convert PHP-Parser JSON to cpg2py Storage.

        Recursively processes the JSON structure, creating nodes for each
        object with nodeType and edges for parent-child relationships.

        Args:
            json_data: Parsed JSON data from PHP-Parser.

        Returns:
            Populated Storage instance.
        """
        storage = Storage()
        self._node_counter = 0

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
                # Array of children
                child_fields.append((key, value))
            else:
                # Scalar property
                properties[key] = value

        # Add node to storage
        storage.add_node(node_id, properties)

        # Create edge from parent if applicable
        if parent_id is not None and field_name is not None:
            edge_props = {"field": field_name}
            if index is not None:
                edge_props["index"] = index
            storage.add_edge(parent_id, node_id, "PARENT_OF", edge_props)

        # Process child fields
        for field_name, field_value in child_fields:
            if isinstance(field_value, list):
                # Array of children
                for idx, item in enumerate(field_value):
                    self._process_node(storage, item, node_id, field_name, idx)
            else:
                # Single child object
                self._process_node(storage, field_value, node_id, field_name, None)

        return node_id
