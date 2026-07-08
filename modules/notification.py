"""
Notification Module
Sends notifications via Slack or Email on build completion or failure
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import requests


class NotificationManager:
    """Manage notifications for build events"""
    
    def __init__(self, config: Dict):
        """Initialize the notification manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.slack_config = config.get('slack', {})
        self.email_config = config.get('email', {})
    
    def send(self, build_metadata: Dict, status: str) -> bool:
        """
        Send notification based on configuration
        
        Args:
            build_metadata: Build metadata
            status: Build status (success or failure)
        
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        success = True
        
        # Send Slack notification
        if self.slack_config.get('enabled', False):
            slack_success = self._send_slack(build_metadata, status)
            success = success and slack_success
        
        # Send Email notification
        if self.email_config.get('enabled', False):
            email_success = self._send_email(build_metadata, status)
            success = success and email_success
        
        return success
    
    def _send_slack(self, build_metadata: Dict, status: str) -> bool:
        """Send Slack notification"""
        try:
            webhook_url = self.slack_config.get('webhook_url')
            if not webhook_url:
                self.logger.warning("Slack webhook URL not configured")
                return False
            
            self.logger.info("Sending Slack notification...")
            
            # Build message
            color = '#36a64f' if status == 'success' else '#ff0000'
            emoji = '✅' if status == 'success' else '❌'
            
            message = {
                'attachments': [
                    {
                        'color': color,
                        'title': f'{emoji} Docker Image Build {status.upper()}',
                        'fields': [
                            {
                                'title': 'Image',
                                'value': f"{build_metadata.get('image_name', 'N/A')}:{build_metadata.get('image_tag', 'latest')}",
                                'short': True
                            },
                            {
                                'title': 'Language',
                                'value': build_metadata.get('language', 'N/A'),
                                'short': True
                            },
                            {
                                'title': 'Registry',
                                'value': build_metadata.get('registry', 'N/A'),
                                'short': True
                            },
                            {
                                'title': 'Vulnerabilities',
                                'value': str(len(build_metadata.get('vulnerabilities', []))),
                                'short': True
                            },
                            {
                                'title': 'Signing Status',
                                'value': build_metadata.get('signing_status', 'N/A'),
                                'short': True
                            },
                            {
                                'title': 'Push Status',
                                'value': build_metadata.get('push_status', 'N/A'),
                                'short': True
                            }
                        ],
                        'footer': 'Docker Image Factory Framework',
                        'ts': int(build_metadata.get('end_time', 0).timestamp()) if build_metadata.get('end_time') else 0
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(webhook_url, json=message, timeout=10)
            
            if response.status_code != 200:
                self.logger.error(f"Slack notification failed: {response.text}")
                return False
            
            self.logger.info("Slack notification sent successfully")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Error sending Slack notification: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending Slack notification: {str(e)}")
            return False
    
    def _send_email(self, build_metadata: Dict, status: str) -> bool:
        """Send Email notification"""
        try:
            smtp_server = self.email_config.get('smtp_server')
            smtp_port = self.email_config.get('smtp_port', 587)
            username = self.email_config.get('username')
            password = self.email_config.get('password')
            from_email = self.email_config.get('from_email')
            to_emails = self.email_config.get('to_emails', [])
            
            if not all([smtp_server, username, password, from_email, to_emails]):
                self.logger.warning("Email configuration incomplete")
                return False
            
            self.logger.info("Sending Email notification...")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Docker Image Build {status.upper()}: {build_metadata.get('image_name', 'N/A')}"
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            
            # Build email body
            emoji = '✅' if status == 'success' else '❌'
            
            text_body = f"""
Docker Image Build {status.upper()}

{emoji} Build Status: {status}

Image Details:
- Image: {build_metadata.get('image_name', 'N/A')}:{build_metadata.get('image_tag', 'latest')}
- Language: {build_metadata.get('language', 'N/A')}
- Registry: {build_metadata.get('registry', 'N/A')}

Security:
- Total Vulnerabilities: {len(build_metadata.get('vulnerabilities', []))}

Pipeline Status:
- Signing: {build_metadata.get('signing_status', 'N/A')}
- Push: {build_metadata.get('push_status', 'N/A')}

Start Time: {build_metadata.get('start_time', 'N/A')}
End Time: {build_metadata.get('end_time', 'N/A')}

---
Generated by Docker Image Factory Framework
"""
            
            html_body = f"""
<html>
<body>
    <h2>{emoji} Docker Image Build {status.upper()}</h2>
    
    <h3>Build Status: {status}</h3>
    
    <h3>Image Details:</h3>
    <ul>
        <li><strong>Image:</strong> {build_metadata.get('image_name', 'N/A')}:{build_metadata.get('image_tag', 'latest')}</li>
        <li><strong>Language:</strong> {build_metadata.get('language', 'N/A')}</li>
        <li><strong>Registry:</strong> {build_metadata.get('registry', 'N/A')}</li>
    </ul>
    
    <h3>Security:</h3>
    <ul>
        <li><strong>Total Vulnerabilities:</strong> {len(build_metadata.get('vulnerabilities', []))}</li>
    </ul>
    
    <h3>Pipeline Status:</h3>
    <ul>
        <li><strong>Signing:</strong> {build_metadata.get('signing_status', 'N/A')}</li>
        <li><strong>Push:</strong> {build_metadata.get('push_status', 'N/A')}</li>
    </ul>
    
    <p><strong>Start Time:</strong> {build_metadata.get('start_time', 'N/A')}</p>
    <p><strong>End Time:</strong> {build_metadata.get('end_time', 'N/A')}</p>
    
    <hr>
    <p><em>Generated by Docker Image Factory Framework</em></p>
</body>
</html>
"""
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            self.logger.info("Email notification sent successfully")
            return True
            
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error sending email: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
            return False
