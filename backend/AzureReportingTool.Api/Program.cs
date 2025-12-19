using AzureReportingTool.Core.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add CORS policy to allow React frontend
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend",
        policy =>
        {
            policy.WithOrigins("http://localhost:5173", "http://localhost:3000")
                  .AllowAnyMethod()
                  .AllowAnyHeader();
        });
});

// Register application services
builder.Services.AddScoped<IAzureFetcherService, AzureFetcherService>();
builder.Services.AddScoped<IAnalysisService, AnalysisService>();

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("AllowFrontend");

// Only use HTTPS redirection when running with HTTPS configured
if (app.Environment.IsProduction() || builder.Configuration.GetValue<bool>("UseHttpsRedirection", false))
{
    app.UseHttpsRedirection();
}

app.UseAuthorization();
app.MapControllers();

app.Run();
