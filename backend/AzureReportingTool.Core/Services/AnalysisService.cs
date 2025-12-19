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
    // Compliance thresholds for scoring
    private const double COST_TAG_COMPLIANCE_THRESHOLD = 0.7;
    private const double OPERATIONAL_TAG_COMPLIANCE_THRESHOLD = 0.8;
    
    // Score calculation thresholds
    private const int SCORE_HIGH_STRENGTH_THRESHOLD = 2;
    private const int SCORE_LOW_WEAKNESS_MULTIPLIER = 2;
    
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
            result.ExecutiveSummaryPillars = GeneratePillarBasedSummary(resources, result);
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
    
    
    private ExecutiveSummaryPillars GeneratePillarBasedSummary(
        List<AzureResource> resources, 
        AnalysisResult analysisResult)
    {
        var pillars = new ExecutiveSummaryPillars();
        
        // Security Pillar Analysis
        pillars.Security = AnalyzeSecurityPillar(resources, analysisResult);
        
        // Cost Optimization Pillar Analysis
        pillars.CostOptimization = AnalyzeCostOptimizationPillar(resources, analysisResult);
        
        // Operational Excellence Pillar Analysis
        pillars.OperationalExcellence = AnalyzeOperationalExcellencePillar(resources, analysisResult);
        
        // Reliability Pillar Analysis
        pillars.Reliability = AnalyzeReliabilityPillar(resources, analysisResult);
        
        // Performance Efficiency Pillar Analysis
        pillars.PerformanceEfficiency = AnalyzePerformanceEfficiencyPillar(resources, analysisResult);
        
        return pillars;
    }
    
    private PillarSummary AnalyzeSecurityPillar(List<AzureResource> resources, AnalysisResult analysisResult)
    {
        var summary = new PillarSummary
        {
            Name = "Security",
            Overview = "Security pillar focuses on protecting applications and data through defense in depth, identity management, network security, and data protection strategies aligned with Microsoft Cloud Adoption Framework (CAF) and Well-Architected Framework (WAF)."
        };
        
        // Analyze security aspects
        var nsgs = resources.Where(r => r.Type.Contains("Microsoft.Network/networkSecurityGroups")).ToList();
        var vms = resources.Where(r => r.Type.Contains("Microsoft.Compute/virtualMachines")).ToList();
        var storageAccounts = resources.Where(r => r.Type.Contains("Microsoft.Storage/storageAccounts")).ToList();
        
        var strengths = new List<string>();
        var weaknesses = new List<string>();
        var recommendations = new List<string>();
        
        // Evaluate NSGs
        if (nsgs.Any())
        {
            strengths.Add($"Network Security Groups are deployed ({nsgs.Count} NSGs found), providing network-level access controls.");
        }
        else if (vms.Any())
        {
            weaknesses.Add("No Network Security Groups detected despite having virtual machines, leaving network traffic unfiltered.");
            recommendations.Add("Implement Network Security Groups (NSGs) to control inbound and outbound traffic to Azure resources.");
        }
        
        // Evaluate VMs security
        if (vms.Any())
        {
            weaknesses.Add($"{vms.Count} virtual machines detected that may require security hardening, patch management, and Just-In-Time (JIT) access configuration.");
            recommendations.Add("Enable Azure Security Center and implement Just-In-Time VM access to reduce attack surface.");
            recommendations.Add("Ensure all VMs have proper endpoint protection, automatic patching enabled, and disk encryption configured.");
        }
        
        // Evaluate storage security
        if (storageAccounts.Any())
        {
            weaknesses.Add($"{storageAccounts.Count} storage accounts require verification of encryption at rest, secure transfer requirements, and network access controls.");
            recommendations.Add("Ensure all storage accounts have 'Secure transfer required' enabled and are configured with appropriate firewall rules and Private Endpoints where applicable.");
        }
        
        // Overall assessment
        var securityScore = CalculateScore(strengths.Count, weaknesses.Count);
        summary.Score = securityScore;
        
        summary.CurrentState = securityScore switch
        {
            "High" => "The environment demonstrates strong security controls with comprehensive network protection, proper access management, and data protection measures in place. However, continuous monitoring and improvement are essential.",
            "Medium" => "The environment has basic security controls in place but requires significant improvements to meet CAF/WAF security best practices. Critical areas such as network isolation, identity management, and data protection need attention.",
            _ => "The environment shows significant security gaps that require immediate attention. Fundamental security controls are missing or inadequately configured, exposing the environment to substantial security risks."
        };
        
        summary.Strengths = strengths;
        summary.Weaknesses = weaknesses;
        summary.Recommendations = recommendations;
        
        return summary;
    }
    
    private PillarSummary AnalyzeCostOptimizationPillar(List<AzureResource> resources, AnalysisResult analysisResult)
    {
        var summary = new PillarSummary
        {
            Name = "Cost Optimization",
            Overview = "Cost optimization pillar focuses on managing costs to maximize value delivered, including proper resource sizing, eliminating waste, and leveraging Azure cost management tools as recommended by Microsoft CAF and WAF."
        };
        
        var strengths = new List<string>();
        var weaknesses = new List<string>();
        var recommendations = new List<string>();
        
        // Analyze tagging for cost allocation
        var resourcesWithCostTags = resources.Count(r => 
            r.Tags.ContainsKey("CostCenter") || 
            r.Tags.ContainsKey("Department") || 
            r.Tags.ContainsKey("Project"));
        
        if (resources.Count > 0 && resourcesWithCostTags > resources.Count * COST_TAG_COMPLIANCE_THRESHOLD)
        {
            strengths.Add($"Good cost allocation tagging: {resourcesWithCostTags} out of {resources.Count} resources have cost-related tags, enabling proper chargeback and showback.");
        }
        else if (resources.Count > 0)
        {
            weaknesses.Add($"Poor cost allocation tagging: Only {resourcesWithCostTags} out of {resources.Count} resources have cost-related tags (CostCenter, Department, or Project).");
            recommendations.Add("Implement comprehensive tagging strategy for cost allocation and tracking. Ensure all resources have CostCenter, Department, and Project tags.");
        }
        
        // Analyze VMs for potential optimization
        var vms = resources.Where(r => r.Type.Contains("Microsoft.Compute/virtualMachines")).ToList();
        if (vms.Any())
        {
            weaknesses.Add($"{vms.Count} virtual machines detected - potential candidates for rightsizing analysis and Azure Hybrid Benefit.");
            recommendations.Add("Conduct VM rightsizing analysis to identify overprovisioned resources and potential savings.");
            recommendations.Add("Evaluate Azure Hybrid Benefit for Windows Server and SQL Server licenses to reduce costs by up to 40%.");
            recommendations.Add("Consider Azure Reserved Instances for predictable workloads to save up to 72% compared to pay-as-you-go pricing.");
        }
        
        // Analyze storage accounts
        var storageAccounts = resources.Where(r => r.Type.Contains("Microsoft.Storage/storageAccounts")).ToList();
        if (storageAccounts.Any())
        {
            weaknesses.Add($"{storageAccounts.Count} storage accounts detected - verify appropriate storage tiers and lifecycle management policies are configured.");
            recommendations.Add("Review storage account access tiers (Hot, Cool, Archive) and implement lifecycle management policies to automatically transition data to lower-cost tiers.");
        }
        
        var costScore = CalculateScore(strengths.Count, weaknesses.Count);
        summary.Score = costScore;
        
        summary.CurrentState = costScore switch
        {
            "High" => "The environment demonstrates excellent cost management practices with comprehensive tagging, appropriate resource sizing, and proactive cost optimization measures in place.",
            "Medium" => "The environment has basic cost management controls but lacks comprehensive cost optimization strategies. Significant opportunities exist for cost reduction through better tagging, rightsizing, and leveraging Azure cost management features.",
            _ => "The environment shows poor cost management practices with limited visibility into cost allocation and numerous opportunities for optimization. Immediate action is needed to implement cost controls and monitoring."
        };
        
        summary.Strengths = strengths;
        summary.Weaknesses = weaknesses;
        summary.Recommendations = recommendations;
        
        return summary;
    }
    
    private PillarSummary AnalyzeOperationalExcellencePillar(List<AzureResource> resources, AnalysisResult analysisResult)
    {
        var summary = new PillarSummary
        {
            Name = "Operational Excellence",
            Overview = "Operational excellence pillar covers operational practices and procedures used to manage production workloads, including automation, monitoring, incident response, and continuous improvement as defined in Microsoft CAF and WAF."
        };
        
        var strengths = new List<string>();
        var weaknesses = new List<string>();
        var recommendations = new List<string>();
        
        // Analyze tagging for operational management
        var resourcesWithOpTags = resources.Count(r => 
            r.Tags.ContainsKey("Environment") || 
            r.Tags.ContainsKey("Owner") || 
            r.Tags.ContainsKey("Application"));
        
        if (resources.Count > 0 && resourcesWithOpTags > resources.Count * OPERATIONAL_TAG_COMPLIANCE_THRESHOLD)
        {
            strengths.Add($"Strong operational tagging: {resourcesWithOpTags} out of {resources.Count} resources have operational tags (Environment, Owner, Application), facilitating resource management and automation.");
        }
        else if (resources.Count > 0)
        {
            weaknesses.Add($"Insufficient operational tagging: Only {resourcesWithOpTags} out of {resources.Count} resources have operational tags.");
            recommendations.Add("Implement comprehensive tagging for operational management including Environment, Owner, Application, and Criticality tags.");
        }
        
        // Resource groups analysis
        var resourceGroups = resources.Select(r => r.ResourceGroup).Distinct().Count();
        if (resourceGroups > 0)
        {
            strengths.Add($"Resources organized into {resourceGroups} resource groups, providing logical grouping for management operations.");
        }
        
        // General operational recommendations
        weaknesses.Add("Operational monitoring and alerting capabilities require verification to ensure proper observability.");
        recommendations.Add("Implement Azure Monitor and Application Insights for comprehensive monitoring and diagnostics.");
        recommendations.Add("Configure Azure Alerts for critical resource metrics and establish incident response procedures.");
        recommendations.Add("Implement Infrastructure as Code (IaC) using ARM templates, Bicep, or Terraform for consistent and repeatable deployments.");
        recommendations.Add("Establish automated backup and disaster recovery procedures aligned with business requirements.");
        
        var opScore = CalculateScore(strengths.Count, weaknesses.Count);
        summary.Score = opScore;
        
        summary.CurrentState = opScore switch
        {
            "High" => "The environment shows strong operational practices with good resource organization, comprehensive tagging, and structured management approach. Continuing to mature automation and monitoring capabilities will further enhance operational excellence.",
            "Medium" => "The environment has foundational operational practices in place but requires enhancement in areas such as monitoring, automation, and standardization to fully align with CAF/WAF operational excellence principles.",
            _ => "The environment demonstrates limited operational maturity with insufficient monitoring, automation, and standardization. Significant investment in operational practices and tooling is required to improve manageability and reduce operational overhead."
        };
        
        summary.Strengths = strengths;
        summary.Weaknesses = weaknesses;
        summary.Recommendations = recommendations;
        
        return summary;
    }
    
    private PillarSummary AnalyzeReliabilityPillar(List<AzureResource> resources, AnalysisResult analysisResult)
    {
        var summary = new PillarSummary
        {
            Name = "Reliability",
            Overview = "Reliability pillar focuses on the ability of a system to recover from failures and continue to function, including aspects of resiliency, availability, disaster recovery, and backup as outlined in Microsoft CAF and WAF."
        };
        
        var strengths = new List<string>();
        var weaknesses = new List<string>();
        var recommendations = new List<string>();
        
        // Analyze resource distribution
        var locations = resources.Select(r => r.Location).Distinct().Count();
        if (locations > 1)
        {
            strengths.Add($"Resources deployed across {locations} Azure regions, providing geographic distribution for improved resilience.");
        }
        else
        {
            weaknesses.Add("All resources appear to be in a single Azure region, creating a single point of failure.");
            recommendations.Add("Consider multi-region deployment strategy for critical workloads to improve disaster recovery capabilities.");
        }
        
        // Analyze VMs
        var vms = resources.Where(r => r.Type.Contains("Microsoft.Compute/virtualMachines")).ToList();
        if (vms.Any())
        {
            weaknesses.Add($"{vms.Count} virtual machines require validation of availability set/zone configuration, backup policies, and disaster recovery setup.");
            recommendations.Add("Deploy VMs in Availability Zones or Availability Sets to protect against datacenter-level failures.");
            recommendations.Add("Configure Azure Site Recovery (ASR) for critical VMs to enable disaster recovery capabilities.");
            recommendations.Add("Implement Azure Backup with appropriate retention policies for all virtual machines.");
        }
        
        // Analyze storage
        var storageAccounts = resources.Where(r => r.Type.Contains("Microsoft.Storage/storageAccounts")).ToList();
        if (storageAccounts.Any())
        {
            weaknesses.Add($"{storageAccounts.Count} storage accounts require verification of replication strategy (LRS, GRS, RA-GRS, ZRS).");
            recommendations.Add("Ensure storage accounts use appropriate replication strategy based on data criticality (consider GRS or RA-GRS for critical data).");
        }
        
        // General reliability recommendations
        recommendations.Add("Implement health checks and automated failover mechanisms for critical workloads.");
        recommendations.Add("Define and test disaster recovery procedures regularly, including RTO and RPO targets.");
        recommendations.Add("Use Azure Traffic Manager or Azure Front Door for global load balancing and automatic failover.");
        
        var reliabilityScore = CalculateScore(strengths.Count, weaknesses.Count);
        summary.Score = reliabilityScore;
        
        summary.CurrentState = reliabilityScore switch
        {
            "High" => "The environment demonstrates strong reliability characteristics with appropriate redundancy, geographic distribution, and disaster recovery capabilities. Continue to test and refine recovery procedures to maintain high availability.",
            "Medium" => "The environment has basic reliability measures in place but lacks comprehensive disaster recovery and high availability configurations. Improvements are needed to meet CAF/WAF reliability standards for production workloads.",
            _ => "The environment shows significant reliability gaps with limited redundancy, lack of disaster recovery capabilities, and insufficient backup strategies. Immediate action is required to improve system resilience and protect against data loss."
        };
        
        summary.Strengths = strengths;
        summary.Weaknesses = weaknesses;
        summary.Recommendations = recommendations;
        
        return summary;
    }
    
    private PillarSummary AnalyzePerformanceEfficiencyPillar(List<AzureResource> resources, AnalysisResult analysisResult)
    {
        var summary = new PillarSummary
        {
            Name = "Performance Efficiency",
            Overview = "Performance efficiency pillar focuses on the ability to scale resources to meet demand efficiently, including selecting the right resource types and sizes, monitoring performance, and optimizing for efficiency as guided by Microsoft CAF and WAF."
        };
        
        var strengths = new List<string>();
        var weaknesses = new List<string>();
        var recommendations = new List<string>();
        
        // Analyze resource types
        var resourceTypes = resources.Select(r => r.Type).Distinct().Count();
        strengths.Add($"Environment utilizes {resourceTypes} different Azure resource types, indicating diverse workload support.");
        
        // Analyze VMs
        var vms = resources.Where(r => r.Type.Contains("Microsoft.Compute/virtualMachines")).ToList();
        if (vms.Any())
        {
            weaknesses.Add($"{vms.Count} virtual machines detected - performance monitoring and auto-scaling configuration require verification.");
            recommendations.Add("Implement performance monitoring using Azure Monitor to track CPU, memory, disk, and network metrics.");
            recommendations.Add("Consider migrating appropriate workloads to PaaS services (App Service, Azure SQL, etc.) for better performance and automatic scaling.");
            recommendations.Add("Evaluate VM sizes and series to ensure they align with workload requirements and leverage modern VM types with better price-performance ratios.");
        }
        
        // Analyze storage
        var storageAccounts = resources.Where(r => r.Type.Contains("Microsoft.Storage/storageAccounts")).ToList();
        if (storageAccounts.Any())
        {
            weaknesses.Add($"{storageAccounts.Count} storage accounts require performance tier validation and consideration of Premium storage for high-performance workloads.");
            recommendations.Add("Review storage account performance tiers and consider Premium SSD for I/O intensive workloads.");
        }
        
        // Analyze networks
        var vnets = resources.Where(r => r.Type.Contains("Microsoft.Network/virtualNetworks")).ToList();
        if (vnets.Any())
        {
            strengths.Add($"{vnets.Count} virtual networks configured, enabling network segmentation and optimized traffic routing.");
            recommendations.Add("Implement Azure ExpressRoute for high-throughput, low-latency connections to on-premises resources if applicable.");
        }
        
        // General performance recommendations
        recommendations.Add("Implement Content Delivery Network (CDN) for static content to improve global performance and reduce latency.");
        recommendations.Add("Use Application Gateway or Azure Load Balancer to distribute traffic and improve application responsiveness.");
        recommendations.Add("Configure auto-scaling policies based on performance metrics to handle variable workloads efficiently.");
        
        var perfScore = CalculateScore(strengths.Count, weaknesses.Count);
        summary.Score = perfScore;
        
        summary.CurrentState = perfScore switch
        {
            "High" => "The environment demonstrates strong performance efficiency characteristics with appropriate resource selection, good network design, and consideration for scalability. Continue monitoring and optimizing based on performance metrics.",
            "Medium" => "The environment has adequate performance capabilities but would benefit from enhanced monitoring, optimization of resource types, and implementation of auto-scaling capabilities to fully align with CAF/WAF performance efficiency principles.",
            _ => "The environment shows performance efficiency gaps with potential resource sizing issues, lack of performance monitoring, and limited scalability mechanisms. Performance optimization efforts are needed to ensure workloads meet business requirements."
        };
        
        summary.Strengths = strengths;
        summary.Weaknesses = weaknesses;
        summary.Recommendations = recommendations;
        
        return summary;
    }
    
    private string CalculateScore(int strengthCount, int weaknessCount)
    {
        if (strengthCount > weaknessCount && strengthCount > SCORE_HIGH_STRENGTH_THRESHOLD)
        {
            return "High";
        }
        else if (weaknessCount > strengthCount * SCORE_LOW_WEAKNESS_MULTIPLIER)
        {
            return "Low";
        }
        return "Medium";
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
