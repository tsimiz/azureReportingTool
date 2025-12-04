"""Module for analyzing Azure resource tags against required tags."""

import logging
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


class TagAnalyzer:
    """Analyzes Azure resource tags for compliance against required tags."""

    def __init__(self, required_tags: Optional[List[str]] = None):
        """Initialize tag analyzer.
        
        Args:
            required_tags: List of tag names that are required on resources.
        """
        self.required_tags = set(required_tags) if required_tags else set()
        logger.info(f"Tag analyzer initialized with {len(self.required_tags)} required tags")

    def analyze_resource_tags(self, resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze tags across all resources.
        
        Args:
            resources: Dictionary of resource type to list of resources
            
        Returns:
            Dictionary containing tag analysis results
        """
        logger.info("Starting tag analysis...")
        
        all_tags: Dict[str, int] = {}  # tag_name -> count
        resources_with_tags = 0
        resources_without_tags = 0
        total_resources = 0
        
        # Track missing tags per resource
        missing_tags_by_resource: List[Dict[str, Any]] = []
        
        # Track tag usage
        tag_values: Dict[str, Dict[str, int]] = {}  # tag_name -> {value -> count}
        
        # Track resource groups and their tags
        resource_groups_info: Dict[str, Dict[str, Any]] = {}  # rg_name -> {tags, resources}
        
        # First, extract resource group information
        resource_groups_list = resources.get('resource_groups', [])
        for rg in resource_groups_list:
            if isinstance(rg, dict):
                rg_name = rg.get('name', 'Unknown')
                rg_tags = rg.get('tags', {}) or {}
                rg_tag_names = set(rg_tags.keys())
                
                # Check resource group compliance
                rg_missing_tags = list(self.required_tags - rg_tag_names) if self.required_tags else []
                
                resource_groups_info[rg_name] = {
                    'name': rg_name,
                    'tags': rg_tags,
                    'existing_tags': list(rg_tag_names),
                    'missing_tags': rg_missing_tags,
                    'compliance_rate': self._calculate_resource_compliance(rg_tag_names),
                    'resources': []
                }
        
        # Analyze each resource type
        for resource_type, resource_list in resources.items():
            if not isinstance(resource_list, list):
                continue
            
            # Skip resource_groups as we've already processed them
            # Skip all_resources as it's a duplicate collection
            if resource_type in ('resource_groups', 'all_resources'):
                continue
                
            for resource in resource_list:
                if not isinstance(resource, dict):
                    continue
                    
                total_resources += 1
                resource_tags = resource.get('tags', {}) or {}
                resource_group_name = resource.get('resource_group', 'N/A')
                
                if resource_tags:
                    resources_with_tags += 1
                else:
                    resources_without_tags += 1
                
                # Count tag usage
                for tag_name, tag_value in resource_tags.items():
                    all_tags[tag_name] = all_tags.get(tag_name, 0) + 1
                    
                    if tag_name not in tag_values:
                        tag_values[tag_name] = {}
                    tag_value_str = str(tag_value) if tag_value else "(empty)"
                    tag_values[tag_name][tag_value_str] = tag_values[tag_name].get(tag_value_str, 0) + 1
                
                # Check for missing required tags
                resource_tag_names = set(resource_tags.keys())
                missing = self.required_tags - resource_tag_names if self.required_tags else set()
                
                resource_info = {
                    'resource_type': resource_type,
                    'resource_name': resource.get('name', 'Unknown'),
                    'resource_id': resource.get('id', 'N/A'),
                    'resource_group': resource_group_name,
                    'existing_tags': list(resource_tag_names),
                    'missing_tags': list(missing),
                    'compliance_rate': self._calculate_resource_compliance(resource_tag_names)
                }
                
                if missing:
                    missing_tags_by_resource.append(resource_info)
                
                # Add resource to its resource group
                if resource_group_name in resource_groups_info:
                    resource_groups_info[resource_group_name]['resources'].append(resource_info)
        
        # Calculate compliance metrics
        compliance_rate = self._calculate_overall_compliance(missing_tags_by_resource, total_resources)
        
        # Build tag summary
        tag_summary = []
        for tag_name, count in sorted(all_tags.items(), key=lambda x: -x[1]):
            tag_summary.append({
                'tag_name': tag_name,
                'usage_count': count,
                'usage_percentage': round(count / total_resources * 100, 1) if total_resources > 0 else 0,
                'is_required': tag_name in self.required_tags,
                'unique_values': len(tag_values.get(tag_name, {}))
            })
        
        # Build required tags compliance summary
        required_tags_summary = []
        for tag_name in self.required_tags:
            count = all_tags.get(tag_name, 0)
            required_tags_summary.append({
                'tag_name': tag_name,
                'compliant_resources': count,
                'non_compliant_resources': total_resources - count,
                'compliance_percentage': round(count / total_resources * 100, 1) if total_resources > 0 else 0
            })
        
        # Build resource groups by compliance summary
        resource_groups_by_compliance = self._build_resource_groups_summary(resource_groups_info)
        
        analysis_result = {
            'summary': {
                'total_resources': total_resources,
                'resources_with_tags': resources_with_tags,
                'resources_without_tags': resources_without_tags,
                'unique_tags_found': len(all_tags),
                'required_tags_count': len(self.required_tags),
                'overall_compliance_rate': compliance_rate,
                'total_resource_groups': len(resource_groups_info)
            },
            'tag_usage': tag_summary,
            'required_tags_compliance': required_tags_summary,
            'non_compliant_resources': missing_tags_by_resource,
            'resource_groups_details': resource_groups_by_compliance,
            'findings': self._generate_findings(
                missing_tags_by_resource, 
                compliance_rate, 
                resources_without_tags,
                total_resources
            )
        }
        
        logger.info(f"Tag analysis complete. Compliance rate: {compliance_rate}%")
        return analysis_result

    def _build_resource_groups_summary(
        self, 
        resource_groups_info: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build a summary of resource groups with their tag compliance.
        
        Args:
            resource_groups_info: Dictionary of resource group information
            
        Returns:
            List of resource groups with compliance details, sorted by compliance rate
        """
        summary = []
        for rg_name, rg_info in resource_groups_info.items():
            # Count non-compliant resources in this resource group
            non_compliant_count = sum(
                1 for res in rg_info['resources'] 
                if res.get('missing_tags') and len(res['missing_tags']) > 0
            )
            
            summary.append({
                'name': rg_name,
                'tags': rg_info['tags'],
                'existing_tags': rg_info['existing_tags'],
                'missing_tags': rg_info['missing_tags'],
                'compliance_rate': rg_info['compliance_rate'],
                'total_resources': len(rg_info['resources']),
                'non_compliant_resources': non_compliant_count,
                'resources': rg_info['resources']
            })
        
        # Sort by compliance rate (ascending) to show worst first
        summary.sort(key=lambda x: x['compliance_rate'])
        return summary

    def _calculate_resource_compliance(self, resource_tags: Set[str]) -> float:
        """Calculate compliance rate for a single resource.
        
        Args:
            resource_tags: Set of tag names on the resource
            
        Returns:
            Compliance rate as percentage (0-100)
        """
        if not self.required_tags:
            return 100.0
        
        matching_tags = resource_tags & self.required_tags
        return round(len(matching_tags) / len(self.required_tags) * 100, 1)

    def _calculate_overall_compliance(
        self, 
        missing_tags_by_resource: List[Dict[str, Any]], 
        total_resources: int
    ) -> float:
        """Calculate overall tag compliance rate.
        
        Args:
            missing_tags_by_resource: List of resources with missing tags
            total_resources: Total number of resources analyzed
            
        Returns:
            Overall compliance rate as percentage
        """
        if not self.required_tags or total_resources == 0:
            return 100.0
        
        # Calculate average compliance across all resources
        compliant_resources = total_resources - len(missing_tags_by_resource)
        partially_compliant = [r for r in missing_tags_by_resource if r['compliance_rate'] > 0]
        
        # Weight: fully compliant resources contribute 100%, partial contributes their rate
        total_compliance = (compliant_resources * 100)
        for resource in partially_compliant:
            total_compliance += resource['compliance_rate']
        
        return round(total_compliance / total_resources, 1)

    def _generate_findings(
        self, 
        missing_tags_by_resource: List[Dict[str, Any]],
        compliance_rate: float,
        resources_without_tags: int,
        total_resources: int
    ) -> List[Dict[str, Any]]:
        """Generate findings from tag analysis.
        
        Args:
            missing_tags_by_resource: List of resources with missing tags
            compliance_rate: Overall compliance rate
            resources_without_tags: Count of resources without any tags
            total_resources: Total number of resources
            
        Returns:
            List of findings
        """
        findings = []
        
        # Overall compliance finding
        if compliance_rate < 50:
            severity = 'high'
            issue = f"Tag compliance is critically low at {compliance_rate}%"
        elif compliance_rate < 80:
            severity = 'medium'
            issue = f"Tag compliance is below target at {compliance_rate}%"
        elif compliance_rate < 100:
            severity = 'low'
            issue = f"Tag compliance is good but not complete at {compliance_rate}%"
        else:
            severity = None
            
        if severity:
            findings.append({
                'resource': 'All Resources',
                'category': 'tagging',
                'severity': severity,
                'issue': issue,
                'recommendation': 'Implement a tagging policy to ensure all resources have required tags'
            })
        
        # Resources without any tags
        if resources_without_tags > 0:
            pct = round(resources_without_tags / total_resources * 100, 1) if total_resources > 0 else 0
            if pct > 25:
                severity = 'high'
            elif pct > 10:
                severity = 'medium'
            else:
                severity = 'low'
                
            findings.append({
                'resource': 'Multiple Resources',
                'category': 'tagging',
                'severity': severity,
                'issue': f"{resources_without_tags} resources ({pct}%) have no tags at all",
                'recommendation': 'Apply at minimum the required tags to all resources for proper cost allocation and management'
            })
        
        # Group missing tags by tag name to identify most common gaps
        tag_gaps: Dict[str, int] = {}
        for resource in missing_tags_by_resource:
            for tag in resource['missing_tags']:
                tag_gaps[tag] = tag_gaps.get(tag, 0) + 1
        
        # Report on most commonly missing tags
        for tag_name, count in sorted(tag_gaps.items(), key=lambda x: -x[1])[:5]:
            pct = round(count / total_resources * 100, 1) if total_resources > 0 else 0
            if pct > 50:
                severity = 'high'
            elif pct > 25:
                severity = 'medium'
            else:
                severity = 'low'
                
            findings.append({
                'resource': f"Tag: {tag_name}",
                'category': 'tagging',
                'severity': severity,
                'issue': f"Required tag '{tag_name}' is missing from {count} resources ({pct}%)",
                'recommendation': f"Apply the '{tag_name}' tag to all resources to improve compliance"
            })
        
        return findings
