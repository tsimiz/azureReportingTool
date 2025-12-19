using Azure.Core;
using Azure.Identity;
using Azure.ResourceManager;
using Azure.ResourceManager.Resources;
using AzureReportingTool.Core.Models;

namespace AzureReportingTool.Core.Services;

public interface IAzureFetcherService
{
    Task<List<AzureResource>> FetchAllResourcesAsync(string subscriptionId);
}

public class AzureFetcherService : IAzureFetcherService
{
    private readonly ArmClient _armClient;

    public AzureFetcherService(ArmClient armClient)
    {
        _armClient = armClient;
    }

    public async Task<List<AzureResource>> FetchAllResourcesAsync(string subscriptionId)
    {
        var subscription = _armClient.GetSubscriptionResource(new ResourceIdentifier($"/subscriptions/{subscriptionId}"));
        var resources = new List<AzureResource>();
        
        await foreach (var resource in subscription.GetGenericResourcesAsync())
        {
            var azureResource = new AzureResource
            {
                Id = resource.Id.ToString(),
                Name = resource.Data.Name,
                Type = resource.Data.ResourceType.ToString(),
                Location = resource.Data.Location.ToString(),
                ResourceGroup = resource.Id.ResourceGroupName ?? string.Empty,
                Tags = resource.Data.Tags?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value) ?? new Dictionary<string, string>()
            };
            
            resources.Add(azureResource);
        }
        
        return resources;
    }
}
