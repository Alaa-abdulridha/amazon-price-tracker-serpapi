"""
SerpApi Client for Amazon Price Tracking
Handles all interactions with the SerpApi service for Amazon product searches
"""

import time
import logging
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import json

logger = logging.getLogger(__name__)


class SerpApiError(Exception):
    """Custom exception for SerpApi related errors"""
    pass


class SerpApiRateLimitError(SerpApiError):
    """Exception for rate limit errors"""
    pass


class SerpApiClient:
    """
    Client for interacting with SerpApi Amazon Search API
    """
    
    BASE_URL = "https://serpapi.com/search.json"
    
    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize SerpApi client

        Args:
            api_key: SerpApi key
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        
        logger.info("SerpApi client initialized")
    
    def search_amazon_products(
        self,
        query: str,
        amazon_domain: str = "amazon.com",
        language: str = "en_US",
        sort_by: str = "relevanceblender",
        max_results: int = 20,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search for Amazon products using SerpApi
        
        Args:
            query: Search query for products
            amazon_domain: Amazon domain to search (amazon.com, amazon.co.uk, etc.)
            language: Language for search results
            sort_by: Sorting method for results
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            Dict containing search results and metadata
            
        Raises:
            SerpApiError: If API request fails
            SerpApiRateLimitError: If rate limit is exceeded
        """
        params = {
            "engine": "amazon",
            "k": query,
            "amazon_domain": amazon_domain,
            "language": language,
            "api_key": self.api_key,
            "s": sort_by,
            **kwargs
        }
        
        try:
            response_data = self._make_request(params)
            
            # Extract and process results
            results = self._process_search_results(response_data, max_results)
            
            logger.info(f"Successfully searched for '{query}' - found {len(results.get('products', []))} products")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search Amazon products for query '{query}': {e}")
            raise SerpApiError(f"Amazon search failed: {e}")
    
    def get_product_by_asin(
        self,
        asin: str,
        amazon_domain: str = "amazon.com",
        language: str = "en_US"
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific product information by ASIN
        
        Args:
            asin: Amazon Standard Identification Number
            amazon_domain: Amazon domain
            language: Language for results
            
        Returns:
            Product information dictionary or None if not found
        """
        try:
            # Search by ASIN is typically done with a specific query format
            query = f"asin:{asin}"
            results = self.search_amazon_products(
                query=query,
                amazon_domain=amazon_domain,
                language=language,
                max_results=1
            )
            
            products = results.get('products', [])
            if products:
                return products[0]
            
            logger.warning(f"No product found for ASIN: {asin}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get product by ASIN {asin}: {e}")
            return None
    
    def get_best_price_match(
        self,
        search_query: str,
        target_keywords: List[str] = None,
        max_price: float = None,
        min_rating: float = None,
        amazon_domain: str = "amazon.com"
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best price match for a search query with optional filters
        
        Args:
            search_query: Product search query
            target_keywords: Keywords that must be in product title
            max_price: Maximum acceptable price
            min_rating: Minimum product rating
            amazon_domain: Amazon domain to search
            
        Returns:
            Best matching product or None
        """
        try:
            # Search with price sorting
            results = self.search_amazon_products(
                query=search_query,
                amazon_domain=amazon_domain,
                sort_by="price-asc-rank",  # Sort by price low to high
                max_results=50
            )
            
            products = results.get('products', [])
            
            # Filter products based on criteria
            filtered_products = []
            
            for product in products:
                # Check if product has required information
                if not product.get('extracted_price'):
                    continue
                
                price = product['extracted_price']
                rating = product.get('rating', 0)
                title = product.get('title', '').lower()
                
                # Apply filters
                if max_price and price > max_price:
                    continue
                
                if min_rating and rating < min_rating:
                    continue
                
                if target_keywords:
                    if not all(keyword.lower() in title for keyword in target_keywords):
                        continue
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(product, search_query)
                product['relevance_score'] = relevance_score
                
                filtered_products.append(product)
            
            if not filtered_products:
                logger.info(f"No products match criteria for query: {search_query}")
                return None
            
            # Sort by relevance score and return best match
            best_match = max(filtered_products, key=lambda p: p['relevance_score'])
            
            logger.info(f"Found best match for '{search_query}': {best_match.get('title')} - ${best_match.get('extracted_price')}")
            
            return best_match
            
        except Exception as e:
            logger.error(f"Failed to find best price match for '{search_query}': {e}")
            return None
    
    def get_price_history_simulation(
        self,
        asin: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Simulate price history by checking multiple times
        Note: This is for demonstration - real price history requires historical data
        
        Args:
            asin: Product ASIN
            days: Number of days to simulate
            
        Returns:
            List of simulated price points
        """
        # In a real implementation, this would query historical price data
        # For now, we'll return the current price as a single data point
        current_product = self.get_product_by_asin(asin)
        
        if not current_product:
            return []
        
        # Return current price as single data point
        return [{
            'date': time.strftime('%Y-%m-%d'),
            'price': current_product.get('extracted_price'),
            'title': current_product.get('title'),
            'rating': current_product.get('rating'),
            'reviews': current_product.get('reviews')
        }]
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to SerpApi with rate limiting and retry logic
        
        Args:
            params: Request parameters
            
        Returns:
            API response data
            
        Raises:
            SerpApiError: If request fails after retries
            SerpApiRateLimitError: If rate limited
        """
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        url = self.BASE_URL
        
        for attempt in range(self.retries + 1):
            try:
                logger.debug(f"Making SerpApi request (attempt {attempt + 1}): {params.get('k', 'N/A')}")
                
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'AmazonPriceTracker/1.0',
                        'Accept': 'application/json'
                    }
                )
                
                self.last_request_time = time.time()
                
                # Check response status
                if response.status_code == 429:
                    logger.warning("Rate limit exceeded")
                    raise SerpApiRateLimitError("Rate limit exceeded")
                
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # Check for API errors
                if 'error' in data:
                    error_msg = data['error']
                    logger.error(f"SerpAPI error: {error_msg}")
                    raise SerpApiError(f"API error: {error_msg}")
                
                # Log usage information
                search_metadata = data.get('search_metadata', {})
                logger.debug(f"Request successful - ID: {search_metadata.get('id', 'N/A')}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.retries:
                    sleep_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    raise SerpApiError(f"Request failed after {self.retries + 1} attempts: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error during request: {e}")
                raise SerpApiError(f"Unexpected error: {e}")
    
    def _process_search_results(
        self,
        raw_data: Dict[str, Any],
        max_results: int
    ) -> Dict[str, Any]:
        """
        Process raw SerpAPI response into structured format
        
        Args:
            raw_data: Raw API response
            max_results: Maximum products to return
            
        Returns:
            Processed results dictionary
        """
        processed_results = {
            'search_metadata': raw_data.get('search_metadata', {}),
            'search_parameters': raw_data.get('search_parameters', {}),
            'search_information': raw_data.get('search_information', {}),
            'products': [],
            'ads': raw_data.get('product_ads', {}),
            'related_searches': raw_data.get('related_searches', []),
            'total_results': 0
        }
        
        # Extract organic results
        organic_results = raw_data.get('organic_results', [])
        
        # Process each product
        for i, result in enumerate(organic_results[:max_results]):
            processed_product = self._process_product_result(result)
            if processed_product:
                processed_results['products'].append(processed_product)
        
        processed_results['total_results'] = len(processed_results['products'])
        
        return processed_results
    
    def _process_product_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process individual product result
        
        Args:
            result: Raw product result from API
            
        Returns:
            Processed product data or None if invalid
        """
        try:
            # Extract core product information
            product = {
                'position': result.get('position'),
                'asin': result.get('asin'),
                'title': result.get('title'),
                'link': result.get('link_clean', result.get('link')),
                'image_url': result.get('thumbnail'),
                
                # Price information
                'price': result.get('price'),
                'extracted_price': result.get('extracted_price'),
                'old_price': result.get('old_price'),
                'extracted_old_price': result.get('extracted_old_price'),
                'price_unit': result.get('price_unit'),
                'extracted_price_unit': result.get('extracted_price_unit'),
                
                # Product details
                'rating': result.get('rating'),
                'reviews_count': result.get('reviews'),
                'prime_eligible': result.get('prime', False),
                'sponsored': result.get('sponsored', False),
                
                # Availability and shipping
                'availability': result.get('availability'),
                'delivery': result.get('delivery', []),
                'shipping': result.get('shipping'),
                
                # Deal information
                'discount_percentage': None,
                'savings_amount': None,
                'is_deal': False,
                
                # Additional metadata
                'tags': result.get('tags', []),
                'options': result.get('options'),
                'seller': result.get('seller'),
                'bought_last_month': result.get('bought_last_month'),
                
                # Raw data for debugging
                'raw_data': json.dumps(result) if logger.isEnabledFor(logging.DEBUG) else None
            }
            
            # Calculate deal information
            if product['extracted_price'] and product['extracted_old_price']:
                old_price = product['extracted_old_price']
                current_price = product['extracted_price']
                
                if old_price > current_price:
                    savings = old_price - current_price
                    discount_pct = (savings / old_price) * 100
                    
                    product['savings_amount'] = savings
                    product['discount_percentage'] = round(discount_pct, 2)
                    product['is_deal'] = discount_pct >= 5.0  # Consider 5%+ a deal
            
            # Validate required fields
            if not product['extracted_price']:
                logger.debug(f"Skipping product without price: {product.get('title', 'Unknown')}")
                return None
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to process product result: {e}")
            return None
    
    def _calculate_relevance_score(
        self,
        product: Dict[str, Any],
        search_query: str
    ) -> float:
        """
        Calculate relevance score for a product based on search query
        
        Args:
            product: Product data
            search_query: Original search query
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        title = product.get('title', '').lower()
        query_words = search_query.lower().split()
        
        # Title relevance (40% of score)
        title_matches = sum(1 for word in query_words if word in title)
        title_score = (title_matches / len(query_words)) * 0.4
        score += title_score
        
        # Rating score (20% of score)
        rating = product.get('rating', 0)
        rating_score = (rating / 5.0) * 0.2
        score += rating_score
        
        # Reviews count score (15% of score)
        reviews = product.get('reviews_count', 0)
        if reviews > 0:
            # Logarithmic scale for reviews (1000+ reviews = full score)
            import math
            reviews_score = min(math.log10(reviews) / 3.0, 1.0) * 0.15
            score += reviews_score
        
        # Prime eligibility bonus (10% of score)
        if product.get('prime_eligible', False):
            score += 0.1
        
        # Deal bonus (15% of score)
        if product.get('is_deal', False):
            discount = product.get('discount_percentage', 0)
            deal_score = min(discount / 50.0, 1.0) * 0.15  # Max at 50% discount
            score += deal_score
        
        return min(score, 1.0)  # Cap at 1.0
    
    def test_connection(self) -> bool:
        """
        Test the SerpAPI connection
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Make a simple test request
            test_params = {
                "engine": "amazon",
                "k": "test",
                "api_key": self.api_key,
                "num": 1  # Only get 1 result for testing
            }
            
            response_data = self._make_request(test_params)
            
            if response_data and 'search_metadata' in response_data:
                logger.info("SerpAPI connection test successful")
                return True
            else:
                logger.error("SerpAPI connection test failed - invalid response")
                return False
                
        except Exception as e:
            logger.error(f"SerpAPI connection test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information and usage statistics
        
        Returns:
            Account information dictionary
        """
        try:
            # SerpAPI account endpoint
            account_url = "https://serpapi.com/account.json"
            
            response = requests.get(
                account_url,
                params={"api_key": self.api_key},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            account_data = response.json()
            
            logger.info("Retrieved SerpAPI account information")
            return account_data
            
        except Exception as e:
            logger.error(f"Failed to get SerpAPI account info: {e}")
            return {}
