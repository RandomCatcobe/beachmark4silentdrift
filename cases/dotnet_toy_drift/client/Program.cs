var paths = Environment.GetEnvironmentVariable("DOTNET_ADAPTER_PACKAGE_PATHS") ?? "";
var firstPath = paths.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries).FirstOrDefault();
if (firstPath is null)
{
    Console.Error.WriteLine("DOTNET_ADAPTER_PACKAGE_PATHS was empty");
    Environment.Exit(2);
}

Console.WriteLine(File.ReadAllText(Path.Combine(firstPath, "value.txt")).Trim());
