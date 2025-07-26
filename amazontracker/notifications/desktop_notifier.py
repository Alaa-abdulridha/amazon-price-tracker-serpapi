"""
Desktop notification sender for price alerts
"""

import asyncio
import logging
import platform
import subprocess
from typing import Optional, Any
from datetime import datetime

from ..utils.config import settings

logger = logging.getLogger(__name__)


class DesktopNotifier:
    """
    Desktop notification sender for price alerts
    """
    
    def __init__(self):
        """Initialize desktop notifier"""
        self.system = platform.system().lower()
        self.enabled = settings.desktop_notifications_enabled
        
        logger.info(f"Desktop notifier initialized for {self.system}")
    
    async def send_notification(
        self,
        title: str,
        message: str,
        product: Any,
        price_record: Any,
        duration: int = 5000
    ) -> bool:
        """
        Send desktop notification
        
        Args:
            title: Notification title
            message: Notification message
            product: Product object
            price_record: Price record object
            duration: Notification duration in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Desktop notifications disabled")
            return False
        
        try:
            # Run notification in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self._send_system_notification,
                title,
                message,
                duration
            )
            
            if success:
                logger.info(f"Desktop notification sent: {title}")
            else:
                logger.error(f"Failed to send desktop notification: {title}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending desktop notification: {e}")
            return False
    
    async def send_price_alert_notification(
        self,
        product: Any,
        price_record: Any,
        alert_type: str
    ) -> bool:
        """
        Send price alert desktop notification with formatted content
        
        Args:
            product: Product object
            price_record: Price record object
            alert_type: Type of alert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate notification content
            title, message = self._generate_notification_content(
                product, price_record, alert_type
            )
            
            return await self.send_notification(
                title=title,
                message=message,
                product=product,
                price_record=price_record
            )
            
        except Exception as e:
            logger.error(f"Error sending price alert notification: {e}")
            return False
    
    async def send_simple_notification(
        self,
        title: str,
        message: str,
        duration: int = 3000
    ) -> bool:
        """
        Send simple desktop notification
        
        Args:
            title: Notification title
            message: Notification message
            duration: Duration in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self._send_system_notification,
                title,
                message,
                duration
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending simple notification: {e}")
            return False
    
    async def test_notification(self) -> bool:
        """
        Send test notification
        
        Returns:
            True if successful, False otherwise
        """
        try:
            title = "Amazon Price Tracker"
            message = f"Test notification - {datetime.now().strftime('%H:%M:%S')}"
            
            return await self.send_simple_notification(title, message)
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return False
    
    def _send_system_notification(
        self,
        title: str,
        message: str,
        duration: int = 5000
    ) -> bool:
        """
        Send system notification based on platform
        
        Args:
            title: Notification title
            message: Notification message
            duration: Duration in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "windows":
                return self._send_windows_notification(title, message, duration)
            elif self.system == "darwin":  # macOS
                return self._send_macos_notification(title, message, duration)
            elif self.system == "linux":
                return self._send_linux_notification(title, message, duration)
            else:
                logger.warning(f"Desktop notifications not supported on {self.system}")
                return False
                
        except Exception as e:
            logger.error(f"Error in _send_system_notification: {e}")
            return False
    
    def _send_windows_notification(
        self,
        title: str,
        message: str,
        duration: int
    ) -> bool:
        """Send notification on Windows using PowerShell"""
        try:
            # Use PowerShell to show Windows toast notification
            ps_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $notification = New-Object System.Windows.Forms.NotifyIcon
            $notification.Icon = [System.Drawing.SystemIcons]::Information
            $notification.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
            $notification.BalloonTipText = "{message}"
            $notification.BalloonTipTitle = "{title}"
            $notification.Visible = $true
            $notification.ShowBalloonTip({duration})
            Start-Sleep -Seconds {duration // 1000 + 1}
            $notification.Dispose()
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Windows notification error: {e}")
            return False
    
    def _send_macos_notification(
        self,
        title: str,
        message: str,
        duration: int
    ) -> bool:
        """Send notification on macOS using osascript"""
        try:
            # Use AppleScript to show macOS notification
            script = f'''
            display notification "{message}" with title "{title}"
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"macOS notification error: {e}")
            return False
    
    def _send_linux_notification(
        self,
        title: str,
        message: str,
        duration: int
    ) -> bool:
        """Send notification on Linux using notify-send"""
        try:
            # Use notify-send for Linux desktop notifications
            result = subprocess.run(
                [
                    "notify-send",
                    "-t", str(duration),
                    "-i", "dialog-information",
                    title,
                    message
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except FileNotFoundError:
            logger.error("notify-send not found. Install libnotify-bin package.")
            return False
        except Exception as e:
            logger.error(f"Linux notification error: {e}")
            return False
    
    def _generate_notification_content(
        self,
        product: Any,
        price_record: Any,
        alert_type: str
    ) -> tuple:
        """
        Generate notification title and message
        
        Args:
            product: Product object
            price_record: Price record object
            alert_type: Type of alert
            
        Returns:
            Tuple of (title, message)
        """
        # Generate emoji based on alert type
        if alert_type == 'target_reached':
            emoji = "🎯"
            title = f"{emoji} Target Price Reached!"
        elif alert_type == 'deal_found':
            emoji = "🔥"
            title = f"{emoji} Great Deal Found!"
        elif alert_type == 'price_drop':
            emoji = "📉"
            title = f"{emoji} Price Drop Alert!"
        else:
            emoji = "💰"
            title = f"{emoji} Price Alert!"
        
        # Truncate product name for notification
        product_name = product.name
        if len(product_name) > 40:
            product_name = product_name[:37] + "..."
        
        # Generate message
        message = f"{product_name}\n${price_record.price:.2f}"
        
        # Add savings info if available
        if hasattr(price_record, 'savings_amount') and price_record.savings_amount:
            message += f" (Save ${price_record.savings_amount:.2f})"
        
        return title, message
    
    def is_supported(self) -> bool:
        """
        Check if desktop notifications are supported on current platform
        
        Returns:
            True if supported, False otherwise
        """
        if not self.enabled:
            return False
        
        if self.system == "windows":
            # Windows should support PowerShell notifications
            return True
        elif self.system == "darwin":
            # macOS should support osascript
            return True
        elif self.system == "linux":
            # Check if notify-send is available
            try:
                result = subprocess.run(
                    ["which", "notify-send"],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except Exception:
                return False
        else:
            return False
    
    def get_system_info(self) -> dict:
        """
        Get system information for debugging
        
        Returns:
            Dictionary with system information
        """
        return {
            'system': self.system,
            'platform': platform.platform(),
            'enabled': self.enabled,
            'supported': self.is_supported()
        }
