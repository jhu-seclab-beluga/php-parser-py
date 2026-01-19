"""Unit tests for Edge class."""

import pytest
from cpg2py import Storage

from php_parser_py._edge import Edge


class TestEdge:
    """Test suite for Edge class."""

    @pytest.fixture
    def storage_with_edge(self):
        """Create a storage with test nodes and an edge."""
        from cpg2py import Storage

        storage = Storage()
        storage.add_node("node1")
        storage.set_node_props("node1", {"nodeType": "Stmt_Echo"})
        storage.add_node("node2")
        storage.set_node_props("node2", {"nodeType": "Stmt_Return"})
        storage.add_edge(("node1", "node2", "PARENT_OF"))
        storage.set_edge_props(("node1", "node2", "PARENT_OF"), {"field": "stmts", "index": 0})
        return storage

    def test_edge_initialization(self, storage_with_edge):
        """Test Edge initialization."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        assert edge.edge_type == "PARENT_OF"

    def test_edge_type_property(self, storage_with_edge):
        """Test type property."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        assert edge.edge_type == "PARENT_OF"

    def test_edge_field_property(self, storage_with_edge):
        """Test field property."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        assert edge.field == "stmts"

    def test_edge_index_property(self, storage_with_edge):
        """Test index property."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        assert edge.index == 0

    def test_all_properties(self, storage_with_edge):
        """Test all_properties returns complete dict."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        props = edge.all_properties
        assert isinstance(props, dict)
        assert "field" in props
        assert "index" in props
        assert props["field"] == "stmts"
        assert props["index"] == 0

    def test_dict_like_access(self, storage_with_edge):
        """Test dict-like access with __getitem__."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        assert edge["field"] == "stmts"
        assert edge["index"] == 0

    def test_dict_like_access_keyerror(self, storage_with_edge):
        """Test __getitem__ raises KeyError for missing keys."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        with pytest.raises(KeyError):
            _ = edge["nonexistent"]

    def test_contains_operator(self, storage_with_edge):
        """Test 'in' operator."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        assert "field" in edge
        assert "index" in edge
        assert "nonexistent" not in edge

    def test_get_method(self, storage_with_edge):
        """Test get() method with default."""
        edge = Edge(storage_with_edge, "node1", "node2", "PARENT_OF")
        assert edge.get("field") == "stmts"
        assert edge.get("nonexistent", "default") == "default"
        assert edge.get("nonexistent") is None

    def test_edge_without_properties(self):
        """Test edge creation without properties."""
        from cpg2py import Storage

        from php_parser_py._edge import Edge

        storage = Storage()
        storage.add_node("node1")
        storage.set_node_props("node1", {"nodeType": "Stmt_Echo"})
        storage.add_node("node2")
        storage.set_node_props("node2", {"nodeType": "Stmt_Return"})
        storage.add_edge(("node1", "node2", "PARENT_OF"))

        edge = Edge(storage, "node1", "node2", "PARENT_OF")
        assert edge.from_nid == "node1"
        assert edge.to_nid == "node2"
        assert edge.edge_type == "PARENT_OF"
        assert edge.field is None
        assert edge.index is None
        assert edge.all_properties == {}
