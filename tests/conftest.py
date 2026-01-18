"""Test configuration and fixtures for php-parser-py tests."""

import pytest


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
