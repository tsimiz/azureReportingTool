"""Module for analyzing Azure resource costs and providing optimization recommendations."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CostAnalyzer:
    """Analyzes Azure resource costs and provides optimization recommendations."""

    # VM size categories for cost optimization recommendations
    VM_SIZE_CATEGORIES = {
        'burstable': ['Standard_B'],
        'general_purpose': ['Standard_D', 'Standard_DS'],
        'compute_optimized': ['Standard_F', 'Standard_FS'],
        'memory_optimized': ['Standard_E', 'Standard_ES', 'Standard_M'],
        'storage_optimized': ['Standard_L'],
        'gpu': ['Standard_N', 'Standard_NC', 'Standard_ND', 'Standard_NV'],
    }

    # Storage redundancy cost tiers (relative cost order)
    STORAGE_REDUNDANCY_COST = {
        'Standard_LRS': 1,
        'Standard_ZRS': 2,
        'Standard_GRS': 3,
        'Standard_RAGRS': 4,
        'Standard_GZRS': 5,
        'Standard_RAGZRS': 6,
        'Premium_LRS': 7,
        'Premium_ZRS': 8,
    }

    def __init__(self, cost_data: Optional[Dict[str, Any]] = None):
        """Initialize cost analyzer.
        
        Args:
            cost_data: Optional cost data from Azure Cost Management API.
                      If not provided, analysis will be based on resource configuration.
        """
        self.cost_data = cost_data or {}
        logger.info("Cost analyzer initialized")

    def analyze_costs(self, resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze costs across all resources and generate optimization recommendations.
        
        Args:
            resources: Dictionary of resource type to list of resources
            
        Returns:
            Dictionary containing cost analysis results and recommendations
        """
        logger.info("Starting cost analysis...")
        
        findings = []
        recommendations = []
        
        # Analyze virtual machines
        vm_findings = self._analyze_vm_costs(resources.get('virtual_machines', []))
        findings.extend(vm_findings)
        
        # Analyze storage accounts
        storage_findings = self._analyze_storage_costs(resources.get('storage_accounts', []))
        findings.extend(storage_findings)
        
        # Analyze resource groups for orphaned resources
        orphan_findings = self._analyze_orphaned_resources(resources)
        findings.extend(orphan_findings)
        
        # Analyze all resources for general cost patterns
        general_findings = self._analyze_general_cost_patterns(resources.get('all_resources', []))
        findings.extend(general_findings)
        
        # Generate summary
        summary = self._generate_summary(findings, resources)
        
        # Generate optimization recommendations
        recommendations = self._generate_recommendations(findings)
        
        analysis_result = {
            'summary': summary,
            'findings': findings,
            'recommendations': recommendations,
            'optimization_opportunities': self._count_opportunities(findings),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"Cost analysis complete. Found {len(findings)} cost optimization opportunities.")
        return analysis_result

    def _analyze_vm_costs(self, vms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze virtual machine costs and identify optimization opportunities.
        
        Args:
            vms: List of virtual machine resources
            
        Returns:
            List of cost-related findings
        """
        findings = []
        
        for vm in vms:
            vm_name = vm.get('name', 'Unknown')
            vm_size = vm.get('vm_size', '')
            statuses = vm.get('statuses', [])
            
            # Check for deallocated VMs still incurring storage costs
            if any('deallocated' in str(s).lower() for s in statuses):
                findings.append({
                    'resource': vm_name,
                    'resource_type': 'Virtual Machine',
                    'category': 'cost',
                    'severity': 'medium',
                    'issue': f"VM '{vm_name}' is deallocated but still incurs storage costs",
                    'recommendation': 'Consider deleting the VM if no longer needed, or use Azure Reserved Instances for cost savings',
                    'potential_savings': 'Storage costs for deallocated VM',
                    'optimization_type': 'deallocated_vm'
                })
            
            # Check for stopped (not deallocated) VMs still incurring compute costs
            if any('stopped' in str(s).lower() and 'deallocated' not in str(s).lower() for s in statuses):
                findings.append({
                    'resource': vm_name,
                    'resource_type': 'Virtual Machine',
                    'category': 'cost',
                    'severity': 'high',
                    'issue': f"VM '{vm_name}' is stopped but not deallocated - still incurring compute charges",
                    'recommendation': 'Deallocate the VM to stop compute charges, or delete if no longer needed',
                    'potential_savings': 'Full compute costs while stopped',
                    'optimization_type': 'stopped_vm'
                })
            
            # Check for oversized VMs (GPU VMs in non-GPU workloads detection)
            if any(vm_size.startswith(prefix) for prefix in self.VM_SIZE_CATEGORIES.get('gpu', [])):
                findings.append({
                    'resource': vm_name,
                    'resource_type': 'Virtual Machine',
                    'category': 'cost',
                    'severity': 'medium',
                    'issue': f"VM '{vm_name}' uses GPU-enabled size ({vm_size}) - verify GPU is required",
                    'recommendation': 'Review if GPU capabilities are being utilized. If not, switch to a non-GPU VM size',
                    'potential_savings': 'GPU VMs cost significantly more than non-GPU alternatives',
                    'optimization_type': 'gpu_vm_review'
                })
            
            # Check for memory-optimized VMs
            if any(vm_size.startswith(prefix) for prefix in self.VM_SIZE_CATEGORIES.get('memory_optimized', [])):
                findings.append({
                    'resource': vm_name,
                    'resource_type': 'Virtual Machine',
                    'category': 'cost',
                    'severity': 'low',
                    'issue': f"VM '{vm_name}' uses memory-optimized size ({vm_size})",
                    'recommendation': 'Verify memory-intensive workloads. Consider right-sizing if memory utilization is low',
                    'potential_savings': 'Right-sizing can reduce costs by 20-50%',
                    'optimization_type': 'memory_vm_review'
                })
            
            # Recommend reserved instances for running VMs
            if any('running' in str(s).lower() for s in statuses):
                findings.append({
                    'resource': vm_name,
                    'resource_type': 'Virtual Machine',
                    'category': 'cost',
                    'severity': 'low',
                    'issue': f"VM '{vm_name}' is running - consider Reserved Instances",
                    'recommendation': 'For consistently running VMs, Azure Reserved Instances can save up to 72% compared to pay-as-you-go',
                    'potential_savings': 'Up to 72% savings with 3-year Reserved Instance',
                    'optimization_type': 'reserved_instance'
                })
        
        return findings

    def _analyze_storage_costs(self, storage_accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze storage account costs and identify optimization opportunities.
        
        Args:
            storage_accounts: List of storage account resources
            
        Returns:
            List of cost-related findings
        """
        findings = []
        
        for sa in storage_accounts:
            sa_name = sa.get('name', 'Unknown')
            sku = sa.get('sku', '')
            kind = sa.get('kind', '')
            
            # Check for premium storage
            if 'Premium' in str(sku):
                findings.append({
                    'resource': sa_name,
                    'resource_type': 'Storage Account',
                    'category': 'cost',
                    'severity': 'medium',
                    'issue': f"Storage account '{sa_name}' uses Premium tier ({sku})",
                    'recommendation': 'Premium storage is significantly more expensive. Ensure high IOPS/low latency is required',
                    'potential_savings': 'Standard storage can be 80% cheaper than Premium',
                    'optimization_type': 'premium_storage_review'
                })
            
            # Check for geo-redundant storage
            if any(tier in str(sku) for tier in ['GRS', 'RAGRS', 'GZRS', 'RAGZRS']):
                findings.append({
                    'resource': sa_name,
                    'resource_type': 'Storage Account',
                    'category': 'cost',
                    'severity': 'low',
                    'issue': f"Storage account '{sa_name}' uses geo-redundant replication ({sku})",
                    'recommendation': 'If geo-redundancy is not required, consider LRS or ZRS for lower costs',
                    'potential_savings': 'LRS costs about 50% less than GRS',
                    'optimization_type': 'storage_redundancy_review'
                })
            
            # Check for BlobStorage kind (legacy)
            if kind == 'BlobStorage':
                findings.append({
                    'resource': sa_name,
                    'resource_type': 'Storage Account',
                    'category': 'cost',
                    'severity': 'low',
                    'issue': f"Storage account '{sa_name}' uses legacy BlobStorage kind",
                    'recommendation': 'Consider migrating to StorageV2 for better features and potential cost savings',
                    'potential_savings': 'StorageV2 offers better tiering options for cost optimization',
                    'optimization_type': 'legacy_storage'
                })
        
        return findings

    def _analyze_orphaned_resources(self, resources: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Analyze for potentially orphaned resources.
        
        Args:
            resources: Dictionary of all resources
            
        Returns:
            List of orphaned resource findings
        """
        findings = []
        all_resources = resources.get('all_resources', [])
        
        # Common orphaned resource types
        orphan_types = {
            'Microsoft.Network/publicIPAddresses': 'Public IP Address',
            'Microsoft.Network/networkInterfaces': 'Network Interface',
            'Microsoft.Compute/disks': 'Managed Disk',
            'Microsoft.Network/networkSecurityGroups': 'Network Security Group',
        }
        
        for resource in all_resources:
            resource_type = resource.get('type', '')
            resource_name = resource.get('name', 'Unknown')
            
            # Check for unattached disks
            if resource_type == 'Microsoft.Compute/disks':
                # This is a simplified check - in production, you'd check disk attachment status
                findings.append({
                    'resource': resource_name,
                    'resource_type': 'Managed Disk',
                    'category': 'cost',
                    'severity': 'medium',
                    'issue': f"Review disk '{resource_name}' for attachment status",
                    'recommendation': 'Unattached managed disks still incur charges. Delete if not needed or consider snapshots',
                    'potential_savings': 'Unattached disk storage costs',
                    'optimization_type': 'orphaned_disk_review'
                })
            
            # Check for unassociated public IPs
            if resource_type == 'Microsoft.Network/publicIPAddresses':
                findings.append({
                    'resource': resource_name,
                    'resource_type': 'Public IP Address',
                    'category': 'cost',
                    'severity': 'low',
                    'issue': f"Review public IP '{resource_name}' for association status",
                    'recommendation': 'Unassociated public IPs incur charges. Delete if not needed',
                    'potential_savings': 'Public IP hourly charges',
                    'optimization_type': 'orphaned_ip_review'
                })
        
        return findings

    def _analyze_general_cost_patterns(self, all_resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze general cost patterns across all resources.
        
        Args:
            all_resources: List of all resources
            
        Returns:
            List of general cost pattern findings
        """
        findings = []
        
        # Count resources by type
        resource_counts = {}
        for resource in all_resources:
            resource_type = resource.get('type', 'Unknown')
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
        
        # Check for large number of similar resources (potential consolidation)
        for resource_type, count in resource_counts.items():
            if count >= 10:
                simple_type = resource_type.split('/')[-1] if '/' in resource_type else resource_type
                findings.append({
                    'resource': f'{count} {simple_type} resources',
                    'resource_type': simple_type,
                    'category': 'cost',
                    'severity': 'low',
                    'issue': f"High number of {simple_type} resources ({count})",
                    'recommendation': 'Review for consolidation opportunities or consider shared resources',
                    'potential_savings': 'Consolidation may reduce management overhead and costs',
                    'optimization_type': 'resource_consolidation'
                })
        
        # Check for resources without cost allocation tags
        untagged_count = sum(1 for r in all_resources if not r.get('tags'))
        if untagged_count > 0 and all_resources:
            untagged_pct = round(untagged_count / len(all_resources) * 100, 1)
            if untagged_pct > 20:
                severity = 'high' if untagged_pct > 50 else 'medium'
                findings.append({
                    'resource': f'{untagged_count} resources',
                    'resource_type': 'Multiple',
                    'category': 'cost',
                    'severity': severity,
                    'issue': f"{untagged_count} resources ({untagged_pct}%) lack cost allocation tags",
                    'recommendation': 'Apply cost allocation tags (CostCenter, Project, Owner) to enable cost tracking and showback',
                    'potential_savings': 'Improved cost visibility and accountability',
                    'optimization_type': 'cost_allocation_tags'
                })
        
        return findings

    def _generate_summary(self, findings: List[Dict[str, Any]], 
                         resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate a summary of cost analysis.
        
        Args:
            findings: List of all findings
            resources: Dictionary of all resources
            
        Returns:
            Summary dictionary
        """
        # Count findings by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for finding in findings:
            severity = finding.get('severity', 'low').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Count findings by optimization type
        optimization_types = {}
        for finding in findings:
            opt_type = finding.get('optimization_type', 'other')
            optimization_types[opt_type] = optimization_types.get(opt_type, 0) + 1
        
        return {
            'total_resources_analyzed': sum(
                len(r) for r in resources.values() 
                if isinstance(r, (list, dict, set, tuple))
            ),
            'total_findings': len(findings),
            'findings_by_severity': severity_counts,
            'optimization_opportunities': len(findings),
            'optimization_types': optimization_types,
            'analysis_scope': list(resources.keys())
        }

    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate prioritized cost optimization recommendations.
        
        Args:
            findings: List of all findings
            
        Returns:
            List of prioritized recommendations
        """
        # Group findings by optimization type and prioritize
        recommendations = []
        
        # Priority order for optimization types
        priority_order = [
            'stopped_vm',
            'deallocated_vm',
            'orphaned_disk_review',
            'orphaned_ip_review',
            'gpu_vm_review',
            'premium_storage_review',
            'reserved_instance',
            'storage_redundancy_review',
            'memory_vm_review',
            'cost_allocation_tags',
            'resource_consolidation',
            'legacy_storage',
        ]
        
        # Group findings
        grouped = {}
        for finding in findings:
            opt_type = finding.get('optimization_type', 'other')
            if opt_type not in grouped:
                grouped[opt_type] = []
            grouped[opt_type].append(finding)
        
        # Create recommendations in priority order
        for opt_type in priority_order:
            if opt_type in grouped:
                count = len(grouped[opt_type])
                sample = grouped[opt_type][0]
                recommendations.append({
                    'type': opt_type,
                    'priority': priority_order.index(opt_type) + 1,
                    'affected_resources': count,
                    'summary': sample.get('issue', ''),
                    'action': sample.get('recommendation', ''),
                    'potential_impact': sample.get('potential_savings', '')
                })
        
        # Add any remaining types
        for opt_type, items in grouped.items():
            if opt_type not in priority_order:
                sample = items[0]
                recommendations.append({
                    'type': opt_type,
                    'priority': len(priority_order) + 1,
                    'affected_resources': len(items),
                    'summary': sample.get('issue', ''),
                    'action': sample.get('recommendation', ''),
                    'potential_impact': sample.get('potential_savings', '')
                })
        
        return recommendations

    def _count_opportunities(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count optimization opportunities by category.
        
        Args:
            findings: List of all findings
            
        Returns:
            Dictionary of opportunity counts
        """
        opportunities = {
            'immediate_actions': 0,  # High/critical severity
            'review_needed': 0,      # Medium severity
            'best_practices': 0      # Low severity
        }
        
        for finding in findings:
            severity = finding.get('severity', 'low').lower()
            if severity in ['critical', 'high']:
                opportunities['immediate_actions'] += 1
            elif severity == 'medium':
                opportunities['review_needed'] += 1
            else:
                opportunities['best_practices'] += 1
        
        return opportunities
