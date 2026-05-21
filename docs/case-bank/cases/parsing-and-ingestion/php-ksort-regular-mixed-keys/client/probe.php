<?php

$items = [
    "a" => "letter-a",
    "1" => "number-one",
    "b" => "letter-b",
    "2" => "number-two",
];

ksort($items, SORT_REGULAR);

echo json_encode([
    "php_version" => PHP_VERSION,
    "sorted_keys" => array_keys($items),
    "sorted_values" => array_values($items),
], JSON_UNESCAPED_SLASHES) . PHP_EOL;
