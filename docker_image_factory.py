#!/usr/bin/env python3
"""
Docker Image Factory Framework
A comprehensive framework for building, scanning, signing, and pushing Docker images
with support for multiple languages and automated security workflows.
"""

import argparse
import json
import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import modules
sys.path.insert(0, str(Path(__file__).parent))
from modules.dockerfile_generator import DockerfileGenerator
from modules.security_scanner import SecurityScanner
from modules.image_signer import ImageSigner
from modules.registry_pusher import RegistryPusher
from modules.report_generator import ReportGenerator
from modules.notification import NotificationManager
from modules.metadata_storage import MetadataStorage
from modules.config_loader import ConfigLoader


class DockerImageFactory:
    """Main class for Docker Image Factory operations"""
    
    def __init__(self, config_path: str = None):
        """Initialize the Docker Image Factory"""
        self.config = ConfigLoader(config_path).load_config()
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize modules
        self.dockerfile_gen = DockerfileGenerator(self.config)
        self.security_scanner = SecurityScanner(self.config)
        self.image_signer = ImageSigner(self.config)
        self.registry_pusher = RegistryPusher(self.config)
        self.report_gen = ReportGenerator(self.config)
        self.notification = NotificationManager(self.config)
        self.metadata_storage = MetadataStorage(self.config)
        
        # Build metadata
        self.build_metadata = {
            'start_time': datetime.utcnow().isoformat(),
            'status': 'in_progress',
            'language': None,
            'image_name': None,
            'image_tag': None,
            'registry': None,
            'vulnerabilities': [],
            'scan_results': {},
            'signing_status': None,
            'push_status': None
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(self.config.get('log_dir', 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f'build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def build_image(self, language: str, app_path: str, image_name: str, 
                    image_tag: str = 'latest', base_image: str = None,
                    custom_args: Dict = None) -> bool:
        """
        Build a Docker image with the specified parameters
        
        Args:
            language: Programming language/framework (python, java, node, groovy, robot, go, dotnet)
            app_path: Path to the application source code
            image_name: Name for the Docker image
            image_tag: Tag for the Docker image (default: latest)
            base_image: Custom base image (optional)
            custom_args: Additional custom arguments for Dockerfile generation
        
        Returns:
            bool: True if build successful, False otherwise
        """
        try:
            self.logger.info(f"Starting Docker image build for {language}")
            self.build_metadata['language'] = language
            self.build_metadata['image_name'] = image_name
            self.build_metadata['image_tag'] = image_tag
            
            # Generate Dockerfile
            self.logger.info("Generating Dockerfile...")
            dockerfile_path = self.dockerfile_gen.generate(
                language=language,
                app_path=app_path,
                base_image=base_image,
                custom_args=custom_args or {}
            )
            
            if not dockerfile_path:
                self.logger.error("Failed to generate Dockerfile")
                return False
            
            # Build the image
            self.logger.info(f"Building Docker image {image_name}:{image_tag}...")
            build_cmd = [
                'docker', 'build',
                '-f', dockerfile_path,
                '-t', f'{image_name}:{image_tag}',
                app_path
            ]
            
            result = subprocess.run(build_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Docker build failed: {result.stderr}")
                return False
            
            self.logger.info("Docker image built successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during image build: {str(e)}")
            return False
    
    def scan_image(self, image_name: str, image_tag: str = 'latest') -> Dict:
        """
        Scan Docker image for vulnerabilities using Trivy/Snyk
        
        Args:
            image_name: Name of the Docker image
            image_tag: Tag of the Docker image
        
        Returns:
            Dict: Scan results including vulnerabilities found
        """
        try:
            self.logger.info(f"Scanning image {image_name}:{image_tag} for vulnerabilities...")
            scan_results = self.security_scanner.scan(image_name, image_tag)
            
            self.build_metadata['scan_results'] = scan_results
            self.build_metadata['vulnerabilities'] = scan_results.get('vulnerabilities', [])
            
            self.logger.info(f"Scan complete. Found {len(scan_results.get('vulnerabilities', []))} vulnerabilities")
            return scan_results
            
        except Exception as e:
            self.logger.error(f"Error during security scan: {str(e)}")
            return {'error': str(e)}
    
    def sign_image(self, image_name: str, image_tag: str = 'latest', 
                   method: str = 'cosign') -> bool:
        """
        Sign Docker image using Cosign or Docker Content Trust
        
        Args:
            image_name: Name of the Docker image
            image_tag: Tag of the Docker image
            method: Signing method (cosign or docker-trust)
        
        Returns:
            bool: True if signing successful, False otherwise
        """
        try:
            self.logger.info(f"Signing image {image_name}:{image_tag} using {method}...")
            success = self.image_signer.sign(image_name, image_tag, method)
            
            self.build_metadata['signing_status'] = 'success' if success else 'failed'
            
            if success:
                self.logger.info("Image signed successfully")
            else:
                self.logger.error("Image signing failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during image signing: {str(e)}")
            self.build_metadata['signing_status'] = 'failed'
            return False
    
    def push_image(self, image_name: str, image_tag: str = 'latest', 
                   registry: str = None) -> bool:
        """
        Push Docker image to registry (ECR or DockerHub)
        
        Args:
            image_name: Name of the Docker image
            image_tag: Tag of the Docker image
            registry: Target registry (ecr or dockerhub)
        
        Returns:
            bool: True if push successful, False otherwise
        """
        try:
            registry = registry or self.config.get('default_registry', 'dockerhub')
            self.logger.info(f"Pushing image {image_name}:{image_tag} to {registry}...")
            
            success = self.registry_pusher.push(image_name, image_tag, registry)
            
            self.build_metadata['push_status'] = 'success' if success else 'failed'
            self.build_metadata['registry'] = registry
            
            if success:
                self.logger.info("Image pushed successfully")
            else:
                self.logger.error("Image push failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during image push: {str(e)}")
            self.build_metadata['push_status'] = 'failed'
            return False
    
    def generate_report(self, output_path: str = None) -> str:
        """
        Generate HTML report with build and vulnerability summary
        
        Args:
            output_path: Path to save the HTML report
        
        Returns:
            str: Path to the generated report
        """
        try:
            self.logger.info("Generating build report...")
            report_path = self.report_gen.generate(self.build_metadata, output_path)
            self.logger.info(f"Report generated at {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            return None
    
    def store_metadata(self) -> bool:
        """
        Store build metadata in DynamoDB or S3
        
        Returns:
            bool: True if storage successful, False otherwise
        """
        try:
            self.logger.info("Storing build metadata...")
            success = self.metadata_storage.store(self.build_metadata)
            
            if success:
                self.logger.info("Metadata stored successfully")
            else:
                self.logger.error("Metadata storage failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error storing metadata: {str(e)}")
            return False
    
    def send_notification(self, status: str = 'success') -> bool:
        """
        Send notification via Slack or Email
        
        Args:
            status: Build status (success or failure)
        
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            self.logger.info(f"Sending {status} notification...")
            success = self.notification.send(self.build_metadata, status)
            
            if success:
                self.logger.info("Notification sent successfully")
            else:
                self.logger.error("Notification failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def run_full_pipeline(self, language: str, app_path: str, image_name: str,
                         image_tag: str = 'latest', base_image: str = None,
                         custom_args: Dict = None, registry: str = None,
                         sign_method: str = 'cosign', skip_scan: bool = False,
                         skip_sign: bool = False, skip_push: bool = False) -> bool:
        """
        Run the complete Docker image factory pipeline
        
        Args:
            language: Programming language/framework
            app_path: Path to application source code
            image_name: Name for the Docker image
            image_tag: Tag for the Docker image
            base_image: Custom base image
            custom_args: Additional custom arguments
            registry: Target registry
            sign_method: Image signing method
            skip_scan: Skip security scanning
            skip_sign: Skip image signing
            skip_push: Skip registry push
        
        Returns:
            bool: True if pipeline successful, False otherwise
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("Starting Docker Image Factory Pipeline")
            self.logger.info("=" * 80)
            
            # Build image
            if not self.build_image(language, app_path, image_name, image_tag, base_image, custom_args):
                self.build_metadata['status'] = 'failed'
                self.build_metadata['end_time'] = datetime.utcnow().isoformat()
                self.send_notification('failure')
                return False
            
            # Security scan
            if not skip_scan:
                self.scan_image(image_name, image_tag)
            
            # Sign image
            if not skip_sign:
                if not self.sign_image(image_name, image_tag, sign_method):
                    self.logger.warning("Image signing failed, continuing...")
            
            # Push image
            if not skip_push:
                if not self.push_image(image_name, image_tag, registry):
                    self.logger.warning("Image push failed, continuing...")
            
            # Generate report
            self.generate_report()
            
            # Store metadata
            self.store_metadata()
            
            # Send notification
            self.build_metadata['status'] = 'success'
            self.build_metadata['end_time'] = datetime.utcnow().isoformat()
            self.send_notification('success')
            
            self.logger.info("=" * 80)
            self.logger.info("Docker Image Factory Pipeline completed successfully")
            self.logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            self.build_metadata['status'] = 'failed'
            self.build_metadata['end_time'] = datetime.utcnow().isoformat()
            self.build_metadata['error'] = str(e)
            self.send_notification('failure')
            return False


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Docker Image Factory Framework - Build, scan, sign, and push Docker images'
    )
    
    parser.add_argument(
        '--language', '-l',
        required=True,
        choices=['python', 'java', 'node', 'groovy', 'robot', 'go', 'dotnet'],
        help='Programming language/framework'
    )
    
    parser.add_argument(
        '--app-path', '-a',
        required=True,
        help='Path to application source code'
    )
    
    parser.add_argument(
        '--image-name', '-i',
        required=True,
        help='Name for the Docker image'
    )
    
    parser.add_argument(
        '--image-tag', '-t',
        default='latest',
        help='Tag for the Docker image (default: latest)'
    )
    
    parser.add_argument(
        '--base-image', '-b',
        help='Custom base image'
    )
    
    parser.add_argument(
        '--registry', '-r',
        choices=['ecr', 'dockerhub'],
        help='Target registry (ecr or dockerhub)'
    )
    
    parser.add_argument(
        '--sign-method', '-s',
        choices=['cosign', 'docker-trust'],
        default='cosign',
        help='Image signing method (default: cosign)'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--skip-scan',
        action='store_true',
        help='Skip security scanning'
    )
    
    parser.add_argument(
        '--skip-sign',
        action='store_true',
        help='Skip image signing'
    )
    
    parser.add_argument(
        '--skip-push',
        action='store_true',
        help='Skip registry push'
    )
    
    parser.add_argument(
        '--custom-args',
        help='JSON string of custom arguments for Dockerfile generation'
    )
    
    args = parser.parse_args()
    
    # Parse custom args if provided
    custom_args = {}
    if args.custom_args:
        try:
            custom_args = json.loads(args.custom_args)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in custom-args")
            sys.exit(1)
    
    # Initialize factory
    factory = DockerImageFactory(args.config)
    
    # Run pipeline
    success = factory.run_full_pipeline(
        language=args.language,
        app_path=args.app_path,
        image_name=args.image_name,
        image_tag=args.image_tag,
        base_image=args.base_image,
        custom_args=custom_args,
        registry=args.registry,
        sign_method=args.sign_method,
        skip_scan=args.skip_scan,
        skip_sign=args.skip_sign,
        skip_push=args.skip_push
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
