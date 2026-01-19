"""Unit tests for AST class."""

import pytest

from php_parser_py import Parser
from php_parser_py._ast import AST


class TestAST:
    """Test suite for AST class."""

    def test_ast_initialization(self, simple_php_code):
        """Test AST can be created from parser."""
        parser = Parser()
        ast = parser.parse(simple_php_code)
        assert isinstance(ast, AST)

    def test_nodes_method(self, function_php_code):
        """Test nodes() method returns all nodes."""
        parser = Parser()
        ast = parser.parse(function_php_code)
        
        nodes = list(ast.nodes())
        assert len(nodes) > 0
        assert all(hasattr(n, "node_type") for n in nodes)

    def test_nodes_with_predicate(self, function_php_code):
        """Test nodes() with predicate filter."""
        parser = Parser()
        ast = parser.parse(function_php_code)
        
        # Find only function nodes
        functions = list(ast.nodes(lambda n: n.node_type == "Stmt_Function"))
        assert len(functions) == 1
        assert functions[0].node_type == "Stmt_Function"

    def test_first_node(self, function_php_code):
        """Test first_node() method."""
        parser = Parser()
        ast = parser.parse(function_php_code)
        
        func = ast.first_node(lambda n: n.node_type == "Stmt_Function")
        assert func is not None
        assert func.node_type == "Stmt_Function"

    def test_first_node_not_found(self, simple_php_code):
        """Test first_node() returns None when not found."""
        parser = Parser()
        ast = parser.parse(simple_php_code)
        
        result = ast.first_node(lambda n: n.node_type == "Stmt_Class")
        assert result is None

    def test_to_json(self, simple_php_code):
        """Test JSON reconstruction."""
        import json

        parser = Parser()
        ast = parser.parse(simple_php_code)
        json_str = ast.to_json()
        assert isinstance(json_str, str)
        
        # Parse the JSON string
        json_data = json.loads(json_str)
        assert isinstance(json_data, list)
        assert len(json_data) > 0
        assert json_data[0]["nodeType"] == "Stmt_Echo"

    def test_node_count(self, class_php_code):
        """Test counting different node types."""
        parser = Parser()
        ast = parser.parse(class_php_code)
        
        all_nodes = list(ast.nodes())
        classes = list(ast.nodes(lambda n: n.node_type == "Stmt_Class"))
        methods = list(ast.nodes(lambda n: n.node_type == "Stmt_ClassMethod"))
        
        assert len(all_nodes) > len(classes)
        assert len(classes) == 1
        assert len(methods) >= 1

    def test_traversal(self, function_php_code):
        """Test AST traversal finds nested nodes."""
        parser = Parser()
        ast = parser.parse(function_php_code)
        
        # Should find echo statement inside function
        echos = list(ast.nodes(lambda n: n.node_type == "Stmt_Echo"))
        assert len(echos) >= 1
