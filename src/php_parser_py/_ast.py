"""AST representation for PHP code using cpg2py's graph framework."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from cpg2py import AbcGraphQuerier, Storage

from php_parser_py._edge import Edge
from php_parser_py._node import Node

logger = logging.getLogger(__name__)


class AST(AbcGraphQuerier[Node, Edge]):
    """Represents a PHP Abstract Syntax Tree.

    This class extends cpg2py's AbcGraphQuerier with generic type parameters
    specifying that it works with Node and Edge types.

    The AST structure follows a hierarchy:
    - Project node (ID: "project") - root of the AST
    - File nodes (ID: hex hash) - children of project
    - Statement nodes (ID: {hex}_{counter}) - children of files

    Type Parameters:
        Node: The concrete node type for PHP AST nodes
        Edge: The concrete edge type for parent-child relationships

    Provides graph traversal methods, JSON reconstruction for code generation,
    and AST merging capabilities.

    Attributes:
        _storage: cpg2py Storage containing AST nodes and edges.
        _root_node_id: ID of the root project node (always "project").
    """

    def __init__(self, storage: Storage, root_node_id: str = "project") -> None:
        """Initialize AST with populated storage.

        Args:
            storage: cpg2py Storage containing AST nodes and edges.
            root_node_id: ID of the root node. Defaults to "project".
        """
        super().__init__(storage)
        self._storage = storage
        self._root_node_id = root_node_id

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

    @property
    def root_node(self) -> Optional[Node]:
        """Return the root project node of the AST.

        The root node is always the project node with ID "project".

        Returns:
            Root Node instance or None if root node doesn't exist.
        """
        if not self._storage.contains_node(self._root_node_id):
            return None
        return Node(self._storage, self._root_node_id)

    @property
    def project_node(self) -> Optional[Node]:
        """Return the project node (alias for root_node).

        Returns:
            Project Node instance or None if not found.
        """
        return self.root_node

    def files(self) -> list[Node]:
        """Return all file nodes in the project.

        Returns:
            List of File Node instances.
        """
        if not self.root_node:
            return []

        file_nodes = []
        for edge_id in self._storage.get_edges():
            from_id, to_id, edge_type = edge_id
            if from_id == self._root_node_id and edge_type == "PARENT_OF":
                file_node = self.node(to_id)
                if file_node and file_node.get_property("nodeType") == "File":
                    file_nodes.append(file_node)

        # Sort by file path for consistent ordering
        return sorted(file_nodes, key=lambda n: n.get_property("filePath", ""))

    def get_file(self, node_id: str) -> Optional[Node]:
        """Get the file node that contains the given node.

        Traverses upward from the given node via PARENT_OF edges until
        finding a File node. If the node itself is a File node, returns it.

        Args:
            node_id: ID of any node in the AST.

        Returns:
            File Node instance containing the given node, or None if:
            - Node ID doesn't exist
            - Node is the project node (project doesn't belong to a file)
            - Node is not under any file node
        """
        if not self._storage.contains_node(node_id):
            return None

        # Check if the node itself is a File node
        node = self.node(node_id)
        if node and node.get_property("nodeType") == "File":
            return node

        # Check if it's the project node
        if node_id == self._root_node_id:
            return None

        # Traverse upward via PARENT_OF edges to find File node
        current_id = node_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)

            # Find parent node via incoming PARENT_OF edge (each node has one parent)
            parent_id = None
            for edge_id in self._storage.get_edges():
                from_id, to_id, edge_type = edge_id
                if to_id == current_id and edge_type == "PARENT_OF":
                    parent_id = from_id
                    break

            if not parent_id:
                # No parent found, can't determine file
                return None

            # Check parent node
            parent_node = self.node(parent_id)
            if not parent_node:
                return None

            node_type = parent_node.get_property("nodeType")
            if node_type == "File":
                return parent_node
            elif node_type == "Project":
                # Reached project, no file found
                return None

            # Continue traversing upward
            current_id = parent_id

        return None

    def to_json(self, file_hash: Optional[str] = None) -> str:
        """Reconstruct PHP-Parser JSON from Storage for code generation.

        If file_hash is provided, exports only that file's statements.
        Otherwise, exports all statements from all files, or root nodes if no file structure exists.

        Args:
            file_hash: Optional file hash to export only that file.

        Returns:
            JSON string compatible with PHP-Parser's JsonDecoder.
        """
        if file_hash:
            # Export single file
            file_node = self.node(file_hash)
            if not file_node:
                return json.dumps([])
            top_level_nodes = self._get_file_statements(file_hash)
        else:
            # Try to export from file structure first
            file_nodes = self.files()
            if file_nodes:
                # Export all files (flattened)
                top_level_nodes = []
                for file_node in file_nodes:
                    top_level_nodes.extend(self._get_file_statements(file_node.id))
            else:
                # No file structure - find root nodes (nodes without incoming PARENT_OF edges)
                # Exclude project node if it exists
                all_nodes = set(self._storage.get_nodes())
                nodes_with_parents = set()

                for edge_id in self._storage.get_edges():
                    from_id, to_id, edge_type = edge_id
                    if edge_type == "PARENT_OF":
                        nodes_with_parents.add(to_id)

                root_nodes = all_nodes - nodes_with_parents
                # Exclude project node if present
                root_nodes.discard(self._root_node_id)
                top_level_nodes = sorted(list(root_nodes))

        result = [self._reconstruct_node(nid) for nid in top_level_nodes]
        return json.dumps(result)

    def _get_file_statements(self, file_hash: str) -> list[str]:
        """Get top-level statement nodes for a specific file.

        Args:
            file_hash: File node ID (hash).

        Returns:
            List of statement node IDs.
        """
        statement_nodes = []
        for edge_id in self._storage.get_edges():
            from_id, to_id, edge_type = edge_id
            if from_id == file_hash and edge_type == "PARENT_OF":
                edge_props = self._storage.get_edge_props(edge_id)
                if edge_props and edge_props.get("field") == "stmts":
                    statement_nodes.append(to_id)

        # Sort by edge index to preserve order
        def get_index(nid: str) -> int:
            edge_props = self._storage.get_edge_props((file_hash, nid, "PARENT_OF"))
            if edge_props:
                return edge_props.get("index", 999999)
            return 999999

        return sorted(statement_nodes, key=get_index)

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
                # All other fields go directly in result
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

            # Skip project/file structure edges when reconstructing
            if field_name in ("files", "stmts"):
                # Only include stmts edges for file nodes
                if field_name == "stmts":
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
            else:
                # Regular child field
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
        if node_type and ("attrGroups" not in result):
            if (node_type.startswith("Stmt_") or 
                node_type == "Param" or
                node_type.startswith("Expr_Closure") or
                node_type.startswith("Expr_ArrowFunction")):
                result["attrGroups"] = []
        
        return result
