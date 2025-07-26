"""
FastAPI web dashboard for Amazon Price Tracker
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import asyncio
import json
from datetime import datetime, timedelta

from ..core.tracker import PriceTracker
from ..services.price_monitor import PriceMonitor
from ..notifications.manager import NotificationManager
from ..ai.prediction import PricePredictionEngine
from ..utils.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Amazon Price Tracker",
    description="AI-powered Amazon price monitoring and alerts",
    version="1.0.0"
)

# Templates and static files
templates = Jinja2Templates(directory="templates")

# Global instances
tracker = PriceTracker()
price_monitor = PriceMonitor()
notification_manager = NotificationManager()
prediction_engine = PricePredictionEngine()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        # Get dashboard data
        products = tracker.get_products(active_only=False)
        active_products = [p for p in products if p.is_active]
        deals = tracker.get_current_deals()
        
        # Get notification stats
        notif_stats = notification_manager.get_notification_stats()
        
        dashboard_data = {
            "total_products": len(products),
            "active_products": len(active_products),
            "current_deals": len(deals),
            "notifications_sent": notif_stats.get("sent", 0),
            "recent_deals": deals[:5],  # Top 5 deals
            "recent_products": products[:10]  # Last 10 products
        }
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "data": dashboard_data,
                "settings": settings
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products")
async def get_products():
    """Get all tracked products"""
    try:
        products = tracker.get_products()
        return {
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "target_price": p.target_price,
                    "current_price": getattr(p, 'current_price', None),
                    "is_active": p.is_active,
                    "check_interval": p.check_interval,
                    "last_checked": p.last_checked_at.isoformat() if p.last_checked_at else None,
                    "amazon_url": getattr(p, 'amazon_url', None),
                    "search_query": p.search_query
                }
                for p in products
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products")
async def add_product(
    search_query: Optional[str] = Form(None),
    asin: Optional[str] = Form(None),
    target_price: float = Form(...),
    check_interval: str = Form("1h")
):
    """Add a new product to track"""
    try:
        if not search_query and not asin:
            raise HTTPException(status_code=400, detail="Either search_query or asin must be provided")
        
        result = tracker.add_product(
            name=search_query or f"Product-{asin}",
            search_query=search_query or asin,
            target_price=target_price,
            check_interval=check_interval
        )
        
        if result:
            return {"success": True, "product": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to add product")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/products/{product_id}")
async def remove_product(product_id: str):
    """Remove a tracked product"""
    try:
        success = tracker.remove_product(product_id)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products/{product_id}/check")
async def check_product_price(product_id: str):
    """Check price for a specific product"""
    try:
        result = await tracker.check_product_price(product_id)
        if result:
            return {"success": True, "result": result}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/check-all")
async def check_all_prices():
    """Check prices for all products"""
    try:
        results = await tracker.check_all_prices()
        return {
            "success": True,
            "checked": len(results),
            "alerts": sum(len(r.get('alerts', [])) for r in results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/deals")
async def get_current_deals():
    """Get current deals"""
    try:
        deals = await tracker.get_current_deals()
        return {"deals": deals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}/history")
async def get_price_history(product_id: str, days: int = 30):
    """Get price history for a product"""
    try:
        history = await tracker.get_price_history(product_id, days)
        return {
            "product_id": product_id,
            "history": [
                {
                    "price": h.price,
                    "old_price": h.old_price,
                    "discount_percentage": h.discount_percentage,
                    "checked_at": h.checked_at.isoformat(),
                    "rating": h.rating,
                    "reviews_count": h.reviews_count
                }
                for h in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}/predict")
async def predict_price(product_id: str, days_ahead: int = 7):
    """Get AI price prediction for a product"""
    try:
        prediction = await prediction_engine.predict_price(product_id, days_ahead)
        if prediction:
            return {"success": True, "prediction": prediction}
        else:
            return {"success": False, "error": "Insufficient data for prediction"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}/analysis")
async def get_price_analysis(product_id: str, period_days: int = 30):
    """Get AI price analysis for a product"""
    try:
        analysis = await prediction_engine.analyze_price_trends(product_id, period_days)
        return {"success": True, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/status")
async def get_monitoring_status():
    """Get monitoring service status"""
    try:
        return {
            "running": price_monitor.is_running(),
            "next_check": price_monitor.get_next_check_time(),
            "total_products": len(tracker.get_products(active_only=False)),
            "active_products": len([p for p in tracker.get_products(active_only=False) if p.is_active])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitoring/start")
async def start_monitoring():
    """Start the monitoring service"""
    try:
        await price_monitor.start()
        return {"success": True, "message": "Monitoring started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitoring/stop")
async def stop_monitoring():
    """Stop the monitoring service"""
    try:
        await price_monitor.stop()
        return {"success": True, "message": "Monitoring stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notifications/test")
async def test_notifications(notification_type: str = Form("all")):
    """Test notification systems"""
    try:
        results = {}
        
        if notification_type in ["all", "email"]:
            results["email"] = await notification_manager.send_test_notification("email")
        
        if notification_type in ["all", "slack"]:
            results["slack"] = await notification_manager.send_test_notification("slack")
        
        if notification_type in ["all", "desktop"]:
            results["desktop"] = await notification_manager.send_test_notification("desktop")
        
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_statistics():
    """Get application statistics"""
    try:
        products = tracker.get_products(active_only=False)
        deals = tracker.get_current_deals()
        notif_stats = notification_manager.get_notification_stats()
        
        return {
            "products": {
                "total": len(products),
                "active": len([p for p in products if p.is_active]),
                "inactive": len([p for p in products if p.status != "active"])
            },
            "deals": {
                "current": len(deals),
                "total_savings": sum(d.get('savings', 0) for d in deals)
            },
            "notifications": notif_stats,
            "monitoring": {
                "running": price_monitor.is_running(),
                "next_check": price_monitor.get_next_check_time()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/price-trends")
async def get_price_trends_data():
    """Get data for price trends chart"""
    try:
        # Get all products with recent price history
        products = tracker.get_products(active_only=False)
        chart_data = []
        
        for product in products[:10]:  # Limit to 10 products for performance
            history = tracker.get_price_history(product.id, 30)
            if history:
                product_data = {
                    "name": product.name[:20] + "..." if len(product.name) > 20 else product.name,
                    "data": [
                        {
                            "x": h.checked_at.isoformat(),
                            "y": float(h.price)
                        }
                        for h in history[-30:]  # Last 30 data points
                    ]
                }
                chart_data.append(product_data)
        
        return {"chart_data": chart_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/deals-distribution")
async def get_deals_distribution_data():
    """Get data for deals distribution chart"""
    try:
        deals = await tracker.get_current_deals()
        
        # Group deals by savings range
        savings_ranges = {
            "0-10": 0,
            "10-25": 0,
            "25-50": 0,
            "50-100": 0,
            "100+": 0
        }
        
        for deal in deals:
            savings = deal.get('savings', 0)
            if savings < 10:
                savings_ranges["0-10"] += 1
            elif savings < 25:
                savings_ranges["10-25"] += 1
            elif savings < 50:
                savings_ranges["25-50"] += 1
            elif savings < 100:
                savings_ranges["50-100"] += 1
            else:
                savings_ranges["100+"] += 1
        
        return {
            "chart_data": {
                "labels": list(savings_ranges.keys()),
                "values": list(savings_ranges.values())
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"error": "Not found"}
        )
    else:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    else:
        return templates.TemplateResponse(
            "500.html",
            {"request": request},
            status_code=500
        )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Initialize database
        from ..database.connection import init_database
        init_database()
        
        # Start monitoring if enabled
        if settings.auto_start_monitoring:
            await price_monitor.start()
            
    except Exception as e:
        print(f"Error during startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        # Stop monitoring
        if price_monitor.is_running():
            await price_monitor.stop()
            
    except Exception as e:
        print(f"Error during shutdown: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1
    )
