# JVM / Java Drift Idea Bank

Independent language idea bank for local, deterministic JVM/Java silent-drift candidates.

## RUN-20260520-001: Independent JVM Agent Batch

- Target: 10 candidates.
- Result: 10/10 candidates found.
- Language judgment: JVM/Java has abundant candidate material; no exhaustion judgment.
- Promotion note: prefer pure library/CLI cases over full server/database fixtures unless the JVM adapter boundary explicitly supports the harness.

| ID | Package / Tool | API Surface | Version Boundary | Source | Behavior Hypothesis | Why Silent | Reproduction Sketch | Confidence |
|---|---|---|---|---|---|---|---|---|
| JVM-JAVA-01 | Jackson XML | `XmlMapper`, `FromXmlParser.Feature.EMPTY_ELEMENT_AS_NULL` default | 2.9-2.11 -> 2.12 | https://github.com/FasterXML/jackson/wiki/Jackson-Release-2.12 | Empty XML element `<x/>` maps as `null` before 2.12 and as non-null empty value after 2.12. | Same XML and API; no compile signal. | Parse `<root><x/></root>` with `XmlMapper.readTree`; compare null/text behavior. | High |
| JVM-JAVA-02 | Gson | enum deserialization via `Gson.fromJson` | 2.9.0 -> 2.9.1 | https://google.github.io/gson/CHANGELOG.html | Enum constants with overridden `toString()` start deserializing from the `toString()` value instead of yielding `null`. | Same enum and JSON literal parse without compile changes. | Parse `"wire"` into an enum whose `toString()` returns `wire`; compare result. | High |
| JVM-JAVA-03 | Hibernate ORM | native query scalar result mapping | 5.x -> 6.0 | https://docs.hibernate.org/orm/6.0/migration-guide/ | Native `select count(*)` result changes from `BigInteger` to `Long`. | Same SQL and `getSingleResult()` succeed; runtime value type changes. | Run `createNativeQuery("select count(*) from person").getSingleResult().getClass()`. | High |
| JVM-JAVA-04 | Spring Boot MVC/Security | request path matching, `mvcMatchers` | 2.5 -> 2.6 | https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.6-Release-Notes | Default MVC matching changes from `AntPathMatcher` to `PathPatternParser`, changing pattern behavior. | App starts; request authorization/routing result changes. | App with `/hello` endpoint and `mvcMatchers("hello").permitAll()`; compare `/hello` status. | High |
| JVM-JAVA-05 | JUnit Jupiter | `@ParameterizedTest` argument lifecycle | 5.7 -> 5.8 | https://junit.org/junit5/docs/5.8.0/release-notes/index.html | `AutoCloseable` parameterized-test arguments are closed automatically by default. | Same annotation and source; lifecycle side effects differ. | Supply an `AutoCloseable` from `@MethodSource`; record close count after suite. | High |
| JVM-JAVA-06 | Guava | `InternetDomainName` public suffix data | 33.4.4 -> 33.4.5 | https://github.com/google/guava/releases/tag/v33.4.5 | Embedded Public Suffix List update changes domain classification for touched suffixes. | Same API and hostname; bundled data changes boolean/domain results. | Choose a PSL-added/removed suffix and compare `publicSuffix()` or `isPublicSuffix()`. | Medium |
| JVM-JAVA-07 | Apache Commons CSV | `CSVRecord.get(Enum)` | 1.9.0 -> 1.10.0 | https://commons.apache.org/proper/commons-csv/changes.html | Enum header lookup changes from `Enum.toString()` to `Enum.name()`. | Same CSV and enum compile; returned column can change. | Enum `H.X` whose `toString()` returns `Y`; CSV header `X,Y`; compare `get(H.X)`. | High |
| JVM-JAVA-08 | Log4j 2 | PatternLayout message lookup expansion | 2.14.1 -> 2.15.0 | https://logging.apache.org/log4j/2.x/release-notes.html | `%m` no longer expands lookup expressions in message text by default. | Same logger call and pattern; log line content changes. | Pattern `%m%n`; log `${java:version}`; compare expanded vs literal output. | High |
| JVM-JAVA-09 | Maven | `.mvn/maven.config` parsing | 3.8.x -> 3.9.0 | https://maven.apache.org/docs/3.9.0/release-notes.html | Each line in `.mvn/maven.config` is interpreted as a single argument, changing multi-option lines. | Same project config and command; effective properties can differ. | Put `-Dfoo=bar -Dbar=baz` on one line; evaluate properties under Maven 3.8 vs 3.9. | High |
| JVM-JAVA-10 | Java stdlib | default charset APIs such as `new String(bytes)`, `FileReader`, `Scanner` | JDK 17 -> JDK 18 | https://openjdk.org/jeps/400 | Default charset becomes UTF-8, changing decoding/encoding on platforms that previously used legacy charsets. | Same source and public APIs; bytes decode differently at runtime. | On a legacy-default platform, decode byte `0xE9` with `new String(...)`; compare result. | High |

## Verification Log

### 2026-05-21: JVM-JAVA-07 Apache Commons CSV enum header lookup

- Pipeline result: `data\verification\jvm_commons_csv_enum_header\attempt_001\result.json`
- Dependency roots: local Maven cache jars `commons-csv-1.9.0.jar` and `commons-csv-1.10.0.jar`.
- Client: `data\verification\jvm_commons_csv_enum_header\DriftClient.java`.
- Probe: enum constant `Header.X` overrides `toString()` to return `Y`; CSV header is `X,Y` and data row is `left,right`.
- Old behavior: `commons-csv` 1.9.0 resolves `record.get(Header.X)` via `toString()` and returns `right`.
- New behavior: `commons-csv` 1.10.0 resolves `record.get(Header.X)` via `name()` and returns `left`.
- Verdict: keep. True silent drift, both sides compile and exit 0.
