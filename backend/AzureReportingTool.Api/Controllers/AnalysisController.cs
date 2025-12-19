using Microsoft.AspNetCore.Mvc;
using AzureReportingTool.Core.Models;
using AzureReportingTool.Core.Services;

namespace AzureReportingTool.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AnalysisController : ControllerBase
{
    private readonly IAzureFetcherService _azureFetcher;
    private readonly IAnalysisService _analysisService;
    private readonly ILogger<AnalysisController> _logger;

    public AnalysisController(
        IAzureFetcherService azureFetcher,
        IAnalysisService analysisService,
        ILogger<AnalysisController> logger)
    {
        _azureFetcher = azureFetcher;
        _analysisService = analysisService;
        _logger = logger;
    }

    [HttpPost("run")]
    public async Task<ActionResult<AnalysisResult>> RunAnalysis([FromBody] AnalysisRequest request)
    {
        try
        {
            if (request.SubscriptionId.Equals(AzureFetcherService.AllSubscriptionsIdentifier, StringComparison.OrdinalIgnoreCase))
            {
                _logger.LogInformation("Starting analysis for all subscriptions");
            }
            else
            {
                _logger.LogInformation("Starting analysis for subscription: {SubscriptionId}", request.SubscriptionId);
            }
            
            // Fetch Azure resources
            var resources = await _azureFetcher.FetchAllResourcesAsync(request.SubscriptionId);
            _logger.LogInformation("Fetched {Count} resources", resources.Count);
            
            // Analyze resources
            var result = await _analysisService.AnalyzeResourcesAsync(resources, request.Settings);
            _logger.LogInformation("Analysis completed with {Count} findings", result.Findings.Count);
            
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during analysis");
            return StatusCode(500, new { error = ex.Message });
        }
    }
}

public class AnalysisRequest
{
    public string SubscriptionId { get; set; } = string.Empty;
    public AnalysisSettings Settings { get; set; } = new();
}
