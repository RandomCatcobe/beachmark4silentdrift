<?php

function describe($first, $second) {
    return [
        "first" => $first,
        "second" => $second,
    ];
}

$args = [
    "second" => "B",
    "first" => "A",
];

$result = describe(...array_values($args));
$via_call_user_func_array = call_user_func_array("describe", $args);

echo json_encode([
    "php_version" => PHP_VERSION,
    "array_values_baseline" => $result,
    "call_user_func_array" => $via_call_user_func_array,
], JSON_UNESCAPED_SLASHES) . PHP_EOL;
