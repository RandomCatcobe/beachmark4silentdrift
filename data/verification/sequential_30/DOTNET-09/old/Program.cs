using System.Globalization;
using CsvHelper;

CultureInfo.CurrentCulture = new CultureInfo("de-DE");
using var reader = new StringReader("A;B\r\n1;2\r\n");
using var csv = new CsvReader(reader);
csv.Read();
Console.WriteLine(csv.Context.Record.Length);
Console.WriteLine(string.Join("|", csv.Context.Record));
