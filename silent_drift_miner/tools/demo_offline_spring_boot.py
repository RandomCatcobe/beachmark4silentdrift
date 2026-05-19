"""
Offline demo: feed real Spring Boot release-notes text (gathered via
web_search) directly to the rule extractor, bypassing the GitHub fetcher.

Use this to validate that the pipeline catches realistic silent-drift
language without needing GitHub API access in the sandbox.

Run from this package directory:
    python tools/demo_offline_spring_boot.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from silent_drift_miner.cli import summarize, write_candidates_jsonl  # noqa: E402
from silent_drift_miner.extractors.rules import extract_candidates    # noqa: E402
from silent_drift_miner.schema import utc_now_iso                     # noqa: E402


# Real text fragments from Spring Boot release-note wiki pages, retrieved
# via search on 2026-05. URLs are preserved on each blob so provenance is
# kept; text is paraphrased only minimally to fit the test format.
SAMPLES = [
    {
        "version": "3.4.0-M3",
        "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.4.0-M3-Release-Notes",
        "body": """
- Graceful shutdown of the embedded web server (Jetty, Reactor Netty, Tomcat, or Undertow) is now enabled by default. If you need to restore the previous behavior, set server.shutdown to immediate.
- Now that ActiveMQ Classic supports an embedded broker again, the auto-configuration has been updated to support it.
- A new PulsarContainerFactoryCustomizer interface has been added.
""",
    },
    {
        "version": "3.0.0-M4",
        "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0.0-M4-Release-Notes",
        "body": """
- Spring Boot 3.0 uses Hibernate 6.1 by default. Please see the Hibernate 6.0 and 6.1 migration guides to learn how this may affect your application.
- Trailing slash matching is no longer enabled by default. Until your application fully adapts to this change, you can change the default by configuring setUseTrailingSlashMatch(true).
- The spring.jpa.hibernate.use-new-id-generator-mappings configuration property has been removed.
- Spring Boot 3.0 uses Flyway 9.0 by default.
""",
    },
    {
        "version": "3.5.0-M3",
        "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.5.0-M3-Release-Notes",
        "body": """
- The property server.tomcat.use-apr now defaults to never. If you want to use Tomcat's APR, set the property to when-available or always.
- Removed the default value of OtlpMetricsProperties.url. However, this should lead to no visible changes as Micrometer then provides the default value.
- Logback and Log4j2 now respect the console charset.
- The transport-specific configuration properties for GraphQL have been reorganized. spring.graphql.path is now spring.graphql.http.path and spring.graphql.sse.timeout is replaced by spring.graphql.http.sse.timeout.
""",
    },
    {
        "version": "3.3-final",
        "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.3-Release-Notes",
        "body": """
- The properties spring.pulsar.listener.observation-enabled and spring.pulsar.template.observations-enabled changed their default value from true to false. This has been done to unify the observation-enabled properties, all of which now default to false.
- Spring Boot 3.3 includes support for the Prometheus Client 1.x. This release of the client contains some breaking changes, e.g. changes to the exported metric names.
- This release upgrades to Flyway 10.
""",
    },
    {
        "version": "3.5-final",
        "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.5-Release-Notes",
        "body": """
- Users of WebClient can now use properties for global configuration such as timeouts and redirect settings. As a result, some default behavior has changed to be aligned with the blocking clients; for example, follow redirects are now enabled by default.
- The default version of the Apache Pulsar client has been upgraded from 3.3.x to 4.0.x.
- Due to changes in Spring Boot's support for configuring Couchbase to use SSL, Couchbase Capella's embedded certificate will no longer be picked up automatically.
""",
    },
    {
        "version": "3.5.0-M1",
        "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.5.0-M1-Release-Notes",
        "body": """
- The spring.data.redis.database property is now ignored when spring.data.redis.url is configured, aligning its behavior with the host, port, username, and password properties. When spring.data.redis.url is configured, the Redis database that is used is determined by the URL. If the URL does not specify a database, the default of 0 is used.
- Rules for profile naming have been tightened with this release and are now more consistent. Profiles can now only contain - (dash), _ (underscore), letters and digits.
- Previous versions of Spring Boot would sometimes use conditions that considered any value other than false as enabled. Supported values for .enabled properties have been tightened.
""",
    },
    {
        "version": "3.5.0-final",
        "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.5.0-Release-Notes",
        "body": """
- The heapdump actuator endpoint now defaults to access=NONE. The aim is to help reduce the likelihood of a misconfiguration application leaking sensitive information. If you want to use it, you now need to both expose it, and configure access (previously, you only needed to expose it).
- The application_name property of the Postgres docker container is now configured by default using spring.application.name.
- The auto-configuration for Jackson retains modules that have been added prior to its execution, rather than overwriting them.
""",
    },
    {
        "version": "3.4.0-RC1",
        "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.4.0-RC1-Release-Notes",
        "body": """
- The behavior of @ConditionalOnBean and @ConditionalOnMissingBean has changed when used on a @Bean method and the annotation attribute is set. Previously, this default was not used if name, type, or value had been set. As of Spring Boot 3.4, this default will also not be used if annotation has been set.
- Support for auto-configuring RestClient and RestTemplate to use Reactor Netty's HttpClient or the JDK's HttpClient has been added.
""",
    },
]


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=str(ROOT.parent / ".demo_artifacts" / "offline_spring_boot" / "spring-boot.jsonl"),
        help="candidate JSONL output path",
    )
    parser.add_argument("--retrieved-at", default=None, help="stable ISO timestamp override")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    now = args.retrieved_at or utc_now_iso()
    all_cands = []
    for s in SAMPLES:
        cands = extract_candidates(
            library="spring-boot",
            ecosystem="jvm",
            version_label=s["version"],
            section_body=s["body"],
            source_url=s["url"],
            threshold=4,
            retrieved_at=now,
        )
        all_cands.extend(cands)

    print(f"\nTotal WEAK candidates: {len(all_cands)}\n")
    for c in all_cands:
        print(f"[{c.category.value}] {c.version_new}")
        print(f"  title: {c.title}")
        print(f"  rules: {', '.join(c.why_flagged)}")
        print(f"  url: {c.evidence[0].url}")
        print()

    out = Path(args.out)
    write_candidates_jsonl(all_cands, out)
    print(f"wrote -> {out}")

    summary = summarize(all_cands)
    print("\nsummary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
