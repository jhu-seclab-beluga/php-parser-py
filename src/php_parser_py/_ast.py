"""AST representation for PHP code using cpg2py's graph framework."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Iterable, Optional

from cpg2py import AbcGraphQuerier, Storage

from php_parser_py._edge import Edge
from php_parser_py._node import Node

logger = logging.getLogger(__name__)


class AST(AbcGraphQuerier[Node, Edge]):
    """Represents a PHP Abstract Syntax Tree.

    This class extends cpg2py's AbcGraphQuerier with generic type parameters
    specifying that it works with Node and Edge types.

    The AST is stored as a graph in cpg2py Storage, where:
    - Nodes represent PHP-Parser AST nodes (statements, expressions, etc.)
    - Edges represent parent-child relationships with field names

    Type Parameters:
        Node: The concrete node type for PHP AST nodes
        Edge: The concrete edge type for parent-child relationships

    Provides graph traversal methods and JSON reconstruction
    for code generation.

    Attributes:
        _storage: cpg2py Storage containing AST nodes and edges.
    """

    def __init__(self, storage: Storage) -> None:
        """Initialize AST with populated storage.

        Args:
            storage: cpg2py Storage containing AST nodes and edges.
        """
        super().__init__(storage)
        self._storage = storage

    def node(self, whose_id_is: str) -> Optional[Node]:
        """Return node wrapper by ID.

        Args:
            whose_id_is: Node ID string.

        Returns:
            Node instance or None if not found.
        """
        if not self._storage.contains_node(whose_id_is):
            return None
        return Node(self._storage, whose_id_is)

    def edge(self, fid: str, tid: str, eid: str) -> Optional[Edge]:
        """Return edge wrapper by IDs.

        Args:
            fid: From node ID.
            tid: To node ID.
            eid: Edge type.

        Returns:
            Edge instance or None if not found.
        """
        edge_id = (fid, tid, eid)
        if not self._storage.contains_edge(edge_id):
            return None
        return Edge(self._storage, fid, tid, eid)

    def to_json(self) -> str:
        """Reconstruct PHP-Parser JSON from Storage for code generation.

        Traverses the graph to rebuild the nested JSON structure that matches
        PHP-Parser's original output format. This enables lossless round-trip
        from parsing to code generation.

        Returns:
            JSON string compatible with PHP-Parser's JsonDecoder.
        """
        root_nodes = self._find_root_nodes()
        result = [self._reconstruct_node(nid) for nid in root_nodes]
        return json.dumps(result)

    def _find_root_nodes(self) -> list[str]:
        """Find nodes with no incoming PARENT_OF edges."""
        all_nodes = set(self._storage.get_nodes())
        child_nodes = set()

        for edge_id in self._storage.get_edges():
            _, to_id, edge_type = edge_id
            if edge_type == "PARENT_OF":
                child_nodes.add(to_id)

        root_nodes = all_nodes - child_nodes
        return sorted(root_nodes)

    def _reconstruct_node(self, nid: str) -> dict[str, Any]:
        """Recursively reconstruct JSON object for a node."""
        props = self._storage.get_node_props(nid)
        if props is None:
            return {}

        result: dict[str, Any] = {}
        node_type = props.get("nodeType")
        if node_type:
            result["nodeType"] = node_type

        # Collect attribute fields
        attributes = {}
        child_fields: dict[str, Any] = {}

        for key, value in props.items():
            if key == "nodeType":
                continue
            # Attributes are typically line numbers and metadata
            if key in (
                "startLine",
                "endLine",
                "startFilePos",
                "endFilePos",
                "startTokenPos",
                "endTokenPos",
                "kind",
                "comments",
            ):
                attributes[key] = value
            else:
                # All other fields (scalars, arrays, etc.) go directly in result
                # Child nodes will be added separately via edges
                result[key] = value

        if attributes:
            result["attributes"] = attributes

        # Reconstruct child nodes from PARENT_OF edges
        outgoing_edges = [
            eid
            for eid in self._storage.get_edges()
            if eid[0] == nid and eid[2] == "PARENT_OF"
        ]

        for from_id, to_id, edge_type in outgoing_edges:
            edge_props = self._storage.get_edge_props((from_id, to_id, edge_type))
            if edge_props is None:
                continue

            field_name = edge_props.get("field")
            if field_name is None:
                continue

            child_json = self._reconstruct_node(to_id)
            index = edge_props.get("index")

            if index is not None:
                # Array field
                if field_name not in child_fields:
                    child_fields[field_name] = {}
                child_fields[field_name][index] = child_json
            else:
                # Single object field
                result[field_name] = child_json

        # Convert indexed dictionaries to arrays
        for field_name, indexed_children in child_fields.items():
            if isinstance(indexed_children, dict):
                # Sort by index and create array
                max_index = max(indexed_children.keys())
                array = [None] * (max_index + 1)
                for idx, child in indexed_children.items():
                    array[idx] = child
                result[field_name] = array

        # Add default values for common optional fields that PHP-Parser expects
        # These prevent "null given, array expected" errors in PrettyPrinter
        # attrGroups is required for many node types in PHP 8+
        if node_type and ("attrGroups" not in result):
            # Most node types that can have attributes need attrGroups
            if (node_type.startswith("Stmt_") or 
                node_type == "Param" or
                node_type.startswith("Expr_Closure") or
                node_type.startswith("Expr_ArrowFunction")):
                result["attrGroups"] = []
        
        return result
