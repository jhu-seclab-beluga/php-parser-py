"""Runner class for PHP-Parser invocation."""

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from php_parser_py._resources import ensure_php_parser_extracted
from php_parser_py.exceptions import ParseError, RunnerError

logger = logging.getLogger(__name__)


class Runner:
    """Manages PHP-Parser invocation via PHP binary.

    Handles execution of PHP scripts for parsing and code generation,
    communicating with PHP-Parser through subprocess stdin/stdout.

    Attributes:
        _php_binary: Path to PHP binary.
        _scripts_dir: Path to directory containing PHP scripts.
        _vendor_dir: Path to directory containing PHP-Parser PHAR.
    """

    def __init__(self) -> None:
        """Initialize Runner with PHP binary and PHP-Parser paths.

        Raises:
            RunnerError: If PHP binary or PHP-Parser cannot be located.
        """
        self._vendor_dir = ensure_php_parser_extracted()

        # Locate PHP binary from system PATH
        php_path = shutil.which("php")
        if php_path is None:
            raise RunnerError(
                "PHP binary not found in system PATH. Please install PHP.", exit_code=1
            )

        self._php_binary = Path(php_path)

        # Locate scripts directory
        module_dir = Path(__file__).parent
        self._scripts_dir = module_dir / "scripts"

        if not self._php_binary.exists():
            raise RunnerError(
                f"PHP binary not found at {self._php_binary}", exit_code=1
            )

    def execute(self, script: str, stdin: str = "") -> str:
        """Execute PHP script with optional stdin.

        Args:
            script: PHP script code to execute.
            stdin: Optional input to pass to script's stdin.

        Returns:
            Script's stdout output.

        Raises:
            RunnerError: If PHP execution fails.
        """
        try:
            result = subprocess.run(
                [str(self._php_binary), "-r", script],
                input=stdin,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                # Log complete error information
                error_msg = f"PHP execution failed with exit code {result.returncode}"
                if result.stderr:
                    logger.error(f"PHP stderr: {result.stderr}")
                    error_msg += f"\nStderr: {result.stderr}"
                if result.stdout:
                    logger.error(f"PHP stdout: {result.stdout}")
                    error_msg += f"\nStdout: {result.stdout}"
                
                raise RunnerError(
                    error_msg,
                    stderr=result.stderr,
                    exit_code=result.returncode,
                )

            return result.stdout

        except FileNotFoundError as e:
            error_msg = f"PHP binary not found: {self._php_binary}"
            logger.error(error_msg)
            raise RunnerError(
                error_msg, stderr=str(e), exit_code=1
            ) from e
        except Exception as e:
            error_msg = f"Failed to execute PHP script: {e}"
            logger.error(error_msg)
            # Don't wrap the error if it's already a RunnerError
            if isinstance(e, RunnerError):
                raise
            raise RunnerError(
                error_msg, stderr=str(e), exit_code=1
            ) from e

    def parse(self, code: str) -> dict[str, Any]:
        """Invoke PHP-Parser parse + JsonSerializer.

        Args:
            code: PHP source code to parse.

        Returns:
            Parsed JSON as dict.

        Raises:
            ParseError: If PHP-Parser reports syntax error.
            RunnerError: If PHP execution fails.
        """
        parse_script = self._build_parse_script()

        try:
            output = self.execute(parse_script, code)
            result = json.loads(output)

            # Check for parse errors
            if isinstance(result, dict) and "errors" in result:
                errors = result["errors"]
                if errors:
                    first_error = errors[0]
                    raise ParseError(
                        first_error.get("message", "Unknown parse error"),
                        first_error.get("line"),
                    )

            return result

        except json.JSONDecodeError as e:
            raise RunnerError(
                f"Failed to decode PHP-Parser JSON output: {e}",
                stderr=str(e),
                exit_code=1,
            ) from e

    def print(self, ast_json: str) -> str:
        """Invoke PHP-Parser JsonDecoder + PrettyPrinter.

        Args:
            ast_json: AST JSON string from PHP-Parser format.

        Returns:
            Generated PHP source code.

        Raises:
            RunnerError: If PHP execution fails.
        """
        print_script = self._build_print_script()
        return self.execute(print_script, ast_json)

    def _build_parse_script(self) -> str:
        """Build PHP script for parsing."""
        phar_path = self._vendor_dir / "php-parser.phar"
        return f"""
error_reporting(E_ALL & ~E_DEPRECATED);
require_once 'phar://{phar_path}/vendor/autoload.php';

use PhpParser\\ParserFactory;
use PhpParser\\NodeDumper;
use PhpParser\\ErrorHandler\\Collecting;

$code = file_get_contents('php://stdin');
$errorHandler = new Collecting();
$parser = (new ParserFactory())->createForNewestSupportedVersion();

try {{
    $stmts = $parser->parse($code, $errorHandler);
    if ($errorHandler->hasErrors()) {{
        $errors = array_map(fn($e) => [
            'message' => $e->getMessage(),
            'line' => $e->getStartLine()
        ], $errorHandler->getErrors());
        echo json_encode(['errors' => $errors]);
        exit(1);
    }}
    $dumper = new NodeDumper([
        'dumpComments' => true,
        'dumpPositions' => true
    ]);
    echo json_encode($dumper->dump($stmts));
}} catch (Exception $e) {{
    echo json_encode(['error' => $e->getMessage()]);
    exit(1);
}}
"""

    def _build_print_script(self) -> str:
        """Build PHP script for code generation."""
        phar_path = self._vendor_dir / "php-parser.phar"
        return f"""
error_reporting(E_ALL & ~E_DEPRECATED);
require_once 'phar://{phar_path}/vendor/autoload.php';

use PhpParser\\JsonDecoder;
use PhpParser\\PrettyPrinter\\Standard;

$json = file_get_contents('php://stdin');

try {{
    $decoder = new JsonDecoder();
    $stmts = $decoder->decode($json);
    $printer = new Standard();
    echo $printer->prettyPrintFile($stmts);
}} catch (Exception $e) {{
    echo json_encode(['error' => $e->getMessage()]);
    exit(1);
}}
"""
