"""
Comprehensive tests for notification system functionality
Tests email, Slack, desktop notifications, and notification management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import smtplib
import requests

from amazontracker.notifications.manager import NotificationManager
from amazontracker.notifications.email_sender import EmailSender
from amazontracker.notifications.slack_sender import SlackSender
from amazontracker.notifications.desktop_notifier import DesktopNotifier


class TestNotificationManager:
    """Test notification manager coordination"""
    
    def test_manager_initialization(self, test_settings):
        """Test notification manager initializes correctly"""
        with patch('amazontracker.notifications.manager.settings', test_settings):
            manager = NotificationManager()
            
            assert manager.email_sender is not None
            assert manager.slack_sender is not None
            assert manager.desktop_notifier is not None
    
    def test_send_price_alert_all_channels(self, test_settings):
        """Test sending price alert to all enabled channels"""
        test_settings.email_enabled = True
        test_settings.slack_enabled = True
        test_settings.desktop_notifications_enabled = True
        
        with patch('amazontracker.notifications.manager.settings', test_settings):
            manager = NotificationManager()
            
            # Mock all senders
            manager.email_sender = Mock()
            manager.slack_sender = Mock()
            manager.desktop_notifier = Mock()
            
            manager.email_sender.send_price_alert.return_value = {"success": True}
            manager.slack_sender.send_price_alert.return_value = {"success": True}
            manager.desktop_notifier.send_price_alert.return_value = {"success": True}
            
            product_data = {
                "name": "iPhone 15",
                "current_price": 899.99,
                "target_price": 999.99,
                "savings": 100.00
            }
            
            result = manager.send_price_alert(product_data)
            
            assert result["success"] is True
            assert len(result["channels_sent"]) == 3
            manager.email_sender.send_price_alert.assert_called_once()
            manager.slack_sender.send_price_alert.assert_called_once()
            manager.desktop_notifier.send_price_alert.assert_called_once()
    
    def test_send_price_alert_selective_channels(self, test_settings):
        """Test sending alerts only to enabled channels"""
        test_settings.email_enabled = True
        test_settings.slack_enabled = False
        test_settings.desktop_notifications_enabled = True
        
        with patch('amazontracker.notifications.manager.settings', test_settings):
            manager = NotificationManager()
            
            manager.email_sender = Mock()
            manager.slack_sender = Mock()
            manager.desktop_notifier = Mock()
            
            manager.email_sender.send_price_alert.return_value = {"success": True}
            manager.desktop_notifier.send_price_alert.return_value = {"success": True}
            
            product_data = {"name": "iPhone 15", "current_price": 899.99}
            
            result = manager.send_price_alert(product_data)
            
            assert result["success"] is True
            assert len(result["channels_sent"]) == 2
            manager.email_sender.send_price_alert.assert_called_once()
            manager.slack_sender.send_price_alert.assert_not_called()
            manager.desktop_notifier.send_price_alert.assert_called_once()
    
    def test_send_deal_alert(self, test_settings):
        """Test sending deal alerts"""
        with patch('amazontracker.notifications.manager.settings', test_settings):
            manager = NotificationManager()
            
            manager.email_sender = Mock()
            manager.slack_sender = Mock()
            manager.desktop_notifier = Mock()
            
            manager.email_sender.send_deal_alert.return_value = {"success": True}
            manager.slack_sender.send_deal_alert.return_value = {"success": True}
            manager.desktop_notifier.send_deal_alert.return_value = {"success": True}
            
            deal_data = {
                "name": "iPhone 15",
                "current_price": 799.99,
                "original_price": 999.99,
                "discount_percentage": 20.0
            }
            
            result = manager.send_deal_alert(deal_data)
            
            assert result["success"] is True
    
    def test_notification_error_handling(self, test_settings):
        """Test handling of notification errors"""
        with patch('amazontracker.notifications.manager.settings', test_settings):
            manager = NotificationManager()
            
            manager.email_sender = Mock()
            manager.email_sender.send_price_alert.side_effect = Exception("Email failed")
            
            product_data = {"name": "iPhone 15", "current_price": 899.99}
            
            result = manager.send_price_alert(product_data)
            
            # Should handle errors gracefully
            assert "errors" in result
            assert len(result["errors"]) > 0
    
    def test_get_notification_stats(self, test_settings):
        """Test getting notification statistics"""
        with patch('amazontracker.notifications.manager.settings', test_settings):
            manager = NotificationManager()
            
            with patch('amazontracker.notifications.manager.get_db_session') as mock_session:
                mock_session_context = Mock()
                mock_session.return_value.__enter__.return_value = mock_session_context
                mock_session_context.query.return_value.count.return_value = 50
                
                stats = manager.get_notification_stats()
                
                assert "sent" in stats
                assert "success_rate" in stats
                assert "by_channel" in stats
    
    def test_send_test_notification(self, test_settings):
        """Test sending test notifications"""
        with patch('amazontracker.notifications.manager.settings', test_settings):
            manager = NotificationManager()
            
            manager.desktop_notifier = Mock()
            manager.desktop_notifier.send_test_notification.return_value = {"success": True}
            
            result = manager.send_test_notification("desktop")
            
            assert result["success"] is True
            manager.desktop_notifier.send_test_notification.assert_called_once()


class TestEmailSender:
    """Test email notification functionality"""
    
    def test_email_sender_initialization(self, test_settings):
        """Test email sender initializes correctly"""
        test_settings.email_enabled = True
        test_settings.email_username = "test@example.com"
        test_settings.email_password = "password"
        
        with patch('amazontracker.notifications.email_sender.settings', test_settings):
            sender = EmailSender()
            
            assert sender.smtp_server == test_settings.smtp_server
            assert sender.smtp_port == test_settings.smtp_port
            assert sender.username == test_settings.email_username
    
    def test_send_price_alert_email_success(self, test_settings):
        """Test successful price alert email sending"""
        test_settings.email_enabled = True
        test_settings.email_username = "test@example.com"
        test_settings.email_password = "password"
        
        with patch('amazontracker.notifications.email_sender.settings', test_settings):
            sender = EmailSender()
            
            with patch('smtplib.SMTP') as mock_smtp:
                mock_server = Mock()
                mock_smtp.return_value.__enter__.return_value = mock_server
                
                product_data = {
                    "name": "iPhone 15",
                    "current_price": 899.99,
                    "target_price": 999.99,
                    "link": "https://amazon.com/product",
                    "savings": 100.00
                }
                
                result = sender.send_price_alert(product_data, "test@example.com")
                
                assert result["success"] is True
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once()
                mock_server.send_message.assert_called_once()
    
    def test_send_price_alert_email_failure(self, test_settings):
        """Test price alert email sending failure"""
        test_settings.email_enabled = True
        test_settings.email_username = "test@example.com"
        test_settings.email_password = "wrong_password"
        
        with patch('amazontracker.notifications.email_sender.settings', test_settings):
            sender = EmailSender()
            
            with patch('smtplib.SMTP') as mock_smtp:
                mock_server = Mock()
                mock_smtp.return_value.__enter__.return_value = mock_server
                mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
                
                product_data = {"name": "iPhone 15", "current_price": 899.99}
                
                result = sender.send_price_alert(product_data, "test@example.com")
                
                assert result["success"] is False
                assert "error" in result
    
    def test_send_deal_alert_email(self, test_settings):
        """Test sending deal alert email"""
        test_settings.email_enabled = True
        test_settings.email_username = "test@example.com"
        test_settings.email_password = "password"
        
        with patch('amazontracker.notifications.email_sender.settings', test_settings):
            sender = EmailSender()
            
            with patch('smtplib.SMTP') as mock_smtp:
                mock_server = Mock()
                mock_smtp.return_value.__enter__.return_value = mock_server
                
                deal_data = {
                    "name": "iPhone 15",
                    "current_price": 799.99,
                    "original_price": 999.99,
                    "discount_percentage": 20.0,
                    "link": "https://amazon.com/product"
                }
                
                result = sender.send_deal_alert(deal_data, "test@example.com")
                
                assert result["success"] is True
                mock_server.send_message.assert_called_once()
    
    def test_email_template_generation(self, test_settings):
        """Test email template generation"""
        with patch('amazontracker.notifications.email_sender.settings', test_settings):
            sender = EmailSender()
            
            product_data = {
                "name": "iPhone 15 Pro",
                "current_price": 899.99,
                "target_price": 999.99,
                "savings": 100.00,
                "link": "https://amazon.com/product"
            }
            
            subject, body = sender.generate_price_alert_email(product_data)
            
            assert "Price Alert" in subject
            assert "iPhone 15 Pro" in subject
            assert "iPhone 15 Pro" in body
            assert "$899.99" in body
            assert "$100.00" in body
    
    def test_email_disabled_handling(self, test_settings):
        """Test handling when email is disabled"""
        test_settings.email_enabled = False
        
        with patch('amazontracker.notifications.email_sender.settings', test_settings):
            sender = EmailSender()
            
            product_data = {"name": "iPhone 15", "current_price": 899.99}
            
            result = sender.send_price_alert(product_data, "test@example.com")
            
            assert result["success"] is False
            assert "disabled" in result["error"].lower()


class TestSlackSender:
    """Test Slack notification functionality"""
    
    def test_slack_sender_initialization(self, test_settings):
        """Test Slack sender initializes correctly"""
        test_settings.slack_enabled = True
        test_settings.slack_webhook_url = "https://hooks.slack.com/test"
        
        with patch('amazontracker.notifications.slack_sender.settings', test_settings):
            sender = SlackSender()
            
            assert sender.webhook_url == test_settings.slack_webhook_url
            assert sender.channel == test_settings.slack_channel
    
    def test_send_price_alert_slack_success(self, test_settings):
        """Test successful Slack price alert sending"""
        test_settings.slack_enabled = True
        test_settings.slack_webhook_url = "https://hooks.slack.com/test"
        
        with patch('amazontracker.notifications.slack_sender.settings', test_settings):
            sender = SlackSender()
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response
                
                product_data = {
                    "name": "iPhone 15",
                    "current_price": 899.99,
                    "target_price": 999.99,
                    "link": "https://amazon.com/product",
                    "savings": 100.00
                }
                
                result = sender.send_price_alert(product_data)
                
                assert result["success"] is True
                mock_post.assert_called_once()
                
                # Verify payload
                call_args = mock_post.call_args
                payload = call_args[1]["json"]
                assert "iPhone 15" in payload["text"]
                assert "$899.99" in payload["text"]
    
    def test_send_price_alert_slack_failure(self, test_settings):
        """Test Slack price alert sending failure"""
        test_settings.slack_enabled = True
        test_settings.slack_webhook_url = "https://hooks.slack.com/invalid"
        
        with patch('amazontracker.notifications.slack_sender.settings', test_settings):
            sender = SlackSender()
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 404
                mock_response.text = "Not Found"
                mock_post.return_value = mock_response
                
                product_data = {"name": "iPhone 15", "current_price": 899.99}
                
                result = sender.send_price_alert(product_data)
                
                assert result["success"] is False
                assert "error" in result
    
    def test_send_deal_alert_slack(self, test_settings):
        """Test sending deal alert to Slack"""
        test_settings.slack_enabled = True
        test_settings.slack_webhook_url = "https://hooks.slack.com/test"
        
        with patch('amazontracker.notifications.slack_sender.settings', test_settings):
            sender = SlackSender()
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response
                
                deal_data = {
                    "name": "iPhone 15",
                    "current_price": 799.99,
                    "original_price": 999.99,
                    "discount_percentage": 20.0
                }
                
                result = sender.send_deal_alert(deal_data)
                
                assert result["success"] is True
                
                # Verify deal-specific content
                call_args = mock_post.call_args
                payload = call_args[1]["json"]
                assert "20%" in payload["text"]
    
    def test_slack_message_formatting(self, test_settings):
        """Test Slack message formatting"""
        with patch('amazontracker.notifications.slack_sender.settings', test_settings):
            sender = SlackSender()
            
            product_data = {
                "name": "iPhone 15 Pro Max",
                "current_price": 1099.99,
                "target_price": 1199.99,
                "savings": 100.00,
                "link": "https://amazon.com/product"
            }
            
            message = sender.format_price_alert_message(product_data)
            
            assert "🔔" in message  # Alert emoji
            assert "iPhone 15 Pro Max" in message
            assert "$1,099.99" in message
            assert "$100.00" in message
            assert "https://amazon.com/product" in message
    
    def test_slack_disabled_handling(self, test_settings):
        """Test handling when Slack is disabled"""
        test_settings.slack_enabled = False
        
        with patch('amazontracker.notifications.slack_sender.settings', test_settings):
            sender = SlackSender()
            
            product_data = {"name": "iPhone 15", "current_price": 899.99}
            
            result = sender.send_price_alert(product_data)
            
            assert result["success"] is False
            assert "disabled" in result["error"].lower()
    
    def test_slack_network_error_handling(self, test_settings):
        """Test handling of Slack network errors"""
        test_settings.slack_enabled = True
        test_settings.slack_webhook_url = "https://hooks.slack.com/test"
        
        with patch('amazontracker.notifications.slack_sender.settings', test_settings):
            sender = SlackSender()
            
            with patch('requests.post') as mock_post:
                mock_post.side_effect = requests.ConnectionError("Network error")
                
                product_data = {"name": "iPhone 15", "current_price": 899.99}
                
                result = sender.send_price_alert(product_data)
                
                assert result["success"] is False
                assert "error" in result


class TestDesktopNotifier:
    """Test desktop notification functionality"""
    
    def test_desktop_notifier_initialization(self, test_settings):
        """Test desktop notifier initializes correctly"""
        with patch('amazontracker.notifications.desktop_notifier.settings', test_settings):
            notifier = DesktopNotifier()
            
            assert notifier.enabled == test_settings.desktop_notifications_enabled
    
    def test_send_price_alert_desktop_success(self, test_settings):
        """Test successful desktop price alert"""
        test_settings.desktop_notifications_enabled = True
        
        with patch('amazontracker.notifications.desktop_notifier.settings', test_settings):
            notifier = DesktopNotifier()
            
            with patch('plyer.notification.notify') as mock_notify:
                product_data = {
                    "name": "iPhone 15",
                    "current_price": 899.99,
                    "target_price": 999.99,
                    "savings": 100.00
                }
                
                result = notifier.send_price_alert(product_data)
                
                assert result["success"] is True
                mock_notify.assert_called_once()
                
                # Verify notification content
                call_args = mock_notify.call_args
                kwargs = call_args[1]
                assert "Price Alert" in kwargs["title"]
                assert "iPhone 15" in kwargs["message"]
                assert "$899.99" in kwargs["message"]
    
    def test_send_deal_alert_desktop(self, test_settings):
        """Test desktop deal alert"""
        test_settings.desktop_notifications_enabled = True
        
        with patch('amazontracker.notifications.desktop_notifier.settings', test_settings):
            notifier = DesktopNotifier()
            
            with patch('plyer.notification.notify') as mock_notify:
                deal_data = {
                    "name": "iPhone 15",
                    "current_price": 799.99,
                    "original_price": 999.99,
                    "discount_percentage": 20.0
                }
                
                result = notifier.send_deal_alert(deal_data)
                
                assert result["success"] is True
                mock_notify.assert_called_once()
                
                # Verify deal-specific content
                call_args = mock_notify.call_args
                kwargs = call_args[1]
                assert "Deal Alert" in kwargs["title"]
                assert "20%" in kwargs["message"]
    
    def test_desktop_notification_error_handling(self, test_settings):
        """Test desktop notification error handling"""
        test_settings.desktop_notifications_enabled = True
        
        with patch('amazontracker.notifications.desktop_notifier.settings', test_settings):
            notifier = DesktopNotifier()
            
            with patch('plyer.notification.notify') as mock_notify:
                mock_notify.side_effect = Exception("Notification system error")
                
                product_data = {"name": "iPhone 15", "current_price": 899.99}
                
                result = notifier.send_price_alert(product_data)
                
                assert result["success"] is False
                assert "error" in result
    
    def test_desktop_disabled_handling(self, test_settings):
        """Test handling when desktop notifications are disabled"""
        test_settings.desktop_notifications_enabled = False
        
        with patch('amazontracker.notifications.desktop_notifier.settings', test_settings):
            notifier = DesktopNotifier()
            
            product_data = {"name": "iPhone 15", "current_price": 899.99}
            
            result = notifier.send_price_alert(product_data)
            
            assert result["success"] is False
            assert "disabled" in result["error"].lower()
    
    def test_send_test_notification_desktop(self, test_settings):
        """Test sending test desktop notification"""
        test_settings.desktop_notifications_enabled = True
        
        with patch('amazontracker.notifications.desktop_notifier.settings', test_settings):
            notifier = DesktopNotifier()
            
            with patch('plyer.notification.notify') as mock_notify:
                result = notifier.send_test_notification()
                
                assert result["success"] is True
                mock_notify.assert_called_once()
                
                # Verify test notification content
                call_args = mock_notify.call_args
                kwargs = call_args[1]
                assert "Test" in kwargs["title"]
    
    def test_notification_message_formatting(self, test_settings):
        """Test notification message formatting"""
        with patch('amazontracker.notifications.desktop_notifier.settings', test_settings):
            notifier = DesktopNotifier()
            
            product_data = {
                "name": "Very Long Product Name That Should Be Truncated",
                "current_price": 1234.56,
                "target_price": 1299.99,
                "savings": 65.43
            }
            
            title, message = notifier.format_price_alert_notification(product_data)
            
            assert len(title) <= 64  # Title should be truncated if too long
            assert "$1,234.56" in message
            assert "$65.43" in message
    
    def test_notification_timeout_configuration(self, test_settings):
        """Test notification timeout configuration"""
        test_settings.desktop_notifications_enabled = True
        
        with patch('amazontracker.notifications.desktop_notifier.settings', test_settings):
            notifier = DesktopNotifier()
            notifier.timeout = 10  # 10 seconds
            
            with patch('plyer.notification.notify') as mock_notify:
                product_data = {"name": "iPhone 15", "current_price": 899.99}
                
                notifier.send_price_alert(product_data)
                
                call_args = mock_notify.call_args
                kwargs = call_args[1]
                assert kwargs["timeout"] == 10
