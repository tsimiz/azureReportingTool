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
        
        # Analyze each resource type
        for resource_type, resource_list in resources.items():
            if not isinstance(resource_list, list):
                continue
                
            for resource in resource_list:
                if not isinstance(resource, dict):
                    continue
                    
                total_resources += 1
                resource_tags = resource.get('tags', {}) or {}
                
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
                if self.required_tags:
                    resource_tag_names = set(resource_tags.keys())
                    missing = self.required_tags - resource_tag_names
                    
                    if missing:
                        missing_tags_by_resource.append({
                            'resource_type': resource_type,
                            'resource_name': resource.get('name', 'Unknown'),
                            'resource_id': resource.get('id', 'N/A'),
                            'resource_group': resource.get('resource_group', 'N/A'),
                            'existing_tags': list(resource_tag_names),
                            'missing_tags': list(missing),
                            'compliance_rate': self._calculate_resource_compliance(resource_tag_names)
                        })
        
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
        
        analysis_result = {
            'summary': {
                'total_resources': total_resources,
                'resources_with_tags': resources_with_tags,
                'resources_without_tags': resources_without_tags,
                'unique_tags_found': len(all_tags),
                'required_tags_count': len(self.required_tags),
                'overall_compliance_rate': compliance_rate
            },
            'tag_usage': tag_summary,
            'required_tags_compliance': required_tags_summary,
            'non_compliant_resources': missing_tags_by_resource,
            'findings': self._generate_findings(
                missing_tags_by_resource, 
                compliance_rate, 
                resources_without_tags,
                total_resources
            )
        }
        
        logger.info(f"Tag analysis complete. Compliance rate: {compliance_rate}%")
        return analysis_result

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
