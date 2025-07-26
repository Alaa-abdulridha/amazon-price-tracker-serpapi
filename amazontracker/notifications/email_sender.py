"""
Email notification sender for price alerts
"""

import asyncio
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any
from datetime import datetime

from ..utils.config import settings

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Email sender for price alerts and notifications
    """
    
    def __init__(self):
        """Initialize email sender with SMTP configuration"""
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.email_username
        self.smtp_password = settings.email_password
        self.use_tls = settings.smtp_use_tls
        self.from_email = settings.email_from or settings.email_username
        
        logger.info("Email sender initialized")
    
    async def send_price_alert(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        product: Any,
        price_record: Any,
        attachment_path: Optional[str] = None
    ) -> bool:
        """
        Send price alert email with formatted content
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            product: Product object
            price_record: Price record object
            attachment_path: Optional path to attachment
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachment if provided
            if attachment_path:
                try:
                    with open(attachment_path, 'rb') as f:
                        attachment = MIMEBase('application', 'octet-stream')
                        attachment.set_payload(f.read())
                        encoders.encode_base64(attachment)
                        attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment_path.split("/")[-1]}'
                        )
                        msg.attach(attachment)
                except Exception as e:
                    logger.warning(f"Failed to attach file {attachment_path}: {e}")
            
            # Send email
            success = await self._send_email(msg, to_email)
            
            if success:
                logger.info(f"Price alert email sent to {to_email} for product: {product.name}")
            else:
                logger.error(f"Failed to send price alert email to {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending price alert email: {e}")
            return False
    
    async def send_simple_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Send simple email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            text_content: Plain text content
            html_content: Optional HTML content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if html_content:
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            else:
                msg = MIMEText(text_content, 'plain', 'utf-8')
            
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Send email
            success = await self._send_email(msg, to_email)
            
            if success:
                logger.info(f"Email sent to {to_email}: {subject}")
            else:
                logger.error(f"Failed to send email to {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def send_daily_summary(
        self,
        to_email: str,
        products_checked: int,
        deals_found: int,
        alerts_sent: int,
        top_deals: list,
        errors: list
    ) -> bool:
        """
        Send daily summary email
        
        Args:
            to_email: Recipient email
            products_checked: Number of products checked
            deals_found: Number of deals found
            alerts_sent: Number of alerts sent
            top_deals: List of top deals
            errors: List of errors encountered
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subject = f"Daily Amazon Price Tracker Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Generate content
            text_content = self._generate_summary_text(
                products_checked, deals_found, alerts_sent, top_deals, errors
            )
            html_content = self._generate_summary_html(
                products_checked, deals_found, alerts_sent, top_deals, errors
            )
            
            return await self.send_simple_email(
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False
    
    async def send_error_alert(
        self,
        to_email: str,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send error alert email
        
        Args:
            to_email: Recipient email
            error_type: Type of error
            error_message: Error message
            error_details: Additional error details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subject = f"🚨 Amazon Tracker Error Alert: {error_type}"
            
            text_content = f"""
Amazon Price Tracker Error Alert
================================

Error Type: {error_type}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Error Message:
{error_message}
"""
            
            if error_details:
                text_content += f"\nError Details:\n"
                for key, value in error_details.items():
                    text_content += f"  {key}: {value}\n"
            
            return await self.send_simple_email(
                to_email=to_email,
                subject=subject,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending error alert: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Test SMTP connection and authentication
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.smtp_username, self.smtp_password)
            server.quit()
            
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
    
    async def _send_email(self, msg: MIMEMultipart, to_email: str) -> bool:
        """
        Internal method to send email via SMTP
        
        Args:
            msg: Email message object
            to_email: Recipient email
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Run SMTP operations in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self._send_smtp_email,
                msg,
                to_email
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error in _send_email: {e}")
            return False
    
    def _send_smtp_email(self, msg: MIMEMultipart, to_email: str) -> bool:
        """
        Synchronous SMTP email sending
        
        Args:
            msg: Email message
            to_email: Recipient email
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create SMTP connection
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            # Login and send
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return False
    
    def _generate_summary_text(
        self,
        products_checked: int,
        deals_found: int,
        alerts_sent: int,
        top_deals: list,
        errors: list
    ) -> str:
        """Generate plain text summary content"""
        content = f"""
Amazon Price Tracker Daily Summary
==================================
Date: {datetime.now().strftime('%Y-%m-%d')}

STATISTICS
----------
Products Checked: {products_checked}
Deals Found: {deals_found}
Alerts Sent: {alerts_sent}

"""
        
        if top_deals:
            content += "TOP DEALS FOUND\n"
            content += "---------------\n"
            for i, deal in enumerate(top_deals[:5], 1):
                content += f"{i}. {deal.get('name', 'Unknown Product')}\n"
                content += f"   Price: ${deal.get('price', 0):.2f}\n"
                content += f"   Savings: ${deal.get('savings', 0):.2f}\n\n"
        
        if errors:
            content += "ERRORS ENCOUNTERED\n"
            content += "------------------\n"
            for error in errors[:5]:
                content += f"• {error}\n"
        
        return content
    
    def _generate_summary_html(
        self,
        products_checked: int,
        deals_found: int,
        alerts_sent: int,
        top_deals: list,
        errors: list
    ) -> str:
        """Generate HTML summary content"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; padding: 15px; background-color: #e9ecef; border-radius: 5px; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .deals {{ margin: 20px 0; }}
                .deal {{ padding: 10px; border-left: 4px solid #28a745; margin: 10px 0; background-color: #f8f9fa; }}
                .errors {{ margin: 20px 0; }}
                .error {{ padding: 10px; border-left: 4px solid #dc3545; margin: 10px 0; background-color: #f8d7da; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Summary</h1>
                    <p>{datetime.now().strftime('%Y-%m-%d')}</p>
                </div>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{products_checked}</div>
                        <div>Products Checked</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{deals_found}</div>
                        <div>Deals Found</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{alerts_sent}</div>
                        <div>Alerts Sent</div>
                    </div>
                </div>
        """
        
        if top_deals:
            html += '<div class="deals"><h2>🔥 Top Deals</h2>'
            for deal in top_deals[:5]:
                html += f"""
                <div class="deal">
                    <strong>{deal.get('name', 'Unknown Product')}</strong><br>
                    Price: <span style="color: #28a745; font-weight: bold;">${deal.get('price', 0):.2f}</span>
                    | Savings: <span style="color: #dc3545; font-weight: bold;">${deal.get('savings', 0):.2f}</span>
                </div>
                """
            html += '</div>'
        
        if errors:
            html += '<div class="errors"><h2>⚠️ Errors</h2>'
            for error in errors[:5]:
                html += f'<div class="error">{error}</div>'
            html += '</div>'
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
