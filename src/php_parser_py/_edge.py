"""Edge class for AST relationships."""

from typing import Any

from cpg2py import AbcEdgeQuerier, Storage


class Edge(AbcEdgeQuerier):
    """Represents an edge between AST nodes.

    Extends cpg2py's AbcEdgeQuerier to represent parent-child relationships
    in the PHP AST. Edges store the relationship type and optional metadata
    like field names and array indices for ordered children.

    Note: PHP-Parser doesn't have explicit Edge objects. This is our abstraction
    for representing the graph structure in cpg2py Storage.

    Attributes:
        _storage: cpg2py Storage instance containing edge data.
        _edge_id: Tuple of (from_id, to_id, edge_type).
    """

    def __init__(self, storage: Storage, edge_id: tuple[str, str, str]) -> None:
        """Initialize Edge with storage reference and edge ID.

        Args:
            storage: cpg2py Storage instance containing edge data.
            edge_id: Tuple of (from_id, to_id, edge_type).
        """
        super().__init__(storage, edge_id)
        self._storage = storage
        self._edge_id = edge_id

    # Core properties

    @property
    def type(self) -> str:
        """Return the edge type.

        Returns:
            Edge type string (e.g., "PARENT_OF").
        """
        return self._edge_id[2]

    @property
    def field(self) -> str | None:
        """Return the field name for this edge.

        The field name indicates which subnode property this edge represents
        (e.g., "name", "params", "stmts").

        Returns:
            Field name string or None.
        """
        props = self._storage.get_edge_properties(self._edge_id)
        if props is None:
            return None
        return props.get("field")

    @property
    def index(self) -> int | None:
        """Return the array index for ordered child relationships.

        For edges representing array elements in PHP-Parser JSON, this property
        contains the index position to maintain ordering.

        Returns:
            Integer index or None if not an array element.
        """
        props = self._storage.get_edge_properties(self._edge_id)
        if props is None:
            return None
        return props.get("index")

    @property
    def all_properties(self) -> dict:
        """Return all edge properties.

        Returns:
            Dictionary of edge properties.
        """
        return self._storage.get_edge_properties(self._edge_id) or {}

    # Dict-like access methods

    def __getitem__(self, key: str) -> Any:
        """Access edge properties using dict-like syntax.

        Enables edge["field"], edge["index"], etc.

        Args:
            key: Property name to access.

        Returns:
            Property value.

        Raises:
            KeyError: If property doesn't exist.
        """
        props = self.all_properties
        if key not in props:
            raise KeyError(f"Property '{key}' not found in edge {self._edge_id}")
        return props[key]

    def __contains__(self, key: str) -> bool:
        """Check if property exists using 'in' operator.

        Enables: if "index" in edge: ...

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
