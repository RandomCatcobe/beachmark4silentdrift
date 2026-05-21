# Environment For JS-09

- Runtime: Node.js with a package root containing dotenv.
- Package versions: dotenv 14.3.2 and dotenv 15.0.1.
- Version switching: run with NODE_PATH or an equivalent package root pointing at the selected dotenv installation.
- Adapter/API surface: library-api, parser, config-file.
- Probe shape: run probe.js and parse one JSON object from stdout.
- Command shape: NODE_PATH=<old-or-new-node_modules> node client/probe.js.
