<?php

$input = "Tom's <tag>";

echo json_encode([
    "php_version" => PHP_VERSION,
    "default_htmlspecialchars" => htmlspecialchars($input),
    "explicit_old_flags" => htmlspecialchars($input, ENT_COMPAT | ENT_HTML401, "UTF-8", true),
    "explicit_new_flags" => htmlspecialchars($input, ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML401, "UTF-8", true),
], JSON_UNESCAPED_SLASHES) . PHP_EOL;
