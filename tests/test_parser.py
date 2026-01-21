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

    def test_parse_file_path_properties(self, tmp_path):
        """Test parse_file sets correct path properties."""
        import tempfile
        import os
        from pathlib import Path
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write('<?php function test() {}')
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
        import os
        from pathlib import Path
        
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / 'src'
            subdir.mkdir()
            
            file1 = subdir / 'file1.php'
            file1.write_text('<?php function a() {}')
            
            file2 = subdir / 'file2.php'
            file2.write_text('<?php class B {}')
            
            parser = Parser()
            ast = parser.parse_project([str(file1), str(file2)])
            
            # Check project node has path property (should be common parent)
            project = ast.project_node
            assert project is not None
            project_path = project.get_property("path")
            assert project_path is not None
            assert project_path == str(subdir.resolve())
            
            # Check file nodes have correct path properties
            files = ast.files()
            assert len(files) == 2
            
            for file_node in files:
                file_path = file_node.get_property("path")
                file_abs_path = file_node.get_property("filePath")
                
                assert file_path is not None
                assert file_abs_path is not None
                # Relative path should be just filename
                assert Path(file_path).name in ['file1.php', 'file2.php']
                # Absolute path should be full path
                assert str(subdir) in file_abs_path

    def test_parse_project_with_custom_path(self, tmp_path):
        """Test parse_project with custom project_path."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / 'project'
            project_root.mkdir()
            
            src_dir = project_root / 'src'
            src_dir.mkdir()
            
            file1 = src_dir / 'file1.php'
            file1.write_text('<?php function a() {}')
            
            parser = Parser()
            ast = parser.parse_project([str(file1)], project_path=str(project_root))
            
            # Check project node has custom path
            project = ast.project_node
            assert project is not None
            project_path = project.get_property("path")
            assert project_path == str(project_root.resolve())
            
            # Check file node has correct relative path
            files = ast.files()
            assert len(files) == 1
            file_node = files[0]
            
            file_path = file_node.get_property("path")
            assert file_path is not None
            # Relative path should be src/file1.php
            assert file_path == str(Path('src') / 'file1.php')
