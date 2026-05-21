# Environment For DOTNET-08

- Runtime: .NET SDK capable of building the console probe.
- Package versions: FluentValidation 8.6.2 and 9.0.0.
- Version switching: set DOTNET_ADAPTER_PACKAGE_PATH to the selected NuGet package root.
- Adapter/API surface: library-api, validator.
- Probe shape: run the console project and parse one JSON object from stdout.
- Command shape: DOTNET_ADAPTER_PACKAGE_PATH=<old-or-new-package-root> dotnet run --project client/probe.csproj.
