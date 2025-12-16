using Azure;
using Azure.AI.OpenAI;
using AzureReportingTool.Core.Models;

namespace AzureReportingTool.Core.Services;

public interface IAnalysisService
{
    Task<AnalysisResult> AnalyzeResourcesAsync(List<AzureResource> resources, AnalysisSettings settings);
}

public class AnalysisService : IAnalysisService
{
    public async Task<AnalysisResult> AnalyzeResourcesAsync(List<AzureResource> resources, AnalysisSettings settings)
    {
        var result = new AnalysisResult
        {
            Statistics = new Dictionary<string, object>
            {
                ["TotalResources"] = resources.Count,
                ["ResourceTypes"] = resources.Select(r => r.Type).Distinct().Count()
            }
        };
        
        // Perform tag analysis if enabled
        if (settings.TagAnalysis.Enabled)
        {
            result.TagCompliance = AnalyzeTagCompliance(resources, settings.TagAnalysis);
        }
        
        // Perform cost analysis
        result.CostAnalysis = PerformCostAnalysis(resources);
        
        // AI analysis if enabled
        if (settings.AiEnabled)
        {
            result.ExecutiveSummary = await GenerateAISummaryAsync(resources, settings);
            result.Findings.AddRange(await GenerateAIFindingsAsync(resources, settings));
        }
        
        // Add findings from tag and cost analysis
        if (result.TagCompliance != null)
        {
            result.Findings.AddRange(GenerateTagFindings(result.TagCompliance));
        }
        
        if (result.CostAnalysis != null)
        {
            result.Findings.AddRange(result.CostAnalysis.Findings);
        }
        
        // Update statistics
        result.Statistics["TotalFindings"] = result.Findings.Count;
        result.Statistics["CriticalFindings"] = result.Findings.Count(f => f.Severity == "Critical");
        result.Statistics["HighFindings"] = result.Findings.Count(f => f.Severity == "High");
        
        return result;
    }
    
    private TagComplianceResult AnalyzeTagCompliance(List<AzureResource> resources, TagAnalysisSettings settings)
    {
        var result = new TagComplianceResult
        {
            TotalResources = resources.Count,
            ResourcesWithTags = resources.Count(r => r.Tags.Any()),
            RequiredTags = settings.RequiredTags
        };
        
        var compliantCount = 0;
        foreach (var resource in resources)
        {
            var missingTags = settings.RequiredTags.Where(tag => !resource.Tags.ContainsKey(tag)).ToList();
            var invalidTags = resource.Tags
                .Where(kvp => settings.InvalidTagValues.Contains(kvp.Value.ToLower()))
                .ToList();
            
            if (missingTags.Count == 0 && invalidTags.Count == 0)
            {
                compliantCount++;
            }
        }
        
        result.ComplianceRate = resources.Count > 0 ? (int)((compliantCount * 100.0) / resources.Count) : 100;
        
        // Group by resource group
        var resourceGroups = resources.GroupBy(r => r.ResourceGroup);
        foreach (var rg in resourceGroups)
        {
            var rgCompliant = 0;
            foreach (var resource in rg)
            {
                var missingTags = settings.RequiredTags.Where(tag => !resource.Tags.ContainsKey(tag)).ToList();
                if (missingTags.Count == 0)
                {
                    rgCompliant++;
                }
            }
            
            var rgTotal = rg.Count();
            result.ResourceGroups.Add(new ResourceGroupCompliance
            {
                Name = rg.Key,
                TotalResources = rgTotal,
                NonCompliantResources = rgTotal - rgCompliant,
                ComplianceRate = rgTotal > 0 ? (int)((rgCompliant * 100.0) / rgTotal) : 100
            });
        }
        
        return result;
    }
    
    private CostAnalysisResult PerformCostAnalysis(List<AzureResource> resources)
    {
        var findings = new List<Finding>();
        
        // Analyze VMs
        var vms = resources.Where(r => r.Type.Contains("Microsoft.Compute/virtualMachines")).ToList();
        foreach (var vm in vms)
        {
            if (!vm.Tags.ContainsKey("CostCenter"))
            {
                findings.Add(new Finding
                {
                    ResourceName = vm.Name,
                    Category = "Cost Optimization",
                    Severity = "Medium",
                    Issue = "VM missing cost allocation tags",
                    Recommendation = "Add CostCenter tag for cost tracking",
                    EstimatedEffort = "Low",
                    Priority = findings.Count + 1
                });
            }
        }
        
        return new CostAnalysisResult
        {
            TotalResourcesAnalyzed = resources.Count,
            TotalFindings = findings.Count,
            ImmediateActions = findings.Count(f => f.Severity == "Critical"),
            ReviewsNeeded = findings.Count(f => f.Severity == "High"),
            Findings = findings
        };
    }
    
    private async Task<string> GenerateAISummaryAsync(List<AzureResource> resources, AnalysisSettings settings)
    {
        // Simplified - in production, would use OpenAI API
        await Task.CompletedTask;
        return $"Analysis of {resources.Count} Azure resources across {resources.Select(r => r.Type).Distinct().Count()} resource types. " +
               "The environment shows a mix of compute, storage, and networking resources that require security and cost optimization review.";
    }
    
    private async Task<List<Finding>> GenerateAIFindingsAsync(List<AzureResource> resources, AnalysisSettings settings)
    {
        // Simplified - in production, would use OpenAI API
        await Task.CompletedTask;
        var findings = new List<Finding>();
        
        // Generate sample findings
        var vms = resources.Where(r => r.Type.Contains("Microsoft.Compute/virtualMachines")).Take(3);
        foreach (var vm in vms)
        {
            findings.Add(new Finding
            {
                ResourceName = vm.Name,
                Category = "Security",
                Severity = "High",
                Issue = "Virtual machine may not have proper network security configuration",
                Recommendation = "Review NSG rules and enable Just-In-Time VM access",
                EstimatedEffort = "Medium",
                Priority = findings.Count + 1
            });
        }
        
        return findings;
    }
    
    private List<Finding> GenerateTagFindings(TagComplianceResult tagCompliance)
    {
        var findings = new List<Finding>();
        
        foreach (var rg in tagCompliance.ResourceGroups.Where(rg => rg.NonCompliantResources > 0))
        {
            findings.Add(new Finding
            {
                ResourceName = rg.Name,
                Category = "Tag Compliance",
                Severity = rg.ComplianceRate < 50 ? "High" : "Medium",
                Issue = $"{rg.NonCompliantResources} resources in resource group are missing required tags",
                Recommendation = $"Add required tags to resources in {rg.Name}",
                EstimatedEffort = "Low",
                Priority = findings.Count + 1
            });
        }
        
        return findings;
    }
}
