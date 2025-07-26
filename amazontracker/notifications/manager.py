"""
Notification manager for sending alerts via multiple channels
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .email_sender import EmailSender
from .slack_sender import SlackSender
from .desktop_notifier import DesktopNotifier
from ..database.models import NotificationLog
from ..database.connection import get_db_session
from ..utils.config import settings

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manages all notification channels and delivery
    """
    
    def __init__(self):
        """Initialize notification manager with all channels"""
        self.email_sender = EmailSender() if settings.email_enabled else None
        self.slack_sender = SlackSender() if settings.slack_enabled else None
        self.desktop_notifier = DesktopNotifier() if settings.desktop_notifications_enabled else None
        
        logger.info("Notification manager initialized")
    
    async def send_email_alert(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send email alert notification
        
        Args:
            notification_data: Notification data containing product, price, and alert info
            
        Returns:
            True if successful, False otherwise
        """
        if not self.email_sender:
            logger.warning("Email notifications not enabled")
            return False
        
        try:
            product = notification_data['product']
            price_record = notification_data['price_record']
            alert_data = notification_data['alert_data']
            
            # Prepare email content
            subject = self._generate_email_subject(product, alert_data)
            html_content = self._generate_email_html(notification_data)
            text_content = self._generate_email_text(notification_data)
            
            # Send email
            success = await self.email_sender.send_price_alert(
                to_email=settings.email_username,  # Send to configured email
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                product=product,
                price_record=price_record
            )
            
            # Log notification
            await self._log_notification(
                notification_type="email",
                recipient=settings.email_username,
                subject=subject,
                message=text_content,
                status="sent" if success else "failed",
                product_id=product.id,
                alert_id=notification_data.get('alert', {}).get('id')
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def send_slack_alert(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send Slack alert notification
        
        Args:
            notification_data: Notification data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.slack_sender:
            logger.warning("Slack notifications not enabled")
            return False
        
        try:
            product = notification_data['product']
            price_record = notification_data['price_record']
            alert_data = notification_data['alert_data']
            
            # Generate Slack message
            message = self._generate_slack_message(notification_data)
            
            # Send Slack message
            success = await self.slack_sender.send_price_alert(
                message=message,
                product=product,
                price_record=price_record,
                alert_data=alert_data
            )
            
            # Log notification
            await self._log_notification(
                notification_type="slack",
                recipient="slack_channel",
                subject=f"Price Alert: {product.name}",
                message=message,
                status="sent" if success else "failed",
                product_id=product.id,
                alert_id=notification_data.get('alert', {}).get('id')
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    async def send_desktop_alert(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send desktop notification
        
        Args:
            notification_data: Notification data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.desktop_notifier:
            logger.warning("Desktop notifications not enabled")
            return False
        
        try:
            product = notification_data['product']
            price_record = notification_data['price_record']
            alert_data = notification_data['alert_data']
            
            # Generate desktop notification
            title = f"Price Alert: {product.name}"
            message = self._generate_desktop_message(notification_data)
            
            # Send desktop notification
            success = await self.desktop_notifier.send_notification(
                title=title,
                message=message,
                product=product,
                price_record=price_record
            )
            
            # Log notification
            await self._log_notification(
                notification_type="desktop",
                recipient="local_user",
                subject=title,
                message=message,
                status="sent" if success else "failed",
                product_id=product.id,
                alert_id=notification_data.get('alert', {}).get('id')
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send desktop alert: {e}")
            return False
    
    async def send_test_notification(
        self,
        notification_type: str,
        recipient: Optional[str] = None
    ) -> bool:
        """
        Send test notification to verify configuration
        
        Args:
            notification_type: Type of notification (email, slack, desktop)
            recipient: Optional recipient override
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create test notification data
            test_data = {
                'product': type('TestProduct', (), {
                    'id': 'test-product-id',
                    'name': 'Test Product',
                    'target_price': 99.99,
                    'amazon_url': 'https://amazon.com/test'
                })(),
                'price_record': type('TestPriceRecord', (), {
                    'price': 89.99,
                    'old_price': 109.99,
                    'discount_percentage': 18.18,
                    'savings_amount': 20.00,
                    'rating': 4.5,
                    'reviews_count': 1234,
                    'prime_eligible': True,
                    'checked_at': datetime.now(timezone.utc)
                })(),
                'alert_data': {
                    'type': 'test_alert',
                    'message': 'This is a test notification',
                    'details': {
                        'current_price': 89.99,
                        'target_price': 99.99,
                        'savings': 10.00
                    }
                }
            }
            
            if notification_type == "email":
                return await self.send_email_alert(test_data)
            elif notification_type == "slack":
                return await self.send_slack_alert(test_data)
            elif notification_type == "desktop":
                return await self.send_desktop_alert(test_data)
            else:
                logger.error(f"Unknown notification type: {notification_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return False
    
    async def send_bulk_notification(
        self,
        notification_type: str,
        recipients: List[str],
        subject: str,
        message: str
    ) -> Dict[str, bool]:
        """
        Send notification to multiple recipients
        
        Args:
            notification_type: Type of notification
            recipients: List of recipients
            subject: Notification subject
            message: Notification message
            
        Returns:
            Dictionary mapping recipients to success status
        """
        results = {}
        
        for recipient in recipients:
            try:
                if notification_type == "email" and self.email_sender:
                    success = await self.email_sender.send_simple_email(
                        to_email=recipient,
                        subject=subject,
                        text_content=message
                    )
                    results[recipient] = success
                else:
                    logger.warning(f"Bulk notification not supported for type: {notification_type}")
                    results[recipient] = False
                    
            except Exception as e:
                logger.error(f"Failed to send notification to {recipient}: {e}")
                results[recipient] = False
        
        return results
    
    def _generate_email_subject(self, product, alert_data) -> str:
        """Generate email subject line"""
        alert_type = alert_data['type']
        
        if alert_type == 'target_reached':
            return f"🎯 Target Price Reached: {product.name}"
        elif alert_type == 'deal_found':
            return f"🔥 Great Deal Found: {product.name}"
        elif alert_type == 'price_drop':
            return f"📉 Price Drop Alert: {product.name}"
        else:
            return f"💰 Price Alert: {product.name}"
    
    def _generate_email_html(self, notification_data) -> str:
        """Generate HTML email content"""
        product = notification_data['product']
        price_record = notification_data['price_record']
        alert_data = notification_data['alert_data']
        
        # This would typically use a template engine like Jinja2
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .price-info {{ background-color: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .product-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .current-price {{ font-size: 24px; color: #28a745; font-weight: bold; }}
                .old-price {{ text-decoration: line-through; color: #6c757d; }}
                .savings {{ color: #dc3545; font-weight: bold; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛒 Amazon Price Alert</h1>
                </div>
                <div class="content">
                    <div class="product-title">{product.name}</div>
                    <div class="price-info">
                        <div class="current-price">${price_record.price:.2f}</div>
        """
        
        if price_record.old_price:
            html += f'<div class="old-price">${price_record.old_price:.2f}</div>'
        
        if price_record.savings_amount:
            html += f'<div class="savings">Save ${price_record.savings_amount:.2f}</div>'
        
        html += f"""
                    </div>
                    <p><strong>Alert Type:</strong> {alert_data['type'].replace('_', ' ').title()}</p>
                    <p><strong>Message:</strong> {alert_data['message']}</p>
        """
        
        if hasattr(product, 'amazon_url') and product.amazon_url:
            html += f'<p><a href="{product.amazon_url}" class="button">View on Amazon</a></p>'
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_email_text(self, notification_data) -> str:
        """Generate plain text email content"""
        product = notification_data['product']
        price_record = notification_data['price_record']
        alert_data = notification_data['alert_data']
        
        text = f"Amazon Price Alert: {product.name}\n"
        text += f"{'=' * 50}\n\n"
        text += f"Current Price: ${price_record.price:.2f}\n"
        
        if price_record.old_price:
            text += f"Previous Price: ${price_record.old_price:.2f}\n"
        
        if price_record.savings_amount:
            text += f"Savings: ${price_record.savings_amount:.2f}\n"
        
        text += f"\nAlert: {alert_data['message']}\n"
        
        if hasattr(product, 'amazon_url') and product.amazon_url:
            text += f"\nView on Amazon: {product.amazon_url}\n"
        
        return text
    
    def _generate_slack_message(self, notification_data) -> str:
        """Generate Slack message"""
        product = notification_data['product']
        price_record = notification_data['price_record']
        alert_data = notification_data['alert_data']
        
        emoji = "🎯" if alert_data['type'] == 'target_reached' else "🔥" if alert_data['type'] == 'deal_found' else "📉"
        
        message = f"{emoji} *{product.name}*\n"
        message += f"💰 Current Price: *${price_record.price:.2f}*\n"
        
        if price_record.old_price:
            message += f"~~${price_record.old_price:.2f}~~ "
        
        if price_record.savings_amount:
            message += f"(Save ${price_record.savings_amount:.2f})\n"
        
        message += f"\n{alert_data['message']}"
        
        return message
    
    def _generate_desktop_message(self, notification_data) -> str:
        """Generate desktop notification message"""
        product = notification_data['product']
        price_record = notification_data['price_record']
        alert_data = notification_data['alert_data']
        
        message = f"${price_record.price:.2f}"
        
        if price_record.savings_amount:
            message += f" (Save ${price_record.savings_amount:.2f})"
        
        return message
    
    async def _log_notification(
        self,
        notification_type: str,
        recipient: str,
        subject: str,
        message: str,
        status: str,
        product_id: Optional[str] = None,
        alert_id: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Log notification to database
        
        Args:
            notification_type: Type of notification
            recipient: Notification recipient
            subject: Notification subject
            message: Notification message
            status: Status (sent, failed, pending)
            product_id: Related product ID
            alert_id: Related alert ID
            error_message: Error message if failed
        """
        try:
            with get_db_session() as session:
                log_entry = NotificationLog(
                    notification_type=notification_type,
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    status=status,
                    product_id=product_id,
                    alert_id=alert_id,
                    error_message=error_message,
                    created_at=datetime.now(timezone.utc),
                    sent_at=datetime.now(timezone.utc) if status == "sent" else None
                )
                
                session.add(log_entry)
                session.commit()
                
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            with get_db_session() as session:
                # Get counts by type and status
                total_notifications = session.query(NotificationLog).count()
                
                sent_notifications = session.query(NotificationLog).filter(
                    NotificationLog.status == "sent"
                ).count()
                
                failed_notifications = session.query(NotificationLog).filter(
                    NotificationLog.status == "failed"
                ).count()
                
                # Get counts by type
                email_count = session.query(NotificationLog).filter(
                    NotificationLog.notification_type == "email"
                ).count()
                
                slack_count = session.query(NotificationLog).filter(
                    NotificationLog.notification_type == "slack"
                ).count()
                
                desktop_count = session.query(NotificationLog).filter(
                    NotificationLog.notification_type == "desktop"
                ).count()
                
                return {
                    'total': total_notifications,
                    'sent': sent_notifications,
                    'failed': failed_notifications,
                    'success_rate': (sent_notifications / total_notifications * 100) if total_notifications > 0 else 0,
                    'by_type': {
                        'email': email_count,
                        'slack': slack_count,
                        'desktop': desktop_count
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get notification stats: {e}")
            return {}
    
    def get_available_channels(self) -> List[str]:
        """Get list of available notification channels"""
        channels = []
        
        if self.email_sender:
            channels.append('email')
        
        if self.slack_sender:
            channels.append('slack')
        
        if self.desktop_notifier:
            channels.append('desktop')
        
        return channels
