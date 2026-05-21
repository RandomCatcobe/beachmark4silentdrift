<?php
require $argv[1];
$a = Carbon\Carbon::parse('2020-01-01 00:00:00.000000');
$b = Carbon\Carbon::parse('2020-01-01 00:00:00.500000');
echo json_encode([
    'forward' => $a->diffInSeconds($b),
    'reverse' => $b->diffInSeconds($a),
    'forward_type' => gettype($a->diffInSeconds($b)),
    'reverse_type' => gettype($b->diffInSeconds($a)),
], JSON_UNESCAPED_SLASHES), PHP_EOL;
