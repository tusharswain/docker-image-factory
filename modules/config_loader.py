"""
Config Loader Module
Loads configuration from YAML files and environment variables
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict


class ConfigLoader:
    """Load configuration from YAML files and environment variables"""
    
    def __init__(self, config_path: str = None):
        """Initialize the config loader"""
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._find_config_file()
    
    def _find_config_file(self) -> str:
        """Find configuration file in standard locations"""
        possible_locations = [
            'config.yaml',
            'config.yml',
            'config/config.yaml',
            'config/config.yml',
            str(Path(__file__).parent.parent / 'config.yaml'),
            str(Path(__file__).parent.parent / 'config.yml')
        ]
        
        for location in possible_locations:
            if Path(location).exists():
                return location
        
        return None
    
    def load_config(self) -> Dict:
        """Load configuration from file and environment variables"""
        config = self._load_default_config()
        
        # Load from YAML file if exists
        if self.config_path and Path(self.config_path).exists():
            file_config = self._load_yaml_config(self.config_path)
            config = self._merge_configs(config, file_config)
        
        # Override with environment variables
        config = self._load_env_overrides(config)
        
        return config
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            'log_dir': 'logs',
            'default_registry': 'dockerhub',
            'security': {
                'severity_threshold': 'HIGH'
            },
            'trivy': {
                'enabled': True
            },
            'snyk': {
                'enabled': False
            },
            'signing': {
                'default_method': 'cosign',
                'cosign_key_path': None,
                'docker_trust_passphrase': None
            },
            'ecr': {
                'repository_uri': None,
                'region': 'us-east-1'
            },
            'dockerhub': {
                'username': None,
                'password': None
            },
            'slack': {
                'enabled': False,
                'webhook_url': None
            },
            'email': {
                'enabled': False,
                'smtp_server': None,
                'smtp_port': 587,
                'username': None,
                'password': None,
                'from_email': None,
                'to_emails': []
            },
            'metadata_storage': {
                'type': 'local'
            },
            's3': {
                'bucket_name': None,
                'region': 'us-east-1'
            },
            'dynamodb': {
                'table_name': None,
                'region': 'us-east-1'
            }
        }
    
    def _load_yaml_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.warning(f"Failed to load config file: {str(e)}")
            return {}
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Merge two configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _load_env_overrides(self, config: Dict) -> Dict:
        """Load configuration overrides from environment variables"""
        env_mappings = {
            'DOCKER_FACTORY_LOG_DIR': ('log_dir', str),
            'DOCKER_FACTORY_DEFAULT_REGISTRY': ('default_registry', str),
            'DOCKER_FACTORY_SEVERITY_THRESHOLD': ('security', 'severity_threshold', str),
            'DOCKER_FACTORY_TRIVY_ENABLED': ('trivy', 'enabled', bool),
            'DOCKER_FACTORY_SNYK_ENABLED': ('snyk', 'enabled', bool),
            'DOCKER_FACTORY_SIGNING_METHOD': ('signing', 'default_method', str),
            'DOCKER_FACTORY_COSIGN_KEY_PATH': ('signing', 'cosign_key_path', str),
            'DOCKER_FACTORY_DOCKER_TRUST_PASSPHRASE': ('signing', 'docker_trust_passphrase', str),
            'DOCKER_FACTORY_ECR_REPOSITORY_URI': ('ecr', 'repository_uri', str),
            'DOCKER_FACTORY_ECR_REGION': ('ecr', 'region', str),
            'DOCKER_FACTORY_DOCKERHUB_USERNAME': ('dockerhub', 'username', str),
            'DOCKER_FACTORY_DOCKERHUB_PASSWORD': ('dockerhub', 'password', str),
            'DOCKER_FACTORY_SLACK_ENABLED': ('slack', 'enabled', bool),
            'DOCKER_FACTORY_SLACK_WEBHOOK_URL': ('slack', 'webhook_url', str),
            'DOCKER_FACTORY_EMAIL_ENABLED': ('email', 'enabled', bool),
            'DOCKER_FACTORY_EMAIL_SMTP_SERVER': ('email', 'smtp_server', str),
            'DOCKER_FACTORY_EMAIL_SMTP_PORT': ('email', 'smtp_port', int),
            'DOCKER_FACTORY_EMAIL_USERNAME': ('email', 'username', str),
            'DOCKER_FACTORY_EMAIL_PASSWORD': ('email', 'password', str),
            'DOCKER_FACTORY_EMAIL_FROM_EMAIL': ('email', 'from_email', str),
            'DOCKER_FACTORY_EMAIL_TO_EMAILS': ('email', 'to_emails', list),
            'DOCKER_FACTORY_METADATA_STORAGE_TYPE': ('metadata_storage', 'type', str),
            'DOCKER_FACTORY_S3_BUCKET_NAME': ('s3', 'bucket_name', str),
            'DOCKER_FACTORY_S3_REGION': ('s3', 'region', str),
            'DOCKER_FACTORY_DYNAMODB_TABLE_NAME': ('dynamodb', 'table_name', str),
            'DOCKER_FACTORY_DYNAMODB_REGION': ('dynamodb', 'region', str)
        }
        
        for env_var, mapping in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Navigate to the nested key
                current = config
                for key in mapping[:-2]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Set the value with type conversion
                target_key = mapping[-2]
                value_type = mapping[-1]
                
                if value_type == bool:
                    current[target_key] = value.lower() in ('true', '1', 'yes', 'on')
                elif value_type == int:
                    current[target_key] = int(value)
                elif value_type == list:
                    current[target_key] = [v.strip() for v in value.split(',')]
                else:
                    current[target_key] = value
        
        return config
