"""Unit tests for Parser class."""

import pytest

from php_parser_py import Parser, ParseError
from php_parser_py._ast import AST


class TestParser:
    """Test suite for Parser class."""

    def test_parser_initialization(self):
        """Test Parser can be initialized."""
        parser = Parser()
        assert parser is not None

    def test_parse_simple_code(self, simple_php_code):
        """Test parsing simple PHP code."""
        parser = Parser()
        ast = parser.parse(simple_php_code)
        assert isinstance(ast, AST)
        assert len(list(ast.nodes())) > 0

    def test_parse_function(self, function_php_code):
        """Test parsing PHP function."""
        parser = Parser()
        ast = parser.parse(function_php_code)
        
        # Find function nodes
        functions = list(ast.nodes(lambda n: n.node_type == "Stmt_Function"))
        assert len(functions) == 1
        
        func = functions[0]
        assert func.node_type == "Stmt_Function"

    def test_parse_class(self, class_php_code):
        """Test parsing PHP class."""
        parser = Parser()
        ast = parser.parse(class_php_code)
        
        # Find class nodes
        classes = list(ast.nodes(lambda n: n.node_type == "Stmt_Class"))
        assert len(classes) == 1
        
        cls = classes[0]
        assert cls.node_type == "Stmt_Class"

    def test_parse_complex_code(self, complex_php_code):
        """Test parsing complex PHP code."""
        parser = Parser()
        ast = parser.parse(complex_php_code)
        
        # Should have namespace, use, and class
        namespaces = list(ast.nodes(lambda n: n.node_type == "Stmt_Namespace"))
        classes = list(ast.nodes(lambda n: n.node_type == "Stmt_Class"))
        
        assert len(namespaces) >= 1
        assert len(classes) >= 1

    def test_parse_invalid_code(self):
        """Test parsing invalid PHP code raises ParseError."""
        from php_parser_py.exceptions import ParseError

        invalid_php_code = "<?php function test("
        parser = Parser()

        with pytest.raises(ParseError) as exc_info:
            parser.parse(invalid_php_code)

        assert "Syntax error" in str(exc_info.value)

    def test_parse_empty_code(self):
        """Test parsing empty code."""
        parser = Parser()
        ast = parser.parse("<?php")
        assert isinstance(ast, AST)

    def test_node_attributes(self, function_php_code):
        """Test that parsed nodes have correct attributes."""
        parser = Parser()
        ast = parser.parse(function_php_code)
        
        func = ast.first_node(lambda n: n.node_type == "Stmt_Function")
        assert func is not None
        assert func.node_type == "Stmt_Function"
        assert func.start_line == 2
        # Note: 'name' is in a child Identifier node, not in the function node itself
        assert "byRef" in func
        assert func["byRef"] is False

    def test_parse_file_not_found(self):
        """Test parse_file with non-existent file."""
        parser = Parser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/file.php")
