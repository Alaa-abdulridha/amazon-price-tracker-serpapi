"""
Core Price Tracker class
Main interface for the Amazon Price Tracker application
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..database.models import Product, PriceHistory, PriceAlert
from ..database.connection import get_db_session
from ..services.serpapi_client import SerpAPIClient
from ..services.price_monitor import PriceMonitor
from ..ai.prediction import PricePredictionEngine
from ..notifications.manager import NotificationManager
from ..utils.config import settings

logger = logging.getLogger(__name__)


class PriceTracker:
    """
    Main Price Tracker class providing high-level interface for price tracking operations
    """
    
    def __init__(self):
        """Initialize the Price Tracker with all necessary services"""
        self.serpapi_client = SerpAPIClient(settings.serpapi_key)
        self.price_monitor = PriceMonitor()
        self.prediction_engine = PricePredictionEngine()
        self.notification_manager = NotificationManager()
        
        logger.info("Price Tracker initialized successfully")
    
    def add_product(
        self,
        name: str,
        search_query: str,
        target_price: float,
        max_price: Optional[float] = None,
        check_interval: str = "1h",
        email_notifications: bool = True,
        slack_notifications: bool = False,
        desktop_notifications: bool = True,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Product:
        """
        Add a new product to track
        
        Args:
            name: Human-readable product name
            search_query: Amazon search query to find the product
            target_price: Desired price threshold for alerts
            max_price: Maximum acceptable price
            check_interval: How often to check prices (5m, 15m, 30m, 1h, 2h, 6h, 12h, 24h)
            email_notifications: Enable email alerts
            slack_notifications: Enable Slack alerts
            desktop_notifications: Enable desktop alerts
            category: Product category
            tags: List of tags for organization
            
        Returns:
            Created Product instance
        """
        with get_db_session() as session:
            try:
                # Create new product
                product = Product(
                    name=name,
                    search_query=search_query,
                    target_price=target_price,
                    max_price=max_price,
                    check_interval=check_interval,
                    email_notifications=email_notifications,
                    slack_notifications=slack_notifications,
                    desktop_notifications=desktop_notifications,
                    category=category,
                    tags=",".join(tags) if tags else None
                )
                
                session.add(product)
                session.commit()
                session.refresh(product)
                
                # Perform initial price check
                self._perform_initial_check(product)
                
                logger.info(f"Added new product: {name} (ID: {product.id})")
                return product
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to add product {name}: {e}")
                raise
    
    def remove_product(self, product_id: str) -> bool:
        """
        Remove a product from tracking
        
        Args:
            product_id: ID of the product to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        with get_db_session() as session:
            try:
                product = session.query(Product).filter(Product.id == product_id).first()
                if not product:
                    logger.warning(f"Product {product_id} not found")
                    return False
                
                # Deactivate instead of deleting to preserve history
                product.is_active = False
                session.commit()
                
                logger.info(f"Deactivated product: {product.name} (ID: {product_id})")
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to remove product {product_id}: {e}")
                return False
    
    def get_products(
        self,
        active_only: bool = True,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Product]:
        """
        Get list of tracked products
        
        Args:
            active_only: Only return active products
            category: Filter by category
            limit: Limit number of results
            
        Returns:
            List of Product instances
        """
        with get_db_session() as session:
            query = session.query(Product)
            
            if active_only:
                query = query.filter(Product.is_active == True)
            
            if category:
                query = query.filter(Product.category == category)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Get a specific product by ID
        
        Args:
            product_id: Product ID to retrieve
            
        Returns:
            Product instance or None if not found
        """
        with get_db_session() as session:
            return session.query(Product).filter(Product.id == product_id).first()
    
    def update_product(
        self,
        product_id: str,
        **updates
    ) -> Optional[Product]:
        """
        Update product settings
        
        Args:
            product_id: Product ID to update
            **updates: Fields to update
            
        Returns:
            Updated Product instance or None if not found
        """
        with get_db_session() as session:
            try:
                product = session.query(Product).filter(Product.id == product_id).first()
                if not product:
                    return None
                
                for field, value in updates.items():
                    if hasattr(product, field):
                        setattr(product, field, value)
                
                session.commit()
                session.refresh(product)
                
                logger.info(f"Updated product {product_id}: {updates}")
                return product
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to update product {product_id}: {e}")
                raise
    
    def get_price_history(
        self,
        product_id: str,
        limit: Optional[int] = None,
        days: Optional[int] = None
    ) -> List[PriceHistory]:
        """
        Get price history for a product
        
        Args:
            product_id: Product ID
            limit: Limit number of records
            days: Number of days back to retrieve
            
        Returns:
            List of PriceHistory instances
        """
        with get_db_session() as session:
            query = session.query(PriceHistory).filter(
                PriceHistory.product_id == product_id
            ).order_by(PriceHistory.checked_at.desc())
            
            if days:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                query = query.filter(PriceHistory.checked_at >= cutoff_date)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def get_current_deals(
        self,
        max_price: Optional[float] = None,
        min_discount: Optional[float] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get current best deals
        
        Args:
            max_price: Maximum price filter
            min_discount: Minimum discount percentage
            limit: Maximum number of deals to return
            
        Returns:
            List of deal information
        """
        with get_db_session() as session:
            # Query for recent price history with deals
            query = session.query(PriceHistory).join(Product).filter(
                Product.is_active == True,
                PriceHistory.is_deal == True
            )
            
            if max_price:
                query = query.filter(PriceHistory.price <= max_price)
            
            if min_discount:
                query = query.filter(PriceHistory.discount_percentage >= min_discount)
            
            # Get latest price for each product
            subquery = session.query(
                PriceHistory.product_id,
                func.max(PriceHistory.checked_at).label('latest_check')
            ).group_by(PriceHistory.product_id).subquery()
            
            query = query.join(
                subquery,
                (PriceHistory.product_id == subquery.c.product_id) &
                (PriceHistory.checked_at == subquery.c.latest_check)
            )
            
            results = query.order_by(
                PriceHistory.discount_percentage.desc()
            ).limit(limit).all()
            
            # Format results
            deals = []
            for price_record in results:
                deal = {
                    "product": {
                        "id": price_record.product.id,
                        "name": price_record.product.name,
                        "target_price": price_record.product.target_price,
                    },
                    "price": price_record.price,
                    "old_price": price_record.old_price,
                    "discount_percentage": price_record.discount_percentage,
                    "savings_amount": price_record.savings_amount,
                    "rating": price_record.rating,
                    "reviews_count": price_record.reviews_count,
                    "prime_eligible": price_record.prime_eligible,
                    "checked_at": price_record.checked_at
                }
                deals.append(deal)
            
            return deals
    
    def check_product_price(self, product_id: str) -> Optional[PriceHistory]:
        """
        Manually trigger a price check for a specific product
        
        Args:
            product_id: Product ID to check
            
        Returns:
            Latest PriceHistory record or None
        """
        with get_db_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Product {product_id} not found")
                return None
            
            try:
                # Use price monitor to check price
                price_record = self.price_monitor.check_single_product(product)
                
                if price_record:
                    logger.info(f"Price check completed for {product.name}: ${price_record.price}")
                
                return price_record
                
            except Exception as e:
                logger.error(f"Failed to check price for product {product_id}: {e}")
                return None
    
    def start_monitoring(self) -> None:
        """Start the price monitoring service"""
        logger.info("Starting price monitoring service...")
        self.price_monitor.start()
    
    def stop_monitoring(self) -> None:
        """Stop the price monitoring service"""
        logger.info("Stopping price monitoring service...")
        self.price_monitor.stop()
    
    def get_predictions(
        self,
        product_id: str,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get price predictions for a product
        
        Args:
            product_id: Product ID
            days_ahead: Number of days to predict
            
        Returns:
            List of prediction data
        """
        try:
            predictions = self.prediction_engine.predict_prices(
                product_id=product_id,
                days_ahead=days_ahead
            )
            
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to get predictions for product {product_id}: {e}")
            return []
    
    def send_test_notification(
        self,
        notification_type: str,
        recipient: Optional[str] = None
    ) -> bool:
        """
        Send a test notification
        
        Args:
            notification_type: Type of notification (email, slack, desktop)
            recipient: Notification recipient (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.notification_manager.send_test_notification(
                notification_type=notification_type,
                recipient=recipient
            )
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        
        Returns:
            Dictionary with system stats
        """
        with get_db_session() as session:
            stats = {
                "products": {
                    "total": session.query(Product).count(),
                    "active": session.query(Product).filter(Product.is_active == True).count(),
                    "inactive": session.query(Product).filter(Product.is_active == False).count(),
                },
                "price_checks": {
                    "total": session.query(PriceHistory).count(),
                    "today": session.query(PriceHistory).filter(
                        PriceHistory.checked_at >= datetime.now().date()
                    ).count(),
                },
                "alerts": {
                    "total": session.query(PriceAlert).count(),
                    "pending": session.query(PriceAlert).filter(
                        PriceAlert.notification_status == "pending"
                    ).count(),
                    "sent": session.query(PriceAlert).filter(
                        PriceAlert.notification_status == "sent"
                    ).count(),
                },
                "current_deals": len(self.get_current_deals(limit=100))
            }
            
            return stats
    
    def _perform_initial_check(self, product: Product) -> None:
        """
        Perform initial price check for a newly added product
        
        Args:
            product: Product instance to check
        """
        try:
            # Schedule immediate price check
            asyncio.create_task(self._async_initial_check(product))
            
        except Exception as e:
            logger.error(f"Failed to schedule initial check for {product.name}: {e}")
    
    async def _async_initial_check(self, product: Product) -> None:
        """
        Async initial price check
        
        Args:
            product: Product to check
        """
        try:
            # Small delay to ensure database transaction is committed
            await asyncio.sleep(1)
            
            # Perform price check
            price_record = self.price_monitor.check_single_product(product)
            
            if price_record:
                logger.info(f"Initial price check completed for {product.name}: ${price_record.price}")
            else:
                logger.warning(f"Initial price check failed for {product.name}")
                
        except Exception as e:
            logger.error(f"Async initial check failed for {product.name}: {e}")


# Global tracker instance
tracker = PriceTracker()
