"""
Comprehensive tests for the PriceTracker core functionality
Tests all product management, price checking, and monitoring features
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import uuid
from sqlalchemy import func

from amazontracker.core.tracker import PriceTracker
from amazontracker.database.models import Product, PriceHistory, PriceAlert


class TestPriceTracker:
    """Test cases for PriceTracker core functionality"""

    @pytest.fixture
    def tracker(self):
        """Create PriceTracker instance for testing"""
        return PriceTracker()

    @pytest.fixture
    def sample_product_data(self):
        """Sample product data for testing"""
        return {
            "name": "Test Product",
            "search_query": "test product amazon",
            "target_price": 99.99,
            "max_price": 150.0,
            "check_interval": "1h",
            "email_notifications": True,
            "slack_notifications": False,
            "desktop_notifications": True,
            "category": "Electronics",
            "tags": ["gadget", "tech"]
        }

    @pytest.fixture
    def mock_product(self):
        """Mock Product instance"""
        product = Mock(spec=Product)
        product.id = str(uuid.uuid4())
        product.name = "Test Product"
        product.search_query = "test product"
        product.target_price = 99.99
        product.is_active = True
        product.category = "Electronics"
        product.check_interval = "1h"
        return product

    @pytest.fixture
    def mock_price_history(self):
        """Mock PriceHistory instance"""
        history = Mock(spec=PriceHistory)
        history.id = str(uuid.uuid4())
        history.price = 89.99
        history.checked_at = datetime.now()
        history.is_deal = True
        history.discount_percentage = 10.0
        return history

    def test_add_product_success(self, tracker, sample_product_data):
        """Test successful product addition"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock the Product creation
            mock_product = Mock(spec=Product)
            mock_product.id = str(uuid.uuid4())
            mock_product.name = sample_product_data["name"]
            mock_product.target_price = sample_product_data["target_price"]
            mock_product.check_interval = sample_product_data["check_interval"]
            
            # Mock the _perform_initial_check method
            with patch.object(tracker, '_perform_initial_check') as mock_initial:
                result = tracker.add_product(**sample_product_data)
                
                # Verify session operations
                mock_session_context.add.assert_called_once()
                mock_session_context.commit.assert_called_once()
                mock_session_context.refresh.assert_called_once()
                
                # Verify initial check was called
                mock_initial.assert_called_once()

    def test_add_product_with_database_error(self, tracker, sample_product_data):
        """Test product addition with database error"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.commit.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                tracker.add_product(**sample_product_data)
            
            # Verify rollback was called
            mock_session_context.rollback.assert_called_once()

    def test_remove_product_success(self, tracker):
        """Test successful product removal"""
        product_id = str(uuid.uuid4())
        
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_product = Mock(spec=Product)
            mock_product.name = "Test Product"
            mock_session_context.query.return_value.filter.return_value.first.return_value = mock_product
            
            result = tracker.remove_product(product_id)
            
            # Verify product was deactivated
            assert mock_product.is_active is False
            mock_session_context.commit.assert_called_once()
            assert result is True

    def test_remove_product_not_found(self, tracker):
        """Test product removal when product doesn't exist"""
        product_id = str(uuid.uuid4())
        
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = None
            
            result = tracker.remove_product(product_id)
            
            assert result is False

    def test_get_products_active_only(self, tracker):
        """Test getting active products only"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [Mock(is_active=True), Mock(is_active=True)]
            
            result = tracker.get_products(active_only=True)
            
            # Verify filter was applied for active products
            mock_query.filter.assert_called()
            assert len(result) == 2

    def test_get_products_with_category_filter(self, tracker):
        """Test getting products with category filter"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = []
            
            tracker.get_products(category="Electronics")
            
            # Verify category filter was applied
            assert mock_query.filter.call_count >= 1

    def test_get_products_with_limit(self, tracker):
        """Test getting products with limit"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            tracker.get_products(limit=10)
            
            # Verify limit was applied
            mock_query.limit.assert_called_with(10)

    def test_get_product_by_id_found(self, tracker, mock_product):
        """Test getting product by ID when found"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = mock_product
            
            result = tracker.get_product(mock_product.id)
            
            assert result == mock_product

    def test_get_product_by_id_not_found(self, tracker):
        """Test getting product by ID when not found"""
        product_id = str(uuid.uuid4())
        
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = None
            
            result = tracker.get_product(product_id)
            
            assert result is None

    def test_update_product_success(self, tracker, mock_product):
        """Test successful product update"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = mock_product
            
            updates = {"target_price": 79.99, "name": "Updated Product"}
            result = tracker.update_product(mock_product.id, **updates)
            
            # Verify updates were applied
            assert mock_product.target_price == 79.99
            assert mock_product.name == "Updated Product"
            mock_session_context.commit.assert_called_once()
            mock_session_context.refresh.assert_called_once()
            assert result == mock_product

    def test_update_product_not_found(self, tracker):
        """Test updating product when not found"""
        product_id = str(uuid.uuid4())
        
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = None
            
            result = tracker.update_product(product_id, target_price=99.99)
            
            assert result is None

    def test_get_price_history_basic(self, tracker, mock_price_history):
        """Test getting price history"""
        product_id = str(uuid.uuid4())
        
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_price_history]
            
            result = tracker.get_price_history(product_id)
            
            assert len(result) == 1
            assert result[0] == mock_price_history

    def test_get_price_history_with_limit(self, tracker):
        """Test getting price history with limit"""
        product_id = str(uuid.uuid4())
        
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            tracker.get_price_history(product_id, limit=5)
            
            mock_query.limit.assert_called_with(5)

    def test_get_current_deals(self, tracker):
        """Test getting current deals"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock complex query chain
            mock_query = Mock()
            mock_session_context.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            # Mock price record with product
            mock_price_record = Mock()
            mock_price_record.product = Mock()
            mock_price_record.product.id = str(uuid.uuid4())
            mock_price_record.product.name = "Deal Product"
            mock_price_record.product.target_price = 99.99
            mock_price_record.price = 79.99
            mock_price_record.old_price = 99.99
            mock_price_record.discount_percentage = 20.0
            mock_price_record.savings_amount = 20.0
            mock_price_record.rating = 4.5
            mock_price_record.reviews_count = 100
            mock_price_record.prime_eligible = True
            mock_price_record.checked_at = datetime.now()
            
            mock_query.all.return_value = [mock_price_record]
            
            result = tracker.get_current_deals(max_price=100.0, min_discount=10.0)
            
            assert len(result) == 1
            assert result[0]["price"] == 79.99
            assert result[0]["discount_percentage"] == 20.0

    def test_check_product_price_success(self, tracker, mock_product, mock_price_history):
        """Test manual price check success"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = mock_product
            
            with patch.object(tracker.price_monitor, 'check_single_product', return_value=mock_price_history):
                result = tracker.check_product_price(mock_product.id)
                
                assert result == mock_price_history
                tracker.price_monitor.check_single_product.assert_called_once_with(mock_product)

    def test_check_product_price_not_found(self, tracker):
        """Test manual price check for non-existent product"""
        product_id = str(uuid.uuid4())
        
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            mock_session_context.query.return_value.filter.return_value.first.return_value = None
            
            result = tracker.check_product_price(product_id)
            
            assert result is None

    def test_start_monitoring(self, tracker):
        """Test starting price monitoring"""
        with patch.object(tracker.price_monitor, 'start') as mock_start:
            tracker.start_monitoring()
            mock_start.assert_called_once()

    def test_stop_monitoring(self, tracker):
        """Test stopping price monitoring"""
        with patch.object(tracker.price_monitor, 'stop') as mock_stop:
            tracker.stop_monitoring()
            mock_stop.assert_called_once()

    def test_get_predictions_success(self, tracker):
        """Test getting price predictions"""
        product_id = str(uuid.uuid4())
        mock_prediction = {
            "date": "2024-01-01", 
            "predicted_price": 89.99, 
            "confidence": 0.85
        }
        
        with patch.object(tracker.prediction_engine, 'predict_price') as mock_predict:
            mock_predict.return_value = mock_prediction
            
            # Mock asyncio.run to return the prediction directly
            with patch('asyncio.run', return_value=mock_prediction):
                result = tracker.get_predictions(product_id, days_ahead=7)
                
                assert len(result) == 1
                assert result[0] == mock_prediction

    def test_get_predictions_error(self, tracker):
        """Test getting predictions with error"""
        product_id = str(uuid.uuid4())
        
        with patch('asyncio.run', side_effect=Exception("Prediction error")):
            result = tracker.get_predictions(product_id)
            
            assert result == []

    def test_send_test_notification_success(self, tracker):
        """Test sending test notification successfully"""
        with patch.object(tracker.notification_manager, 'send_test_notification') as mock_send:
            mock_send.return_value = True
            
            # Mock asyncio.run to return True
            with patch('asyncio.run', return_value=True):
                result = tracker.send_test_notification("email", "test@example.com")
                
                assert result is True

    def test_send_test_notification_error(self, tracker):
        """Test sending test notification with error"""
        with patch('asyncio.run', side_effect=Exception("Send error")):
            result = tracker.send_test_notification("email")
            
            assert result is False

    def test_get_system_stats(self, tracker):
        """Test getting system statistics"""
        with patch('amazontracker.core.tracker.get_db_session') as mock_session:
            mock_session_context = Mock()
            mock_session.return_value.__enter__.return_value = mock_session_context
            
            # Mock query counts
            mock_session_context.query.return_value.count.return_value = 10
            mock_session_context.query.return_value.filter.return_value.count.return_value = 8
            
            with patch.object(tracker, 'get_current_deals', return_value=[]):
                result = tracker.get_system_stats()
                
                assert "products" in result
                assert "price_checks" in result
                assert "alerts" in result
                assert "current_deals" in result
                assert isinstance(result["products"]["total"], int)

    def test_perform_initial_check(self, tracker, mock_product):
        """Test performing initial check for new product"""
        with patch('asyncio.create_task') as mock_create_task:
            tracker._perform_initial_check(mock_product)
            
            # Verify async task was created
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_initial_check_success(self, tracker, mock_product, mock_price_history):
        """Test async initial check success"""
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(tracker.price_monitor, 'check_single_product', return_value=mock_price_history):
                await tracker._async_initial_check(mock_product)
                
                mock_sleep.assert_called_once_with(1)
                tracker.price_monitor.check_single_product.assert_called_once_with(mock_product)

    @pytest.mark.asyncio
    async def test_async_initial_check_failure(self, tracker, mock_product):
        """Test async initial check with failure"""
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(tracker.price_monitor, 'check_single_product', return_value=None):
                await tracker._async_initial_check(mock_product)
                
                mock_sleep.assert_called_once_with(1)
                tracker.price_monitor.check_single_product.assert_called_once_with(mock_product)
