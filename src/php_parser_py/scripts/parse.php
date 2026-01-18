<?php
/**
 * PHP-Parser parse script.
 * Reads PHP code from stdin, parses it, and outputs JSON AST.
 */

// Suppress deprecation warnings for PHP 8.5 compatibility
error_reporting(E_ALL & ~E_DEPRECATED);

// Load PHP-Parser PHAR
$pharPath = __DIR__ . '/../vendor/php-parser.phar';
if (!file_exists($pharPath)) {
    echo json_encode(['error' => 'PHP-Parser PHAR not found']);
    exit(1);
}

// Include the PHAR autoloader
require_once 'phar://' . $pharPath . '/vendor/autoload.php';

use PhpParser\ParserFactory;
use PhpParser\NodeDumper;
use PhpParser\ErrorHandler\Collecting;

$code = file_get_contents('php://stdin');
$errorHandler = new Collecting();
$parser = (new ParserFactory())->createForNewestSupportedVersion();

try {
    $stmts = $parser->parse($code, $errorHandler);
    if ($errorHandler->hasErrors()) {
        $errors = array_map(fn($e) => [
            'message' => $e->getMessage(),
            'line' => $e->getStartLine()
        ], $errorHandler->getErrors());
        echo json_encode(['errors' => $errors]);
        exit(1);
    }
    // Use NodeDumper to convert AST to array, then JSON encode
    $dumper = new NodeDumper([
        'dumpComments' => true,
        'dumpPositions' => true
    ]);
    echo json_encode($dumper->dump($stmts));
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
    exit(1);
}

