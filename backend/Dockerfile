# Backend Dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy solution and project files
COPY backend/AzureReportingTool.sln ./
COPY backend/AzureReportingTool.Api/AzureReportingTool.Api.csproj ./AzureReportingTool.Api/
COPY backend/AzureReportingTool.Core/AzureReportingTool.Core.csproj ./AzureReportingTool.Core/

# Restore dependencies
RUN dotnet restore

# Copy source code
COPY backend/ ./

# Build the application
RUN dotnet publish AzureReportingTool.Api/AzureReportingTool.Api.csproj -c Release -o /app/publish

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app/publish .

# Expose port
EXPOSE 5000

# Set environment variables
ENV ASPNETCORE_URLS=http://+:5000

# Run the application
ENTRYPOINT ["dotnet", "AzureReportingTool.Api.dll"]
