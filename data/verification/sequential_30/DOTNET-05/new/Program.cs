using Microsoft.Extensions.Configuration;

var dict = new Dictionary<string, string[]>
{
    ["Key"] = new[] { "InitialValue" },
};

var config = new ConfigurationBuilder()
    .AddInMemoryCollection(new Dictionary<string, string?>
    {
        ["Key:0"] = "NewValue",
    })
    .Build();

config.Bind(dict);

Console.WriteLine(string.Join("|", dict["Key"]));
