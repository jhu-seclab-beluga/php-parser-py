"""Unit tests for Modifier class."""

import pytest
from cpg2py import Storage

from php_parser_py import Modifier
from php_parser_py._ast import AST


@pytest.fixture
def ast_with_modifier():
    """Create an AST with one node and wrap in Modifier."""
    storage = Storage()
    storage.add_node("root")
    storage.set_node_props("root", {"nodeType": "Project"})
    ast = AST(storage, root_node_id="root")
    return ast, Modifier(ast)


class TestModifierAddNode:
    """Tests for Modifier.add_node."""

    def test_add_node_creates_node(self, ast_with_modifier):
        """Test add_node creates a node visible via AST query."""
        ast, modifier = ast_with_modifier
        node = modifier.add_node("n1", "Stmt_Echo", value="hello")
        assert node.id == "n1"
        assert node.node_type == "Stmt_Echo"
        assert node.get("value") == "hello"
        assert ast.node("n1").node_type == "Stmt_Echo"

    def test_add_node_duplicate_raises_value_error(self, ast_with_modifier):
        """Test add_node raises ValueError for existing node ID."""
        _, modifier = ast_with_modifier
        modifier.add_node("n1", "Stmt_Echo")
        with pytest.raises(ValueError, match="already exists"):
            modifier.add_node("n1", "Stmt_Return")


class TestModifierRemoveNode:
    """Tests for Modifier.remove_node."""

    def test_remove_node_removes_from_graph(self, ast_with_modifier):
        """Test remove_node makes node inaccessible via AST."""
        ast, modifier = ast_with_modifier
        modifier.add_node("n1", "Stmt_Echo")
        modifier.remove_node("n1")
        with pytest.raises(KeyError):
            ast.node("n1")

    def test_remove_node_missing_raises_key_error(self, ast_with_modifier):
        """Test remove_node raises KeyError for non-existent node."""
        _, modifier = ast_with_modifier
        with pytest.raises(KeyError, match="not found"):
            modifier.remove_node("nonexistent")

    def test_remove_node_also_removes_edges(self, ast_with_modifier):
        """Test remove_node removes all connected edges."""
        ast, modifier = ast_with_modifier
        modifier.add_node("child", "Stmt_Return")
        modifier.add_edge("root", "child", field="stmts", index=0)
        modifier.remove_node("child")
        with pytest.raises(KeyError):
            ast.node("child")
        with pytest.raises(KeyError):
            ast.edge("root", "child", "PARENT_OF")


class TestModifierAddEdge:
    """Tests for Modifier.add_edge."""

    def test_add_edge_creates_edge(self, ast_with_modifier):
        """Test add_edge creates an edge visible via AST query."""
        ast, modifier = ast_with_modifier
        modifier.add_node("child", "Stmt_Echo")
        edge = modifier.add_edge("root", "child", field="stmts", index=0)
        assert edge.type == "PARENT_OF"
        assert edge.get("field") == "stmts"
        assert edge.get("index") == 0
        children = list(ast.succ(ast.node("root")))
        assert len(children) == 1
        assert children[0].id == "child"

    def test_add_edge_missing_source_raises_key_error(self, ast_with_modifier):
        """Test add_edge raises KeyError if source node missing."""
        _, modifier = ast_with_modifier
        modifier.add_node("child", "Stmt_Echo")
        with pytest.raises(KeyError, match="Source node not found"):
            modifier.add_edge("nonexistent", "child")

    def test_add_edge_missing_target_raises_key_error(self, ast_with_modifier):
        """Test add_edge raises KeyError if target node missing."""
        _, modifier = ast_with_modifier
        with pytest.raises(KeyError, match="Target node not found"):
            modifier.add_edge("root", "nonexistent")

    def test_add_edge_duplicate_raises_value_error(self, ast_with_modifier):
        """Test add_edge raises ValueError for existing edge."""
        _, modifier = ast_with_modifier
        modifier.add_node("child", "Stmt_Echo")
        modifier.add_edge("root", "child")
        with pytest.raises(ValueError, match="already exists"):
            modifier.add_edge("root", "child")


class TestModifierRemoveEdge:
    """Tests for Modifier.remove_edge."""

    def test_remove_edge_removes_from_graph(self, ast_with_modifier):
        """Test remove_edge makes edge inaccessible."""
        ast, modifier = ast_with_modifier
        modifier.add_node("child", "Stmt_Echo")
        modifier.add_edge("root", "child")
        modifier.remove_edge("root", "child")
        assert list(ast.succ(ast.node("root"))) == []

    def test_remove_edge_missing_raises_key_error(self, ast_with_modifier):
        """Test remove_edge raises KeyError for non-existent edge."""
        _, modifier = ast_with_modifier
        with pytest.raises(KeyError, match="not found"):
            modifier.remove_edge("root", "nonexistent")


class TestModifierAstProperty:
    """Tests for Modifier.ast property."""

    def test_ast_returns_wrapped_ast(self, ast_with_modifier):
        """Test ast property returns the AST passed to constructor."""
        ast, modifier = ast_with_modifier
        assert modifier.ast is ast
