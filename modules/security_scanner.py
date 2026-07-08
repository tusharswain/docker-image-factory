"""
Security Scanner Module
Integrates Trivy and Snyk for vulnerability scanning of Docker images
"""

import json
import logging
import subprocess
from typing import Dict, List, Optional


class SecurityScanner:
    """Scan Docker images for vulnerabilities using Trivy and Snyk"""
    
    def __init__(self, config: Dict):
        """Initialize the security scanner"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.trivy_enabled = config.get('trivy', {}).get('enabled', True)
        self.snyk_enabled = config.get('snyk', {}).get('enabled', False)
        self.severity_threshold = config.get('security', {}).get('severity_threshold', 'HIGH')
    
    def scan(self, image_name: str, image_tag: str = 'latest') -> Dict:
        """
        Scan Docker image for vulnerabilities
        
        Args:
            image_name: Name of the Docker image
            image_tag: Tag of the Docker image
        
        Returns:
            Dict: Scan results including vulnerabilities found
        """
        results = {
            'image': f'{image_name}:{image_tag}',
            'trivy_results': {},
            'snyk_results': {},
            'vulnerabilities': [],
            'summary': {}
        }
        
        # Run Trivy scan
        if self.trivy_enabled:
            self.logger.info("Running Trivy scan...")
            trivy_results = self._run_trivy(image_name, image_tag)
            results['trivy_results'] = trivy_results
            results['vulnerabilities'].extend(trivy_results.get('vulnerabilities', []))
        
        # Run Snyk scan
        if self.snyk_enabled:
            self.logger.info("Running Snyk scan...")
            snyk_results = self._run_snyk(image_name, image_tag)
            results['snyk_results'] = snyk_results
            results['vulnerabilities'].extend(snyk_results.get('vulnerabilities', []))
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        return results
    
    def _run_trivy(self, image_name: str, image_tag: str) -> Dict:
        """Run Trivy vulnerability scanner"""
        try:
            image_ref = f'{image_name}:{image_tag}'
            
            # Trivy command
            cmd = [
                'trivy', 'image',
                '--format', 'json',
                '--severity', self.severity_threshold,
                '--no-progress',
                image_ref
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.warning(f"Trivy scan completed with warnings: {result.stderr}")
            
            # Parse JSON output
            try:
                trivy_data = json.loads(result.stdout)
                vulnerabilities = self._parse_trivy_results(trivy_data)
                
                return {
                    'success': True,
                    'vulnerabilities': vulnerabilities,
                    'raw_output': trivy_data
                }
            except json.JSONDecodeError:
                self.logger.error("Failed to parse Trivy JSON output")
                return {
                    'success': False,
                    'error': 'Failed to parse Trivy output',
                    'vulnerabilities': []
                }
                
        except FileNotFoundError:
            self.logger.error("Trivy not found. Please install Trivy.")
            return {
                'success': False,
                'error': 'Trivy not found',
                'vulnerabilities': []
            }
        except Exception as e:
            self.logger.error(f"Error running Trivy: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'vulnerabilities': []
            }
    
    def _parse_trivy_results(self, trivy_data: Dict) -> List[Dict]:
        """Parse Trivy scan results"""
        vulnerabilities = []
        
        for result in trivy_data.get('Results', []):
            for vuln in result.get('Vulnerabilities', []):
                vulnerabilities.append({
                    'scanner': 'trivy',
                    'vulnerability_id': vuln.get('VulnerabilityID', 'UNKNOWN'),
                    'package_name': vuln.get('PkgName', 'UNKNOWN'),
                    'installed_version': vuln.get('InstalledVersion', 'UNKNOWN'),
                    'fixed_version': vuln.get('FixedVersion', 'None'),
                    'severity': vuln.get('Severity', 'UNKNOWN'),
                    'title': vuln.get('Title', ''),
                    'description': vuln.get('Description', ''),
                    'references': vuln.get('References', [])
                })
        
        return vulnerabilities
    
    def _run_snyk(self, image_name: str, image_tag: str) -> Dict:
        """Run Snyk vulnerability scanner"""
        try:
            image_ref = f'{image_name}:{image_tag}'
            
            # Snyk command
            cmd = [
                'snyk', 'container', 'test',
                '--json',
                image_ref
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.warning(f"Snyk scan completed with warnings: {result.stderr}")
            
            # Parse JSON output
            try:
                snyk_data = json.loads(result.stdout)
                vulnerabilities = self._parse_snyk_results(snyk_data)
                
                return {
                    'success': True,
                    'vulnerabilities': vulnerabilities,
                    'raw_output': snyk_data
                }
            except json.JSONDecodeError:
                self.logger.error("Failed to parse Snyk JSON output")
                return {
                    'success': False,
                    'error': 'Failed to parse Snyk output',
                    'vulnerabilities': []
                }
                
        except FileNotFoundError:
            self.logger.error("Snyk not found. Please install Snyk CLI.")
            return {
                'success': False,
                'error': 'Snyk not found',
                'vulnerabilities': []
            }
        except Exception as e:
            self.logger.error(f"Error running Snyk: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'vulnerabilities': []
            }
    
    def _parse_snyk_results(self, snyk_data: Dict) -> List[Dict]:
        """Parse Snyk scan results"""
        vulnerabilities = []
        
        for vuln in snyk_data.get('vulnerabilities', []):
            vulnerabilities.append({
                'scanner': 'snyk',
                'vulnerability_id': vuln.get('id', 'UNKNOWN'),
                'package_name': vuln.get('package', 'UNKNOWN'),
                'installed_version': vuln.get('version', 'UNKNOWN'),
                'fixed_version': vuln.get('fixedIn', 'None'),
                'severity': vuln.get('severity', 'UNKNOWN'),
                'title': vuln.get('title', ''),
                'description': vuln.get('description', ''),
                'references': vuln.get('references', [])
            })
        
        return vulnerabilities
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of scan results"""
        vulnerabilities = results['vulnerabilities']
        
        # Count by severity
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'UNKNOWN': 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'UNKNOWN').upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return {
            'total_vulnerabilities': len(vulnerabilities),
            'severity_counts': severity_counts,
            'scanners_used': []
        }
