#!/usr/bin/env python3
"""
Amazon Price Tracker - Main Entry Point
A powerful Amazon price tracking application powered by SerpApi

Author: Alaa Abdulridha
Company: SerpApi, LLC
Email: alaa@serpapi.com
GitHub: https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi

Run this script to start the application
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Amazon Price Tracker - AI-powered price monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available modes:
  web       - Start web dashboard (default)
  cli       - Run command-line interface
  monitor   - Start background monitoring only
  setup     - Initial setup and configuration

Examples:
  python main.py                    # Start web dashboard
  python main.py web --port 8080    # Start web on custom port
  python main.py cli add "iPhone 15" --target-price 999.99
  python main.py monitor            # Start monitoring daemon
  python main.py setup              # Run initial setup
        """
    )
    
    parser.add_argument(
        "mode",
        nargs="?",
        default="web",
        choices=["web", "cli", "monitor", "setup"],
        help="Application mode to run"
    )
    
    # Web mode arguments
    parser.add_argument("--host", default="0.0.0.0", help="Web server host")
    parser.add_argument("--port", type=int, default=8000, help="Web server port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args, remaining = parser.parse_known_args()
    
    if args.mode == "web":
        start_web_server(args)
    elif args.mode == "cli":
        run_cli(remaining)
    elif args.mode == "monitor":
        start_monitoring()
    elif args.mode == "setup":
        run_setup()
    else:
        parser.print_help()


def start_web_server(args):
    """Start the web dashboard"""
    print("🚀 Starting Amazon Price Tracker Web Dashboard...")
    print(f"📊 Dashboard will be available at: http://{args.host}:{args.port}")
    print("📝 API documentation at: http://{args.host}:{args.port}/docs")
    print("🛑 Press Ctrl+C to stop\n")
    
    try:
        import uvicorn
        from amazontracker.web.app import app
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            access_log=True
        )
    except ImportError:
        print("❌ Error: uvicorn not installed. Run: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        sys.exit(1)


def run_cli(remaining_args):
    """Run the CLI interface"""
    try:
        # Import and run CLI
        from cli import main as cli_main
        
        # Update sys.argv to include remaining arguments
        sys.argv = ["cli.py"] + remaining_args
        cli_main()
        
    except ImportError as e:
        print(f"❌ Error importing CLI: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running CLI: {e}")
        sys.exit(1)


def start_monitoring():
    """Start background monitoring service"""
    print("🔍 Starting Amazon Price Tracker Monitoring Service...")
    print("📊 Monitoring will run in the background")
    print("🛑 Press Ctrl+C to stop\n")
    
    async def run_monitor():
        try:
            from amazontracker.services.price_monitor import PriceMonitor
            from amazontracker.database.connection import init_database
            
            # Initialize database
            await init_database()
            print("✅ Database initialized")
            
            # Start monitoring
            monitor = PriceMonitor()
            await monitor.start()
            print("✅ Monitoring service started")
            
            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping monitoring...")
                await monitor.stop()
                print("✅ Monitoring stopped")
                
        except Exception as e:
            print(f"❌ Error in monitoring: {e}")
            sys.exit(1)
    
    try:
        asyncio.run(run_monitor())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


def run_setup():
    """Run initial setup and configuration"""
    print("⚙️  Amazon Price Tracker Setup")
    print("=" * 40)
    
    try:
        from amazontracker.utils.config import settings
        from amazontracker.database.connection import init_database
        
        # Check configuration
        print("🔍 Checking configuration...")
        
        # Validate SerpAPI key
        if not settings.serpapi_key or len(settings.serpapi_key) < 10:
            print("❌ SerpAPI key not configured")
            print("💡 Please set SERPAPI_KEY in your .env file")
            print("   Get your key from: https://serpapi.com/")
            print()
        else:
            print("✅ SerpAPI key configured")
        
        # Check database
        print("🗄️  Setting up database...")
        init_database()
        print("✅ Database initialized")
        
        # Test notifications
        print("\n📧 Testing notification systems...")
        
        if settings.email_enabled:
            print(f"   Email: Enabled ({settings.email_username})")
        else:
            print("   Email: Disabled")
            print("   💡 Set EMAIL_ENABLED=true and configure SMTP settings")
        
        if settings.slack_enabled:
            print("   Slack: Enabled")
        else:
            print("   Slack: Disabled")
            print("   💡 Set SLACK_ENABLED=true and SLACK_WEBHOOK_URL")
        
        if settings.desktop_notifications_enabled:
            print("   Desktop: Enabled")
        else:
            print("   Desktop: Disabled")
        
        print("\n✅ Setup completed!")
        print("🚀 You can now run:")
        print("   python main.py web     # Start web dashboard")
        print("   python main.py cli     # Use command line")
        print("   python main.py monitor # Start monitoring")
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        sys.exit(1)


def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
        ("requests", "requests"),
        ("aiohttp", "aiohttp"),
        ("apscheduler", "apscheduler"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("sklearn", "scikit-learn")
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
        print("   OR")
        print(f"   pip install {' '.join(missing_packages)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Check requirements first
        check_requirements()
        
        # Run main function
        main()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
