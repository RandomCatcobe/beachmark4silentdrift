# Environment For RB-RACK-005

- Runtime: Ruby with rack available on the load path.
- Package versions: rack 2.2.9 and rack 3.1.0.
- Version switching: pass the selected rack lib directory with -I or RUBYLIB.
- Adapter/API surface: library-api, parser.
- Probe shape: run probe.rb and parse one JSON object from stdout.
- Command shape: ruby -I <old-or-new-rack-lib> client/probe.rb.
