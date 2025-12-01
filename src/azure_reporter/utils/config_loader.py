"""Configuration loader utility."""

import os
import yaml
import logging
from typing import Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads configuration from environment variables and YAML files."""

    def __init__(self, config_path: str = None):
        """Initialize configuration loader."""
        # Load environment variables
        load_dotenv()
        
        self.config = {}
        
        # Load YAML config if provided
        if config_path and os.path.exists(config_path):
            self.load_yaml_config(config_path)
        else:
            # Use default configuration
            self.config = self._get_default_config()
        
        # Override with environment variables
        self._load_env_config()
        
        logger.info("Configuration loaded")

    def load_yaml_config(self, config_path: str):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'output': {
                'directory': './output',
                'report_filename': 'azure_report.pdf',
                'export_format': 'pdf',
                'backlog_filename': 'improvement_backlog'
            },
            'resources': {
                'virtual_machines': True,
                'storage_accounts': True,
                'network_security_groups': True,
                'virtual_networks': True,
                'resource_groups': True
            },
            'ai_analysis': {
                'enabled': True,
                'model': 'gpt-4',
                'temperature': 0.3
            },
            'tag_analysis': {
                'enabled': False,
                'required_tags': []
            },
            'cost_analysis': {
                'enabled': True
            },
            'report': {
                'include_executive_summary': True,
                'include_detailed_findings': True,
                'include_security_analysis': True,
                'include_cost_analysis': True
            }
        }

    def _load_env_config(self):
        """Load configuration from environment variables."""
        # Azure credentials
        self.azure_tenant_id = os.getenv('AZURE_TENANT_ID')
        self.azure_client_id = os.getenv('AZURE_CLIENT_ID')
        self.azure_client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.azure_subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 
                                      self.config['ai_analysis'].get('model', 'gpt-4'))
        
        # Azure OpenAI (alternative)
        self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_key = os.getenv('AZURE_OPENAI_KEY')
        self.azure_openai_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')

    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self.config

    def get_azure_credentials(self) -> Dict[str, str]:
        """Get Azure credentials."""
        return {
            'tenant_id': self.azure_tenant_id,
            'client_id': self.azure_client_id,
            'client_secret': self.azure_client_secret,
            'subscription_id': self.azure_subscription_id
        }

    def get_openai_config(self) -> Dict[str, str]:
        """Get OpenAI or Azure OpenAI configuration."""
        config = {
            'temperature': self.config['ai_analysis'].get('temperature', 0.3)
        }
        
        # Prefer Azure OpenAI if configured
        if self.azure_openai_endpoint and self.azure_openai_key and self.azure_openai_deployment:
            config.update({
                'api_key': self.azure_openai_key,
                'azure_endpoint': self.azure_openai_endpoint,
                'azure_deployment': self.azure_openai_deployment,
                'model': self.azure_openai_deployment  # Used by AIAnalyzer; Azure OpenAI uses deployment name as model identifier
            })
        else:
            config.update({
                'api_key': self.openai_api_key,
                'model': self.openai_model
            })
        
        return config

    def validate_config(self) -> bool:
        """Validate that required configuration is present."""
        errors = []
        
        # Check Azure credentials
        if not self.azure_subscription_id:
            errors.append("AZURE_SUBSCRIPTION_ID is required")
        
        # Check AI configuration
        if self.config['ai_analysis']['enabled']:
            has_openai = bool(self.openai_api_key)
            has_azure_openai = bool(self.azure_openai_endpoint and self.azure_openai_key and self.azure_openai_deployment)
            
            if not has_openai and not has_azure_openai:
                errors.append("Either OPENAI_API_KEY or complete Azure OpenAI configuration (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT) is required for AI analysis")
            
            # If Azure OpenAI is partially configured, warn about missing parts
            if (self.azure_openai_endpoint or self.azure_openai_key or self.azure_openai_deployment) and not has_azure_openai:
                missing = []
                if not self.azure_openai_endpoint:
                    missing.append("AZURE_OPENAI_ENDPOINT")
                if not self.azure_openai_key:
                    missing.append("AZURE_OPENAI_KEY")
                if not self.azure_openai_deployment:
                    missing.append("AZURE_OPENAI_DEPLOYMENT")
                errors.append(f"Azure OpenAI partially configured. Missing: {', '.join(missing)}")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True
