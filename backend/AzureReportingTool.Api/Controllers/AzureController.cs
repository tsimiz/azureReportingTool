using Microsoft.AspNetCore.Mvc;
using Azure.Identity;
using Azure.ResourceManager;
using Azure.Core;

namespace AzureReportingTool.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AzureController : ControllerBase
{
    private readonly ILogger<AzureController> _logger;

    public AzureController(ILogger<AzureController> logger)
    {
        _logger = logger;
    }

    [HttpGet("login-status")]
    public async Task<IActionResult> GetLoginStatus()
    {
        try
        {
            var credential = new DefaultAzureCredential();
            var armClient = new ArmClient(credential);
            
            // Get default subscription
            var subscription = await armClient.GetDefaultSubscriptionAsync();
            var subscriptionData = subscription.Data;
            
            // Try to get user information from the token
            string userName = "Azure User";
            try
            {
                var tokenRequestContext = new TokenRequestContext(new[] { "https://management.azure.com/.default" });
                var token = await credential.GetTokenAsync(tokenRequestContext, default);
                
                // For Azure CLI, the user info is typically in the UPN or OID claim
                // For now, we'll use a generic name but the authentication is verified
                userName = subscriptionData.DisplayName != null ? $"User ({subscriptionData.DisplayName})" : "Azure User";
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Could not retrieve detailed user information");
            }
            
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
            var credential = new DefaultAzureCredential();
            var armClient = new ArmClient(credential);
            
            var subscriptions = new List<object>();
            var defaultSubscription = await armClient.GetDefaultSubscriptionAsync();
            var defaultSubscriptionId = defaultSubscription.Data.SubscriptionId;
            
            await foreach (var subscription in armClient.GetSubscriptions().GetAllAsync())
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
