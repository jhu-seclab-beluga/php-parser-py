"""Unit tests for Parser class."""

import sys
from pathlib import Path

import pytest

# Add tests directory to path to import conftest
sys.path.insert(0, str(Path(__file__).parent))

from conftest import parse_code_to_ast  # noqa: E402

from php_parser_py import ParseError, Parser
from php_parser_py._ast import AST


class TestParser:
    """Test suite for Parser class."""

    def test_parser_initialization_creates_runner(self):
        """Test Parser initialization creates Runner instance."""
        parser = Parser()
        assert parser is not None
        assert hasattr(parser, "_runner")

    def test_parse_simple_code_returns_ast_with_nodes(self, simple_php_code):
        """Test parsing simple PHP code returns AST with nodes."""
        ast = parse_code_to_ast(simple_php_code)
        assert isinstance(ast, AST)
        assert len(list(ast.nodes())) > 0

    def test_parse_function_creates_function_node(self, function_php_code):
        """Test parsing PHP function creates Stmt_Function node."""
        ast = parse_code_to_ast(function_php_code)
        functions = list(ast.nodes(lambda n: n.node_type == "Stmt_Function"))
        assert len(functions) == 1
        assert functions[0].node_type == "Stmt_Function"

    def test_parse_class_creates_class_node(self, class_php_code):
        """Test parsing PHP class creates Stmt_Class node."""
        ast = parse_code_to_ast(class_php_code)
        classes = list(ast.nodes(lambda n: n.node_type == "Stmt_Class"))
        assert len(classes) == 1
        assert classes[0].node_type == "Stmt_Class"

    def test_parse_complex_code(self, complex_php_code):
        """Test parsing complex PHP code."""
        ast = parse_code_to_ast(complex_php_code)

        # Should have namespace, use, and class
        namespaces = list(ast.nodes(lambda n: n.node_type == "Stmt_Namespace"))
        classes = list(ast.nodes(lambda n: n.node_type == "Stmt_Class"))

        assert len(namespaces) >= 1
        assert len(classes) >= 1

    def test_parse_invalid_code_raises_parse_error(self):
        """Test parsing invalid PHP code raises ParseError."""
        from php_parser_py._exceptions import ParseError

        invalid_php_code = "<?php function test("

        with pytest.raises(ParseError) as exc_info:
            parse_code_to_ast(invalid_php_code)

        assert "Syntax error" in str(exc_info.value)

    def test_parse_empty_code_returns_valid_ast(self):
        """Test parsing empty code returns valid AST."""
        ast = parse_code_to_ast("<?php")
        assert isinstance(ast, AST)

    def test_node_attributes(self, function_php_code):
        """Test that parsed nodes have correct attributes."""
        ast = parse_code_to_ast(function_php_code)

        func = ast.first_node(lambda n: n.node_type == "Stmt_Function")
        assert func is not None
        assert func.node_type == "Stmt_Function"
        assert func.start_line == 2
        # Note: 'name' is in a child Identifier node, not in the function node itself
        assert "byRef" in func
        assert func["byRef"] is False

    def test_parse_file_nonexistent_raises_file_not_found_error(self):
        """Test parse_file with non-existent file raises FileNotFoundError."""
        parser = Parser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/file.php")

    def test_parse_file_path_properties(self, tmp_path):
        """Test parse_file sets correct path properties."""
        import os
        import tempfile
        from pathlib import Path

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
            f.write("<?php function test() {}")
            temp_file = f.name

        try:
            parser = Parser()
            ast = parser.parse_file(temp_file)

            # Check project node has path property
            project = ast.project_node
            assert project is not None
            project_path = project.get_property("path")
            assert project_path is not None
            # Use resolve() to handle symlinks (e.g., /var -> /private/var on macOS)
            assert project_path == str(Path(temp_file).parent.resolve())

            # Check file node has path and filePath properties
            files = ast.files()
            assert len(files) == 1
            file_node = files[0]

            file_path = file_node.get_property("path")
            file_abs_path = file_node.get_property("filePath")

            assert file_path is not None
            assert file_abs_path is not None
            assert file_path == Path(temp_file).name  # Relative path is filename
            # Use resolve() to handle symlinks
            assert file_abs_path == str(Path(temp_file).resolve())  # Absolute path
        finally:
            os.unlink(temp_file)

    def test_parse_project_path_properties(self, tmp_path):
        """Test parse_project sets correct path properties."""
        import tempfile
        from pathlib import Path

        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()

            src_dir = project_root / "src"
            src_dir.mkdir()

            file1 = src_dir / "file1.php"
            file1.write_text("<?php function a() {}")

            file2 = src_dir / "file2.php"
            file2.write_text("<?php class B {}")

            parser = Parser()
            ast = parser.parse_project(str(project_root))

            # Check project node has path property
            project = ast.project_node
            assert project is not None
            project_path = project.get_property("path")
            assert project_path is not None
            assert project_path == str(project_root.resolve())

            # Check file nodes have correct path properties
            files = ast.files()
            assert len(files) == 2

            file_paths = {file_node.get_property("path") for file_node in files}
            file_abs_paths = {file_node.get_property("filePath") for file_node in files}

            # Relative paths should be src/file1.php and src/file2.php
            assert str(Path("src") / "file1.php") in file_paths
            assert str(Path("src") / "file2.php") in file_paths

            # Absolute paths should contain full paths
            assert str(file1.resolve()) in file_abs_paths
            assert str(file2.resolve()) in file_abs_paths

    def test_parse_project_recursive(self, tmp_path):
        """Test parse_project recursively finds all PHP files."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()

            src_dir = project_root / "src"
            src_dir.mkdir()

            subdir = src_dir / "sub"
            subdir.mkdir()

            file1 = src_dir / "file1.php"
            file1.write_text("<?php function a() {}")

            file2 = subdir / "file2.php"
            file2.write_text("<?php class B {}")

            parser = Parser()
            ast = parser.parse_project(str(project_root))

            # Check project node has correct path
            project = ast.project_node
            assert project is not None
            project_path = project.get_property("path")
            assert project_path == str(project_root.resolve())

            # Check all files are found
            files = ast.files()
            assert len(files) == 2

            file_paths = {file_node.get_property("path") for file_node in files}
            # Relative paths should be src/file1.php and src/sub/file2.php
            assert str(Path("src") / "file1.php") in file_paths
            assert str(Path("src") / "sub" / "file2.php") in file_paths

    def test_parse_project_with_file_filter(self, tmp_path):
        """Test parse_project with custom file filter."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()

            src_dir = project_root / "src"
            src_dir.mkdir()

            file1 = src_dir / "file1.php"
            file1.write_text("<?php function a() {}")

            file2 = src_dir / "file2.phtml"
            file2.write_text("<?php class B {}")

            file3 = src_dir / "file3.txt"
            file3.write_text("not php")

            parser = Parser()

            # Default filter (only .php files)
            ast1 = parser.parse_project(str(project_root))
            files1 = ast1.files()
            assert len(files1) == 1
            file_paths1 = {f.get_property("path") for f in files1}
            assert any("file1.php" in p for p in file_paths1)

            # Custom filter (include .php and .phtml)
            ast2 = parser.parse_project(
                str(project_root), file_filter=lambda p: p.suffix in [".php", ".phtml"]
            )
            files2 = ast2.files()
            assert len(files2) == 2
            file_paths2 = {f.get_property("path") for f in files2}
            assert any("file1.php" in p for p in file_paths2)
            assert any("file2.phtml" in p for p in file_paths2)

            # Custom filter (exclude specific files)
            ast3 = parser.parse_project(
                str(project_root),
                file_filter=lambda p: p.suffix == ".php" and "file1" not in p.name,
            )
            files3 = ast3.files()
            assert len(files3) == 0  # file1.php is excluded, no other .php files
