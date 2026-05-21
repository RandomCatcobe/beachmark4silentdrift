# Environment For JS-06

- Runtime: Node.js with a package root containing zod.
- Package versions: zod 3.25.76 and zod 4.1.12.
- Version switching: run with NODE_PATH or an equivalent package root pointing at the selected zod installation.
- Adapter/API surface: library-api, validator.
- Probe shape: run probe.js and parse one JSON object from stdout.
- Command shape: NODE_PATH=<old-or-new-node_modules> node client/probe.js.
