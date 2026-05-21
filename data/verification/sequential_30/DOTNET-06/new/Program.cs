using Microsoft.EntityFrameworkCore;

using (var seed = new ShopContext())
{
    seed.Database.EnsureDeleted();
    seed.Database.EnsureCreated();
    seed.Categories.Add(new Category
    {
        Id = 1,
        Name = "Shared",
        Products =
        {
            new Product { Id = 10, Name = "A" },
            new Product { Id = 11, Name = "B" },
        },
    });
    seed.SaveChanges();
}

using var db = new ShopContext();
var products = db.Products
    .AsNoTracking()
    .Include(product => product.Category)
    .OrderBy(product => product.Id)
    .ToList();

Console.WriteLine(ReferenceEquals(products[0].Category, products[1].Category));
Console.WriteLine(products[0].Category?.Name + "|" + products[1].Category?.Name);

public sealed class ShopContext : DbContext
{
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Product> Products => Set<Product>();

    protected override void OnConfiguring(DbContextOptionsBuilder options)
        => options.UseInMemoryDatabase("dotnet06");
}

public sealed class Category
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public List<Product> Products { get; } = new();
}

public sealed class Product
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public int CategoryId { get; set; }
    public Category? Category { get; set; }
}
