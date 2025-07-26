"""
Comprehensive tests for the PriceTracker core functionality
Tests all product management, price checking, and monitoring features
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid

from amazontracker.core.tracker import PriceTracker
from amazontracker.database.models import Product, PriceHistory


class TestPriceTrackerProductManagement:
    """Test product management functionality"""
    
    def test_add_product_with_valid_data(self, temp_database, sample_product_data):
        """Test adding a product with valid data"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            # Setup mock session
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            tracker = PriceTracker()
            
            # Test adding product
            result = tracker.add_product(**sample_product_data)
            
            # Verify product was created
            assert result is not None
            assert isinstance(result, Product)
            assert result.name == sample_product_data["name"]
            assert result.target_price == sample_product_data["target_price"]
            assert result.check_interval == sample_product_data["check_interval"]
            
            # Verify database operations
            mock_session_context.add.assert_called_once()
            mock_session_context.commit.assert_called_once()
    
    def test_add_product_with_invalid_price(self, temp_database):
        """Test adding product with invalid price raises error"""
        tracker = PriceTracker()
        
        with pytest.raises(ValueError):
            tracker.add_product(
                name="Test Product",
                search_query="test",
                target_price=-10.0  # Invalid negative price
            )
    
    def test_add_product_with_empty_name(self, temp_database):
        """Test adding product with empty name raises error"""
        tracker = PriceTracker()
        
        with pytest.raises(ValueError):
            tracker.add_product(
                name="",  # Empty name
                search_query="test",
                target_price=99.99
            )
    
    def test_get_products_active_only(self, temp_database):
        """Test getting only active products"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock query results
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [Mock(is_active=True), Mock(is_active=True)]
            
            tracker = PriceTracker()
            products = tracker.get_products(active_only=True)
            
            # Verify filter was applied
            mock_query.filter.assert_called_once()
            assert len(products) == 2
    
    def test_get_products_with_category_filter(self, temp_database):
        """Test getting products filtered by category"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [Mock(category="electronics")]
            
            tracker = PriceTracker()
            products = tracker.get_products(category="electronics")
            
            # Verify category filter was applied
            assert mock_query.filter.call_count >= 1
            assert len(products) == 1
    
    def test_get_product_by_id_existing(self, temp_database):
        """Test getting existing product by ID"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock existing product
            mock_product = Mock()
            mock_product.id = "test-id-123"
            mock_session_context.query.return_value.filter.return_value.first.return_value = mock_product
            
            tracker = PriceTracker()
            result = tracker.get_product("test-id-123")
            
            assert result == mock_product
    
    def test_get_product_by_id_nonexistent(self, temp_database):
        """Test getting non-existent product returns None"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = None
            
            tracker = PriceTracker()
            result = tracker.get_product("nonexistent-id")
            
            assert result is None
    
    def test_remove_product_existing(self, temp_database):
        """Test removing existing product"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock existing product
            mock_product = Mock()
            mock_product.is_active = True
            mock_session_context.query.return_value.filter.return_value.first.return_value = mock_product
            
            tracker = PriceTracker()
            result = tracker.remove_product("test-id")
            
            assert result is True
            assert mock_product.is_active is False
            mock_session_context.commit.assert_called_once()
    
    def test_remove_product_nonexistent(self, temp_database):
        """Test removing non-existent product returns False"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = None
            
            tracker = PriceTracker()
            result = tracker.remove_product("nonexistent-id")
            
            assert result is False


class TestPriceTrackerPriceChecking:
    """Test price checking and monitoring functionality"""
    
    def test_check_product_price_success(self, temp_database, mock_serpapi_response):
        """Test successful price check for a product"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock product
            mock_product = Mock()
            mock_product.id = "test-id"
            mock_product.name = "iPhone 15"
            mock_session_context.query.return_value.filter.return_value.first.return_value = mock_product
            
            # Mock price monitor
            mock_price_record = Mock()
            mock_price_record.price = 999.99
            
            tracker = PriceTracker()
            with patch.object(tracker, 'price_monitor') as mock_monitor:
                mock_monitor.check_single_product.return_value = mock_price_record
                
                result = tracker.check_product_price("test-id")
                
                assert result == mock_price_record
                mock_monitor.check_single_product.assert_called_once_with(mock_product)
    
    def test_check_product_price_product_not_found(self, temp_database):
        """Test price check for non-existent product"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = None
            
            tracker = PriceTracker()
            result = tracker.check_product_price("nonexistent-id")
            
            assert result is None
    
    def test_check_product_price_api_failure(self, temp_database):
        """Test price check with API failure"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_product = Mock()
            mock_session_context.query.return_value.filter.return_value.first.return_value = mock_product
            
            tracker = PriceTracker()
            with patch.object(tracker, 'price_monitor') as mock_monitor:
                mock_monitor.check_single_product.side_effect = Exception("API Error")
                
                result = tracker.check_product_price("test-id")
                
                assert result is None


class TestPriceTrackerPriceHistory:
    """Test price history functionality"""
    
    def test_get_price_history_with_data(self, temp_database, sample_price_history):
        """Test getting price history with existing data"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock price history records
            mock_records = [Mock(price=data["price"]) for data in sample_price_history]
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = mock_records
            
            tracker = PriceTracker()
            result = tracker.get_price_history("test-id", days=7)
            
            assert len(result) == len(sample_price_history)
    
    def test_get_price_history_no_data(self, temp_database):
        """Test getting price history with no data"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            tracker = PriceTracker()
            result = tracker.get_price_history("test-id", days=7)
            
            assert len(result) == 0


class TestPriceTrackerDealsAndAlerts:
    """Test deals detection and alert functionality"""
    
    def test_get_current_deals(self, temp_database):
        """Test getting current deals"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock deals
            mock_deals = [Mock(target_price=100, name="Deal 1"), Mock(target_price=200, name="Deal 2")]
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = mock_deals
            
            tracker = PriceTracker()
            deals = tracker.get_current_deals()
            
            assert len(deals) == 2
    
    def test_send_test_notification_success(self, temp_database, mock_notification_manager):
        """Test sending test notification successfully"""
        tracker = PriceTracker()
        tracker.notification_manager = mock_notification_manager
        
        result = tracker.send_test_notification("desktop")
        
        assert result["success"] is True
        mock_notification_manager.send_test_notification.assert_called_once_with("desktop")
    
    def test_send_test_notification_failure(self, temp_database):
        """Test sending test notification with failure"""
        mock_manager = Mock()
        mock_manager.send_test_notification.side_effect = Exception("Notification failed")
        
        tracker = PriceTracker()
        tracker.notification_manager = mock_manager
        
        result = tracker.send_test_notification("email")
        
        assert result["success"] is False
        assert "error" in result


class TestPriceTrackerSystemStats:
    """Test system statistics functionality"""
    
    def test_get_system_stats(self, temp_database):
        """Test getting system statistics"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock various queries for stats
            mock_session_context.query.return_value.count.return_value = 5
            mock_session_context.query.return_value.filter.return_value.count.return_value = 3
            
            tracker = PriceTracker()
            with patch.object(tracker, 'notification_manager') as mock_manager:
                mock_manager.get_notification_stats.return_value = {"sent": 10}
                
                stats = tracker.get_system_stats()
                
                assert "products" in stats
                assert "notifications" in stats
                assert "uptime" in stats
    
    def test_get_predictions_with_data(self, temp_database):
        """Test getting price predictions"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock prediction data
            mock_predictions = [Mock(predicted_price=95.99, confidence=0.8)]
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = mock_predictions
            
            tracker = PriceTracker()
            predictions = tracker.get_predictions("test-id")
            
            assert len(predictions) == 1
            assert predictions[0].predicted_price == 95.99


class TestPriceTrackerEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_add_product_database_error(self, temp_database):
        """Test adding product with database error"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.commit.side_effect = Exception("Database error")
            
            tracker = PriceTracker()
            
            with pytest.raises(Exception):
                tracker.add_product(
                    name="Test Product",
                    search_query="test",
                    target_price=99.99
                )
            
            mock_session_context.rollback.assert_called_once()
    
    def test_update_product_nonexistent(self, temp_database):
        """Test updating non-existent product"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = None
            
            tracker = PriceTracker()
            result = tracker.update_product("nonexistent-id", target_price=199.99)
            
            assert result is False
    
    def test_monitoring_lifecycle(self, temp_database):
        """Test monitoring start/stop lifecycle"""
        tracker = PriceTracker()
        
        # Test start monitoring
        tracker.start_monitoring()
        # Should not raise exception
        
        # Test stop monitoring
        tracker.stop_monitoring()
        # Should not raise exception
