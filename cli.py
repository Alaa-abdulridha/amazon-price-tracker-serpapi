#!/usr/bin/env python3
"""
Amazon Price Tracker CLI
Command-line interface for managing price tracking

Author: Alaa Abdulridha
Company: SerpApi, LLC
Email: alaa@serpapi.com
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from amazontracker.core.tracker import PriceTracker
from amazontracker.utils.config import settings
from amazontracker.database.connection import init_database
from amazontracker.services.price_monitor import PriceMonitor
from amazontracker.notifications.manager import NotificationManager


async def add_product(args):
    """Add a new product to track"""
    try:
        tracker = PriceTracker()
        
        # Add product with provided parameters
        result = tracker.add_product(
            name=args.query,
            search_query=args.query,
            target_price=args.target_price,
            check_interval=args.interval or "1h"
        )
        
        if result:
            print(f"✅ Product added successfully!")
            print(f"Product ID: {result.id}")
            print(f"Name: {result.name}")
            print(f"Target Price: ${result.target_price:.2f}")
            print(f"Search Query: {result.search_query}")
        else:
            print("❌ Failed to add product")
            
    except Exception as e:
        print(f"❌ Error adding product: {e}")


async def list_products(args):
    """List all tracked products"""
    try:
        tracker = PriceTracker()
        products = tracker.get_products()
        
        if not products:
            print("No products are currently being tracked.")
            return
        
        print(f"\n📦 Tracked Products ({len(products)} total):")
        print("-" * 80)
        
        for product in products:
            status_emoji = "✅" if product.is_active else "⏸️"
            print(f"{status_emoji} {product.name[:50]}{'...' if len(product.name) > 50 else ''}")
            print(f"   ID: {product.id}")
            print(f"   Target: ${product.target_price:.2f} | Interval: {product.check_interval}")
            print(f"   Active: {product.is_active} | Last Check: {product.last_checked_at or 'Never'}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing products: {e}")


async def check_prices(args):
    """Check prices for all products or specific product"""
    try:
        tracker = PriceTracker()
        
        if args.product_id:
            # Check specific product
            result = tracker.check_product_price(args.product_id)
            if result:
                print(f"✅ Price check completed for product {args.product_id}")
                print(f"Current Price: ${result.price:.2f}")
            else:
                print(f"❌ Failed to check price for product {args.product_id}")
        else:
            # Check all products
            products = tracker.get_products(active_only=True)
            results = []
            for product in products:
                result = tracker.check_product_price(product.id)
                if result:
                    results.append(result)
            
            print(f"✅ Checked {len(results)} products")
                
    except Exception as e:
        print(f"❌ Error checking prices: {e}")


async def start_monitoring(args):
    """Start the price monitoring service"""
    try:
        print("🚀 Starting Amazon Price Tracker monitoring service...")
        
        # Initialize database
        await init_database()
        print("✅ Database initialized")
        
        # Start price monitor
        monitor = PriceMonitor()
        await monitor.start()
        print("✅ Price monitoring started")
        
        print("\n📊 Monitoring is now running. Press Ctrl+C to stop.")
        print(f"🔍 Check interval: {settings.default_check_interval}")
        print(f"📧 Email notifications: {'Enabled' if settings.email_enabled else 'Disabled'}")
        print(f"💬 Slack notifications: {'Enabled' if settings.slack_enabled else 'Disabled'}")
        print(f"🖥️ Desktop notifications: {'Enabled' if settings.desktop_notifications_enabled else 'Disabled'}")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring service...")
            await monitor.stop()
            print("✅ Monitoring service stopped")
            
    except Exception as e:
        print(f"❌ Error starting monitoring: {e}")


async def test_notifications(args):
    """Test notification systems"""
    try:
        print("🧪 Testing notification systems...")
        
        notification_manager = NotificationManager()
        
        # Test each notification type
        if args.type == "all" or args.type == "email":
            if notification_manager.email_sender:
                print("📧 Testing email notification...")
                success = await notification_manager.send_test_notification("email")
                print(f"   Email: {'✅ Success' if success else '❌ Failed'}")
            else:
                print("   Email: ⏭️ Disabled")
        
        if args.type == "all" or args.type == "slack":
            if notification_manager.slack_sender:
                print("💬 Testing Slack notification...")
                success = await notification_manager.send_test_notification("slack")
                print(f"   Slack: {'✅ Success' if success else '❌ Failed'}")
            else:
                print("   Slack: ⏭️ Disabled")
        
        if args.type == "all" or args.type == "desktop":
            if notification_manager.desktop_notifier:
                print("🖥️ Testing desktop notification...")
                success = await notification_manager.send_test_notification("desktop")
                print(f"   Desktop: {'✅ Success' if success else '❌ Failed'}")
            else:
                print("   Desktop: ⏭️ Disabled")
                
    except Exception as e:
        print(f"❌ Error testing notifications: {e}")


async def show_stats(args):
    """Show tracking statistics"""
    try:
        tracker = PriceTracker()
        
        # Get basic stats
        products = tracker.get_products(active_only=False)
        active_products = [p for p in products if p.is_active]
        
        print("📊 Amazon Price Tracker Statistics")
        print("=" * 40)
        print(f"Total Products: {len(products)}")
        print(f"Active Products: {len(active_products)}")
        print(f"Inactive Products: {len(products) - len(active_products)}")
        
        # Show deals if any
        deals = tracker.get_current_deals()
        if deals:
            print(f"\n🔥 Current Deals ({len(deals)}):")
            for deal in deals[:5]:  # Show top 5 deals
                print(f"  • {deal.name[:40]}{'...' if len(deal.name) > 40 else ''}")
                print(f"    Target: ${deal.target_price:.2f}")
        
        # Notification stats
        notification_manager = NotificationManager()
        notif_stats = notification_manager.get_notification_stats()
        if notif_stats:
            print(f"\n📨 Notification Statistics:")
            print(f"  Total Sent: {notif_stats.get('sent', 0)}")
            print(f"  Success Rate: {notif_stats.get('success_rate', 0):.1f}%")
            
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Amazon Price Tracker - AI-powered price monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add "iPhone 15 Pro" --target-price 999.99
  %(prog)s add --asin B0B123456 --target-price 49.99
  %(prog)s list
  %(prog)s check
  %(prog)s check --product-id abc123
  %(prog)s monitor
  %(prog)s test-notifications
  %(prog)s stats
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add product command
    add_parser = subparsers.add_parser("add", help="Add a product to track")
    add_parser.add_argument("query", nargs="?", help="Product search query")
    add_parser.add_argument("--asin", help="Amazon ASIN (alternative to search query)")
    add_parser.add_argument("--target-price", type=float, required=True, help="Target price for alerts")
    add_parser.add_argument("--interval", help="Check interval (e.g., 30m, 1h, 6h)")
    add_parser.set_defaults(func=add_product)
    
    # List products command
    list_parser = subparsers.add_parser("list", help="List all tracked products")
    list_parser.set_defaults(func=list_products)
    
    # Check prices command
    check_parser = subparsers.add_parser("check", help="Check product prices")
    check_parser.add_argument("--product-id", help="Check specific product by ID")
    check_parser.set_defaults(func=check_prices)
    
    # Start monitoring command
    monitor_parser = subparsers.add_parser("monitor", help="Start monitoring service")
    monitor_parser.set_defaults(func=start_monitoring)
    
    # Test notifications command
    test_parser = subparsers.add_parser("test-notifications", help="Test notification systems")
    test_parser.add_argument("--type", choices=["all", "email", "slack", "desktop"], 
                           default="all", help="Notification type to test")
    test_parser.set_defaults(func=test_notifications)
    
    # Statistics command
    stats_parser = subparsers.add_parser("stats", help="Show tracking statistics")
    stats_parser.set_defaults(func=show_stats)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the selected command
    try:
        asyncio.run(args.func(args))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
