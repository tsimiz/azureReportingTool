"""Module for AI-powered analysis of Azure resources against best practices."""

import logging
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI, AzureOpenAI

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Analyzes Azure resources using AI against Microsoft best practices."""

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gpt-4", 
        temperature: float = 0.3,
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None
    ):
        """Initialize AI analyzer with OpenAI or Azure OpenAI client.
        
        Args:
            api_key: API key (required). For OpenAI or Azure OpenAI.
            model: Model name (used for OpenAI, ignored for Azure OpenAI)
            temperature: Sampling temperature
            azure_endpoint: Azure OpenAI endpoint URL (optional, for Azure OpenAI)
            azure_deployment: Azure OpenAI deployment name (required if azure_endpoint provided)
            
        Raises:
            ValueError: If api_key is not provided, or if azure_endpoint is provided without azure_deployment
        """
        # Use Azure OpenAI if endpoint is provided
        if azure_endpoint and api_key:
            if not azure_deployment:
                raise ValueError("azure_deployment is required when using Azure OpenAI")
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=azure_endpoint
            )
            # For Azure OpenAI, use deployment name instead of model name
            self.model = azure_deployment
            logger.info(f"AI Analyzer initialized with Azure OpenAI deployment: {azure_deployment}")
        elif api_key:
            self.client = OpenAI(api_key=api_key)
            self.model = model
            logger.info(f"AI Analyzer initialized with OpenAI model: {model}")
        else:
            raise ValueError("Either api_key must be provided for OpenAI, or both api_key and azure_endpoint for Azure OpenAI")
        
        self.temperature = temperature

    def analyze_virtual_machines(self, vms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze virtual machines against best practices."""
        logger.info(f"Analyzing {len(vms)} virtual machines...")
        
        if not vms:
            return {
                'status': 'no_vms',
                'findings': [],
                'recommendations': []
            }
        
        prompt = f"""Analyze the following Azure Virtual Machines configuration against Microsoft's best practices.
Focus on: security, performance, cost optimization, and operational excellence.

Virtual Machines Data:
{json.dumps(vms, indent=2)}

Provide analysis in the following JSON format:
{{
    "overall_score": <1-10>,
    "findings": [
        {{
            "resource": "<vm_name>",
            "category": "<security|performance|cost|operations>",
            "severity": "<critical|high|medium|low>",
            "issue": "<description>",
            "recommendation": "<specific recommendation>"
        }}
    ],
    "best_practices_met": ["<list of practices that are followed>"],
    "summary": "<brief summary of overall VM posture>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an Azure architecture expert specializing in best practices and recommendations. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            analysis = json.loads(response.choices[0].message.content)
            logger.info("Virtual machines analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing virtual machines: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'findings': [],
                'recommendations': []
            }

    def analyze_storage_accounts(self, storage_accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze storage accounts against best practices."""
        logger.info(f"Analyzing {len(storage_accounts)} storage accounts...")
        
        if not storage_accounts:
            return {
                'status': 'no_storage',
                'findings': [],
                'recommendations': []
            }
        
        prompt = f"""Analyze the following Azure Storage Accounts configuration against Microsoft's best practices.
Focus on: security (encryption, network access, HTTPS), redundancy, and cost optimization.

Storage Accounts Data:
{json.dumps(storage_accounts, indent=2)}

Provide analysis in the following JSON format:
{{
    "overall_score": <1-10>,
    "findings": [
        {{
            "resource": "<storage_account_name>",
            "category": "<security|performance|cost|operations>",
            "severity": "<critical|high|medium|low>",
            "issue": "<description>",
            "recommendation": "<specific recommendation>"
        }}
    ],
    "best_practices_met": ["<list of practices that are followed>"],
    "summary": "<brief summary of overall storage posture>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an Azure security and storage expert specializing in best practices. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            analysis = json.loads(response.choices[0].message.content)
            logger.info("Storage accounts analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing storage accounts: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'findings': [],
                'recommendations': []
            }

    def analyze_network_security(self, nsgs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze network security groups against best practices."""
        logger.info(f"Analyzing {len(nsgs)} network security groups...")
        
        if not nsgs:
            return {
                'status': 'no_nsgs',
                'findings': [],
                'recommendations': []
            }
        
        prompt = f"""Analyze the following Azure Network Security Groups (NSGs) configuration against Microsoft's security best practices.
Focus on: overly permissive rules, unrestricted internet access, use of "Any" in rules, and security risks.

NSG Data:
{json.dumps(nsgs, indent=2)}

Provide analysis in the following JSON format:
{{
    "overall_score": <1-10>,
    "findings": [
        {{
            "resource": "<nsg_name>",
            "category": "<security|network|operations>",
            "severity": "<critical|high|medium|low>",
            "issue": "<description>",
            "recommendation": "<specific recommendation>"
        }}
    ],
    "best_practices_met": ["<list of practices that are followed>"],
    "summary": "<brief summary of overall network security posture>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an Azure network security expert specializing in NSG best practices. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            analysis = json.loads(response.choices[0].message.content)
            logger.info("Network security analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing network security: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'findings': [],
                'recommendations': []
            }

    def analyze_virtual_networks(self, vnets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze virtual networks against best practices."""
        logger.info(f"Analyzing {len(vnets)} virtual networks...")
        
        if not vnets:
            return {
                'status': 'no_vnets',
                'findings': [],
                'recommendations': []
            }
        
        prompt = f"""Analyze the following Azure Virtual Networks configuration against Microsoft's best practices.
Focus on: subnet design, address space planning, network segmentation, and connectivity.

Virtual Networks Data:
{json.dumps(vnets, indent=2)}

Provide analysis in the following JSON format:
{{
    "overall_score": <1-10>,
    "findings": [
        {{
            "resource": "<vnet_name>",
            "category": "<network|performance|operations>",
            "severity": "<critical|high|medium|low>",
            "issue": "<description>",
            "recommendation": "<specific recommendation>"
        }}
    ],
    "best_practices_met": ["<list of practices that are followed>"],
    "summary": "<brief summary of overall network architecture>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an Azure network architecture expert specializing in best practices. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            analysis = json.loads(response.choices[0].message.content)
            logger.info("Virtual networks analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing virtual networks: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'findings': [],
                'recommendations': []
            }

    def generate_executive_summary(self, all_analyses: Dict[str, Any]) -> str:
        """Generate an executive summary from all analyses."""
        logger.info("Generating executive summary...")
        
        prompt = f"""Based on the following Azure environment analysis results, create a concise executive summary 
suitable for management and stakeholders. Focus on key findings, risks, and high-priority recommendations.

Analysis Results:
{json.dumps(all_analyses, indent=2)}

Provide a clear, professional executive summary (3-5 paragraphs) covering:
1. Overall environment health
2. Critical findings requiring immediate attention
3. Key recommendations for improvement
4. Positive aspects and best practices already in place"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an Azure consultant creating executive summaries for stakeholders."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            summary = response.choices[0].message.content
            logger.info("Executive summary generated")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return "Error generating executive summary."

    def _summarize_resources_for_analysis(self, resources: List[Dict[str, Any]], max_resources: int = 50) -> str:
        """Summarize resources for AI analysis to avoid token limits.
        
        Args:
            resources: List of resources to summarize
            max_resources: Maximum number of resources to include in full detail
            
        Returns:
            JSON string representation of resources (full or summarized)
        """
        if len(resources) <= max_resources:
            return json.dumps(resources, indent=2)
        
        # For large resource lists, provide summary statistics and sample
        summary = {
            'total_count': len(resources),
            'sample_resources': resources[:10],  # Include first 10 as samples
            'locations': list(set(r.get('location', 'unknown') for r in resources)),
            'resource_groups': list(set(r.get('resource_group', 'unknown') for r in resources))
        }
        
        logger.info(f"Resource list too large ({len(resources)} items), providing summary instead")
        return json.dumps(summary, indent=2)

    def analyze_generic_resources(self, all_resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze all generic resources grouped by type."""
        logger.info(f"Analyzing {len(all_resources)} generic resources...")
        
        if not all_resources:
            return {
                'status': 'no_resources',
                'findings': [],
                'recommendations': [],
                'resource_types': {}
            }
        
        # Group resources by type
        resources_by_type = {}
        for resource in all_resources:
            resource_type = resource.get('type', 'Unknown')
            if resource_type not in resources_by_type:
                resources_by_type[resource_type] = []
            resources_by_type[resource_type].append(resource)
        
        logger.info(f"Found {len(resources_by_type)} unique resource types")
        
        # Analyze each resource type
        type_analyses = {}
        for resource_type, resources_list in resources_by_type.items():
            logger.info(f"Analyzing {len(resources_list)} resources of type {resource_type}...")
            
            # Summarize resources if list is too large
            resources_data = self._summarize_resources_for_analysis(resources_list)
            
            prompt = f"""Analyze the following Azure resources of type '{resource_type}' against Microsoft's best practices.
Focus on: security, performance, cost optimization, operational excellence, and reliability.

Resources Data:
{resources_data}

Provide analysis in the following JSON format:
{{
    "overall_score": <1-10>,
    "findings": [
        {{
            "resource": "<resource_name>",
            "category": "<security|performance|cost|operations|reliability>",
            "severity": "<critical|high|medium|low>",
            "issue": "<description>",
            "recommendation": "<specific recommendation>"
        }}
    ],
    "best_practices_met": ["<list of practices that are followed>"],
    "summary": "<brief summary of this resource type's posture>"
}}"""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an Azure architecture expert specializing in best practices and recommendations. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature
                )
                
                analysis = json.loads(response.choices[0].message.content)
                type_analyses[resource_type] = analysis
                logger.info(f"Analysis completed for {resource_type}")
                
            except Exception as e:
                logger.error(f"Error analyzing {resource_type}: {e}")
                type_analyses[resource_type] = {
                    'status': 'error',
                    'error': str(e),
                    'findings': [],
                    'recommendations': []
                }
        
        return {
            'status': 'analyzed',
            'resource_types': type_analyses,
            'total_resource_types': len(resources_by_type),
            'total_resources': len(all_resources)
        }

    def analyze_all_resources(self, resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze all Azure resources."""
        logger.info("Starting comprehensive AI analysis of all resources...")
        
        analyses = {
            'virtual_machines': self.analyze_virtual_machines(resources.get('virtual_machines', [])),
            'storage_accounts': self.analyze_storage_accounts(resources.get('storage_accounts', [])),
            'network_security_groups': self.analyze_network_security(resources.get('network_security_groups', [])),
            'virtual_networks': self.analyze_virtual_networks(resources.get('virtual_networks', []))
        }
        
        # Analyze generic resources if available
        all_resources = resources.get('all_resources', [])
        if all_resources:
            analyses['generic_resources'] = self.analyze_generic_resources(all_resources)
        
        # Generate executive summary
        analyses['executive_summary'] = self.generate_executive_summary(analyses)
        
        logger.info("Comprehensive AI analysis completed")
        return analyses
