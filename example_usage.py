#!/usr/bin/env python
"""
Example usage script for Azure Reporting Tool.

This script demonstrates how to use the Azure Reporting Tool programmatically.
For most use cases, you can simply run:
    python -m azure_reporter.main

Or with custom configuration:
    python -m azure_reporter.main --config config.yaml
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from azure_reporter.main import AzureReporter


def main():
    """
    Example: Run the Azure Reporting Tool with default or specified configuration.
    
    Before running:
    1. Copy .env.example to .env and fill in your Azure credentials
    2. (Optional) Copy config.example.yaml to config.yaml for custom settings
    """
    
    print("="*70)
    print("Azure Reporting Tool - Example Usage")
    print("="*70)
    print()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("ERROR: .env file not found!")
        print()
        print("Please follow these steps:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print()
        print("2. Edit .env and add your Azure credentials:")
        print("   - AZURE_TENANT_ID")
        print("   - AZURE_CLIENT_ID")
        print("   - AZURE_CLIENT_SECRET")
        print("   - AZURE_SUBSCRIPTION_ID")
        print("   - OPENAI_API_KEY")
        print()
        print("See README.md for detailed instructions on obtaining these credentials.")
        print()
        sys.exit(1)
    
    # Check if config file exists, use it if available
    config_path = None
    if os.path.exists('config.yaml'):
        config_path = 'config.yaml'
        print(f"Using configuration from: {config_path}")
    else:
        print("Using default configuration (no config.yaml found)")
        print("To customize settings, copy config.example.yaml to config.yaml")
    
    print()
    print("Starting report generation...")
    print()
    
    try:
        # Create and run the reporter
        reporter = AzureReporter(config_path)
        reporter.run()
        
        print()
        print("="*70)
        print("Report generation completed successfully!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\nReport generation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: Report generation failed: {e}")
        print("\nFor detailed error information, check the logs above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
