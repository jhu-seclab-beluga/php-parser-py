<?php
/**
 * PHP-Parser parse script.
 * Reads PHP code from stdin, parses it, and outputs JSON AST.
 */

require_once __DIR__ . '/../vendor/php-parser.phar';

use PhpParser\ParserFactory;
use PhpParser\JsonSerializer;
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
    $serializer = new JsonSerializer();
    echo $serializer->serialize($stmts);
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
    exit(1);
}
