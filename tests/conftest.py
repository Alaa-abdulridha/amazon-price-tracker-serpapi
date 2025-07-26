"""
Test configuration and fixtures for Amazon Price Tracker
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from amazontracker.database.models import Base
from amazontracker.database.connection import init_database
from amazontracker.utils.config import Settings


@pytest.fixture
def temp_database():
    """Create a temporary SQLite database for testing"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Override settings for testing
    with patch('amazontracker.utils.config.settings') as mock_settings:
        mock_settings.database_url = f"sqlite:///{temp_db.name}"
        mock_settings.serpapi_key = "test_key_123"
        mock_settings.data_dir = "test_data"
        mock_settings.email_enabled = False
        mock_settings.slack_enabled = False
        mock_settings.desktop_notifications_enabled = True
        
        # Initialize test database
        engine = create_engine(f"sqlite:///{temp_db.name}")
        Base.metadata.create_all(bind=engine)
        
        yield temp_db.name
    
    # Cleanup
    if os.path.exists(temp_db.name):
        os.unlink(temp_db.name)


@pytest.fixture
def mock_serpapi_response():
    """Mock SerpAPI response for testing"""
    return {
        "shopping_results": [
            {
                "title": "iPhone 15 Pro Max 256GB",
                "price": "$1,199.99",
                "rating": 4.5,
                "reviews": 1234,
                "link": "https://amazon.com/product/test",
                "position": 1,
                "delivery": "FREE delivery",
                "thumbnail": "https://example.com/image.jpg"
            },
            {
                "title": "iPhone 15 Pro 128GB",
                "price": "$999.99",
                "rating": 4.6,
                "reviews": 2345,
                "link": "https://amazon.com/product/test2",
                "position": 2,
                "delivery": "FREE delivery",
                "thumbnail": "https://example.com/image2.jpg"
            }
        ]
    }


@pytest.fixture
def mock_notification_manager():
    """Mock notification manager for testing"""
    manager = Mock()
    manager.send_price_alert.return_value = {"success": True, "channels_sent": ["desktop"]}
    manager.send_deal_alert.return_value = {"success": True, "channels_sent": ["desktop"]}
    manager.get_notification_stats.return_value = {
        "sent": 10,
        "success_rate": 90.0,
        "by_channel": {"desktop": 8, "email": 2, "slack": 0}
    }
    return manager


@pytest.fixture
def test_settings():
    """Test settings configuration"""
    return Settings(
        serpapi_key="test_key_12345678901234567890123456789012",
        database_url="sqlite:///test.db",
        email_enabled=False,
        slack_enabled=False,
        desktop_notifications_enabled=True,
        secret_key="test_secret_key_for_testing_12345678901234567890123456",
        data_dir="test_data",
        debug=True
    )


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "name": "iPhone 15 Pro",
        "search_query": "iPhone 15 Pro",
        "target_price": 999.99,
        "check_interval": "1h",
        "email_notifications": True,
        "slack_notifications": False,
        "desktop_notifications": True
    }


@pytest.fixture
def sample_price_history():
    """Sample price history data for testing"""
    return [
        {"price": 1199.99, "timestamp": "2025-07-20T10:00:00Z", "source": "amazon"},
        {"price": 1149.99, "timestamp": "2025-07-21T10:00:00Z", "source": "amazon"},
        {"price": 1099.99, "timestamp": "2025-07-22T10:00:00Z", "source": "amazon"},
        {"price": 999.99, "timestamp": "2025-07-23T10:00:00Z", "source": "amazon"},
    ]
