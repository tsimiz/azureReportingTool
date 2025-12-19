using Microsoft.AspNetCore.Mvc;
using Azure.ResourceManager;
using System.Text.Json.Serialization;

namespace AzureReportingTool.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AzureController : ControllerBase
{
    private readonly ILogger<AzureController> _logger;
    private readonly ArmClient _armClient;

    public AzureController(ILogger<AzureController> logger, ArmClient armClient)
    {
        _logger = logger;
        _armClient = armClient;
    }

    [HttpGet("login-status")]
    public async Task<IActionResult> GetLoginStatus()
    {
        try
        {
            // Get default subscription
            var subscription = await _armClient.GetDefaultSubscriptionAsync();
            var subscriptionData = subscription.Data;
            
            // For DefaultAzureCredential, we don't have direct access to user details
            // The user is authenticated via Azure CLI, Managed Identity, or other methods
            // We use "Authenticated User" as a generic display name
            string userName = "Authenticated User";
            
            _logger.LogInformation("Successfully authenticated with subscription: {SubscriptionId}", subscriptionData.SubscriptionId);
            
            return Ok(new LoginStatusResponse
            {
                LoggedIn = true,
                User = userName,
                SubscriptionId = subscriptionData.SubscriptionId,
                SubscriptionName = subscriptionData.DisplayName
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to authenticate with Azure");
            return Ok(new LoginStatusResponse
            {
                LoggedIn = false,
                User = "Not authenticated",
                SubscriptionId = "",
                SubscriptionName = "No subscription available"
            });
        }
    }

    [HttpGet("subscriptions")]
    public async Task<IActionResult> GetSubscriptions()
    {
        try
        {
            var subscriptions = new List<SubscriptionInfo>();
            var defaultSubscription = await _armClient.GetDefaultSubscriptionAsync();
            var defaultSubscriptionId = defaultSubscription.Data.SubscriptionId;
            
            await foreach (var subscription in _armClient.GetSubscriptions().GetAllAsync())
            {
                subscriptions.Add(new SubscriptionInfo
                {
                    Id = subscription.Data.SubscriptionId,
                    Name = subscription.Data.DisplayName,
                    IsDefault = subscription.Data.SubscriptionId == defaultSubscriptionId
                });
            }
            
            _logger.LogInformation("Retrieved {Count} subscriptions", subscriptions.Count);
            return Ok(subscriptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to fetch subscriptions");
            return StatusCode(500, new { error = "Failed to fetch subscriptions. Please ensure you are authenticated with Azure (e.g., using 'az login', managed identity, or service principal credentials)." });
        }
    }
}

public class LoginStatusResponse
{
    [JsonPropertyName("logged_in")]
    public bool LoggedIn { get; set; }
    
    [JsonPropertyName("user")]
    public string User { get; set; } = string.Empty;
    
    [JsonPropertyName("subscription_id")]
    public string SubscriptionId { get; set; } = string.Empty;
    
    [JsonPropertyName("subscription_name")]
    public string SubscriptionName { get; set; } = string.Empty;
}

public class SubscriptionInfo
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;
    
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;
    
    [JsonPropertyName("is_default")]
    public bool IsDefault { get; set; }
}
