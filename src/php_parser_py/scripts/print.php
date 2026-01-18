<?php
/**
 * PHP-Parser print script.
 * Reads JSON AST from stdin, decodes it, and outputs formatted PHP code.
 */

require_once __DIR__ . '/../vendor/php-parser.phar';

use PhpParser\JsonDecoder;
use PhpParser\PrettyPrinter;

$json = file_get_contents('php://stdin');

try {
    $decoder = new JsonDecoder();
    $stmts = $decoder->decode($json);
    $printer = new PrettyPrinter\Standard();
    echo $printer->prettyPrintFile($stmts);
} catch (Exception $e) {
    fwrite(STDERR, $e->getMessage());
    exit(1);
}
