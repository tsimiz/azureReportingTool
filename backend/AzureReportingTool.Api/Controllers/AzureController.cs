using Microsoft.AspNetCore.Mvc;

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
    public IActionResult GetLoginStatus()
    {
        // In production, this would check Azure CLI or use proper authentication
        return Ok(new
        {
            logged_in = true,
            user = "Azure User",
            subscription_id = "00000000-0000-0000-0000-000000000000",
            subscription_name = "Default Subscription"
        });
    }

    [HttpGet("subscriptions")]
    public IActionResult GetSubscriptions()
    {
        // In production, this would fetch actual subscriptions
        return Ok(new[]
        {
            new
            {
                id = "00000000-0000-0000-0000-000000000000",
                name = "Default Subscription",
                is_default = true
            }
        });
    }
}
