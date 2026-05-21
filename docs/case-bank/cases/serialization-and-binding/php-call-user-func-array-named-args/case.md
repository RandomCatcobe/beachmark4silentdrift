# PHP-11: call_user_func_array binds string keys as named arguments

## API Or Behavior Under Test

call_user_func_array with string-keyed argument arrays in php-core.

## Version Boundary

PHP 7.4.33 -> PHP 8.0.30

## Old Behavior

String keys in the argument array are ignored and arguments bind by insertion order.

## New Behavior

The same string keys are interpreted as named parameter names and bind by name.

## Why The Drift Is Silent

The function call succeeds in both runtimes and returns an array with the same shape, but values bind to different parameters.

## Realistic Impact Scenario

Plugin dispatchers, hook systems, or dynamic method invocations that pass associative arrays can silently swap business values between parameters.
