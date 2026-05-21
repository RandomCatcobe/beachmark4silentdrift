using System;
using FluentValidation;

public sealed class Model
{
    public string Email { get; set; } = "";
}

public sealed class EmailValidator : AbstractValidator<Model>
{
    public EmailValidator()
    {
        RuleFor(model => model.Email).EmailAddress();
    }
}

public static class Program
{
    public static void Main()
    {
        var validator = new EmailValidator();
        var samples = new[]
        {
            "a@b",
            "x@y.z",
            "plainaddress",
            "@missing-local",
            "x y@example.com"
        };

        Console.Write("{\"results\":{");
        for (var i = 0; i < samples.Length; i++)
        {
            var sample = samples[i];
            var valid = validator.Validate(new Model { Email = sample }).IsValid;
            if (i > 0)
            {
                Console.Write(",");
            }

            Console.Write("\"");
            Console.Write(Escape(sample));
            Console.Write("\":");
            Console.Write(valid ? "true" : "false");
        }

        Console.WriteLine("}}");
    }

    private static string Escape(string value)
    {
        return value.Replace("\\", "\\\\").Replace("\"", "\\\"");
    }
}
