"""Integration tests for php-parser-py."""

import sys
from pathlib import Path

import pytest

# Add tests directory to path to import conftest
sys.path.insert(0, str(Path(__file__).parent))

from conftest import parse_code_to_ast  # noqa: E402

from php_parser_py import Parser, PrettyPrinter, parse_file


@pytest.mark.integration
class TestIntegration:
    """Integration tests for complete workflows."""

    def test_parse_convenience_function(self, simple_php_code):
        """Test parsing code string into AST."""
        ast = parse_code_to_ast(simple_php_code)
        assert ast is not None
        assert len(list(ast.nodes())) > 0

    def test_full_workflow(self, function_php_code):
        """Test complete parse → query → modify → print workflow."""
        # Parse
        ast = parse_code_to_ast(function_php_code)

        # Query
        func = ast.first_node(lambda n: n.node_type == "Stmt_Function")
        assert func is not None

        # Check properties
        assert func.start_line is not None

        # Print
        printer = PrettyPrinter()
        generated = printer.print(ast)
        assert isinstance(generated, dict)
        code = list(generated.values())[0]
        assert "function" in code

    def test_multiple_parses(self, simple_php_code, function_php_code):
        """Test parsing multiple code samples."""
        ast1 = parse_code_to_ast(simple_php_code)
        ast2 = parse_code_to_ast(function_php_code)

        nodes1 = list(ast1.nodes())
        nodes2 = list(ast2.nodes())

        # Different code should have different node counts
        assert len(nodes1) != len(nodes2)

    def test_complex_query_workflow(self, class_php_code):
        """Test complex querying workflow."""
        ast = parse_code_to_ast(class_php_code)

        # Find class
        classes = list(ast.nodes(lambda n: n.node_type == "Stmt_Class"))
        cls = classes[0]
        assert cls.node_type == "Stmt_Class"
        # Note: 'name' is in a child Identifier node is not None

        # Find all methods
        methods = list(ast.nodes(lambda n: n.node_type == "Stmt_ClassMethod"))
        assert len(methods) >= 2  # __construct and getName

        # Check method properties
        for method in methods:
            assert method.start_line is not None
            assert method.end_line is not None

    def test_roundtrip_preserves_structure(self, complex_php_code):
        """Test that round-trip preserves code structure."""
        parser = Parser()
        printer = PrettyPrinter()

        # Parse original
        ast1 = parse_code_to_ast(complex_php_code)

        # Generate code
        generated = printer.print(ast1)
        assert isinstance(generated, dict)
        code = list(generated.values())[0]

        # Parse generated
        ast2 = parse_code_to_ast(code)

        # Compare node counts
        nodes1 = list(ast1.nodes())
        nodes2 = list(ast2.nodes())
        assert len(nodes1) == len(nodes2)

        # Compare specific node types
        classes1 = list(ast1.nodes(lambda n: n.node_type == "Stmt_Class"))
        classes2 = list(ast2.nodes(lambda n: n.node_type == "Stmt_Class"))
        assert len(classes1) == len(classes2)

    def test_error_recovery(self):
        """Test error recovery with invalid code."""
        from php_parser_py._exceptions import ParseError

        invalid_php_code = "<?php function test("

        with pytest.raises(ParseError):
            parse_code_to_ast(invalid_php_code)

        # Should still be able to parse valid code after error
        valid_code = "<?php echo 'test';"
        ast = parse_code_to_ast(valid_code)
        assert ast is not None

    def test_property_access_patterns(self, function_php_code):
        """Test different property access patterns."""
        ast = parse_code_to_ast(function_php_code)
        func = ast.first_node(lambda n: n.node_type == "Stmt_Function")

        # Pythonic property access
        assert func.node_type == "Stmt_Function"
        assert func.start_line is not None

        # Dict-like access
        assert func["nodeType"] == "Stmt_Function"

        # get() method
        assert func.get("byRef") is not None
        assert func.get("nonexistent", "default") == "default"

        # Attribute methods - these work on actual properties
        assert func.has_attribute("byRef")
        assert func.get_attribute("byRef") is not None
