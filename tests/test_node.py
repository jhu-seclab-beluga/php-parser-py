"""Unit tests for Node class."""

import pytest
from cpg2py import Storage

from php_parser_py._node import Node


class TestNode:
    """Test suite for Node class."""

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

    def test_relative_path_for_file_node(self):
        """Test relative_path property for File node."""
        storage = Storage()
        storage.add_node("file_abc123")
        storage.set_node_props(
            "file_abc123",
            {
                "nodeType": "File",
                "relativePath": "src/index.php",
                "absolutePath": "/home/user/project/src/index.php",
            },
        )
        node = Node(storage, "file_abc123")
        assert node.relative_path == "src/index.php"

    def test_absolute_path_for_file_node(self):
        """Test absolute_path property for File node."""
        storage = Storage()
        storage.add_node("file_abc123")
        storage.set_node_props(
            "file_abc123",
            {
                "nodeType": "File",
                "relativePath": "src/index.php",
                "absolutePath": "/home/user/project/src/index.php",
            },
        )
        node = Node(storage, "file_abc123")
        assert node.absolute_path == "/home/user/project/src/index.php"

    def test_relative_path_for_project_node(self):
        """Test relative_path property for Project node."""
        storage = Storage()
        storage.add_node("project")
        storage.set_node_props(
            "project",
            {
                "nodeType": "Project",
                "absolutePath": "/home/user/project",
                "startLine": -1,
                "endLine": -1,
            },
        )
        node = Node(storage, "project")
        # Project nodes may not have relativePath
        assert node.relative_path is None

    def test_absolute_path_for_project_node(self):
        """Test absolute_path property for Project node."""
        storage = Storage()
        storage.add_node("project")
        storage.set_node_props(
            "project",
            {
                "nodeType": "Project",
                "absolutePath": "/home/user/project",
                "startLine": -1,
                "endLine": -1,
            },
        )
        node = Node(storage, "project")
        assert node.absolute_path == "/home/user/project"

    def test_relative_path_for_child_node_via_prefix(self):
        """Test relative_path for a statement node using ID prefix convention."""
        storage = Storage()
        # Create a file node
        storage.add_node("file_abc123")
        storage.set_node_props(
            "file_abc123",
            {
                "nodeType": "File",
                "relativePath": "test.php",
                "absolutePath": "/home/user/test.php",
            },
        )
        # Create a statement node with file hash prefix
        storage.add_node("file_abc123_1")
        storage.set_node_props(
            "file_abc123_1",
            {"nodeType": "Stmt_Function", "startLine": 5, "endLine": 10},
        )

        node = Node(storage, "file_abc123_1")
        assert node.relative_path == "test.php"
        assert node.absolute_path == "/home/user/test.php"

    def test_path_properties_return_none_for_node_without_file_prefix(self):
        """Test that path properties return None for nodes without ID prefix convention."""
        storage = Storage()
        # Create a node without the file_hash_N pattern
        storage.add_node("orphan_node")
        storage.set_node_props("orphan_node", {"nodeType": "Stmt_Function"})

        node = Node(storage, "orphan_node")
        # Should return None because node ID doesn't follow prefix convention
        assert node.relative_path is None
        assert node.absolute_path is None

    def test_path_properties_return_none_for_orphan_node(self):
        """Test that path properties return None for nodes without file context."""
        storage = Storage()
        storage.add_node("orphan")
        storage.set_node_props("orphan", {"nodeType": "Stmt_Function"})

        node = Node(storage, "orphan")
        assert node.relative_path is None
        assert node.absolute_path is None
