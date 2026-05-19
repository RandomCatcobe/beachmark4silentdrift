You are writing a minimal Python reproduction client.
Use only the redacted public context below.
Do not infer or include withheld outputs, private validation logic, private paths, repair hints, or truth labels.
Return only Python source code for a client with a main() entrypoint.

Public context:
{
  "library": "pandas",
  "ecosystem": "python",
  "version_old": "1.5.3",
  "version_new": "2.0.3",
  "api_surface": [
    "pandas.Series.str.replace"
  ],
  "public_intent": "Exercise public behavior of pandas.Series.str.replace without expected old/new outputs.",
  "allowed_imports": [
    "json",
    "pandas"
  ],
  "forbidden_terms": [
    "withheld expected outputs",
    "private validation logic",
    "private validation paths",
    "repair hints",
    "observed old/new diffs",
    "curated truth labels"
  ]
}

Constraints:
- Keep the client deterministic.
- Do not read clocks, network, random sources, or local files unless explicitly required by public_intent.
- Print a JSON object with enough public observations for the reproduction harness to diff.
