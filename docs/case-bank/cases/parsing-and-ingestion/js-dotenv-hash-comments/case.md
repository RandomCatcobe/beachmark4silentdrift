# JS-09: dotenv starts treating unquoted hash text as comments

## API Or Behavior Under Test

dotenv.parse for .env content in dotenv.

## Version Boundary

dotenv 14.3.2 -> dotenv 15.0.1

## Old Behavior

An unquoted hash character inside a value remains part of the parsed value.

## New Behavior

The same unquoted hash starts a comment, so only the prefix before the hash is parsed as the value.

## Why The Drift Is Silent

The .env input parses successfully in both versions and the key is still present.

## Realistic Impact Scenario

Secrets, tokens, and connection strings containing hash characters can be truncated unless they are quoted.
