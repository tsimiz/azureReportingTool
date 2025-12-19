using Microsoft.AspNetCore.Mvc;
using Azure.ResourceManager;

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
            
            return Ok(new
            {
                logged_in = true,
                user = userName,
                subscription_id = subscriptionData.SubscriptionId,
                subscription_name = subscriptionData.DisplayName
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to authenticate with Azure");
            return Ok(new
            {
                logged_in = false,
                user = "Not authenticated",
                subscription_id = "",
                subscription_name = "No subscription available"
            });
        }
    }

    [HttpGet("subscriptions")]
    public async Task<IActionResult> GetSubscriptions()
    {
        try
        {
            var subscriptions = new List<object>();
            var defaultSubscription = await _armClient.GetDefaultSubscriptionAsync();
            var defaultSubscriptionId = defaultSubscription.Data.SubscriptionId;
            
            await foreach (var subscription in _armClient.GetSubscriptions().GetAllAsync())
            {
                subscriptions.Add(new
                {
                    id = subscription.Data.SubscriptionId,
                    name = subscription.Data.DisplayName,
                    is_default = subscription.Data.SubscriptionId == defaultSubscriptionId
                });
            }
            
            _logger.LogInformation("Retrieved {Count} subscriptions", subscriptions.Count);
            return Ok(subscriptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to fetch subscriptions");
            return StatusCode(500, new { error = "Failed to fetch subscriptions. Please ensure you are logged in with Azure CLI (az login)." });
        }
    }
}
