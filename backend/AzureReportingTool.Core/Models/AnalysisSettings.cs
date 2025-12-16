namespace AzureReportingTool.Core.Models;

public class AnalysisSettings
{
    public string OutputDirectory { get; set; } = "./output";
    public string ReportFilename { get; set; } = "azure_report";
    public string ExportFormat { get; set; } = "pdf";
    public bool AiEnabled { get; set; } = true;
    public string AiModel { get; set; } = "gpt-4";
    public float AiTemperature { get; set; } = 0.3f;
    public ResourceSettings Resources { get; set; } = new();
    public TagAnalysisSettings TagAnalysis { get; set; } = new();
}

public class ResourceSettings
{
    public bool VirtualMachines { get; set; } = true;
    public bool StorageAccounts { get; set; } = true;
    public bool NetworkSecurityGroups { get; set; } = true;
    public bool VirtualNetworks { get; set; } = true;
    public bool AnalyzeAllResources { get; set; } = true;
}

public class TagAnalysisSettings
{
    public bool Enabled { get; set; } = false;
    public List<string> RequiredTags { get; set; } = new();
    public List<string> InvalidTagValues { get; set; } = new();
}
