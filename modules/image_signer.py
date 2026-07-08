"""
Image Signer Module
Signs Docker images using Cosign or Docker Content Trust
"""

import logging
import subprocess
import os
from typing import Dict


class ImageSigner:
    """Sign Docker images using Cosign or Docker Content Trust"""
    
    def __init__(self, config: Dict):
        """Initialize the image signer"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.default_method = config.get('signing', {}).get('default_method', 'cosign')
        self.cosign_key = config.get('signing', {}).get('cosign_key_path')
    
    def sign(self, image_name: str, image_tag: str = 'latest', 
             method: str = None) -> bool:
        """
        Sign Docker image
        
        Args:
            image_name: Name of the Docker image
            image_tag: Tag of the Docker image
            method: Signing method (cosign or docker-trust)
        
        Returns:
            bool: True if signing successful, False otherwise
        """
        method = method or self.default_method
        image_ref = f'{image_name}:{image_tag}'
        
        if method == 'cosign':
            return self._sign_with_cosign(image_ref)
        elif method == 'docker-trust':
            return self._sign_with_docker_trust(image_ref)
        else:
            self.logger.error(f"Unknown signing method: {method}")
            return False
    
    def _sign_with_cosign(self, image_ref: str) -> bool:
        """Sign image using Cosign"""
        try:
            self.logger.info(f"Signing {image_ref} with Cosign...")
            
            # Cosign sign command
            cmd = ['cosign', 'sign', image_ref]
            
            # Add key if specified
            if self.cosign_key:
                cmd.extend(['--key', self.cosign_key])
            else:
                # Use keyless signing
                cmd.append('--yes')
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Cosign signing failed: {result.stderr}")
                return False
            
            self.logger.info("Cosign signing successful")
            
            # Verify signature
            return self._verify_with_cosign(image_ref)
            
        except FileNotFoundError:
            self.logger.error("Cosign not found. Please install Cosign.")
            return False
        except Exception as e:
            self.logger.error(f"Error signing with Cosign: {str(e)}")
            return False
    
    def _verify_with_cosign(self, image_ref: str) -> bool:
        """Verify Cosign signature"""
        try:
            self.logger.info(f"Verifying signature for {image_ref}...")
            
            cmd = ['cosign', 'verify', image_ref]
            
            if self.cosign_key:
                cmd.extend(['--key', self.cosign_key])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.warning(f"Signature verification failed: {result.stderr}")
                return False
            
            self.logger.info("Signature verification successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying signature: {str(e)}")
            return False
    
    def _sign_with_docker_trust(self, image_ref: str) -> bool:
        """Sign image using Docker Content Trust"""
        try:
            self.logger.info(f"Signing {image_ref} with Docker Content Trust...")
            
            # Enable Docker Content Trust
            env = os.environ.copy()
            env['DOCKER_CONTENT_TRUST'] = '1'
            env['DOCKER_CONTENT_TRUST_REPOSITORY_PASSPHRASE'] = self.config.get(
                'signing', {}
            ).get('docker_trust_passphrase', '')
            
            # Docker trust sign command
            cmd = ['docker', 'trust', 'sign', image_ref]
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                self.logger.error(f"Docker trust signing failed: {result.stderr}")
                return False
            
            self.logger.info("Docker Content Trust signing successful")
            return True
            
        except FileNotFoundError:
            self.logger.error("Docker not found. Please install Docker.")
            return False
        except Exception as e:
            self.logger.error(f"Error signing with Docker Trust: {str(e)}")
            return False
