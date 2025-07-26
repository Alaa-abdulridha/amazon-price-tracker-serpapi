"""
Comprehensive tests for SerpAPI client functionality
Tests all API interactions, search operations, and data parsing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from amazontracker.services.serpapi_client import SerpAPIClient


class TestSerpAPIClientInitialization:
    """Test SerpAPI client initialization and configuration"""
    
    def test_client_initialization_with_valid_key(self, test_settings):
        """Test client initializes correctly with valid API key"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            assert client.api_key == test_settings.serpapi_key
            assert client.timeout == test_settings.serpapi_timeout
            assert client.retries == test_settings.serpapi_retries
    
    def test_client_initialization_with_missing_key(self):
        """Test client raises error with missing API key"""
        with patch('amazontracker.services.serpapi_client.settings') as mock_settings:
            mock_settings.serpapi_key = ""
            
            with pytest.raises(ValueError, match="SerpAPI key is required"):
                SerpAPIClient()
    
    def test_client_default_parameters(self, test_settings):
        """Test client sets correct default parameters"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            expected_params = {
                "engine": "google_shopping",
                "api_key": test_settings.serpapi_key,
                "location": "United States",
                "hl": "en",
                "gl": "us"
            }
            
            for key, value in expected_params.items():
                assert client.default_params[key] == value


class TestSerpAPIClientSearchOperations:
    """Test search operations and API calls"""
    
    def test_search_products_success(self, test_settings, mock_serpapi_response):
        """Test successful product search"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_serpapi_response
                mock_get.return_value = mock_response
                
                results = client.search_products("iPhone 15")
                
                assert len(results) == 2
                assert results[0]["title"] == "iPhone 15 Pro Max 256GB"
                assert results[0]["price"] == "$1,199.99"
                assert results[1]["title"] == "iPhone 15 Pro 128GB"
                
                # Verify API call
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                assert "q=iPhone 15" in call_args[1]["params"]["q"]
    
    def test_search_products_by_asin_success(self, test_settings, mock_serpapi_response):
        """Test successful product search by ASIN"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_serpapi_response
                mock_get.return_value = mock_response
                
                results = client.search_by_asin("B0CHX1W1XY")
                
                assert len(results) == 2
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                assert "asin=B0CHX1W1XY" in str(call_args)
    
    def test_search_products_api_error(self, test_settings):
        """Test handling of API errors"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 400
                mock_response.text = "Bad Request"
                mock_get.return_value = mock_response
                
                results = client.search_products("iPhone 15")
                
                assert results == []
    
    def test_search_products_network_timeout(self, test_settings):
        """Test handling of network timeouts"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            with patch('requests.get') as mock_get:
                mock_get.side_effect = requests.Timeout("Request timed out")
                
                results = client.search_products("iPhone 15")
                
                assert results == []
    
    def test_search_products_connection_error(self, test_settings):
        """Test handling of connection errors"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            with patch('requests.get') as mock_get:
                mock_get.side_effect = requests.ConnectionError("Connection failed")
                
                results = client.search_products("iPhone 15")
                
                assert results == []
    
    def test_search_products_with_retry_logic(self, test_settings):
        """Test retry logic on transient failures"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            client.retries = 3
            
            with patch('requests.get') as mock_get:
                # First two calls fail, third succeeds
                mock_get.side_effect = [
                    requests.Timeout("Timeout 1"),
                    requests.Timeout("Timeout 2"),
                    Mock(status_code=200, json=lambda: {"shopping_results": []})
                ]
                
                results = client.search_products("iPhone 15")
                
                assert mock_get.call_count == 3
                assert results == []


class TestSerpAPIClientDataParsing:
    """Test data parsing and extraction functionality"""
    
    def test_parse_price_valid_formats(self, test_settings):
        """Test parsing various price formats"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            # Test different price formats
            test_cases = [
                ("$99.99", 99.99),
                ("$1,299.99", 1299.99),
                ("£89.99", 89.99),
                ("€149.99", 149.99),
                ("199.99", 199.99),
                ("$12.50", 12.50),
                ("$1,234,567.89", 1234567.89)
            ]
            
            for price_str, expected in test_cases:
                result = client.parse_price(price_str)
                assert result == expected
    
    def test_parse_price_invalid_formats(self, test_settings):
        """Test parsing invalid price formats returns None"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            invalid_prices = [
                "Free shipping",
                "Out of stock",
                "",
                None,
                "Price varies",
                "Contact seller"
            ]
            
            for invalid_price in invalid_prices:
                result = client.parse_price(invalid_price)
                assert result is None
    
    def test_extract_product_data_complete(self, test_settings):
        """Test extracting complete product data"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            raw_product = {
                "title": "iPhone 15 Pro Max 256GB - Natural Titanium",
                "price": "$1,199.99",
                "rating": 4.5,
                "reviews": 1234,
                "link": "https://amazon.com/product/test",
                "delivery": "FREE delivery",
                "thumbnail": "https://example.com/image.jpg",
                "position": 1
            }
            
            result = client.extract_product_data(raw_product)
            
            assert result["title"] == raw_product["title"]
            assert result["price"] == 1199.99
            assert result["rating"] == 4.5
            assert result["reviews"] == 1234
            assert result["link"] == raw_product["link"]
            assert result["delivery"] == raw_product["delivery"]
            assert result["thumbnail"] == raw_product["thumbnail"]
            assert result["position"] == 1
    
    def test_extract_product_data_minimal(self, test_settings):
        """Test extracting minimal product data"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            raw_product = {
                "title": "Basic Product",
                "price": "$29.99"
            }
            
            result = client.extract_product_data(raw_product)
            
            assert result["title"] == "Basic Product"
            assert result["price"] == 29.99
            assert result["rating"] is None
            assert result["reviews"] is None
            assert result["link"] is None
    
    def test_find_best_price_match_exact(self, test_settings, mock_serpapi_response):
        """Test finding best price match with exact query"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            products = [client.extract_product_data(p) for p in mock_serpapi_response["shopping_results"]]
            
            best_match = client.find_best_price_match(products, "iPhone 15 Pro Max")
            
            assert best_match is not None
            assert "iPhone 15 Pro Max" in best_match["title"]
            assert best_match["price"] == 1199.99
    
    def test_find_best_price_match_partial(self, test_settings, mock_serpapi_response):
        """Test finding best price match with partial query"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            products = [client.extract_product_data(p) for p in mock_serpapi_response["shopping_results"]]
            
            best_match = client.find_best_price_match(products, "iPhone")
            
            assert best_match is not None
            assert "iPhone" in best_match["title"]
    
    def test_find_best_price_match_no_match(self, test_settings, mock_serpapi_response):
        """Test finding best price match with no match"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            products = [client.extract_product_data(p) for p in mock_serpapi_response["shopping_results"]]
            
            best_match = client.find_best_price_match(products, "Samsung Galaxy")
            
            assert best_match is None


class TestSerpAPIClientFiltering:
    """Test filtering and sorting functionality"""
    
    def test_filter_by_price_range(self, test_settings, mock_serpapi_response):
        """Test filtering products by price range"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            products = [client.extract_product_data(p) for p in mock_serpapi_response["shopping_results"]]
            
            filtered = client.filter_by_price_range(products, min_price=500, max_price=1100)
            
            assert len(filtered) == 1  # Only iPhone 15 Pro 128GB ($999.99)
            assert filtered[0]["price"] == 999.99
    
    def test_filter_by_rating(self, test_settings, mock_serpapi_response):
        """Test filtering products by minimum rating"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            products = [client.extract_product_data(p) for p in mock_serpapi_response["shopping_results"]]
            
            filtered = client.filter_by_rating(products, min_rating=4.6)
            
            assert len(filtered) == 1  # Only iPhone 15 Pro 128GB (4.6 rating)
            assert filtered[0]["rating"] == 4.6
    
    def test_sort_by_price_ascending(self, test_settings, mock_serpapi_response):
        """Test sorting products by price (ascending)"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            products = [client.extract_product_data(p) for p in mock_serpapi_response["shopping_results"]]
            
            sorted_products = client.sort_by_price(products, ascending=True)
            
            assert len(sorted_products) == 2
            assert sorted_products[0]["price"] == 999.99
            assert sorted_products[1]["price"] == 1199.99
    
    def test_sort_by_price_descending(self, test_settings, mock_serpapi_response):
        """Test sorting products by price (descending)"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            products = [client.extract_product_data(p) for p in mock_serpapi_response["shopping_results"]]
            
            sorted_products = client.sort_by_price(products, ascending=False)
            
            assert len(sorted_products) == 2
            assert sorted_products[0]["price"] == 1199.99
            assert sorted_products[1]["price"] == 999.99
    
    def test_sort_by_rating(self, test_settings, mock_serpapi_response):
        """Test sorting products by rating"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            products = [client.extract_product_data(p) for p in mock_serpapi_response["shopping_results"]]
            
            sorted_products = client.sort_by_rating(products)
            
            assert len(sorted_products) == 2
            assert sorted_products[0]["rating"] == 4.6  # Higher rating first
            assert sorted_products[1]["rating"] == 4.5


class TestSerpAPIClientRateLimiting:
    """Test rate limiting and API usage tracking"""
    
    def test_rate_limiting_enforcement(self, test_settings):
        """Test rate limiting prevents excessive API calls"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            client.requests_per_minute = 2  # Very low limit for testing
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"shopping_results": []}
                mock_get.return_value = mock_response
                
                # Make rapid requests
                client.search_products("test1")
                client.search_products("test2")
                
                # Third request should be rate limited
                with patch('time.sleep') as mock_sleep:
                    client.search_products("test3")
                    mock_sleep.assert_called()  # Should sleep to respect rate limit
    
    def test_api_usage_tracking(self, test_settings):
        """Test API usage is tracked correctly"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"shopping_results": []}
                mock_get.return_value = mock_response
                
                initial_usage = client.get_api_usage()
                
                client.search_products("test")
                
                final_usage = client.get_api_usage()
                
                assert final_usage["requests_today"] == initial_usage["requests_today"] + 1
    
    def test_quota_exceeded_handling(self, test_settings):
        """Test handling when API quota is exceeded"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 429  # Too Many Requests
                mock_response.text = "Quota exceeded"
                mock_get.return_value = mock_response
                
                results = client.search_products("test")
                
                assert results == []
                # Should log quota exceeded error


class TestSerpAPIClientCaching:
    """Test caching functionality"""
    
    def test_cache_hit_avoids_api_call(self, test_settings):
        """Test cache hit avoids making API call"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            client.enable_caching = True
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"shopping_results": [{"title": "test"}]}
                mock_get.return_value = mock_response
                
                # First call should hit API
                result1 = client.search_products("iPhone 15")
                assert mock_get.call_count == 1
                
                # Second call should use cache
                result2 = client.search_products("iPhone 15")
                assert mock_get.call_count == 1  # No additional API call
                assert result1 == result2
    
    def test_cache_expiry(self, test_settings):
        """Test cache expires after configured time"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            client.enable_caching = True
            client.cache_duration = 1  # 1 second for testing
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"shopping_results": []}
                mock_get.return_value = mock_response
                
                with patch('time.time') as mock_time:
                    # First call
                    mock_time.return_value = 1000
                    client.search_products("iPhone 15")
                    assert mock_get.call_count == 1
                    
                    # Second call after cache expiry
                    mock_time.return_value = 1002  # 2 seconds later
                    client.search_products("iPhone 15")
                    assert mock_get.call_count == 2  # Cache expired, new API call
    
    def test_cache_clear(self, test_settings):
        """Test cache can be cleared manually"""
        with patch('amazontracker.services.serpapi_client.settings', test_settings):
            client = SerpAPIClient()
            client.enable_caching = True
            
            # Add some data to cache
            client._cache = {"test_key": {"data": [], "timestamp": 1000}}
            
            client.clear_cache()
            
            assert len(client._cache) == 0
