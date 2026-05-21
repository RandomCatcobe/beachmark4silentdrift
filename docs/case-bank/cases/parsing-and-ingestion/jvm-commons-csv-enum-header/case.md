# JVM-JAVA-07: Commons CSV enum header lookup changed from toString to name

## API Or Behavior Under Test

CSVRecord.get(Enum) in org.apache.commons:commons-csv.

## Version Boundary

commons-csv 1.9.0 -> 1.10.0

## Old Behavior

Enum header lookup uses the enum constant's toString value.

## New Behavior

The same lookup uses the enum constant's name value.

## Why The Drift Is Silent

The CSV input, enum type, and get call compile and run in both versions.

## Realistic Impact Scenario

CSV ingestion code using enums with custom toString values can read a different column without any exception.
