using Azure.Core;
using Azure.Identity;
using Azure.ResourceManager;
using Azure.ResourceManager.Resources;
using AzureReportingTool.Core.Models;
using Microsoft.Extensions.Logging;

namespace AzureReportingTool.Core.Services;

public interface IAzureFetcherService
{
    Task<List<AzureResource>> FetchAllResourcesAsync(string subscriptionId);
}

public class AzureFetcherService : IAzureFetcherService
{
    public const string AllSubscriptionsIdentifier = "all";
    
    private readonly ArmClient _armClient;
    private readonly ILogger<AzureFetcherService> _logger;

    public AzureFetcherService(ArmClient armClient, ILogger<AzureFetcherService> logger)
    {
        _armClient = armClient;
        _logger = logger;
    }

    public async Task<List<AzureResource>> FetchAllResourcesAsync(string subscriptionId)
    {
        var resources = new List<AzureResource>();
        
        // If subscriptionId is "all", iterate through all subscriptions
        if (subscriptionId.Equals(AllSubscriptionsIdentifier, StringComparison.OrdinalIgnoreCase))
        {
            await foreach (var subscription in _armClient.GetSubscriptions().GetAllAsync())
            {
                try
                {
                    _logger.LogInformation("Fetching resources from subscription: {SubscriptionId}", subscription.Data.SubscriptionId);
                    
                    await foreach (var resource in subscription.GetGenericResourcesAsync())
                    {
                        resources.Add(MapToAzureResource(resource));
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Failed to fetch resources from subscription {SubscriptionId}. Skipping this subscription.", subscription.Data.SubscriptionId);
                    // Continue with the next subscription instead of failing the entire operation
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

    private static AzureResource MapToAzureResource(GenericResource resource)
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
