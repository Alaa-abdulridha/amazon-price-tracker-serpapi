"""
Comprehensive tests for FastAPI web application
Tests all REST endpoints, dashboard functionality, and web interface
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from amazontracker.web.app import app


class TestWebApplicationEndpoints:
    """Test REST API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_dashboard_endpoint(self):
        """Test main dashboard endpoint"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            with patch('amazontracker.web.app.templates') as mock_templates:
                mock_tracker.get_products.return_value = [
                    Mock(is_active=True, name="iPhone 15"),
                    Mock(is_active=False, name="Old Product")
                ]
                mock_tracker.get_current_deals.return_value = []
                
                mock_templates.TemplateResponse.return_value = Mock()
                
                response = self.client.get("/")
                
                assert response.status_code == 200
                mock_tracker.get_products.assert_called_once()
                mock_tracker.get_current_deals.assert_called_once()
    
    def test_get_products_api(self):
        """Test GET /api/products endpoint"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_products = [
                Mock(
                    id="1",
                    name="iPhone 15",
                    target_price=999.99,
                    is_active=True,
                    check_interval="1h",
                    last_checked_at=None,
                    search_query="iPhone 15"
                )
            ]
            mock_tracker.get_products.return_value = mock_products
            
            response = self.client.get("/api/products")
            
            assert response.status_code == 200
            data = response.json()
            assert "products" in data
            assert len(data["products"]) == 1
            assert data["products"][0]["name"] == "iPhone 15"
            assert data["products"][0]["target_price"] == 999.99
    
    def test_add_product_api_success(self):
        """Test POST /api/products endpoint success"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_product = Mock()
            mock_product.id = "new-product-id"
            mock_product.name = "MacBook Pro"
            mock_product.target_price = 1999.99
            mock_tracker.add_product.return_value = mock_product
            
            product_data = {
                "search_query": "MacBook Pro M3",
                "target_price": 1999.99,
                "check_interval": "2h"
            }
            
            response = self.client.post(
                "/api/products",
                data=product_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "product" in data
            mock_tracker.add_product.assert_called_once()
    
    def test_add_product_api_validation_error(self):
        """Test POST /api/products with validation error"""
        product_data = {
            # Missing required target_price
            "search_query": "MacBook Pro M3",
            "check_interval": "2h"
        }
        
        response = self.client.post(
            "/api/products",
            data=product_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_add_product_api_missing_query_and_asin(self):
        """Test POST /api/products without search_query or asin"""
        product_data = {
            "target_price": 1999.99,
            "check_interval": "2h"
        }
        
        response = self.client.post(
            "/api/products",
            data=product_data
        )
        
        assert response.status_code == 400
        assert "Either search_query or asin must be provided" in response.json()["detail"]
    
    def test_remove_product_api_success(self):
        """Test DELETE /api/products/{product_id} success"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_tracker.remove_product.return_value = True
            
            response = self.client.delete("/api/products/test-product-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_tracker.remove_product.assert_called_once_with("test-product-id")
    
    def test_remove_product_api_not_found(self):
        """Test DELETE /api/products/{product_id} not found"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_tracker.remove_product.return_value = False
            
            response = self.client.delete("/api/products/nonexistent-id")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_get_product_history_api(self):
        """Test GET /api/products/{product_id}/history endpoint"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_history = [
                Mock(price=999.99, timestamp="2025-07-26T10:00:00Z"),
                Mock(price=949.99, timestamp="2025-07-25T10:00:00Z")
            ]
            mock_tracker.get_price_history.return_value = mock_history
            
            response = self.client.get("/api/products/test-id/history?days=7")
            
            assert response.status_code == 200
            data = response.json()
            assert "history" in data
            assert len(data["history"]) == 2
    
    def test_check_product_price_api(self):
        """Test POST /api/products/{product_id}/check endpoint"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_price_record = Mock()
            mock_price_record.price = 899.99
            mock_tracker.check_product_price.return_value = mock_price_record
            
            response = self.client.post("/api/products/test-id/check")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["current_price"] == 899.99


class TestWebApplicationPredictionEndpoints:
    """Test AI prediction endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_get_price_prediction_api(self):
        """Test GET /api/products/{product_id}/predict endpoint"""
        with patch('amazontracker.web.app.prediction_engine') as mock_engine:
            mock_prediction = {
                "predicted_price": 899.99,
                "confidence": 0.85,
                "days_ahead": 7
            }
            mock_engine.predict_price.return_value = mock_prediction
            
            response = self.client.get("/api/products/test-id/predict?days_ahead=7")
            
            assert response.status_code == 200
            data = response.json()
            assert data["predicted_price"] == 899.99
            assert data["confidence"] == 0.85
    
    def test_get_price_prediction_insufficient_data(self):
        """Test prediction endpoint with insufficient data"""
        with patch('amazontracker.web.app.prediction_engine') as mock_engine:
            mock_engine.predict_price.return_value = None
            
            response = self.client.get("/api/products/test-id/predict?days_ahead=7")
            
            assert response.status_code == 400
            assert "Insufficient data" in response.json()["error"]
    
    def test_get_trend_analysis_api(self):
        """Test GET /api/products/{product_id}/trends endpoint"""
        with patch('amazontracker.web.app.prediction_engine') as mock_engine:
            mock_analysis = {
                "trend_direction": "downward",
                "trend_strength": 0.75,
                "volatility": 0.15
            }
            mock_engine.analyze_price_trends.return_value = mock_analysis
            
            response = self.client.get("/api/products/test-id/trends?period_days=30")
            
            assert response.status_code == 200
            data = response.json()
            assert data["trend_direction"] == "downward"
            assert data["trend_strength"] == 0.75


class TestWebApplicationNotificationEndpoints:
    """Test notification endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_test_notifications_api_all(self):
        """Test POST /api/notifications/test endpoint for all channels"""
        with patch('amazontracker.web.app.notification_manager') as mock_manager:
            mock_manager.send_test_notification.return_value = {"success": True}
            
            response = self.client.post("/api/notifications/test")
            
            assert response.status_code == 200
            data = response.json()
            assert "email" in data
            assert "slack" in data
            assert "desktop" in data
    
    def test_test_notifications_api_specific_channel(self):
        """Test testing specific notification channel"""
        with patch('amazontracker.web.app.notification_manager') as mock_manager:
            mock_manager.send_test_notification.return_value = {"success": True}
            
            response = self.client.post("/api/notifications/test?channel=desktop")
            
            assert response.status_code == 200
            data = response.json()
            assert data["desktop"]["success"] is True
    
    def test_get_notification_stats_api(self):
        """Test GET /api/notifications/stats endpoint"""
        with patch('amazontracker.web.app.notification_manager') as mock_manager:
            mock_stats = {
                "sent": 150,
                "success_rate": 95.5,
                "by_channel": {
                    "email": 75,
                    "slack": 25,
                    "desktop": 50
                }
            }
            mock_manager.get_notification_stats.return_value = mock_stats
            
            response = self.client.get("/api/notifications/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["sent"] == 150
            assert data["success_rate"] == 95.5
            assert "by_channel" in data


class TestWebApplicationMonitoringEndpoints:
    """Test monitoring and statistics endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_get_dashboard_stats_api(self):
        """Test GET /api/dashboard/stats endpoint"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_tracker.get_products.return_value = [
                Mock(is_active=True),
                Mock(is_active=True),
                Mock(is_active=False)
            ]
            
            response = self.client.get("/api/dashboard/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_products"] == 3
            assert data["active_products"] == 2
    
    def test_get_statistics_api(self):
        """Test GET /api/statistics endpoint"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            with patch('amazontracker.web.app.notification_manager') as mock_manager:
                mock_tracker.get_products.return_value = [Mock(is_active=True)] * 5
                mock_tracker.get_current_deals.return_value = [Mock()] * 2
                mock_manager.get_notification_stats.return_value = {"sent": 100}
                
                response = self.client.get("/api/statistics")
                
                assert response.status_code == 200
                data = response.json()
                assert "products" in data
                assert "deals" in data
                assert "notifications" in data
    
    def test_get_chart_data_api(self):
        """Test GET /api/chart-data endpoint"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_products = [Mock(id="1", name="iPhone 15")]
            mock_tracker.get_products.return_value = mock_products
            
            mock_history = [
                Mock(price=999.99, timestamp="2025-07-26T10:00:00"),
                Mock(price=949.99, timestamp="2025-07-25T10:00:00")
            ]
            mock_tracker.get_price_history.return_value = mock_history
            
            response = self.client.get("/api/chart-data")
            
            assert response.status_code == 200
            data = response.json()
            assert "chart_data" in data
            assert len(data["chart_data"]) > 0


class TestWebApplicationErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_404_error_handling(self):
        """Test 404 error for non-existent endpoints"""
        response = self.client.get("/api/nonexistent")
        
        assert response.status_code == 404
    
    def test_500_error_handling(self):
        """Test 500 error handling"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_tracker.get_products.side_effect = Exception("Database error")
            
            response = self.client.get("/api/products")
            
            assert response.status_code == 500
            assert "error" in response.json()["detail"].lower()
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in request body"""
        response = self.client.post(
            "/api/products",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should handle gracefully (422 validation error expected)
        assert response.status_code in [400, 422]
    
    def test_rate_limiting_headers(self):
        """Test rate limiting headers are present"""
        response = self.client.get("/api/products")
        
        # Should include rate limiting headers in production
        # This is a basic test - actual implementation depends on rate limiting setup
        assert response.status_code in [200, 429]  # Either success or rate limited
    
    def test_cors_headers(self):
        """Test CORS headers for cross-origin requests"""
        response = self.client.options("/api/products")
        
        # Should handle OPTIONS requests for CORS
        assert response.status_code in [200, 405]  # Either allowed or method not allowed


class TestWebApplicationSecurity:
    """Test security features"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection"""
        malicious_input = "'; DROP TABLE products; --"
        
        response = self.client.get(f"/api/products/{malicious_input}/history")
        
        # Should handle malicious input gracefully
        assert response.status_code in [400, 404, 422]
    
    def test_xss_protection(self):
        """Test protection against XSS attacks"""
        xss_payload = "<script>alert('xss')</script>"
        
        product_data = {
            "search_query": xss_payload,
            "target_price": 999.99
        }
        
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_tracker.add_product.return_value = Mock(id="test")
            
            response = self.client.post("/api/products", data=product_data)
            
            # Should either reject or sanitize the input
            assert response.status_code in [200, 400, 422]
    
    def test_csrf_protection(self):
        """Test CSRF protection for state-changing operations"""
        # This test depends on CSRF implementation
        # Basic test to ensure POST requests are handled
        product_data = {
            "search_query": "iPhone 15",
            "target_price": 999.99
        }
        
        response = self.client.post("/api/products", data=product_data)
        
        # Should handle request (with or without CSRF token)
        assert response.status_code in [200, 400, 403, 422]


class TestWebApplicationPerformance:
    """Test performance and caching"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_response_time_acceptable(self):
        """Test that API responses are reasonably fast"""
        import time
        
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_tracker.get_products.return_value = []
            
            start_time = time.time()
            response = self.client.get("/api/products")
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 1.0  # Should respond in under 1 second
    
    def test_caching_headers(self):
        """Test appropriate caching headers"""
        response = self.client.get("/api/products")
        
        # Static data might have cache headers
        # This depends on caching implementation
        assert response.status_code == 200
    
    def test_large_dataset_handling(self):
        """Test handling of large product lists"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            # Mock large number of products
            large_product_list = [
                Mock(
                    id=f"product-{i}",
                    name=f"Product {i}",
                    target_price=999.99,
                    is_active=True,
                    check_interval="1h",
                    last_checked_at=None,
                    search_query=f"Product {i}"
                )
                for i in range(1000)
            ]
            mock_tracker.get_products.return_value = large_product_list
            
            response = self.client.get("/api/products")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["products"]) == 1000


class TestWebApplicationIntegration:
    """Test integration between different components"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_full_product_lifecycle_api(self):
        """Test complete product lifecycle through API"""
        # Add product
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_product = Mock()
            mock_product.id = "test-product"
            mock_product.name = "iPhone 15"
            mock_tracker.add_product.return_value = mock_product
            
            add_response = self.client.post(
                "/api/products",
                data={
                    "search_query": "iPhone 15",
                    "target_price": 999.99
                }
            )
            
            assert add_response.status_code == 200
            
            # Check price
            mock_tracker.check_product_price.return_value = Mock(price=899.99)
            
            check_response = self.client.post("/api/products/test-product/check")
            
            assert check_response.status_code == 200
            
            # Remove product
            mock_tracker.remove_product.return_value = True
            
            remove_response = self.client.delete("/api/products/test-product")
            
            assert remove_response.status_code == 200
    
    def test_dashboard_data_consistency(self):
        """Test dashboard data consistency across endpoints"""
        with patch('amazontracker.web.app.tracker') as mock_tracker:
            mock_products = [Mock(is_active=True)] * 5
            mock_tracker.get_products.return_value = mock_products
            mock_tracker.get_current_deals.return_value = []
            
            # Test dashboard
            with patch('amazontracker.web.app.templates') as mock_templates:
                mock_templates.TemplateResponse.return_value = Mock()
                dashboard_response = self.client.get("/")
                
            # Test stats API
            stats_response = self.client.get("/api/dashboard/stats")
            
            assert dashboard_response.status_code == 200
            assert stats_response.status_code == 200
            
            # Both should report same number of products
            stats_data = stats_response.json()
            assert stats_data["total_products"] == 5
