"""Main orchestration script for Azure Reporting Tool."""

import os
import sys
import argparse
import logging
from typing import Optional

from azure_reporter.modules.azure_fetcher import AzureFetcher
from azure_reporter.modules.ai_analyzer import AIAnalyzer
from azure_reporter.modules.powerpoint_generator import PowerPointGenerator
from azure_reporter.modules.backlog_generator import BacklogGenerator
from azure_reporter.utils.config_loader import ConfigLoader
from azure_reporter.utils.logger import setup_logger


class AzureReporter:
    """Main class orchestrating the Azure reporting process."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize Azure Reporter."""
        # Setup logging
        self.logger = setup_logger('azure_reporter', logging.INFO)
        self.logger.info("=== Azure Reporting Tool Started ===")
        
        # Load configuration
        self.config_loader = ConfigLoader(config_path)
        if not self.config_loader.validate_config():
            self.logger.error("Configuration validation failed")
            sys.exit(1)
        
        self.config = self.config_loader.get_config()
        self.logger.info("Configuration loaded and validated")
        
        # Create output directory
        output_dir = self.config['output']['directory']
        os.makedirs(output_dir, exist_ok=True)
        self.logger.info(f"Output directory: {output_dir}")

    def run(self):
        """Execute the full reporting workflow."""
        try:
            # Step 1: Fetch Azure resources
            self.logger.info("Step 1/5: Fetching Azure resources...")
            resources = self._fetch_azure_resources()
            
            if not resources:
                self.logger.error("No resources fetched. Exiting.")
                return
            
            # Step 2: Analyze with AI (if enabled)
            self.logger.info("Step 2/5: Analyzing resources with AI...")
            analyses = self._analyze_resources(resources)
            
            # Step 3: Generate PowerPoint report
            self.logger.info("Step 3/5: Generating PowerPoint report...")
            self._generate_powerpoint(resources, analyses)
            
            # Step 4: Generate improvement backlog
            self.logger.info("Step 4/5: Generating improvement backlog...")
            self._generate_backlog(analyses)
            
            # Step 5: Summary
            self.logger.info("Step 5/5: Report generation complete!")
            self._print_summary()
            
        except Exception as e:
            self.logger.error(f"Error during report generation: {e}", exc_info=True)
            sys.exit(1)

    def _fetch_azure_resources(self):
        """Fetch Azure resources."""
        azure_creds = self.config_loader.get_azure_credentials()
        
        fetcher = AzureFetcher(
            subscription_id=azure_creds['subscription_id'],
            tenant_id=azure_creds.get('tenant_id'),
            client_id=azure_creds.get('client_id'),
            client_secret=azure_creds.get('client_secret')
        )
        
        resources = fetcher.fetch_all_resources()
        
        # Log resource counts
        for resource_type, resource_list in resources.items():
            self.logger.info(f"  - {resource_type}: {len(resource_list)} items")
        
        return resources

    def _analyze_resources(self, resources):
        """Analyze resources using AI."""
        if not self.config['ai_analysis']['enabled']:
            self.logger.info("AI analysis disabled in configuration")
            return {}
        
        openai_config = self.config_loader.get_openai_config()
        
        if not openai_config['api_key']:
            self.logger.warning("OpenAI API key not provided. Skipping AI analysis.")
            return {}
        
        analyzer = AIAnalyzer(
            api_key=openai_config['api_key'],
            model=openai_config['model'],
            temperature=openai_config['temperature'],
            azure_endpoint=openai_config.get('azure_endpoint'),
            azure_deployment=openai_config.get('azure_deployment')
        )
        
        analyses = analyzer.analyze_all_resources(resources)
        
        # Log analysis results
        for resource_type, analysis in analyses.items():
            if resource_type != 'executive_summary' and 'findings' in analysis:
                findings_count = len(analysis['findings'])
                self.logger.info(f"  - {resource_type}: {findings_count} findings")
        
        return analyses

    def _generate_powerpoint(self, resources, analyses):
        """Generate PowerPoint presentation."""
        output_dir = self.config['output']['directory']
        report_filename = self.config['output']['report_filename']
        output_path = os.path.join(output_dir, report_filename)
        
        generator = PowerPointGenerator()
        generator.generate_report(resources, analyses, output_path)
        
        self.logger.info(f"  PowerPoint report saved: {output_path}")

    def _generate_backlog(self, analyses):
        """Generate improvement backlog."""
        output_dir = self.config['output']['directory']
        
        generator = BacklogGenerator()
        generator.extract_backlog_items(analyses)
        generator.generate_all_formats(output_dir)
        
        self.logger.info(f"  Backlog files saved in: {output_dir}")

    def _print_summary(self):
        """Print summary of generated reports."""
        output_dir = self.config['output']['directory']
        
        self.logger.info("\n" + "="*60)
        self.logger.info("REPORT GENERATION SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Output directory: {output_dir}")
        self.logger.info("\nGenerated files:")
        self.logger.info(f"  1. PowerPoint Report: {self.config['output']['report_filename']}")
        self.logger.info("  2. Improvement Backlog:")
        self.logger.info("     - improvement_backlog.csv")
        self.logger.info("     - improvement_backlog.json")
        self.logger.info("     - improvement_backlog.md")
        self.logger.info("\nNext steps:")
        self.logger.info("  1. Review the PowerPoint report")
        self.logger.info("  2. Prioritize items in the improvement backlog")
        self.logger.info("  3. Address critical and high-severity findings first")
        self.logger.info("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Azure Reporting Tool - Generate comprehensive Azure environment reports'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration YAML file (default: config.yaml if exists)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Use config.yaml if exists and no config specified
    config_path = args.config
    if not config_path and os.path.exists('config.yaml'):
        config_path = 'config.yaml'
    
    # Create and run reporter
    reporter = AzureReporter(config_path)
    reporter.run()


if __name__ == '__main__':
    main()
