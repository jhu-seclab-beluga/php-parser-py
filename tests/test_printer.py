"""Unit tests for PrettyPrinter class."""

import pytest

from php_parser_py import Parser, PrettyPrinter


class TestPrettyPrinter:
    """Test suite for PrettyPrinter class."""

    def test_printer_initialization(self):
        """Test PrettyPrinter can be initialized."""
        printer = PrettyPrinter()
        assert printer is not None

    def test_print_simple_code(self, simple_php_code):
        """Test printing simple PHP code."""
        parser = Parser()
        printer = PrettyPrinter()
        
        ast = parser.parse(simple_php_code)
        generated = printer.print(ast)
        
        assert isinstance(generated, dict)
        assert len(generated) > 0
        # Get first (and likely only) file's code
        code = list(generated.values())[0]
        assert "<?php" in code
        assert "echo" in code

    def test_print_function(self, function_php_code):
        """Test printing PHP function."""
        parser = Parser()
        printer = PrettyPrinter()
        
        ast = parser.parse(function_php_code)
        generated = printer.print(ast)
        
        assert isinstance(generated, dict)
        code = list(generated.values())[0]
        assert "function" in code
        assert "greet" in code
        assert "echo" in code

    def test_print_class(self, class_php_code):
        """Test printing PHP class."""
        parser = Parser()
        printer = PrettyPrinter()
        
        ast = parser.parse(class_php_code)
        generated = printer.print(ast)
        
        assert isinstance(generated, dict)
        code = list(generated.values())[0]
        assert "class" in code
        assert "User" in code
        assert "__construct" in code

    def test_roundtrip_simple(self, simple_php_code):
        """Test round-trip: parse → print → parse."""
        parser = Parser()
        printer = PrettyPrinter()
        
        # First parse
        ast1 = parser.parse(simple_php_code)
        generated = printer.print(ast1)
        
        # Get code from dict
        code = list(generated.values())[0]
        
        # Second parse
        ast2 = parser.parse(code)
        
        # Should have same number of nodes
        nodes1 = list(ast1.nodes())
        nodes2 = list(ast2.nodes())
        assert len(nodes1) == len(nodes2)

    def test_roundtrip_function(self, function_php_code):
        """Test round-trip with function."""
        parser = Parser()
        printer = PrettyPrinter()
        
        ast1 = parser.parse(function_php_code)
        generated = printer.print(ast1)
        code = list(generated.values())[0]
        ast2 = parser.parse(code)
        
        # Should have same function
        funcs1 = list(ast1.nodes(lambda n: n.node_type == "Stmt_Function"))
        funcs2 = list(ast2.nodes(lambda n: n.node_type == "Stmt_Function"))
        assert len(funcs1) == len(funcs2) == 1

    def test_roundtrip_class(self, class_php_code):
        """Test round-trip with class."""
        parser = Parser()
        printer = PrettyPrinter()
        
        ast1 = parser.parse(class_php_code)
        generated = printer.print(ast1)
        code = list(generated.values())[0]
        ast2 = parser.parse(code)
        
        # Should have same class
        classes1 = list(ast1.nodes(lambda n: n.node_type == "Stmt_Class"))
        classes2 = list(ast2.nodes(lambda n: n.node_type == "Stmt_Class"))
        assert len(classes1) == len(classes2) == 1
