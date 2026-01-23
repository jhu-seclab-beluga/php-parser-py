"""Test configuration and fixtures for php-parser-py tests."""

import tempfile
from pathlib import Path

import pytest

from php_parser_py import parse_file


@pytest.fixture
def simple_php_code():
    """Simple PHP code for basic testing."""
    return "<?php echo 'hello world';"


@pytest.fixture
def function_php_code():
    """PHP code with a function."""
    return """<?php
function greet($name) {
    echo "Hello, " . $name;
    return true;
}
"""


@pytest.fixture
def class_php_code():
    """PHP code with a class."""
    return """<?php
class User {
    private $name;
    private $email;
    
    public function __construct($name, $email) {
        $this->name = $name;
        $this->email = $email;
    }
    
    public function getName() {
        return $this->name;
    }
}
"""


@pytest.fixture
def complex_php_code():
    """Complex PHP code with multiple constructs."""
    return """<?php
namespace App\\Models;

use DateTime;

class Post {
    private $title;
    private $content;
    private $createdAt;
    
    public function __construct($title, $content) {
        $this->title = $title;
        $this->content = $content;
        $this->createdAt = new DateTime();
    }
    
    public function getTitle() {
        return $this->title;
    }
    
    public function setTitle($title) {
        $this->title = $title;
    }
}
"""


@pytest.fixture
def invalid_php_code():
    """Invalid PHP code for error testing."""
    return "<?php function test( { echo 'broken'; }"


def parse_code_to_ast(code: str):
    """Helper function to parse code string into AST using temporary file.

    Args:
        code: PHP source code string.

    Returns:
        AST instance with project -> file -> statements hierarchy.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        return parse_file(temp_path)
    finally:
        Path(temp_path).unlink()


@pytest.fixture
def storage_with_node():
    """Create a storage with a test node for Node tests."""
    from cpg2py import Storage

    storage = Storage()
    storage.add_node("test_node_1")
    storage.set_node_props(
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


@pytest.fixture
def storage_with_edge():
    """Create a storage with test nodes and an edge for Edge tests."""
    from cpg2py import Storage

    storage = Storage()
    storage.add_node("node1")
    storage.set_node_props("node1", {"nodeType": "Stmt_Echo"})
    storage.add_node("node2")
    storage.set_node_props("node2", {"nodeType": "Stmt_Return"})
    storage.add_edge(("node1", "node2", "PARENT_OF"))
    storage.set_edge_props(
        ("node1", "node2", "PARENT_OF"), {"field": "stmts", "index": 0}
    )
    return storage
