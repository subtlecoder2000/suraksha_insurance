"""
services/email_service.py
Real SMTP Email Service for RenewAI

Supports:
- Gmail SMTP (primary)
- Outlook/Office365 SMTP
- Custom SMTP servers
- HTML email templates
- Attachment support
- Delivery tracking
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Production SMTP email sender with multiple provider support
    """
    
    # SMTP Configuration Templates
    PROVIDERS = {
        'gmail': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'display_name': 'Gmail'
        },
        'outlook': {
            'host': 'smtp-mail.outlook.com',
            'port': 587,
            'use_tls': True,
            'display_name': 'Outlook'
        },
        'office365': {
            'host': 'smtp.office365.com',
            'port': 587,
            'use_tls': True,
            'display_name': 'Office 365'
        },
        'custom': {
            'host': None,  # Set via env
            'port': 587,
            'use_tls': True,
            'display_name': 'Custom SMTP'
        }
    }
    
    def __init__(self):
        """
        Initialize email service from environment variables
        
        Required env vars:
        - SMTP_PROVIDER: gmail|outlook|office365|custom
        - SMTP_USERNAME: your email address
        - SMTP_PASSWORD: app password (not your regular password!)
        - SMTP_FROM_NAME: sender display name (optional)
        
        For custom SMTP:
        - SMTP_HOST: custom SMTP server
        - SMTP_PORT: custom port (default 587)
        """
        self.provider = os.getenv('SMTP_PROVIDER', 'gmail').lower()
        self.username = os.getenv('SMTP_USERNAME')
        self.password = os.getenv('SMTP_PASSWORD')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Suraksha Life Insurance')
        
        # Get provider config
        if self.provider in self.PROVIDERS:
            config = self.PROVIDERS[self.provider]
            self.smtp_host = os.getenv('SMTP_HOST', config['host'])
            self.smtp_port = int(os.getenv('SMTP_PORT', config['port']))
            self.use_tls = config['use_tls']
        else:
            raise ValueError(f"Unknown SMTP provider: {self.provider}")
        
        # Validate credentials
        if not self.username or not self.password:
            logger.warning("SMTP credentials not configured. Email sending will be in STUB mode.")
            self.stub_mode = True
        else:
            self.stub_mode = False
            logger.info(f"Email service initialized with {self.provider.upper()} SMTP")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Send an email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML email body
            body_text: Plain text fallback (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            attachments: List of dicts with 'filename' and 'content' keys
        
        Returns:
            Dict with success status, message_id, and metadata
        """
        if self.stub_mode:
            return self._stub_send(to_email, subject, body_html)
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.username}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            msg['Message-ID'] = f"<{datetime.now().timestamp()}@renewai.suraksha.com>"
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Attach text and HTML parts
            if body_text:
                part_text = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(part_text)
            
            part_html = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part_html)
            
            # Attach files if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f"attachment; filename= {attachment['filename']}"
                    )
                    msg.attach(part)
            
            # Connect to SMTP server and send
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.username, self.password)
                server.send_message(msg, from_addr=self.username, to_addrs=recipients)
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            
            return {
                'success': True,
                'message_id': msg['Message-ID'],
                'to': to_email,
                'subject': subject,
                'sent_at': datetime.now().isoformat(),
                'provider': self.provider,
                'status': 'delivered'
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {e}")
            return {
                'success': False,
                'error': 'authentication_failed',
                'message': 'Invalid SMTP credentials. Check username/password.',
                'details': str(e)
            }
        
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return {
                'success': False,
                'error': 'smtp_error',
                'message': 'Failed to send email via SMTP',
                'details': str(e)
            }
        
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {e}")
            return {
                'success': False,
                'error': 'unknown_error',
                'message': 'An unexpected error occurred',
                'details': str(e)
            }
    
    def _stub_send(self, to_email: str, subject: str, body_html: str) -> Dict:
        """
        Stub mode - logs email without actually sending
        """
        logger.info("=" * 80)
        logger.info("📧 EMAIL STUB MODE (No SMTP credentials configured)")
        logger.info("=" * 80)
        logger.info(f"To: {to_email}")
        logger.info(f"From: {self.from_name} <{self.username or 'not-configured'}@example.com>")
        logger.info(f"Subject: {subject}")
        logger.info("-" * 80)
        logger.info("Body Preview:")
        # Strip HTML tags for console preview
        import re
        text_preview = re.sub('<[^<]+?>', '', body_html)[:200]
        logger.info(text_preview + "...")
        logger.info("=" * 80)
        
        return {
            'success': True,
            'message_id': f"stub_{datetime.now().timestamp()}",
            'to': to_email,
            'subject': subject,
            'sent_at': datetime.now().isoformat(),
            'provider': 'stub',
            'status': 'logged_only'
        }
    
    def test_connection(self) -> Dict:
        """
        Test SMTP connection without sending email
        
        Returns:
            Dict with connection status and details
        """
        if self.stub_mode:
            return {
                'success': False,
                'message': 'SMTP credentials not configured',
                'help': 'Set SMTP_PROVIDER, SMTP_USERNAME, SMTP_PASSWORD in .env'
            }
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.username, self.password)
            
            return {
                'success': True,
                'message': f'Successfully connected to {self.provider.upper()} SMTP',
                'provider': self.provider,
                'host': self.smtp_host,
                'port': self.smtp_port,
                'username': self.username
            }
        
        except smtplib.SMTPAuthenticationError:
            return {
                'success': False,
                'message': 'Authentication failed',
                'error': 'Invalid username or password',
                'help': 'For Gmail: Use App Password (not regular password). Enable 2FA first.'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': 'Connection failed',
                'error': str(e)
            }
    
    def send_renewal_email(
        self,
        customer_name: str,
        customer_email: str,
        policy_number: str,
        policy_type: str,
        premium_amount: int,
        due_date: str,
        sum_assured: int,
        offers: List[str],
        payment_link: str,
        language: str = 'en'
    ) -> Dict:
        """
        Send a renewal email with RenewAI branding
        
        This is a convenience method with a pre-built template
        """
        # Generate HTML email from template
        html_body = self._generate_renewal_template(
            customer_name=customer_name,
            policy_number=policy_number,
            policy_type=policy_type,
            premium_amount=premium_amount,
            due_date=due_date,
            sum_assured=sum_assured,
            offers=offers,
            payment_link=payment_link,
            language=language
        )
        
        # Generate subject line
        subject = f"🔔 Renew Your {policy_type} - Exclusive Offers Inside!"
        
        # Send email
        return self.send_email(
            to_email=customer_email,
            subject=subject,
            body_html=html_body,
            body_text=self._strip_html(html_body)
        )
    
    def _generate_renewal_template(
        self,
        customer_name: str,
        policy_number: str,
        policy_type: str,
        premium_amount: int,
        due_date: str,
        sum_assured: int,
        offers: List[str],
        payment_link: str,
        language: str
    ) -> str:
        """
        Generate HTML email template for renewal
        """
        offers_html = "\n".join([f"<li>✅ {offer}</li>" for offer in offers])
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            padding: 30px;
            color: #333;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
        }}
        .policy-details {{
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
        }}
        .offers {{
            background-color: #fff3cd;
            border: 2px dashed #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        .offers h3 {{
            color: #d39e00;
            margin-top: 0;
        }}
        .offers ul {{
            list-style: none;
            padding: 0;
        }}
        .offers li {{
            padding: 8px 0;
            font-size: 15px;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 15px 40px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            margin: 20px 0;
            text-align: center;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
        }}
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Suraksha Life Insurance</h1>
            <p style="margin: 5px 0 0 0;">PROJECT RenewAI</p>
        </div>
        
        <div class="content">
            <div class="greeting">
                Dear <strong>{customer_name}</strong>,
            </div>
            
            <p>
                Your <strong>{policy_type}</strong> policy is due for renewal on <strong>{due_date}</strong>.
                We've been protecting your family's future together, and we'd love to continue this journey!
            </p>
            
            <div class="policy-details">
                <strong>Policy Number:</strong> {policy_number}<br>
                <strong>Coverage:</strong> ₹{sum_assured:,}<br>
                <strong>Annual Premium:</strong> ₹{premium_amount:,}<br>
                <strong>Due Date:</strong> {due_date}
            </div>
            
            <div class="offers">
                <h3>🎉 Special Renewal Offers for You</h3>
                <ul>
                    {offers_html}
                </ul>
            </div>
            
            <p style="text-align: center;">
                <a href="{payment_link}" class="cta-button">
                    💳 Pay Now & Renew
                </a>
            </p>
            
            <p style="font-size: 14px; color: #666;">
                <strong>Questions?</strong> Reply to this email or call us at 
                <strong>1800-XXX-XXXX</strong> (9 AM - 9 PM, 7 days)
            </p>
            
            <p style="font-size: 14px; color: #666;">
                We're here to help you maintain your family's financial security! 🛡️
            </p>
        </div>
        
        <div class="footer">
            <p><strong>Suraksha Life Insurance Ltd.</strong></p>
            <p>IRDAI Reg No: XXX | Established 2003 | Mumbai, India</p>
            <p>
                <a href="#">Privacy Policy</a> | 
                <a href="#">Terms & Conditions</a> | 
                <a href="#">Grievance Redressal</a>
            </p>
            <p style="margin-top: 15px; font-size: 11px;">
                This is an automated renewal reminder. Premium subject to GST.<br>
                Don't want renewal reminders? <a href="#">Unsubscribe</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _strip_html(self, html: str) -> str:
        """
        Strip HTML tags for plain text version
        """
        import re
        text = re.sub('<[^<]+?>', '', html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """
    Get or create EmailService singleton
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
