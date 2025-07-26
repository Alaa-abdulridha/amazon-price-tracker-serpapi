"""
Slack notification sender for price alerts
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..utils.config import settings

logger = logging.getLogger(__name__)


class SlackSender:
    """
    Slack sender for price alerts and notifications
    """
    
    def __init__(self):
        """Initialize Slack sender with webhook configuration"""
        self.webhook_url = settings.slack_webhook_url
        self.channel = settings.slack_channel
        self.username = settings.slack_username or "Amazon Price Tracker"
        self.icon_emoji = settings.slack_icon_emoji or ":shopping_bags:"
        
        logger.info("Slack sender initialized")
    
    async def send_price_alert(
        self,
        message: str,
        product: Any,
        price_record: Any,
        alert_data: Dict[str, Any]
    ) -> bool:
        """
        Send price alert to Slack channel
        
        Args:
            message: Formatted message text
            product: Product object
            price_record: Price record object
            alert_data: Alert metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create rich Slack message with blocks
            blocks = self._create_price_alert_blocks(
                message, product, price_record, alert_data
            )
            
            payload = {
                "channel": self.channel,
                "username": self.username,
                "icon_emoji": self.icon_emoji,
                "blocks": blocks
            }
            
            # Add fallback text for notifications
            payload["text"] = f"Price Alert: {product.name} - ${price_record.price:.2f}"
            
            success = await self._send_slack_message(payload)
            
            if success:
                logger.info(f"Slack alert sent for product: {product.name}")
            else:
                logger.error(f"Failed to send Slack alert for product: {product.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending Slack price alert: {e}")
            return False
    
    async def send_simple_message(
        self,
        message: str,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send simple text message to Slack
        
        Args:
            message: Message text
            channel: Optional channel override
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "channel": channel or self.channel,
                "username": self.username,
                "icon_emoji": self.icon_emoji,
                "text": message
            }
            
            success = await self._send_slack_message(payload)
            
            if success:
                logger.info(f"Slack message sent: {message[:50]}...")
            else:
                logger.error("Failed to send Slack message")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False
    
    async def send_daily_summary(
        self,
        products_checked: int,
        deals_found: int,
        alerts_sent: int,
        top_deals: List[Dict[str, Any]],
        errors: List[str]
    ) -> bool:
        """
        Send daily summary to Slack
        
        Args:
            products_checked: Number of products checked
            deals_found: Number of deals found
            alerts_sent: Number of alerts sent
            top_deals: List of top deals
            errors: List of errors
            
        Returns:
            True if successful, False otherwise
        """
        try:
            blocks = self._create_summary_blocks(
                products_checked, deals_found, alerts_sent, top_deals, errors
            )
            
            payload = {
                "channel": self.channel,
                "username": self.username,
                "icon_emoji": ":bar_chart:",
                "blocks": blocks,
                "text": f"Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
            }
            
            success = await self._send_slack_message(payload)
            
            if success:
                logger.info("Daily summary sent to Slack")
            else:
                logger.error("Failed to send daily summary to Slack")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending daily summary to Slack: {e}")
            return False
    
    async def send_error_alert(
        self,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send error alert to Slack
        
        Args:
            error_type: Type of error
            error_message: Error message
            error_details: Additional error details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 Error Alert: {error_type}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Error Type:*\n{error_type}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error Message:*\n```{error_message}```"
                    }
                }
            ]
            
            if error_details:
                details_text = "\n".join([f"• *{k}:* {v}" for k, v in error_details.items()])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error Details:*\n{details_text}"
                    }
                })
            
            payload = {
                "channel": self.channel,
                "username": self.username,
                "icon_emoji": ":rotating_light:",
                "blocks": blocks,
                "text": f"Error Alert: {error_type}"
            }
            
            success = await self._send_slack_message(payload)
            
            if success:
                logger.info(f"Error alert sent to Slack: {error_type}")
            else:
                logger.error("Failed to send error alert to Slack")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending error alert to Slack: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Test Slack webhook connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_message = f"🧪 Test message from Amazon Price Tracker - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            success = await self.send_simple_message(test_message)
            
            if success:
                logger.info("Slack connection test successful")
            else:
                logger.error("Slack connection test failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Slack connection test error: {e}")
            return False
    
    async def _send_slack_message(self, payload: Dict[str, Any]) -> bool:
        """
        Send message to Slack webhook
        
        Args:
            payload: Slack message payload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Slack API error {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False
    
    def _create_price_alert_blocks(
        self,
        message: str,
        product: Any,
        price_record: Any,
        alert_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create rich blocks for price alert"""
        # Determine alert emoji and color
        alert_type = alert_data.get('type', '')
        if alert_type == 'target_reached':
            emoji = "🎯"
            color = "#28a745"  # Green
        elif alert_type == 'deal_found':
            emoji = "🔥"
            color = "#fd7e14"  # Orange
        elif alert_type == 'price_drop':
            emoji = "📉"
            color = "#17a2b8"  # Blue
        else:
            emoji = "💰"
            color = "#6c757d"  # Gray
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Price Alert: {product.name[:50]}{'...' if len(product.name) > 50 else ''}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Price:*\n${price_record.price:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Alert Type:*\n{alert_data.get('type', 'Unknown').replace('_', ' ').title()}"
                    }
                ]
            }
        ]
        
        # Add additional price info if available
        additional_fields = []
        
        if hasattr(price_record, 'old_price') and price_record.old_price:
            additional_fields.append({
                "type": "mrkdwn",
                "text": f"*Previous Price:*\n~${price_record.old_price:.2f}~"
            })
        
        if hasattr(price_record, 'savings_amount') and price_record.savings_amount:
            additional_fields.append({
                "type": "mrkdwn",
                "text": f"*Savings:*\n${price_record.savings_amount:.2f}"
            })
        
        if hasattr(product, 'target_price') and product.target_price:
            additional_fields.append({
                "type": "mrkdwn",
                "text": f"*Target Price:*\n${product.target_price:.2f}"
            })
        
        if hasattr(price_record, 'rating') and price_record.rating:
            additional_fields.append({
                "type": "mrkdwn",
                "text": f"*Rating:*\n{price_record.rating}⭐"
            })
        
        # Add additional fields in pairs
        if additional_fields:
            for i in range(0, len(additional_fields), 2):
                fields_pair = additional_fields[i:i+2]
                blocks.append({
                    "type": "section",
                    "fields": fields_pair
                })
        
        # Add message text
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Alert:* {alert_data.get('message', message)}"
            }
        })
        
        # Add action button if Amazon URL available
        if hasattr(product, 'amazon_url') and product.amazon_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View on Amazon"
                        },
                        "url": product.amazon_url,
                        "style": "primary"
                    }
                ]
            })
        
        return blocks
    
    def _create_summary_blocks(
        self,
        products_checked: int,
        deals_found: int,
        alerts_sent: int,
        top_deals: List[Dict[str, Any]],
        errors: List[str]
    ) -> List[Dict[str, Any]]:
        """Create blocks for daily summary"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Products Checked:*\n{products_checked}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Deals Found:*\n{deals_found}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Alerts Sent:*\n{alerts_sent}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Success Rate:*\n{(deals_found/products_checked*100):.1f}%" if products_checked > 0 else "*Success Rate:*\n0%"
                    }
                ]
            }
        ]
        
        # Add top deals section
        if top_deals:
            blocks.append({
                "type": "divider"
            })
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔥 Top Deals Found:*"
                }
            })
            
            for i, deal in enumerate(top_deals[:3], 1):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{i}. *{deal.get('name', 'Unknown Product')[:40]}{'...' if len(deal.get('name', '')) > 40 else ''}*\n💰 ${deal.get('price', 0):.2f} (Save ${deal.get('savings', 0):.2f})"
                    }
                })
        
        # Add errors section
        if errors:
            blocks.append({
                "type": "divider"
            })
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ Errors Encountered ({len(errors)}):*"
                }
            })
            
            error_text = "\n".join([f"• {error[:100]}{'...' if len(error) > 100 else ''}" for error in errors[:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{error_text}```"
                }
            })
        
        return blocks
