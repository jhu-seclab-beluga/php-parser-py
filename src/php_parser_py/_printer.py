"""PrettyPrinter class for PHP code generation."""

import logging
from pathlib import Path
from typing import Optional

from php_parser_py._ast import AST
from php_parser_py._runner import Runner

logger = logging.getLogger(__name__)


class PrettyPrinter:
    """Converts AST to PHP code using PHP-Parser's PrettyPrinter.

    Reconstructs JSON from AST graph and invokes PHP-Parser to generate
    formatted PHP source code for each file.

    Attributes:
        _runner: Runner instance for PHP-Parser invocation.
    """

    def __init__(
        self,
        php_binary_path: Optional[Path] = None,
        php_binary_url: Optional[str] = None,
    ) -> None:
        """Initialize PrettyPrinter with Runner.

        Args:
            php_binary_path: Optional path to local PHP binary.
            php_binary_url: Optional URL to download PHP binary from.
        """
        self._runner = Runner(
            php_binary_path=php_binary_path,
            php_binary_url=php_binary_url,
        )

    def print(self, ast: AST) -> dict[str, str]:
        """Generate PHP code from AST, returning a mapping of file paths to code.

        Args:
            ast: AST instance to convert to code.

        Returns:
            Dictionary mapping file paths to generated PHP source code strings.
            If AST has no file structure, returns a single entry with key ""
            as the filename.

        Raises:
            RunnerError: If PHP-Parser execution fails.
        """
        file_nodes = ast.files()

        if not file_nodes:
            # No file structure - export all statements as a single code block
            json_str = ast.to_json()
            code = self._runner.print(json_str)
            return {"": code}

        # Generate code for each file
        result: dict[str, str] = {}
        for file_node in file_nodes:
            file_path = file_node.get_property("filePath", "")
            file_hash = file_node.id

            # Get JSON for this file only
            json_str = ast.to_json(file_hash=file_hash)

            # Generate code
            code = self._runner.print(json_str)

            # Use file path as key, or file hash if path not available
            key = file_path if file_path else file_hash
            result[key] = code

        return result

    def print_file(self, ast: AST, relative_path: str) -> str:
        """Generate PHP code string for a single file selected by relative path.

        This method looks up the file node whose ``path`` property matches the
        given relative path (as stored on file nodes), reconstructs JSON for
        that file only, and returns the generated PHP source code string.

        Args:
            ast: AST instance containing project and file nodes.
            relative_path: Relative file path stored in the ``path`` property
                of the target file node (for example, ``"src/file.php"`` or
                just ``"file.php"`` for single-file projects).

        Returns:
            Generated PHP source code string for the specified file.

        Raises:
            KeyError: If no file node with the given relative path exists
                in the AST.
            RunnerError: If PHP-Parser execution fails.
        """
        # Find file node by its relative path property
        for file_node in ast.files():
            if file_node.get_property("path") == relative_path:
                file_hash = file_node.id
                json_str = ast.to_json(file_hash=file_hash)
                return self._runner.print(json_str)

        raise KeyError(f"File with relative path '{relative_path}' not found in AST.")
