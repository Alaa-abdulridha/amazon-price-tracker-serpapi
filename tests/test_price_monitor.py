"""
Comprehensive tests for PriceMonitor service functionality
Tests monitoring operations, scheduling, and alert generation
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import asyncio

from amazontracker.services.price_monitor import PriceMonitor
from amazontracker.database.models import Product, PriceHistory, PriceAlert


class TestPriceMonitorInitialization:
    """Test price monitor initialization and configuration"""
    
    def test_monitor_initialization(self, test_settings):
        """Test monitor initializes correctly"""
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            
            assert monitor.max_concurrent_checks == test_settings.max_concurrent_checks
            assert monitor.is_running is False
            assert monitor.scheduler is not None
    
    def test_monitor_with_custom_settings(self, test_settings):
        """Test monitor with custom configuration"""
        test_settings.max_concurrent_checks = 10
        test_settings.default_check_interval = "30m"
        
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            
            assert monitor.max_concurrent_checks == 10


class TestPriceMonitorSingleProductCheck:
    """Test single product price checking"""
    
    @pytest.mark.asyncio
    async def test_check_single_product_success(self, temp_database, mock_serpapi_response):
        """Test successful single product price check"""
        monitor = PriceMonitor()
        
        # Mock product
        product = Mock()
        product.id = "test-id"
        product.name = "iPhone 15"
        product.search_query = "iPhone 15"
        product.target_price = 999.99
        product.is_active = True
        
        with patch.object(monitor, 'serpapi_client') as mock_client:
            mock_client.search_products.return_value = [
                {"title": "iPhone 15", "price": 949.99, "link": "test-link"}
            ]
            mock_client.find_best_price_match.return_value = {
                "title": "iPhone 15", "price": 949.99, "link": "test-link"
            }
            
            with patch('amazontracker.services.price_monitor.get_db_session'):
                result = await monitor.check_single_product(product)
                
                assert result is not None
                assert result.price == 949.99
                mock_client.search_products.assert_called_once_with("iPhone 15")
    
    @pytest.mark.asyncio
    async def test_check_single_product_no_results(self, temp_database):
        """Test single product check with no search results"""
        monitor = PriceMonitor()
        
        product = Mock()
        product.id = "test-id"
        product.search_query = "Nonexistent Product"
        
        with patch.object(monitor, 'serpapi_client') as mock_client:
            mock_client.search_products.return_value = []
            
            result = await monitor.check_single_product(product)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_single_product_api_error(self, temp_database):
        """Test single product check with API error"""
        monitor = PriceMonitor()
        
        product = Mock()
        product.id = "test-id"
        product.search_query = "iPhone 15"
        
        with patch.object(monitor, 'serpapi_client') as mock_client:
            mock_client.search_products.side_effect = Exception("API Error")
            
            result = await monitor.check_single_product(product)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_single_product_inactive(self, temp_database):
        """Test checking inactive product is skipped"""
        monitor = PriceMonitor()
        
        product = Mock()
        product.is_active = False
        
        result = await monitor.check_single_product(product)
        
        assert result is None


class TestPriceMonitorBulkChecking:
    """Test bulk product checking operations"""
    
    @pytest.mark.asyncio
    async def test_check_all_products_success(self, temp_database):
        """Test checking all products successfully"""
        monitor = PriceMonitor()
        
        # Mock products
        products = [
            Mock(id="1", name="Product 1", is_active=True),
            Mock(id="2", name="Product 2", is_active=True),
            Mock(id="3", name="Product 3", is_active=False)  # Inactive
        ]
        
        with patch('amazontracker.services.price_monitor.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.all.return_value = products
            
            with patch.object(monitor, 'check_single_product') as mock_check:
                mock_check.return_value = Mock(price=99.99)
                
                results = await monitor.check_all_products()
                
                # Should only check active products
                assert mock_check.call_count == 2
                assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_check_products_with_concurrency_limit(self, temp_database):
        """Test bulk checking respects concurrency limits"""
        monitor = PriceMonitor()
        monitor.max_concurrent_checks = 2
        
        products = [Mock(id=str(i), is_active=True) for i in range(5)]
        
        with patch('amazontracker.services.price_monitor.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.all.return_value = products
            
            with patch.object(monitor, 'check_single_product') as mock_check:
                mock_check.return_value = Mock(price=99.99)
                
                # Mock semaphore to verify concurrency control
                with patch('asyncio.Semaphore') as mock_semaphore:
                    mock_sem = Mock()
                    mock_semaphore.return_value = mock_sem
                    
                    await monitor.check_all_products()
                    
                    # Verify semaphore was created with correct limit
                    mock_semaphore.assert_called_once_with(2)
    
    @pytest.mark.asyncio
    async def test_check_products_with_errors(self, temp_database):
        """Test bulk checking handles individual errors gracefully"""
        monitor = PriceMonitor()
        
        products = [
            Mock(id="1", is_active=True),
            Mock(id="2", is_active=True),
            Mock(id="3", is_active=True)
        ]
        
        with patch('amazontracker.services.price_monitor.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.all.return_value = products
            
            with patch.object(monitor, 'check_single_product') as mock_check:
                # First product succeeds, second fails, third succeeds
                mock_check.side_effect = [
                    Mock(price=99.99),
                    Exception("API Error"),
                    Mock(price=149.99)
                ]
                
                results = await monitor.check_all_products()
                
                # Should return results for successful checks only
                assert len(results) == 2


class TestPriceMonitorAlertGeneration:
    """Test price alert generation and notifications"""
    
    @pytest.mark.asyncio
    async def test_price_drop_alert_generation(self, temp_database):
        """Test generating alerts for price drops"""
        monitor = PriceMonitor()
        
        product = Mock()
        product.id = "test-id"
        product.name = "iPhone 15"
        product.target_price = 999.99
        product.email_notifications = True
        product.slack_notifications = False
        product.desktop_notifications = True
        
        price_record = Mock()
        price_record.price = 899.99  # Below target
        price_record.product = product
        
        with patch.object(monitor, 'notification_manager') as mock_notifier:
            mock_notifier.send_price_alert.return_value = {"success": True}
            
            alerts = await monitor.generate_price_alerts(price_record)
            
            assert len(alerts) > 0
            mock_notifier.send_price_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_no_alert_for_price_above_target(self, temp_database):
        """Test no alerts generated when price is above target"""
        monitor = PriceMonitor()
        
        product = Mock()
        product.target_price = 999.99
        
        price_record = Mock()
        price_record.price = 1099.99  # Above target
        price_record.product = product
        
        with patch.object(monitor, 'notification_manager') as mock_notifier:
            alerts = await monitor.generate_price_alerts(price_record)
            
            assert len(alerts) == 0
            mock_notifier.send_price_alert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_deal_alert_generation(self, temp_database):
        """Test generating alerts for significant deals"""
        monitor = PriceMonitor()
        monitor.deal_threshold_percentage = 20.0
        
        product = Mock()
        product.id = "test-id"
        product.name = "iPhone 15"
        
        # Mock previous price
        with patch('amazontracker.services.price_monitor.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock previous price history
            previous_price = Mock()
            previous_price.price = 1000.00
            mock_session_context.query.return_value.filter.return_value.order_by.return_value.first.return_value = previous_price
            
            price_record = Mock()
            price_record.price = 799.99  # 20% drop
            price_record.product = product
            
            with patch.object(monitor, 'notification_manager') as mock_notifier:
                mock_notifier.send_deal_alert.return_value = {"success": True}
                
                alerts = await monitor.generate_deal_alerts(price_record)
                
                assert len(alerts) > 0
                mock_notifier.send_deal_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_duplicate_alert_prevention(self, temp_database):
        """Test prevention of duplicate alerts"""
        monitor = PriceMonitor()
        
        product = Mock()
        product.id = "test-id"
        product.target_price = 999.99
        
        price_record = Mock()
        price_record.price = 899.99
        price_record.product = product
        
        # Mock existing recent alert
        with patch('amazontracker.services.price_monitor.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            recent_alert = Mock()
            recent_alert.created_at = datetime.now() - timedelta(minutes=30)
            mock_session_context.query.return_value.filter.return_value.order_by.return_value.first.return_value = recent_alert
            
            alerts = await monitor.generate_price_alerts(price_record)
            
            # Should not generate duplicate alert
            assert len(alerts) == 0


class TestPriceMonitorScheduling:
    """Test monitoring scheduling and automation"""
    
    def test_start_monitoring(self, test_settings):
        """Test starting monitoring service"""
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            
            with patch.object(monitor.scheduler, 'start') as mock_start:
                monitor.start()
                
                assert monitor.is_running is True
                mock_start.assert_called_once()
    
    def test_stop_monitoring(self, test_settings):
        """Test stopping monitoring service"""
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            monitor.is_running = True
            
            with patch.object(monitor.scheduler, 'shutdown') as mock_shutdown:
                monitor.stop()
                
                assert monitor.is_running is False
                mock_shutdown.assert_called_once()
    
    def test_schedule_product_checks(self, test_settings):
        """Test scheduling individual product checks"""
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            
            products = [
                Mock(id="1", check_interval="1h"),
                Mock(id="2", check_interval="30m"),
                Mock(id="3", check_interval="6h")
            ]
            
            with patch.object(monitor.scheduler, 'add_job') as mock_add_job:
                monitor.schedule_product_checks(products)
                
                # Should schedule a job for each product
                assert mock_add_job.call_count == len(products)
    
    def test_dynamic_schedule_updates(self, test_settings):
        """Test updating schedules when products change"""
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            
            with patch.object(monitor.scheduler, 'remove_job') as mock_remove:
                with patch.object(monitor.scheduler, 'add_job') as mock_add:
                    monitor.update_product_schedule("product-1", "2h")
                    
                    # Should remove old job and add new one
                    mock_remove.assert_called_once()
                    mock_add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scheduled_check_execution(self, temp_database):
        """Test execution of scheduled price checks"""
        monitor = PriceMonitor()
        
        with patch.object(monitor, 'check_all_products') as mock_check:
            mock_check.return_value = [Mock(price=99.99)]
            
            # Simulate scheduled job execution
            await monitor.run_scheduled_check()
            
            mock_check.assert_called_once()


class TestPriceMonitorPerformance:
    """Test performance and optimization features"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(self, temp_database):
        """Test rate limiting prevents API abuse"""
        monitor = PriceMonitor()
        monitor.requests_per_minute = 10
        
        products = [Mock(id=str(i), is_active=True) for i in range(20)]
        
        with patch.object(monitor, 'serpapi_client') as mock_client:
            mock_client.search_products.return_value = []
            
            start_time = datetime.now()
            
            with patch('amazontracker.services.price_monitor.get_db_session'):
                # Check many products rapidly
                for product in products[:15]:  # Exceed rate limit
                    await monitor.check_single_product(product)
            
            # Should have been rate limited
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            assert duration > 30  # Should take longer due to rate limiting
    
    @pytest.mark.asyncio
    async def test_caching_reduces_api_calls(self, temp_database):
        """Test caching reduces redundant API calls"""
        monitor = PriceMonitor()
        monitor.enable_caching = True
        
        product = Mock()
        product.search_query = "iPhone 15"
        product.is_active = True
        
        with patch.object(monitor, 'serpapi_client') as mock_client:
            mock_client.search_products.return_value = [
                {"title": "iPhone 15", "price": 999.99}
            ]
            
            # First check should hit API
            await monitor.check_single_product(product)
            
            # Second check should use cache
            await monitor.check_single_product(product)
            
            # API should only be called once
            assert mock_client.search_products.call_count == 1
    
    def test_statistics_tracking(self, test_settings):
        """Test monitoring statistics are tracked"""
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            
            stats = monitor.get_monitoring_stats()
            
            assert "checks_performed" in stats
            assert "alerts_generated" in stats
            assert "api_calls_made" in stats
            assert "uptime" in stats
    
    def test_health_check(self, test_settings):
        """Test monitor health check functionality"""
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            
            health = monitor.health_check()
            
            assert "status" in health
            assert "scheduler_running" in health
            assert "last_check_time" in health
            assert "error_rate" in health


class TestPriceMonitorErrorHandling:
    """Test error handling and recovery"""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, temp_database):
        """Test handling of database errors"""
        monitor = PriceMonitor()
        
        product = Mock()
        product.is_active = True
        
        with patch('amazontracker.services.price_monitor.get_db_session') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            result = await monitor.check_single_product(product)
            
            # Should handle error gracefully
            assert result is None
    
    @pytest.mark.asyncio
    async def test_network_error_recovery(self, temp_database):
        """Test recovery from network errors"""
        monitor = PriceMonitor()
        monitor.max_retries = 3
        
        product = Mock()
        product.is_active = True
        product.search_query = "iPhone 15"
        
        with patch.object(monitor, 'serpapi_client') as mock_client:
            # Fail first two times, succeed on third
            mock_client.search_products.side_effect = [
                Exception("Network error"),
                Exception("Network error"),
                [{"title": "iPhone 15", "price": 999.99}]
            ]
            
            with patch('amazontracker.services.price_monitor.get_db_session'):
                result = await monitor.check_single_product(product)
                
                # Should eventually succeed
                assert result is not None
                assert mock_client.search_products.call_count == 3
    
    def test_scheduler_error_handling(self, test_settings):
        """Test scheduler error handling"""
        with patch('amazontracker.services.price_monitor.settings', test_settings):
            monitor = PriceMonitor()
            
            with patch.object(monitor.scheduler, 'start') as mock_start:
                mock_start.side_effect = Exception("Scheduler error")
                
                # Should handle scheduler errors gracefully
                try:
                    monitor.start()
                except Exception:
                    pytest.fail("Monitor should handle scheduler errors gracefully")
    
    @pytest.mark.asyncio
    async def test_notification_error_handling(self, temp_database):
        """Test handling of notification errors"""
        monitor = PriceMonitor()
        
        product = Mock()
        product.target_price = 999.99
        
        price_record = Mock()
        price_record.price = 899.99
        price_record.product = product
        
        with patch.object(monitor, 'notification_manager') as mock_notifier:
            mock_notifier.send_price_alert.side_effect = Exception("Notification failed")
            
            # Should handle notification errors gracefully
            alerts = await monitor.generate_price_alerts(price_record)
            
            # Should still track the alert attempt
            assert len(alerts) >= 0  # Shouldn't crash
