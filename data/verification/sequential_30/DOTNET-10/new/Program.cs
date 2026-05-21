using AutoMapper;

var config = new MapperConfiguration(cfg => cfg.CreateMap<Source, Destination>());
var mapper = config.CreateMapper();
var destination = new Destination();
destination.Values.Add(1);

mapper.Map(new Source { Values = new[] { 2, 3 } }, destination);

Console.WriteLine(string.Join("|", destination.Values));

public sealed class Source
{
    public int[] Values { get; set; } = Array.Empty<int>();
}

public sealed class Destination
{
    public List<int> Values { get; } = new();
}
