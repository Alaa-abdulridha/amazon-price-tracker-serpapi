"""
Amazon Price Tracker - Advanced AI-Driven Price Monitoring System

This package provides comprehensive Amazon price tracking capabilities with:
- AI-powered price prediction and trend analysis
- Multi-channel notification system
- Advanced web dashboard with real-time charts
- Robust scheduling and monitoring
- Comprehensive logging and error handling
"""

__version__ = "1.0.0"
__author__ = "Alaa Abdulridha"
__email__ = "alaa@serpapi.com"

from .core.tracker import PriceTracker
from .services.price_monitor import PriceMonitor
from .ai.prediction import PricePredictionEngine
from .notifications.manager import NotificationManager

__all__ = [
    "PriceTracker",
    "PriceMonitor", 
    "PricePredictionEngine",
    "NotificationManager"
]
