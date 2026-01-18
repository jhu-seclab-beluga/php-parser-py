<?php
/**
 * PHP-Parser print script.
 * Reads AST JSON from stdin and outputs pretty-printed PHP code.
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

use PhpParser\JsonDecoder;
use PhpParser\PrettyPrinter\Standard;

$json = file_get_contents('php://stdin');

try {
    $decoder = new JsonDecoder();
    $stmts = $decoder->decode($json);
    $printer = new Standard();
    echo $printer->prettyPrintFile($stmts);
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
    exit(1);
}
