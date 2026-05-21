<?php

declare(strict_types=1);

$roots = array_filter(explode(PATH_SEPARATOR, getenv('PHP_INCLUDE_PATH') ?: ''));
$autoload = null;
foreach ($roots as $root) {
    $candidate = $root . DIRECTORY_SEPARATOR . 'vendor' . DIRECTORY_SEPARATOR . 'autoload.php';
    if (is_file($candidate)) {
        $autoload = $candidate;
        break;
    }
}

if ($autoload === null) {
    fwrite(STDERR, "vendor/autoload.php not found on PHP_INCLUDE_PATH\n");
    exit(2);
}

require $autoload;

use Carbon\Carbon;

date_default_timezone_set('America/New_York');

$dt = Carbon::createFromTimestamp(0);

echo json_encode([
    'class' => get_class($dt),
    'timezone' => $dt->getTimezone()->getName(),
    'format' => $dt->format('c'),
    'timestamp' => $dt->getTimestamp(),
], JSON_UNESCAPED_SLASHES) . "\n";
