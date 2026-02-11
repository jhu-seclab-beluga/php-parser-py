"""Edge class for AST relationships."""

from typing import Any

from cpg2py import AbcEdgeQuerier, Storage


class Edge(AbcEdgeQuerier):
    """Represents an edge between AST nodes with generic property access.

    Extends cpg2py's AbcEdgeQuerier. Edge type is fixed (e.g. "PARENT_OF");
    other data is stored as arbitrary properties via Storage. For PARENT_OF
    edges in our PHP AST mapping, we use properties "field" and "index" to
    represent the PHP-Parser subnode key and array position—access them via
    edge.get("field"), edge.get("index") or edge["field"], edge["index"];
    they are not special-cased on this class.

    Attributes:
        _storage: cpg2py Storage instance containing edge data.
        _edge_id: Tuple of (from_id, to_id, edge_type).
    """

    def __init__(
        self, graph: Storage, f_nid: str, t_nid: str, e_type: str = "PARENT_OF"
    ) -> None:
        """Initialize Edge with storage and edge identifiers.

        Args:
            graph: cpg2py Storage containing the graph.
            f_nid: From node ID.
            t_nid: To node ID.
            e_type: Edge type (default: "PARENT_OF").
        """
        super().__init__(graph, f_nid, t_nid, e_type)
        self._storage = graph
        self._edge_id = (str(f_nid), str(t_nid), str(e_type))

    # Core properties

    @property
    def type(self) -> str:
        """Return the edge type (e.g. "PARENT_OF")."""
        return self._edge_id[2]

    @property
    def all_properties(self) -> dict[str, Any]:
        """Return all edge properties.

        Returns:
            Dictionary of edge properties.
        """
        return self._storage.get_edge_props(self._edge_id) or {}

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
