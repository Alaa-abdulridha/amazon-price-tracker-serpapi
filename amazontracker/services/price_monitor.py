"""
Price monitoring service
Handles scheduled price checks and monitoring logic
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from ..database.models import Product, PriceHistory, PriceAlert
from ..database.connection import get_db_session
from ..services.serpapi_client import SerpAPIClient, SerpAPIError
from ..notifications.manager import NotificationManager
from ..utils.config import settings, get_interval_seconds

logger = logging.getLogger(__name__)


class PriceMonitor:
    """
    Service for monitoring product prices and triggering alerts
    """
    
    def __init__(self):
        """Initialize the price monitor"""
        self.scheduler = AsyncIOScheduler()
        self.serpapi_client = SerpAPIClient(
            api_key=settings.serpapi_key,
            timeout=settings.serpapi_timeout,
            retries=settings.serpapi_retries,
            retry_delay=settings.serpapi_retry_delay
        )
        self.notification_manager = NotificationManager()
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_checks)
        
        # Performance metrics
        self.metrics = {
            'checks_completed': 0,
            'checks_failed': 0,
            'alerts_sent': 0,
            'last_check_time': None,
            'average_check_time': 0.0
        }
        
        logger.info("Price monitor initialized")
    
    def start(self):
        """Start the price monitoring service"""
        if self.is_running:
            logger.warning("Price monitor is already running")
            return
        
        try:
            # Add scheduled jobs
            self._setup_monitoring_jobs()
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Price monitoring service started")
            
        except Exception as e:
            logger.error(f"Failed to start price monitoring service: {e}")
            raise
    
    def stop(self):
        """Stop the price monitoring service"""
        if not self.is_running:
            logger.warning("Price monitor is not running")
            return
        
        try:
            # Shutdown scheduler
            self.scheduler.shutdown(wait=True)
            
            # Shutdown thread executor
            self.executor.shutdown(wait=True)
            
            self.is_running = False
            
            logger.info("Price monitoring service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping price monitoring service: {e}")
    
    def _setup_monitoring_jobs(self):
        """Setup scheduled monitoring jobs based on product intervals"""
        # Get all active products and group by check interval
        with get_db_session() as session:
            active_products = session.query(Product).filter(
                Product.is_active == True
            ).all()
        
        # Group products by interval
        interval_groups = {}
        for product in active_products:
            interval = product.check_interval
            if interval not in interval_groups:
                interval_groups[interval] = []
            interval_groups[interval].append(product.id)
        
        # Create scheduled jobs for each interval
        for interval, product_ids in interval_groups.items():
            interval_seconds = get_interval_seconds(interval)
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._check_products_batch,
                trigger=IntervalTrigger(seconds=interval_seconds),
                args=[product_ids],
                id=f"price_check_{interval}",
                name=f"Price check every {interval}",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5 minutes grace time
            )
            
            logger.info(f"Scheduled price checks every {interval} for {len(product_ids)} products")
        
        # Add maintenance job (runs daily)
        self.scheduler.add_job(
            func=self._maintenance_job,
            trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
            id="daily_maintenance",
            name="Daily maintenance job",
            max_instances=1
        )
        
        # Add metrics collection job (runs every 5 minutes)
        self.scheduler.add_job(
            func=self._collect_metrics,
            trigger=IntervalTrigger(minutes=5),
            id="metrics_collection",
            name="Metrics collection",
            max_instances=1
        )
    
    async def _check_products_batch(self, product_ids: List[str]):
        """
        Check prices for a batch of products
        
        Args:
            product_ids: List of product IDs to check
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting price check batch for {len(product_ids)} products")
            
            # Get products from database
            with get_db_session() as session:
                products = session.query(Product).filter(
                    Product.id.in_(product_ids),
                    Product.is_active == True
                ).all()
            
            if not products:
                logger.warning("No active products found for batch check")
                return
            
            # Execute price checks concurrently
            tasks = []
            for product in products:
                task = asyncio.create_task(self._check_single_product_async(product))
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_checks = 0
            failed_checks = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_checks += 1
                    logger.error(f"Price check failed for product {products[i].name}: {result}")
                else:
                    successful_checks += 1
                    if result:  # Price record created
                        # Check for alerts
                        await self._check_price_alerts(products[i], result)
            
            # Update metrics
            self.metrics['checks_completed'] += successful_checks
            self.metrics['checks_failed'] += failed_checks
            self.metrics['last_check_time'] = datetime.now(timezone.utc)
            
            elapsed_time = time.time() - start_time
            self.metrics['average_check_time'] = (
                self.metrics['average_check_time'] * 0.9 + elapsed_time * 0.1
            )
            
            logger.info(
                f"Batch price check completed: {successful_checks} successful, "
                f"{failed_checks} failed in {elapsed_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Error in batch price check: {e}")
    
    async def _check_single_product_async(self, product: Product) -> Optional[PriceHistory]:
        """
        Async wrapper for single product price check
        
        Args:
            product: Product to check
            
        Returns:
            PriceHistory record if successful, None otherwise
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Run the synchronous price check in thread executor
            price_record = await loop.run_in_executor(
                self.executor,
                self.check_single_product,
                product
            )
            
            return price_record
            
        except Exception as e:
            logger.error(f"Async price check failed for {product.name}: {e}")
            return None
    
    def check_single_product(self, product: Product) -> Optional[PriceHistory]:
        """
        Check price for a single product
        
        Args:
            product: Product to check
            
        Returns:
            PriceHistory record if successful, None otherwise
        """
        try:
            logger.debug(f"Checking price for: {product.name}")
            
            # Search for product using SerpAPI
            if product.asin:
                # If we have ASIN, search by ASIN for accuracy
                search_result = self.serpapi_client.get_product_by_asin(product.asin)
            else:
                # Search by query and find best match
                search_result = self.serpapi_client.get_best_price_match(
                    search_query=product.search_query,
                    max_price=product.max_price
                )
            
            if not search_result:
                logger.warning(f"No search results found for product: {product.name}")
                return None
            
            # Extract price information
            current_price = search_result.get('extracted_price')
            if not current_price:
                logger.warning(f"No price found for product: {product.name}")
                return None
            
            # Create price history record
            with get_db_session() as session:
                price_record = PriceHistory(
                    product_id=product.id,
                    price=current_price,
                    old_price=search_result.get('extracted_old_price'),
                    price_unit=search_result.get('price_unit'),
                    extracted_price_unit=search_result.get('extracted_price_unit'),
                    title=search_result.get('title'),
                    rating=search_result.get('rating'),
                    reviews_count=search_result.get('reviews_count'),
                    availability=search_result.get('availability'),
                    is_deal=search_result.get('is_deal', False),
                    discount_percentage=search_result.get('discount_percentage'),
                    savings_amount=search_result.get('savings_amount'),
                    prime_eligible=search_result.get('prime_eligible', False),
                    checked_at=datetime.now(timezone.utc),
                    raw_data=search_result.get('raw_data')
                )
                
                session.add(price_record)
                
                # Update product metadata
                product_obj = session.query(Product).filter(Product.id == product.id).first()
                if product_obj:
                    product_obj.last_checked_at = datetime.now(timezone.utc)
                    
                    # Update ASIN if we found one
                    if not product_obj.asin and search_result.get('asin'):
                        product_obj.asin = search_result['asin']
                    
                    # Update image URL if we found one
                    if not product_obj.image_url and search_result.get('image_url'):
                        product_obj.image_url = search_result['image_url']
                    
                    # Update Amazon URL if we found one
                    if not product_obj.amazon_url and search_result.get('link'):
                        product_obj.amazon_url = search_result['link']
                
                session.commit()
                session.refresh(price_record)
                
                logger.info(f"Price check completed for {product.name}: ${current_price}")
                return price_record
                
        except SerpAPIError as e:
            logger.error(f"SerpAPI error checking {product.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking {product.name}: {e}")
            return None
    
    async def _check_price_alerts(self, product: Product, price_record: PriceHistory):
        """
        Check if price alerts should be triggered
        
        Args:
            product: Product that was checked
            price_record: Latest price record
        """
        try:
            current_price = price_record.price
            alerts_to_send = []
            
            # Check target price alert
            if current_price <= product.target_price:
                alerts_to_send.append({
                    'type': 'target_reached',
                    'message': f"Target price reached for {product.name}!",
                    'details': {
                        'current_price': current_price,
                        'target_price': product.target_price,
                        'savings': product.target_price - current_price
                    }
                })
            
            # Check deal alert
            if price_record.is_deal and price_record.discount_percentage >= settings.deal_threshold_percentage:
                alerts_to_send.append({
                    'type': 'deal_found',
                    'message': f"Great deal found for {product.name}!",
                    'details': {
                        'current_price': current_price,
                        'old_price': price_record.old_price,
                        'discount_percentage': price_record.discount_percentage,
                        'savings_amount': price_record.savings_amount
                    }
                })
            
            # Check significant price drop
            with get_db_session() as session:
                # Get previous price record
                previous_record = session.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id,
                    PriceHistory.checked_at < price_record.checked_at
                ).order_by(PriceHistory.checked_at.desc()).first()
                
                if previous_record:
                    price_change_pct = ((previous_record.price - current_price) / previous_record.price) * 100
                    
                    if price_change_pct >= settings.price_change_threshold:
                        alerts_to_send.append({
                            'type': 'price_drop',
                            'message': f"Significant price drop for {product.name}!",
                            'details': {
                                'current_price': current_price,
                                'previous_price': previous_record.price,
                                'price_change_percentage': price_change_pct,
                                'savings': previous_record.price - current_price
                            }
                        })
            
            # Send alerts
            for alert_data in alerts_to_send:
                await self._send_price_alert(product, price_record, alert_data)
                
        except Exception as e:
            logger.error(f"Error checking price alerts for {product.name}: {e}")
    
    async def _send_price_alert(
        self,
        product: Product,
        price_record: PriceHistory,
        alert_data: Dict[str, Any]
    ):
        """
        Send price alert notifications
        
        Args:
            product: Product for alert
            price_record: Price record that triggered alert
            alert_data: Alert information
        """
        try:
            # Create alert record
            with get_db_session() as session:
                alert = PriceAlert(
                    product_id=product.id,
                    alert_type=alert_data['type'],
                    trigger_price=price_record.price,
                    previous_price=alert_data['details'].get('previous_price'),
                    savings_amount=alert_data['details'].get('savings', 0),
                    notification_channels=[],
                    notification_status='pending',
                    created_at=datetime.now(timezone.utc)
                )
                
                session.add(alert)
                session.commit()
                session.refresh(alert)
            
            # Prepare notification data
            notification_data = {
                'product': product,
                'price_record': price_record,
                'alert': alert,
                'alert_data': alert_data
            }
            
            # Send notifications based on product settings
            notification_success = True
            channels_used = []
            
            if product.email_notifications:
                try:
                    await self.notification_manager.send_email_alert(notification_data)
                    channels_used.append('email')
                except Exception as e:
                    logger.error(f"Failed to send email alert: {e}")
                    notification_success = False
            
            if product.slack_notifications:
                try:
                    await self.notification_manager.send_slack_alert(notification_data)
                    channels_used.append('slack')
                except Exception as e:
                    logger.error(f"Failed to send Slack alert: {e}")
                    notification_success = False
            
            if product.desktop_notifications:
                try:
                    await self.notification_manager.send_desktop_alert(notification_data)
                    channels_used.append('desktop')
                except Exception as e:
                    logger.error(f"Failed to send desktop alert: {e}")
                    notification_success = False
            
            # Update alert record with results
            with get_db_session() as session:
                alert_obj = session.query(PriceAlert).filter(PriceAlert.id == alert.id).first()
                if alert_obj:
                    alert_obj.notification_channels = channels_used
                    alert_obj.notification_status = 'sent' if notification_success else 'failed'
                    alert_obj.sent_at = datetime.now(timezone.utc) if notification_success else None
                    session.commit()
            
            if notification_success:
                self.metrics['alerts_sent'] += 1
                logger.info(f"Alert sent for {product.name}: {alert_data['type']}")
            else:
                logger.error(f"Failed to send alert for {product.name}: {alert_data['type']}")
                
        except Exception as e:
            logger.error(f"Error sending price alert for {product.name}: {e}")
    
    async def _maintenance_job(self):
        """Daily maintenance tasks"""
        try:
            logger.info("Running daily maintenance job")
            
            # Clean up old price history (keep last 90 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            
            with get_db_session() as session:
                deleted_count = session.query(PriceHistory).filter(
                    PriceHistory.checked_at < cutoff_date
                ).delete()
                
                session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old price history records")
            
            # Update product priorities based on activity
            await self._update_product_priorities()
            
            # Generate daily metrics report
            await self._generate_daily_report()
            
            logger.info("Daily maintenance job completed")
            
        except Exception as e:
            logger.error(f"Error in daily maintenance job: {e}")
    
    async def _collect_metrics(self):
        """Collect and store system metrics"""
        try:
            # This would typically store metrics to database
            # For now, just log current metrics
            logger.debug(f"Metrics: {self.metrics}")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    async def _update_product_priorities(self):
        """Update product priorities based on activity and user engagement"""
        # Implementation for dynamic priority adjustment
        pass
    
    async def _generate_daily_report(self):
        """Generate daily monitoring report"""
        # Implementation for daily report generation
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current monitoring metrics"""
        return self.metrics.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'scheduler_running': self.scheduler.running if self.scheduler else False,
            'jobs_count': len(self.scheduler.get_jobs()) if self.scheduler else 0,
            'metrics': self.get_metrics()
        }
