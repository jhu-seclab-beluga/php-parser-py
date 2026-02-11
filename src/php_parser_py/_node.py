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
    def node_type(self) -> str:
        """Return the node type from PHP-Parser.

        Returns the `nodeType` field from the stored JSON (e.g. "Stmt_Function").

        Returns:
            Node type string.
        """
        value = self.get_property("nodeType")
        if isinstance(value, str):
            return value
        raise TypeError(f"Invalid nodeType for node {self._nid}: {value!r}")

    @property
    def all_properties(self) -> dict[str, Any]:
        """Return all stored properties for this node.

        Includes both subnodes (structural properties) and attributes (metadata).

        Returns:
            Dictionary containing all properties from PHP-Parser JSON.
        """
        return self.properties or {}

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
    def start_line(self) -> int:
        """Get starting line number.

        Returns:
            Starting line number.
        """
        value = self.get_property("startLine")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise TypeError(f"Invalid startLine for node {self._nid}: {value!r}")

    @property
    def end_line(self) -> int:
        """Get ending line number.

        Returns:
            Ending line number.
        """
        value = self.get_property("endLine")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise TypeError(f"Invalid endLine for node {self._nid}: {value!r}")

    @property
    def start_file_pos(self) -> int:
        """Get starting file position (byte offset).

        Returns:
            Starting byte offset.
        """
        value = self.get_property("startFilePos")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise TypeError(f"Invalid startFilePos for node {self._nid}: {value!r}")

    @property
    def end_file_pos(self) -> int:
        """Get ending file position (byte offset).

        Returns:
            Ending byte offset.
        """
        value = self.get_property("endFilePos")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise TypeError(f"Invalid endFilePos for node {self._nid}: {value!r}")

    @property
    def start_token_pos(self) -> int:
        """Get starting token position.

        Returns:
            Starting token index.
        """
        value = self.get_property("startTokenPos")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise TypeError(f"Invalid startTokenPos for node {self._nid}: {value!r}")

    @property
    def end_token_pos(self) -> int:
        """Get ending token position.

        Returns:
            Ending token index.
        """
        value = self.get_property("endTokenPos")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise TypeError(f"Invalid endTokenPos for node {self._nid}: {value!r}")

    @property
    def comments(self) -> list[str]:
        """Get comments associated with this node.

        Returns:
            List of Comment objects (may be empty).
        """
        value = self.get_property("comments")
        if isinstance(value, list):
            return value
        raise TypeError(f"Invalid comments for node {self._nid}: {value!r}")

    @property
    def relative_path(self) -> str | None:
        """Get the relative path of the file containing this node.

        For File or Project nodes: returns their own relativePath property if set.
        For other nodes: resolves the containing File node and returns its relativePath.

        Returns:
            Relative path string, or None if not available.
        """
        # If this node is a File or Project, get its own relativePath
        if self.node_type in ("File", "Project"):
            value = self.get_property("relativePath")
            return value if isinstance(value, str) else None

        # For other nodes, try to get from containing file via ID prefix convention
        return self._get_file_property("relativePath")

    @property
    def absolute_path(self) -> str | None:
        """Get the absolute path of the file containing this node.

        For File or Project nodes: returns their own absolutePath property if set.
        For other nodes: resolves the containing File node and returns its absolutePath.

        Returns:
            Absolute path string, or None if not available.
        """
        # If this node is a File or Project, get its own absolutePath
        if self.node_type in ("File", "Project"):
            value = self.get_property("absolutePath")
            return value if isinstance(value, str) else None

        # For other nodes, try to get from containing file via ID prefix convention
        return self._get_file_property("absolutePath")

    def _get_file_property(self, prop_name: str) -> str | None:
        """Get a path property from the containing file node via ID prefix convention.

        Node IDs follow the pattern: file_hash_1, file_hash_2, etc.
        This method extracts the file_hash prefix and retrieves the property from that file node.

        Args:
            prop_name: Property name to retrieve ("relativePath" or "absolutePath").

        Returns:
            Property value from the file node, or None if not found.
        """
        if "_" not in self._nid:
            return None

        # Extract prefix: everything before the last underscore followed by digits
        last_underscore = self._nid.rfind("_")
        if last_underscore == -1:
            return None

        potential_index = self._nid[last_underscore + 1 :]
        if not potential_index.isdigit():
            return None

        # Get the file node with ID = prefix
        file_id = self._nid[:last_underscore]
        if not self._storage.contains_node(file_id):
            return None

        file_props = self._storage.get_node_props(file_id)
        if not file_props or file_props.get("nodeType") != "File":
            return None

        value = file_props.get(prop_name)
        return value if isinstance(value, str) else None

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
