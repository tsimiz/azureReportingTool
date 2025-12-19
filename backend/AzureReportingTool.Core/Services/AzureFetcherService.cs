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
        var resources = new List<AzureResource>();
        
        // If subscriptionId is "all", iterate through all subscriptions
        if (subscriptionId.Equals("all", StringComparison.OrdinalIgnoreCase))
        {
            await foreach (var subscription in _armClient.GetSubscriptions().GetAllAsync())
            {
                await foreach (var resource in subscription.GetGenericResourcesAsync())
                {
                    resources.Add(MapToAzureResource(resource));
                }
            }
        }
        else
        {
            // Single subscription case
            var subscription = _armClient.GetSubscriptionResource(new ResourceIdentifier($"/subscriptions/{subscriptionId}"));
            
            await foreach (var resource in subscription.GetGenericResourcesAsync())
            {
                resources.Add(MapToAzureResource(resource));
            }
        }
        
        return resources;
    }

    private static AzureResource MapToAzureResource(Azure.ResourceManager.Resources.GenericResource resource)
    {
        return new AzureResource
        {
            Id = resource.Id.ToString(),
            Name = resource.Data.Name,
            Type = resource.Data.ResourceType.ToString(),
            Location = resource.Data.Location.ToString(),
            ResourceGroup = resource.Id.ResourceGroupName ?? string.Empty,
            Tags = resource.Data.Tags?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value) ?? new Dictionary<string, string>()
        };
    }
}
