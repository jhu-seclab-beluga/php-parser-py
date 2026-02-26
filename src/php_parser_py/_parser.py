"""Parser class for PHP code parsing."""

import hashlib
import logging
from pathlib import Path
from typing import Callable, Optional

from cpg2py import Storage
from static_php_py import PHP

from ._ast import AST
from ._exceptions import ParseError, RunnerError
from ._modifier import Modifier
from ._node import Node
from ._runner import Runner

logger = logging.getLogger(__name__)


class Parser:
    """Parses PHP source code using PHP-Parser.

    Uses Modifier for all AST construction. Parser never calls Storage
    directly — all node/edge creation goes through Modifier.

    Attributes:
        _runner: Runner instance for PHP-Parser invocation.
    """

    def __init__(self, php: Optional[PHP] = None) -> None:
        """Initialize Parser with Runner.

        Args:
            php: Optional PHP instance. If not provided, uses builtin PHP.
        """
        self._runner = Runner(php=php)

    def parse_code(self, code: str) -> list[Node]:
        """Parse PHP code string into a list of top-level statement nodes.

        Does not create project or file nodes. Returns raw statement nodes
        that can be used for analysis or inserted into other AST structures.

        Args:
            code: PHP source code to parse.

        Returns:
            List of Node instances representing top-level statements.

        Raises:
            ParseError: If code has syntax errors.
            RunnerError: If PHP execution fails.
        """
        json_data = self._parse_php(code)
        node_list = self._normalize_json(json_data)

        modifier = Modifier(AST(Storage(), root_node_id="__code_root__"))
        node_counter = [1]
        node_ids: list[str] = []

        for item in node_list:
            node_id = self._process_node(
                modifier, item, None, None, None, node_counter, ""
            )
            if node_id:
                node_ids.append(node_id)

        return [modifier.ast.node(nid) for nid in node_ids]

    def parse_file(self, path: str) -> AST:
        """Parse a single PHP file into an AST with project and file nodes.

        Creates a project node (ID: "project") and a file node (ID: hex
        hash of path). File node contains all statements from the file.

        Args:
            path: File path string.

        Returns:
            AST instance with project -> file -> statements hierarchy.

        Raises:
            ParseError: If PHP-Parser reports syntax error.
            FileNotFoundError: If file does not exist.
        """
        file_path = Path(path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        project_path = file_path.parent
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        code = file_path.read_text(encoding="utf-8")
        json_data = self._parse_php(code)
        file_list = self._normalize_json(json_data)

        modifier = self._build_project_structure(
            [(file_path, file_list)],
            [(file_path, file_hash)],
            project_path=project_path,
        )
        return modifier.ast

    def parse_project(
        self,
        project_path: str,
        file_filter: Callable[[Path], bool] = lambda p: p.suffix == ".php",
    ) -> AST:
        """Parse all PHP files in a project directory into an AST.

        Recursively traverses the project directory to find all PHP files,
        then parses them into a single AST with project and file nodes.

        Args:
            project_path: Project root directory path.
            file_filter: Function to filter files. Takes a Path and returns
                True if the file should be parsed. Defaults to .php suffix.

        Returns:
            AST instance with project -> files -> statements hierarchy.

        Raises:
            ParseError: If any file has syntax errors.
            FileNotFoundError: If project directory does not exist.
            ValueError: If project_path is not a directory.
        """
        project_path_obj = Path(project_path).resolve()

        if not project_path_obj.exists():
            raise FileNotFoundError(f"Project directory not found: {project_path}")
        if not project_path_obj.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")

        php_files = [
            f for f in project_path_obj.rglob("*") if f.is_file() and file_filter(f)
        ]

        if not php_files:
            logger.warning("No PHP files found in project directory: %s", project_path)
            return self._build_empty_project(project_path_obj)

        file_infos = [
            (fp, hashlib.md5(str(fp).encode()).hexdigest()[:8]) for fp in php_files
        ]

        all_json_data = []
        for file_path, _ in file_infos:
            code = file_path.read_text(encoding="utf-8")
            json_data = self._parse_php(code, source=str(file_path))
            all_json_data.append((file_path, self._normalize_json(json_data)))

        modifier = self._build_project_structure(
            all_json_data, file_infos, project_path=project_path_obj
        )
        return modifier.ast

    # -- Internal helpers --

    def _parse_php(self, code: str, source: str = "input") -> object:
        # Invoke PHP-Parser and translate RunnerError into ParseError.
        try:
            return self._runner.parse(code)
        except RunnerError as e:
            if "Syntax error" in str(e):
                raise ParseError(f"Syntax error in {source}", line=1) from e
            raise

    @staticmethod
    def _normalize_json(json_data: object) -> list[dict[str, object]]:
        # Ensure JSON data is always a list of node dicts.
        if isinstance(json_data, list):
            return json_data
        if isinstance(json_data, dict):
            return [json_data]
        return []

    def _build_empty_project(self, project_path: Path) -> AST:
        # Create a project-only AST with no files.
        modifier = Modifier(AST(Storage()))
        modifier.add_node(
            "project",
            "Project",
            absolutePath=str(project_path),
            startLine=-1,
            endLine=-1,
            startFilePos=-1,
            endFilePos=-1,
            startTokenPos=-1,
            endTokenPos=-1,
        )
        return modifier.ast

    def _build_project_structure(
        self,
        files_data: list[tuple[Path, list[dict[str, object]]]],
        file_infos: list[tuple[Path, str]],
        project_path: Path,
    ) -> Modifier:
        # Build project -> files -> statements hierarchy via Modifier.
        modifier = Modifier(AST(Storage()))

        modifier.add_node("project", "Project", absolutePath=str(project_path))

        for (file_path, file_hash), (_, json_data) in zip(file_infos, files_data):
            self._add_file_node(modifier, file_path, file_hash, json_data, project_path)

        # Set sentinel position values on project node.
        project_node = modifier.ast.node("project")
        project_node.set_properties(
            {
                "startLine": -1,
                "endLine": -1,
                "startFilePos": -1,
                "endFilePos": -1,
                "startTokenPos": -1,
                "endTokenPos": -1,
            }
        )

        return modifier

    def _add_file_node(
        self,
        modifier: Modifier,
        file_path: Path,
        file_hash: str,
        stmt_list: list[dict[str, object]],
        project_path: Path,
    ) -> None:
        # Create file node, link to project, process statements.
        try:
            relative_path = file_path.relative_to(project_path)
        except ValueError:
            relative_path = Path(file_path.name)

        end_pos = self._compute_file_end_positions(stmt_list)

        modifier.add_node(
            file_hash,
            "File",
            absolutePath=str(file_path),
            relativePath=str(relative_path),
            startLine=1,
            endLine=end_pos["endLine"],
            startFilePos=0,
            endFilePos=end_pos["endFilePos"],
            startTokenPos=0,
            endTokenPos=end_pos["endTokenPos"],
        )
        modifier.add_edge("project", file_hash, field="files")

        node_counter = [1]
        for idx, item in enumerate(stmt_list):
            self._process_node(
                modifier, item, file_hash, "stmts", idx, node_counter, file_hash
            )

    @staticmethod
    def _compute_file_end_positions(
        stmt_list: list[dict[str, object]],
    ) -> dict[str, int]:
        # Compute file end positions from statement attributes.
        end_line = 1
        end_file_pos = 0
        end_token_pos = 0

        for stmt in stmt_list:
            attrs = stmt.get("attributes", {})
            if not isinstance(attrs, dict):
                continue
            val = attrs.get("endLine")
            if isinstance(val, int) and val > end_line:
                end_line = val
            val = attrs.get("endFilePos")
            if isinstance(val, int) and val > end_file_pos:
                end_file_pos = val
            val = attrs.get("endTokenPos")
            if isinstance(val, int) and val > end_token_pos:
                end_token_pos = val

        return {
            "endLine": end_line,
            "endFilePos": end_file_pos,
            "endTokenPos": end_token_pos,
        }

    def _process_node(
        self,
        modifier: Modifier,
        node_data: object,
        parent_id: str | None,
        field_name: str | None,
        index: int | None,
        node_counter: list[int],
        prefix: str,
    ) -> str | None:
        # Recursively convert a PHP-Parser JSON node into graph nodes/edges.
        if not isinstance(node_data, dict) or "nodeType" not in node_data:
            return None

        node_id = self._generate_node_id(node_counter, prefix)
        properties, child_fields = self._extract_node_data(node_data)

        node_type_val = properties.pop("nodeType")
        if not isinstance(node_type_val, str):
            return None

        modifier.add_node(node_id, node_type_val, **properties)

        if parent_id is not None and field_name is not None:
            if index is not None:
                modifier.add_edge(parent_id, node_id, field=field_name, index=index)
            else:
                modifier.add_edge(parent_id, node_id, field=field_name)

        self._process_children(modifier, child_fields, node_id, node_counter, prefix)
        return node_id

    @staticmethod
    def _generate_node_id(node_counter: list[int], prefix: str) -> str:
        # Generate unique node ID from counter and prefix.
        current = node_counter[0]
        node_counter[0] += 1
        if prefix:
            return f"{prefix}_{current}"
        return f"node_{current}"

    @staticmethod
    def _extract_node_data(
        node_data: dict[str, object],
    ) -> tuple[dict[str, object], list[tuple[str, object]]]:
        # Separate scalar properties from child fields.
        properties: dict[str, object] = {}
        child_fields: list[tuple[str, object]] = []

        for key, value in node_data.items():
            if key == "attributes" and isinstance(value, dict):
                properties.update(value)
            elif isinstance(value, dict):
                child_fields.append((key, value))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                child_fields.append((key, value))
            else:
                properties[key] = value

        return properties, child_fields

    def _process_children(
        self,
        modifier: Modifier,
        child_fields: list[tuple[str, object]],
        parent_id: str,
        node_counter: list[int],
        prefix: str,
    ) -> None:
        # Process child fields recursively.
        for child_key, child_value in child_fields:
            if isinstance(child_value, list):
                for idx, item in enumerate(child_value):
                    self._process_node(
                        modifier, item, parent_id, child_key, idx, node_counter, prefix
                    )
            else:
                self._process_node(
                    modifier,
                    child_value,
                    parent_id,
                    child_key,
                    None,
                    node_counter,
                    prefix,
                )
