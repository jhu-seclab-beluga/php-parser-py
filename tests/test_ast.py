"""Unit tests for AST class."""

import sys
from pathlib import Path

import pytest

# Add tests directory to path to import conftest
sys.path.insert(0, str(Path(__file__).parent))

from conftest import parse_code_to_ast  # noqa: E402

from php_parser_py._ast import AST


class TestAST:
    """Test suite for AST class."""

    def test_ast_initialization(self, simple_php_code):
        """Test AST can be created from parser."""
        ast = parse_code_to_ast(simple_php_code)
        assert isinstance(ast, AST)

    def test_nodes_method(self, function_php_code):
        """Test nodes() method returns all nodes."""
        ast = parse_code_to_ast(function_php_code)

        nodes = list(ast.nodes())
        assert len(nodes) > 0
        assert all(hasattr(n, "node_type") for n in nodes)

    def test_nodes_with_predicate(self, function_php_code):
        """Test nodes() with predicate filter."""
        ast = parse_code_to_ast(function_php_code)

        # Find only function nodes
        functions = list(ast.nodes(lambda n: n.node_type == "Stmt_Function"))
        assert len(functions) == 1
        assert functions[0].node_type == "Stmt_Function"

    def test_first_node(self, function_php_code):
        """Test first_node() method."""
        ast = parse_code_to_ast(function_php_code)

        func = ast.first_node(lambda n: n.node_type == "Stmt_Function")
        assert func is not None
        assert func.node_type == "Stmt_Function"

    def test_first_node_not_found(self, simple_php_code):
        """Test first_node() returns None when not found."""
        ast = parse_code_to_ast(simple_php_code)

        result = ast.first_node(lambda n: n.node_type == "Stmt_Class")
        assert result is None

    def test_to_json(self, simple_php_code):
        """Test JSON reconstruction."""
        import json

        ast = parse_code_to_ast(simple_php_code)
        json_str = ast.to_json()
        assert isinstance(json_str, str)

        # Parse the JSON string
        json_data = json.loads(json_str)
        assert isinstance(json_data, list)
        assert len(json_data) > 0
        assert json_data[0]["nodeType"] == "Stmt_Echo"

    def test_node_count(self, class_php_code):
        """Test counting different node types."""
        ast = parse_code_to_ast(class_php_code)

        all_nodes = list(ast.nodes())
        classes = list(ast.nodes(lambda n: n.node_type == "Stmt_Class"))
        methods = list(ast.nodes(lambda n: n.node_type == "Stmt_ClassMethod"))

        assert len(all_nodes) > len(classes)
        assert len(classes) == 1
        assert len(methods) >= 1

    def test_traversal(self, function_php_code):
        """Test AST traversal finds nested nodes."""
        ast = parse_code_to_ast(function_php_code)

        # Should find echo statement inside function
        echos = list(ast.nodes(lambda n: n.node_type == "Stmt_Echo"))
        assert len(echos) >= 1

    def test_project_node_properties(self, tmp_path):
        """Test project node has path property."""
        import os
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
            f.write("<?php function test() {}")
            temp_file = f.name

        try:
            from php_parser_py import Parser

            parser = Parser()
            ast = parser.parse_file(temp_file)

            project = ast.project_node
            assert project is not None
            assert project.get_property("nodeType") == "Project"
            assert project.get_property("path") is not None
        finally:
            os.unlink(temp_file)

    def test_files_method(self, tmp_path):
        """Test files() method returns file nodes."""
        import os
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
            f.write("<?php function test() {}")
            temp_file = f.name

        try:
            from php_parser_py import Parser

            parser = Parser()
            ast = parser.parse_file(temp_file)

            files = ast.files()
            assert len(files) == 1

            file_node = files[0]
            assert file_node.get_property("nodeType") == "File"
            assert file_node.get_property("path") is not None
            assert file_node.get_property("filePath") is not None
        finally:
            os.unlink(temp_file)

    def test_get_file_method(self, tmp_path):
        """Test get_file() method."""
        import os
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
            f.write("<?php function test() {}")
            temp_file = f.name

        try:
            from php_parser_py import Parser

            parser = Parser()
            ast = parser.parse_file(temp_file)

            # Get a statement node
            func_node = ast.first_node(lambda n: n.node_type == "Stmt_Function")
            assert func_node is not None

            # Get file containing this node
            file_node = ast.get_file(func_node.id)
            assert file_node is not None
            assert file_node.get_property("nodeType") == "File"

            # Project node should return None
            project_file = ast.get_file("project")
            assert project_file is None
        finally:
            os.unlink(temp_file)
