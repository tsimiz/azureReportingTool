"""Main orchestration script for Azure Reporting Tool."""

import os
import sys
import argparse
import logging
from typing import Optional

from azure_reporter.modules.azure_fetcher import AzureFetcher
from azure_reporter.modules.ai_analyzer import AIAnalyzer
from azure_reporter.modules.tag_analyzer import TagAnalyzer
from azure_reporter.modules.powerpoint_generator import PowerPointGenerator
from azure_reporter.modules.pdf_generator import PDFGenerator
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
            self.logger.info("Step 1/6: Fetching Azure resources...")
            resources = self._fetch_azure_resources()
            
            if not resources:
                self.logger.error("No resources fetched. Exiting.")
                return
            
            # Step 2: Analyze with AI (if enabled)
            self.logger.info("Step 2/6: Analyzing resources with AI...")
            analyses = self._analyze_resources(resources)
            
            # Step 3: Analyze tags (if enabled)
            self.logger.info("Step 3/6: Analyzing resource tags...")
            tag_analysis = self._analyze_tags(resources)
            if tag_analysis:
                analyses['tag_analysis'] = tag_analysis
            
            # Step 4: Generate report (PDF or PowerPoint)
            export_format = self.config['output'].get('export_format', 'pdf').lower()
            if export_format == 'pptx':
                self.logger.info("Step 4/6: Generating PowerPoint report...")
                self._generate_powerpoint(resources, analyses)
            else:
                self.logger.info("Step 4/6: Generating PDF report...")
                self._generate_pdf(resources, analyses)
            
            # Step 5: Generate improvement backlog
            self.logger.info("Step 5/6: Generating improvement backlog...")
            self._generate_backlog(analyses)
            
            # Step 6: Summary
            self.logger.info("Step 6/6: Report generation complete!")
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

    def _analyze_tags(self, resources):
        """Analyze resource tags for compliance.
        
        Returns:
            Tag analysis results or None if tag analysis is disabled.
        """
        tag_config = self.config.get('tag_analysis', {})
        
        if not tag_config.get('enabled', False):
            self.logger.info("Tag analysis disabled in configuration")
            return None
        
        required_tags = tag_config.get('required_tags', [])
        
        analyzer = TagAnalyzer(required_tags=required_tags)
        tag_analysis = analyzer.analyze_resource_tags(resources)
        
        # Log tag analysis results
        summary = tag_analysis.get('summary', {})
        self.logger.info(f"  - Total resources analyzed: {summary.get('total_resources', 0)}")
        self.logger.info(f"  - Resources with tags: {summary.get('resources_with_tags', 0)}")
        self.logger.info(f"  - Tag compliance rate: {summary.get('overall_compliance_rate', 0)}%")
        
        if tag_analysis.get('findings'):
            self.logger.info(f"  - Tag findings: {len(tag_analysis['findings'])}")
        
        return tag_analysis

    def _generate_powerpoint(self, resources, analyses):
        """Generate PowerPoint presentation."""
        output_dir = self.config['output']['directory']
        report_filename = self.config['output'].get('report_filename', 'azure_report.pptx')
        # Ensure the filename has .pptx extension
        if not report_filename.endswith('.pptx'):
            report_filename = report_filename.rsplit('.', 1)[0] + '.pptx'
        output_path = os.path.join(output_dir, report_filename)
        
        generator = PowerPointGenerator()
        generator.generate_report(resources, analyses, output_path)
        
        self.logger.info(f"  PowerPoint report saved: {output_path}")

    def _generate_pdf(self, resources, analyses):
        """Generate PDF report."""
        output_dir = self.config['output']['directory']
        report_filename = self.config['output'].get('report_filename', 'azure_report.pdf')
        # Ensure the filename has .pdf extension
        if not report_filename.endswith('.pdf'):
            report_filename = report_filename.rsplit('.', 1)[0] + '.pdf'
        output_path = os.path.join(output_dir, report_filename)
        
        generator = PDFGenerator()
        generator.generate_report(resources, analyses, output_path)
        
        self.logger.info(f"  PDF report saved: {output_path}")

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
        export_format = self.config['output'].get('export_format', 'pdf').lower()
        report_filename = self.config['output'].get('report_filename', 'azure_report.pdf')
        
        # Adjust filename extension based on format
        if export_format == 'pptx':
            if not report_filename.endswith('.pptx'):
                report_filename = report_filename.rsplit('.', 1)[0] + '.pptx'
            report_type = "PowerPoint"
        else:
            if not report_filename.endswith('.pdf'):
                report_filename = report_filename.rsplit('.', 1)[0] + '.pdf'
            report_type = "PDF"
        
        self.logger.info("\n" + "="*60)
        self.logger.info("REPORT GENERATION SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Output directory: {output_dir}")
        self.logger.info("\nGenerated files:")
        self.logger.info(f"  1. {report_type} Report: {report_filename}")
        self.logger.info("  2. Improvement Backlog:")
        self.logger.info("     - improvement_backlog.csv")
        self.logger.info("     - improvement_backlog.json")
        self.logger.info("     - improvement_backlog.md")
        self.logger.info("\nNext steps:")
        self.logger.info(f"  1. Review the {report_type} report")
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
