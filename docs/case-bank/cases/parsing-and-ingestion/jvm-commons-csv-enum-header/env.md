# Environment For JVM-JAVA-07

- Runtime: Java and either Maven or local commons-csv jars.
- Package versions: commons-csv 1.9.0 and 1.10.0.
- Version switching: compile and run with the selected commons-csv jar or Maven dependency version.
- Adapter/API surface: library-api, parser.
- Probe shape: run the Java probe and parse one JSON object from stdout.
- Command shape: mvn -Dcommons.csv.version=<old-or-new> -f client/pom.xml compile exec:java.
