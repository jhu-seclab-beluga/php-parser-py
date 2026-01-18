"""Node class for PHP AST nodes."""

from typing import Any

from cpg2py import AbcNodeQuerier, Storage


class Node(AbcNodeQuerier):
    """Wraps a single AST node with dynamic property access to PHP-Parser JSON fields.

    Extends cpg2py's AbcNodeQuerier to provide access to PHP-Parser node data
    stored in cpg2py Storage. All node properties come from PHP-Parser's JSON
    output and are accessed dynamically without hardcoded field definitions.

    PHP-Parser nodes have two types of data:
    - **Subnodes**: Structural properties like name, params, stmts, byRef, etc.
    - **Attributes**: Metadata like startLine, endLine, comments, etc.

    Both are accessible through this class using dict-like syntax or properties.

    Attributes:
        _storage: cpg2py Storage instance containing node data.
        _nid: Unique identifier for this node.
    """

    def __init__(self, storage: Storage, nid: str) -> None:
        """Initialize Node with storage reference and node ID.

        Args:
            storage: cpg2py Storage instance containing node data.
            nid: Unique identifier for this node.

        Raises:
            Exception: If node ID is not found in storage.
        """
        super().__init__(storage, nid)
        self._storage = storage
        self._nid = nid

    # Core properties

    @property
    def id(self) -> str:
        """Return the node identifier.

        Returns:
            Node ID string.
        """
        return self._nid

    @property
    def node_type(self) -> str | None:
        """Return the node type from PHP-Parser.

        Returns the `nodeType` field from the stored JSON, which contains
        the PHP-Parser class name (e.g., "Stmt_Function", "Expr_Variable").

        Returns:
            Node type string or None if not set.
        """
        return self.get_property("nodeType")

    @property
    def all_properties(self) -> dict:
        """Return all stored properties for this node.

        Includes both subnodes (structural properties) and attributes (metadata).

        Returns:
            Dictionary containing all properties from PHP-Parser JSON.
        """
        return self._storage.get_node_properties(self._nid) or {}

    # Dict-like access methods

    def __getitem__(self, key: str) -> Any:
        """Access node properties using dict-like syntax.

        Enables node["nodeType"], node["name"], node["startLine"], etc.

        Args:
            key: Property name to access.

        Returns:
            Property value.

        Raises:
            KeyError: If property doesn't exist.
        """
        props = self.all_properties
        if key not in props:
            raise KeyError(f"Property '{key}' not found in node {self._nid}")
        return props[key]

    def __contains__(self, key: str) -> bool:
        """Check if property exists using 'in' operator.

        Enables: if "name" in node: ...

        Args:
            key: Property name to check.

        Returns:
            True if property exists, False otherwise.
        """
        return key in self.all_properties

    def get(self, key: str, default: Any = None) -> Any:
        """Get property value with default fallback.

        Args:
            key: Property name to access.
            default: Default value if property doesn't exist.

        Returns:
            Property value or default.
        """
        return self.all_properties.get(key, default)

    # PHP-Parser standard attributes (metadata properties)

    @property
    def start_line(self) -> int | None:
        """Get starting line number.

        Returns:
            Starting line number or None.
        """
        return self.get_property("startLine")

    @property
    def end_line(self) -> int | None:
        """Get ending line number.

        Returns:
            Ending line number or None.
        """
        return self.get_property("endLine")

    @property
    def start_file_pos(self) -> int | None:
        """Get starting file position (byte offset).

        Returns:
            Starting byte offset or None.
        """
        return self.get_property("startFilePos")

    @property
    def end_file_pos(self) -> int | None:
        """Get ending file position (byte offset).

        Returns:
            Ending byte offset or None.
        """
        return self.get_property("endFilePos")

    @property
    def start_token_pos(self) -> int | None:
        """Get starting token position.

        Returns:
            Starting token index or None.
        """
        return self.get_property("startTokenPos")

    @property
    def end_token_pos(self) -> int | None:
        """Get ending token position.

        Returns:
            Ending token index or None.
        """
        return self.get_property("endTokenPos")

    @property
    def comments(self) -> list | None:
        """Get comments associated with this node.

        Returns:
            List of Comment objects or None.
        """
        return self.get_property("comments")

    # Attribute helper methods

    def has_attribute(self, name: str) -> bool:
        """Check if attribute exists.

        Args:
            name: Attribute name to check.

        Returns:
            True if attribute exists, False otherwise.
        """
        return name in self

    def get_attribute(self, name: str, default: Any = None) -> Any:
        """Get attribute value with default.

        Args:
            name: Attribute name.
            default: Default value if attribute doesn't exist.

        Returns:
            Attribute value or default.
        """
        return self.get(name, default)
