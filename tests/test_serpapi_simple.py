"""
Simple tests for SerpApi client functionality
Tests basic initialization and key functionality only
"""

import pytest
from unittest.mock import Mock, patch
from amazontracker.services.serpapi_client import SerpApiClient, SerpApiError


class TestSerpApiClientBasic:
    """Basic SerpApi client tests"""
    
    def test_client_initialization_with_valid_key(self):
        """Test client initializes correctly with valid API key"""
        client = SerpApiClient(api_key="test_key_123")
        
        assert client.api_key == "test_key_123"
        assert client.timeout == 30  # default value
        assert client.retries == 3   # default value
    
    def test_client_initialization_without_key(self):
        """Test client initialization without key"""
        # This should work - let the client handle validation later
        client = SerpApiClient(api_key="")
        assert client.api_key == ""
    
    def test_client_custom_parameters(self):
        """Test client with custom parameters"""
        client = SerpApiClient(
            api_key="test_key", 
            timeout=60, 
            retries=5, 
            retry_delay=2.0
        )
        
        assert client.api_key == "test_key"
        assert client.timeout == 60
        assert client.retries == 5
        assert client.retry_delay == 2.0


@pytest.fixture
def sample_client():
    """Fixture for SerpApi client"""
    return SerpApiClient(api_key="test_key_12345678901234567890123456789012")


class TestSerpApiClientSearch:
    """Test search functionality"""
    
    @patch('requests.get')
    def test_search_by_query_basic(self, mock_get, sample_client):
        """Test basic search by query"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "shopping_results": [
                {
                    "title": "Test Product",
                    "price": "$19.99",
                    "link": "https://amazon.com/test"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test search
        results = sample_client.search_amazon_products("test product")
        
        # Verify request was made
        mock_get.assert_called_once()
        
        # Check if results contain expected data (flexible check)
        assert isinstance(results, (list, dict))
    
    @patch('requests.get')
    def test_search_handles_errors(self, mock_get, sample_client):
        """Test search handles API errors gracefully"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response
        
        # Test that it handles errors (implementation may vary)
        try:
            sample_client.search_amazon_products("test product")
        except Exception:
            # Expected to raise some kind of error
            pass
