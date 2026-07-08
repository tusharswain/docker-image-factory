"""
Report Generator Module
Generates HTML reports with build and vulnerability summaries
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class ReportGenerator:
    """Generate HTML reports for Docker image builds"""
    
    def __init__(self, config: Dict):
        """Initialize the report generator"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reports_dir = Path(__file__).parent.parent / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate(self, build_metadata: Dict, output_path: str = None) -> Optional[str]:
        """
        Generate HTML report
        
        Args:
            build_metadata: Build metadata including scan results
            output_path: Custom output path for the report
        
        Returns:
            str: Path to generated report
        """
        try:
            self.logger.info("Generating HTML report...")
            
            # Generate report filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_name = build_metadata.get('image_name', 'unknown').replace('/', '_')
            filename = f"build_report_{image_name}_{timestamp}.html"
            
            if output_path:
                report_path = Path(output_path)
            else:
                report_path = self.reports_dir / filename
            
            # Generate HTML content
            html_content = self._generate_html(build_metadata)
            
            # Write report
            with open(report_path, 'w') as f:
                f.write(html_content)
            
            self.logger.info(f"Report generated at {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            return None
    
    def _generate_html(self, metadata: Dict) -> str:
        """Generate HTML content for the report"""
        status = metadata.get('status', 'unknown')
        status_color = 'green' if status == 'success' else 'red'
        
        vulnerabilities = metadata.get('vulnerabilities', [])
        scan_results = metadata.get('scan_results', {})
        
        # Calculate severity counts
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'UNKNOWN').upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docker Image Factory Build Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 10px 30px;
            border-radius: 25px;
            font-size: 1.2em;
            font-weight: bold;
            background: {status_color};
            margin-top: 15px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section h2 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .info-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .info-card label {{
            display: block;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        
        .info-card .value {{
            color: #333;
            font-size: 1.1em;
            font-weight: 600;
        }}
        
        .severity-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .severity-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            color: white;
        }}
        
        .severity-critical {{ background: #dc3545; }}
        .severity-high {{ background: #fd7e14; }}
        .severity-medium {{ background: #ffc107; }}
        .severity-low {{ background: #28a745; }}
        
        .severity-card .count {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        
        .severity-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge-critical {{ background: #dc3545; color: white; }}
        .badge-high {{ background: #fd7e14; color: white; }}
        .badge-medium {{ background: #ffc107; color: #333; }}
        .badge-low {{ background: #28a745; color: white; }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #ddd;
        }}
        
        .no-vulnerabilities {{
            text-align: center;
            padding: 40px;
            color: #28a745;
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐳 Docker Image Factory Build Report</h1>
            <div class="status-badge">Status: {status.upper()}</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📋 Build Information</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <label>Image Name</label>
                        <div class="value">{metadata.get('image_name', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <label>Image Tag</label>
                        <div class="value">{metadata.get('image_tag', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <label>Language</label>
                        <div class="value">{metadata.get('language', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <label>Registry</label>
                        <div class="value">{metadata.get('registry', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <label>Start Time</label>
                        <div class="value">{metadata.get('start_time', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <label>End Time</label>
                        <div class="value">{metadata.get('end_time', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <label>Signing Status</label>
                        <div class="value">{metadata.get('signing_status', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <label>Push Status</label>
                        <div class="value">{metadata.get('push_status', 'N/A')}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔒 Security Scan Summary</h2>
                <div class="severity-summary">
                    <div class="severity-card severity-critical">
                        <div class="count">{severity_counts['CRITICAL']}</div>
                        <div class="label">CRITICAL</div>
                    </div>
                    <div class="severity-card severity-high">
                        <div class="count">{severity_counts['HIGH']}</div>
                        <div class="label">HIGH</div>
                    </div>
                    <div class="severity-card severity-medium">
                        <div class="count">{severity_counts['MEDIUM']}</div>
                        <div class="label">MEDIUM</div>
                    </div>
                    <div class="severity-card severity-low">
                        <div class="count">{severity_counts['LOW']}</div>
                        <div class="label">LOW</div>
                    </div>
                </div>
                
                <div class="info-card">
                    <label>Total Vulnerabilities</label>
                    <div class="value">{len(vulnerabilities)}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📝 Vulnerability Details</h2>
                {self._generate_vulnerability_table(vulnerabilities)}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Docker Image Factory Framework on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_vulnerability_table(self, vulnerabilities: list) -> str:
        """Generate HTML table for vulnerabilities"""
        if not vulnerabilities:
            return '<div class="no-vulnerabilities">✅ No vulnerabilities found!</div>'
        
        table_html = """
        <table>
            <thead>
                <tr>
                    <th>Vulnerability ID</th>
                    <th>Package</th>
                    <th>Installed Version</th>
                    <th>Fixed Version</th>
                    <th>Severity</th>
                    <th>Scanner</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for vuln in vulnerabilities[:50]:  # Limit to first 50 for performance
            severity = vuln.get('severity', 'UNKNOWN').upper()
            badge_class = f'badge-{severity.lower()}' if severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] else 'badge-low'
            
            table_html += f"""
                <tr>
                    <td>{vuln.get('vulnerability_id', 'N/A')}</td>
                    <td>{vuln.get('package_name', 'N/A')}</td>
                    <td>{vuln.get('installed_version', 'N/A')}</td>
                    <td>{vuln.get('fixed_version', 'N/A')}</td>
                    <td><span class="badge {badge_class}">{severity}</span></td>
                    <td>{vuln.get('scanner', 'N/A')}</td>
                </tr>
            """
        
        if len(vulnerabilities) > 50:
            table_html += f"""
                <tr>
                    <td colspan="6" style="text-align: center; color: #666;">
                        ... and {len(vulnerabilities) - 50} more vulnerabilities
                    </td>
                </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        
        return table_html
