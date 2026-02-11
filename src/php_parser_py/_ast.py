"""AST representation for PHP code using cpg2py's graph framework."""

from __future__ import annotations

import json
import logging
from typing import Any

from cpg2py import AbcGraphQuerier, Storage

from php_parser_py._edge import Edge
from php_parser_py._exceptions import NodeNotInFileError
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
    and AST merging capabilities. Uses cpg2py graph API (nodes, edges, succ,
    prev, ancestors, descendants); storage is only used where the graph API
    does not provide an alternative (node/edge existence and Node/Edge construction).

    Attributes:
        _root_node_id: ID of the root project node (always "project").
    """

    def __init__(self, storage: Storage, root_node_id: str = "project") -> None:
        """Initialize AST with populated storage.

        Args:
            storage: cpg2py Storage containing AST nodes and edges.
            root_node_id: ID of the root node. Defaults to "project".
        """
        super().__init__(storage)
        self._root_node_id = root_node_id

    def node(self, whose_id_is: str) -> Node:
        """Return node wrapper by ID.

        Args:
            whose_id_is: Node ID string.

        Returns:
            Node instance for the given ID.

        Raises:
            KeyError: If the node ID is not in the graph.
        """
        if not self.storage.contains_node(whose_id_is):
            raise KeyError(f"Node not found: {whose_id_is!r}")
        return Node(self.storage, whose_id_is)

    def edge(self, fid: str, tid: str, eid: str) -> Edge:
        """Return edge wrapper by IDs.

        Args:
            fid: From node ID.
            tid: To node ID.
            eid: Edge type.

        Returns:
            Edge instance for the given (from, to, type).

        Raises:
            KeyError: If the edge is not in the graph.
        """
        edge_id = (fid, tid, eid)
        if not self.storage.contains_edge(edge_id):
            raise KeyError(f"Edge not found: {edge_id!r}")
        return Edge(self.storage, fid, tid, eid)

    def project_node(self) -> Node:
        """Return the project node (root of the AST).

        The project node has ID "project" and is always present when the AST
        was created by parse_file or parse_project.

        Returns:
            Project Node instance.

        Raises:
            KeyError: If the root node is not in the graph.
        """
        if not self.storage.contains_node(self._root_node_id):
            raise KeyError(f"Project node not found: {self._root_node_id!r}")
        return Node(self.storage, self._root_node_id)

    def file_nodes(self) -> list[Node]:
        """Return all file nodes in the project.

        Returns:
            List of File Node instances.
        """
        try:
            project = self.project_node()
        except KeyError:
            return []

        file_nodes = [n for n in self.succ(project) if n.node_type == "File"]
        return sorted(file_nodes, key=lambda n: n.get("filePath", ""))

    def get_file_node(self, node_id: str) -> Node:
        """Get the file node that contains the given node.

        Uses the AST ID convention: file node ID is the file hash (e.g. 8-char hex);
        nodes inside that file have ID ``file_hash + "_" + increment`` (e.g. ``a1b2c3d4_1``).
        Resolves by structure first, then falls back to ancestors() traversal.

        Args:
            node_id: ID of any node in the AST.

        Returns:
            File Node instance containing the given node.

        Raises:
            KeyError: If the node ID is not in the graph.
            NodeNotInFileError: If the node is not under any file (e.g. project node).
        """
        node = self.node(node_id)
        if node.node_type == "File":
            return node

        if node_id == self._root_node_id:
            raise NodeNotInFileError(node_id, "Project node has no containing file.")

        result = self._try_file_by_id_prefix(node_id)
        if result is not None:
            return result

        return self._find_file_ancestor(node)

    def _try_file_by_id_prefix(self, node_id: str) -> Node | None:
        """Try to find file node by ID prefix convention.

        If node_id is like "hash_123", attempts to get file node with ID "hash".
        Returns None if ID doesn't match convention or file not found.
        """
        if "_" not in node_id:
            return None

        prefix, rest = node_id.split("_", 1)
        if not rest.isdigit():
            return None

        try:
            candidate = self.node(prefix)
            if candidate.node_type == "File":
                return candidate
        except KeyError:
            pass

        return None

    def _find_file_ancestor(self, node: Node) -> Node:
        """Find first File ancestor of a node via traversal.

        Raises NodeNotInFileError if no File ancestor exists.
        """
        for ancestor in self.ancestors(node):
            if ancestor.node_type == "File":
                result: Node = ancestor
                return result

        raise NodeNotInFileError(node.id, "No File node among ancestors.")

    def to_json(self, file_hash: str | None = None) -> str:
        """Reconstruct PHP-Parser JSON from Storage for code generation.

        If file_hash is provided, exports only that file's statements.
        Otherwise, exports all statements from all files, or root nodes if no file structure exists.

        Args:
            file_hash: Optional file hash to export only that file.

        Returns:
            JSON string compatible with PHP-Parser's JsonDecoder.
        """
        if file_hash:
            # Export single file (node() raises KeyError if file_hash not in graph)
            self.node(file_hash)
            top_level_nodes = self._get_file_statements(file_hash)
        else:
            # Try to export from file structure first
            file_nodes = self.file_nodes()
            if file_nodes:
                # Export all files (flattened)
                top_level_nodes = []
                for file_node in file_nodes:
                    top_level_nodes.extend(self._get_file_statements(file_node.id))
            else:
                # No file structure - find root nodes via graph API (no incoming PARENT_OF)
                all_nodes = {n.id for n in self.nodes()}
                nodes_with_parents = {
                    e.to_nid for e in self.edges() if e.type == "PARENT_OF"
                }
                root_nodes = all_nodes - nodes_with_parents
                root_nodes.discard(self._root_node_id)
                top_level_nodes = sorted(root_nodes)

        result = [self._reconstruct_node(nid) for nid in top_level_nodes]
        return json.dumps(result)

    def _get_file_statements(self, file_hash: str) -> list[str]:
        """Get top-level statement node IDs for a file (direct children with edge field \"stmts\").

        Uses succ() traversal; statement IDs follow the convention file_hash_1, file_hash_2, ...
        """
        file_node = self.node(file_hash)
        stmts_with_index = []
        for child in self.succ(file_node):
            edge = self.edge(file_hash, child.id, "PARENT_OF")
            if edge.get("field") == "stmts":
                idx = edge.get("index")
                stmts_with_index.append((999999 if idx is None else idx, child.id))
        stmts_with_index.sort(key=lambda t: t[0])
        return [nid for _, nid in stmts_with_index]

    def _reconstruct_node(self, nid: str) -> dict[str, Any]:
        """Recursively reconstruct JSON object for a node.

        Args:
            nid: Node ID to reconstruct.

        Returns:
            Dictionary representing the node in PHP-Parser JSON format.
        """
        node = self.node(nid)
        props = node.all_properties
        result: dict[str, Any] = {"nodeType": node.node_type}

        attributes = self._extract_attributes(props)
        if attributes:
            result["attributes"] = attributes

        self._add_non_attribute_props(result, props)
        self._reconstruct_child_fields(result, nid)
        self._add_default_attrs(result, node.node_type)

        return result

    def _extract_attributes(self, props: dict[str, Any]) -> dict[str, Any]:
        """Extract metadata attributes from node properties.

        Returns dict with position and comment metadata.
        """
        attr_keys = {
            "startLine",
            "endLine",
            "startFilePos",
            "endFilePos",
            "startTokenPos",
            "endTokenPos",
            "kind",
            "comments",
        }
        return {k: v for k, v in props.items() if k in attr_keys}

    def _add_non_attribute_props(
        self, result: dict[str, Any], props: dict[str, Any]
    ) -> None:
        """Add non-attribute, non-nodeType properties to result."""
        attr_keys = {
            "nodeType",
            "startLine",
            "endLine",
            "startFilePos",
            "endFilePos",
            "startTokenPos",
            "endTokenPos",
            "kind",
            "comments",
        }
        for key, value in props.items():
            if key not in attr_keys:
                result[key] = value

    def _reconstruct_child_fields(self, result: dict[str, Any], nid: str) -> None:
        """Reconstruct and add child fields to result.

        Child nodes are fetched via succ() and indexed by edge properties.
        """
        node = self.node(nid)
        child_fields: dict[str, dict[int, Any]] = {}

        for child in self.succ(node):
            try:
                edge = self.edge(nid, child.id, "PARENT_OF")
            except KeyError:
                continue

            field_name = edge.get("field")
            if field_name is None:
                continue

            child_json = self._reconstruct_node(child.id)
            index = edge.get("index")

            if field_name not in child_fields:
                child_fields[field_name] = {}

            if index is not None:
                child_fields[field_name][index] = child_json
            else:
                result[field_name] = child_json

        for field_name, indexed_children in child_fields.items():
            if indexed_children:
                max_index = max(indexed_children.keys())
                array = [None] * (max_index + 1)
                for idx, child in indexed_children.items():
                    array[idx] = child
                result[field_name] = array

    def _add_default_attrs(self, result: dict[str, Any], node_type: str) -> None:
        """Add default attrGroups if not already present.

        PHP-Parser expects attrGroups on certain node types.
        """
        if "attrGroups" in result:
            return

        if any(
            node_type.startswith(prefix)
            for prefix in ("Stmt_", "Expr_Closure", "Expr_ArrowFunction")
        ) or node_type == "Param":
            result["attrGroups"] = []
