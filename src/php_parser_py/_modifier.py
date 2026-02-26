"""Modifier class for AST graph mutation operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ._edge import Edge
from ._node import Node

if TYPE_CHECKING:
    from ._ast import AST

logger = logging.getLogger(__name__)


class Modifier:
    """Encapsulates all graph mutation operations for an AST.

    The only approved way to add, remove, or structurally modify nodes and
    edges in the AST graph. Callers must never use Storage directly.

    AST (AbcGraphQuerier) is a query interface; graph mutation is a separate
    concern handled by this class. Mutations are immediately visible through
    the wrapped AST's query methods.

    Attributes:
        _ast: The AST instance being modified.
        _storage: Reference to the AST's internal Storage.
    """

    def __init__(self, ast: AST) -> None:
        """Wrap an existing AST instance for mutation.

        Args:
            ast: AST instance to modify.
        """
        self._ast = ast
        self._storage = ast.storage

    @property
    def ast(self) -> AST:
        """Return the underlying AST instance."""
        return self._ast

    # -- Node Operations --

    def add_node(self, node_id: str, node_type: str, **props: object) -> Node:
        """Create a new node in the graph with the given type and properties.

        Args:
            node_id: Unique node ID string.
            node_type: PHP-Parser node type (e.g. "Stmt_Break").
            **props: Additional node properties to set.

        Returns:
            Node instance for the newly created node.

        Raises:
            ValueError: If node_id already exists in the graph.
        """
        if self._storage.contains_node(node_id):
            raise ValueError(f"Node already exists: {node_id!r}")

        self._storage.add_node(node_id)
        all_props: dict[str, object] = {"nodeType": node_type, **props}
        self._storage.set_node_props(node_id, all_props)
        return Node(self._storage, node_id)

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its connected edges from the graph.

        Args:
            node_id: Node ID to remove.

        Raises:
            KeyError: If node_id is not in the graph.
        """
        if not self._storage.contains_node(node_id):
            raise KeyError(f"Node not found: {node_id!r}")
        self._storage.remove_node(node_id)

    # -- Edge Operations --

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: str = "PARENT_OF",
        **props: object,
    ) -> Edge:
        """Create a new edge between two existing nodes.

        Args:
            from_id: Source node ID.
            to_id: Target node ID.
            edge_type: Edge type. Defaults to "PARENT_OF".
            **props: Edge properties (e.g. field="stmts", index=0).

        Returns:
            Edge instance for the newly created edge.

        Raises:
            KeyError: If either node does not exist.
            ValueError: If edge already exists.
        """
        if not self._storage.contains_node(from_id):
            raise KeyError(f"Source node not found: {from_id!r}")
        if not self._storage.contains_node(to_id):
            raise KeyError(f"Target node not found: {to_id!r}")

        edge_id = (from_id, to_id, edge_type)
        if self._storage.contains_edge(edge_id):
            raise ValueError(f"Edge already exists: {edge_id!r}")

        self._storage.add_edge(edge_id)
        if props:
            self._storage.set_edge_props(edge_id, props)
        return Edge(self._storage, from_id, to_id, edge_type)

    def remove_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: str = "PARENT_OF",
    ) -> None:
        """Remove an edge from the graph.

        Args:
            from_id: Source node ID.
            to_id: Target node ID.
            edge_type: Edge type. Defaults to "PARENT_OF".

        Raises:
            KeyError: If edge is not in the graph.
        """
        edge_id = (from_id, to_id, edge_type)
        if not self._storage.contains_edge(edge_id):
            raise KeyError(f"Edge not found: {edge_id!r}")
        self._storage.remove_edge(edge_id)
