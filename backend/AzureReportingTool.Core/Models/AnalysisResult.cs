namespace AzureReportingTool.Core.Models;

public class AnalysisResult
{
    public string ExecutiveSummary { get; set; } = string.Empty;
    public List<Finding> Findings { get; set; } = new();
    public Dictionary<string, object> Statistics { get; set; } = new();
    public TagComplianceResult? TagCompliance { get; set; }
    public CostAnalysisResult? CostAnalysis { get; set; }
}

public class Finding
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string ResourceName { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public string Severity { get; set; } = "Medium";
    public string Issue { get; set; } = string.Empty;
    public string Recommendation { get; set; } = string.Empty;
    public string EstimatedEffort { get; set; } = "Medium";
    public int Priority { get; set; }
}

public class TagComplianceResult
{
    public int TotalResources { get; set; }
    public int ResourcesWithTags { get; set; }
    public int ComplianceRate { get; set; }
    public List<string> RequiredTags { get; set; } = new();
    public List<ResourceGroupCompliance> ResourceGroups { get; set; } = new();
}

public class ResourceGroupCompliance
{
    public string Name { get; set; } = string.Empty;
    public int TotalResources { get; set; }
    public int NonCompliantResources { get; set; }
    public int ComplianceRate { get; set; }
    public List<string> MissingTags { get; set; } = new();
}

public class CostAnalysisResult
{
    public int TotalResourcesAnalyzed { get; set; }
    public int TotalFindings { get; set; }
    public int ImmediateActions { get; set; }
    public int ReviewsNeeded { get; set; }
    public List<Finding> Findings { get; set; } = new();
}
