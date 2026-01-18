"""Unit tests for Node class."""

import pytest
from cpg2py import Storage

from php_parser_py._node import Node


class TestNode:
    """Test suite for Node class."""

    @pytest.fixture
    def storage_with_node(self):
        """Create storage with a test node."""
        storage = Storage()
        storage.add_node(
            "test_node_1",
            {
                "nodeType": "Stmt_Function",
                "name": "testFunction",
                "byRef": False,
                "startLine": 10,
                "endLine": 20,
                "startFilePos": 100,
                "endFilePos": 200,
                "startTokenPos": 5,
                "endTokenPos": 15,
                "comments": ["// test comment"],
            },
        )
        return storage

    def test_node_initialization(self, storage_with_node):
        """Test Node initialization."""
        node = Node(storage_with_node, "test_node_1")
        assert node.id == "test_node_1"

    def test_node_type_property(self, storage_with_node):
        """Test node_type property."""
        node = Node(storage_with_node, "test_node_1")
        assert node.node_type == "Stmt_Function"

    def test_all_properties(self, storage_with_node):
        """Test all_properties returns complete dict."""
        node = Node(storage_with_node, "test_node_1")
        props = node.all_properties
        assert isinstance(props, dict)
        assert "nodeType" in props
        assert "name" in props
        assert props["nodeType"] == "Stmt_Function"

    def test_dict_like_access(self, storage_with_node):
        """Test dict-like access with __getitem__."""
        node = Node(storage_with_node, "test_node_1")
        assert node["nodeType"] == "Stmt_Function"
        assert node["name"] == "testFunction"
        assert node["byRef"] is False

    def test_dict_like_access_keyerror(self, storage_with_node):
        """Test __getitem__ raises KeyError for missing keys."""
        node = Node(storage_with_node, "test_node_1")
        with pytest.raises(KeyError):
            _ = node["nonexistent"]

    def test_contains_operator(self, storage_with_node):
        """Test 'in' operator."""
        node = Node(storage_with_node, "test_node_1")
        assert "nodeType" in node
        assert "name" in node
        assert "nonexistent" not in node

    def test_get_method(self, storage_with_node):
        """Test get() method with default."""
        node = Node(storage_with_node, "test_node_1")
        assert node.get("name") == "testFunction"
        assert node.get("nonexistent", "default") == "default"
        assert node.get("nonexistent") is None

    def test_start_line_property(self, storage_with_node):
        """Test start_line property."""
        node = Node(storage_with_node, "test_node_1")
        assert node.start_line == 10

    def test_end_line_property(self, storage_with_node):
        """Test end_line property."""
        node = Node(storage_with_node, "test_node_1")
        assert node.end_line == 20

    def test_start_file_pos_property(self, storage_with_node):
        """Test start_file_pos property."""
        node = Node(storage_with_node, "test_node_1")
        assert node.start_file_pos == 100

    def test_end_file_pos_property(self, storage_with_node):
        """Test end_file_pos property."""
        node = Node(storage_with_node, "test_node_1")
        assert node.end_file_pos == 200

    def test_start_token_pos_property(self, storage_with_node):
        """Test start_token_pos property."""
        node = Node(storage_with_node, "test_node_1")
        assert node.start_token_pos == 5

    def test_end_token_pos_property(self, storage_with_node):
        """Test end_token_pos property."""
        node = Node(storage_with_node, "test_node_1")
        assert node.end_token_pos == 15

    def test_comments_property(self, storage_with_node):
        """Test comments property."""
        node = Node(storage_with_node, "test_node_1")
        assert node.comments == ["// test comment"]

    def test_has_attribute(self, storage_with_node):
        """Test has_attribute() method."""
        node = Node(storage_with_node, "test_node_1")
        assert node.has_attribute("name") is True
        assert node.has_attribute("nonexistent") is False

    def test_get_attribute(self, storage_with_node):
        """Test get_attribute() method."""
        node = Node(storage_with_node, "test_node_1")
        assert node.get_attribute("name") == "testFunction"
        assert node.get_attribute("nonexistent", "default") == "default"
