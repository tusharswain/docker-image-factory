"""
Registry Pusher Module
Pushes Docker images to ECR or DockerHub registries
"""

import logging
import subprocess
import os
from typing import Dict


class RegistryPusher:
    """Push Docker images to container registries"""
    
    def __init__(self, config: Dict):
        """Initialize the registry pusher"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ecr_config = config.get('ecr', {})
        self.dockerhub_config = config.get('dockerhub', {})
    
    def push(self, image_name: str, image_tag: str = 'latest', 
             registry: str = 'dockerhub') -> bool:
        """
        Push Docker image to registry
        
        Args:
            image_name: Name of the Docker image
            image_tag: Tag of the Docker image
            registry: Target registry (ecr or dockerhub)
        
        Returns:
            bool: True if push successful, False otherwise
        """
        if registry == 'ecr':
            return self._push_to_ecr(image_name, image_tag)
        elif registry == 'dockerhub':
            return self._push_to_dockerhub(image_name, image_tag)
        else:
            self.logger.error(f"Unknown registry: {registry}")
            return False
    
    def _push_to_ecr(self, image_name: str, image_tag: str) -> bool:
        """Push image to Amazon ECR"""
        try:
            self.logger.info(f"Pushing {image_name}:{image_tag} to ECR...")
            
            # Get ECR repository URI
            ecr_uri = self.ecr_config.get('repository_uri')
            if not ecr_uri:
                self.logger.error("ECR repository URI not configured")
                return False
            
            # Tag image for ECR
            ecr_image_ref = f'{ecr_uri}/{image_name}:{image_tag}'
            tag_cmd = ['docker', 'tag', f'{image_name}:{image_tag}', ecr_image_ref]
            
            result = subprocess.run(tag_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Docker tag failed: {result.stderr}")
                return False
            
            # Login to ECR if needed
            if not self._ecr_login():
                self.logger.error("ECR login failed")
                return False
            
            # Push to ECR
            push_cmd = ['docker', 'push', ecr_image_ref]
            result = subprocess.run(push_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"ECR push failed: {result.stderr}")
                return False
            
            self.logger.info(f"Successfully pushed to ECR: {ecr_image_ref}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pushing to ECR: {str(e)}")
            return False
    
    def _ecr_login(self) -> bool:
        """Login to Amazon ECR"""
        try:
            self.logger.info("Logging in to ECR...")
            
            region = self.ecr_config.get('region', 'us-east-1')
            
            # Get ECR login password using AWS CLI
            login_cmd = [
                'aws', 'ecr', 'get-login-password',
                '--region', region
            ]
            
            result = subprocess.run(login_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get ECR login password: {result.stderr}")
                return False
            
            password = result.stdout.strip()
            ecr_uri = self.ecr_config.get('repository_uri')
            
            # Docker login
            docker_login_cmd = [
                'docker', 'login',
                '--username', 'AWS',
                '--password-stdin',
                ecr_uri.split('/')[0]
            ]
            
            result = subprocess.run(docker_login_cmd, input=password, 
                                    capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Docker login failed: {result.stderr}")
                return False
            
            self.logger.info("ECR login successful")
            return True
            
        except FileNotFoundError:
            self.logger.error("AWS CLI not found. Please install AWS CLI.")
            return False
        except Exception as e:
            self.logger.error(f"Error during ECR login: {str(e)}")
            return False
    
    def _push_to_dockerhub(self, image_name: str, image_tag: str) -> bool:
        """Push image to DockerHub"""
        try:
            self.logger.info(f"Pushing {image_name}:{image_tag} to DockerHub...")
            
            # Get DockerHub username
            username = self.dockerhub_config.get('username')
            if not username:
                self.logger.error("DockerHub username not configured")
                return False
            
            # Tag image for DockerHub
            dockerhub_image_ref = f'{username}/{image_name}:{image_tag}'
            tag_cmd = ['docker', 'tag', f'{image_name}:{image_tag}', dockerhub_image_ref]
            
            result = subprocess.run(tag_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Docker tag failed: {result.stderr}")
                return False
            
            # Login to DockerHub if needed
            if not self._dockerhub_login():
                self.logger.error("DockerHub login failed")
                return False
            
            # Push to DockerHub
            push_cmd = ['docker', 'push', dockerhub_image_ref]
            result = subprocess.run(push_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"DockerHub push failed: {result.stderr}")
                return False
            
            self.logger.info(f"Successfully pushed to DockerHub: {dockerhub_image_ref}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pushing to DockerHub: {str(e)}")
            return False
    
    def _dockerhub_login(self) -> bool:
        """Login to DockerHub"""
        try:
            self.logger.info("Logging in to DockerHub...")
            
            username = self.dockerhub_config.get('username')
            password = self.dockerhub_config.get('password')
            
            if not username or not password:
                self.logger.error("DockerHub credentials not configured")
                return False
            
            # Docker login
            login_cmd = [
                'docker', 'login',
                '--username', username,
                '--password-stdin'
            ]
            
            result = subprocess.run(login_cmd, input=password, 
                                    capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Docker login failed: {result.stderr}")
                return False
            
            self.logger.info("DockerHub login successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during DockerHub login: {str(e)}")
            return False
