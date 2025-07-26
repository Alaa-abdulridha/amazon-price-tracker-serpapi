"""
Database models for Amazon Price Tracker
Defines all SQLAlchemy ORM models for the application
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
import uuid


Base = declarative_base()


class Product(Base):
    """Product model for tracking Amazon products"""
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    search_query = Column(String(500), nullable=False)
    asin = Column(String(20), nullable=True, index=True)
    amazon_url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    
    # Price thresholds
    target_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=True)
    min_price = Column(Float, nullable=True)
    
    # Monitoring settings
    check_interval = Column(String(10), default="1h")  # 5m, 15m, 30m, 1h, 2h, 6h, 12h, 24h
    is_active = Column(Boolean, default=True)
    priority = Column(String(10), default="normal")  # low, normal, high
    
    # Notification settings
    email_notifications = Column(Boolean, default=True)
    slack_notifications = Column(Boolean, default=False)
    desktop_notifications = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Category and tags
    category = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)  # JSON string of tags
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("PriceAlert", back_populates="product", cascade="all, delete-orphan")
    predictions = relationship("PricePrediction", back_populates="product", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_search_query', 'search_query'),
        Index('idx_product_active_priority', 'is_active', 'priority'),
        Index('idx_product_last_checked', 'last_checked_at'),
    )
    
    def __repr__(self):
        return f"<Product(id='{self.id}', name='{self.name}', target_price={self.target_price})>"


class PriceHistory(Base):
    """Price history model for tracking price changes over time"""
    __tablename__ = "price_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    
    # Price data
    price = Column(Float, nullable=False)
    old_price = Column(Float, nullable=True)
    price_unit = Column(String(20), nullable=True)  # per oz, per count, etc.
    extracted_price_unit = Column(Float, nullable=True)
    
    # Product details at time of check
    title = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=True)
    availability = Column(String(100), nullable=True)
    seller = Column(String(255), nullable=True)
    
    # Deal information
    is_deal = Column(Boolean, default=False)
    discount_percentage = Column(Float, nullable=True)
    savings_amount = Column(Float, nullable=True)
    prime_eligible = Column(Boolean, default=False)
    
    # Metadata
    checked_at = Column(DateTime(timezone=True), default=func.now())
    source = Column(String(50), default="serpapi")
    
    # Raw data
    raw_data = Column(Text, nullable=True)  # JSON string of raw API response
    
    # Relationship
    product = relationship("Product", back_populates="price_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_price_history_product_date', 'product_id', 'checked_at'),
        Index('idx_price_history_price', 'price'),
        Index('idx_price_history_deals', 'is_deal', 'checked_at'),
    )
    
    def __repr__(self):
        return f"<PriceHistory(product_id='{self.product_id}', price={self.price}, checked_at='{self.checked_at}')>"


class PriceAlert(Base):
    """Price alert model for tracking when alerts are sent"""
    __tablename__ = "price_alerts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # price_drop, target_reached, deal_found
    trigger_price = Column(Float, nullable=False)
    previous_price = Column(Float, nullable=True)
    savings_amount = Column(Float, nullable=True)
    
    # Notification details
    notification_channels = Column(Text, nullable=True)  # JSON list of channels used
    notification_status = Column(String(20), default="pending")  # pending, sent, failed
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    product = relationship("Product", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index('idx_alerts_product_type', 'product_id', 'alert_type'),
        Index('idx_alerts_status_created', 'notification_status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<PriceAlert(product_id='{self.product_id}', alert_type='{self.alert_type}', trigger_price={self.trigger_price})>"


class PricePrediction(Base):
    """Price prediction model for ML-generated price forecasts"""
    __tablename__ = "price_predictions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    
    # Prediction details
    predicted_price = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    prediction_horizon_days = Column(Integer, nullable=False)
    
    # Model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False)
    training_data_points = Column(Integer, nullable=False)
    
    # Prediction metadata
    created_at = Column(DateTime(timezone=True), default=func.now())
    is_accurate = Column(Boolean, nullable=True)  # Set after actual price is known
    actual_price = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    
    # Additional prediction data
    trend_direction = Column(String(10), nullable=True)  # up, down, stable
    volatility_score = Column(Float, nullable=True)
    seasonal_factor = Column(Float, nullable=True)
    
    # Relationship
    product = relationship("Product", back_populates="predictions")
    
    # Indexes
    __table_args__ = (
        Index('idx_predictions_product_date', 'product_id', 'prediction_date'),
        Index('idx_predictions_confidence', 'confidence_score'),
        Index('idx_predictions_accuracy', 'is_accurate', 'accuracy_score'),
    )
    
    def __repr__(self):
        return f"<PricePrediction(product_id='{self.product_id}', predicted_price={self.predicted_price}, confidence={self.confidence_score})>"


class SystemMetrics(Base):
    """System metrics model for monitoring application performance"""
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Metric details
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    
    # Categorization
    category = Column(String(50), nullable=False)  # api, database, notifications, predictions
    subcategory = Column(String(50), nullable=True)
    
    # Metadata
    recorded_at = Column(DateTime(timezone=True), default=func.now())
    tags = Column(Text, nullable=True)  # JSON string of additional tags
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_name_category', 'metric_name', 'category'),
        Index('idx_metrics_recorded_at', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<SystemMetrics(metric_name='{self.metric_name}', value={self.metric_value}, category='{self.category}')>"


class NotificationLog(Base):
    """Notification log model for tracking all sent notifications"""
    __tablename__ = "notification_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Notification details
    notification_type = Column(String(50), nullable=False)  # email, slack, desktop
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, sent, failed, bounced
    attempts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Related data
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    alert_id = Column(String, ForeignKey("price_alerts.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_logs_type_status', 'notification_type', 'status'),
        Index('idx_notification_logs_created_at', 'created_at'),
        Index('idx_notification_logs_product', 'product_id'),
    )
    
    def __repr__(self):
        return f"<NotificationLog(type='{self.notification_type}', recipient='{self.recipient}', status='{self.status}')>"


class APIUsage(Base):
    """API usage tracking model"""
    __tablename__ = "api_usage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # API details
    api_name = Column(String(50), nullable=False)  # serpapi, internal_api
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    
    # Usage metrics
    request_count = Column(Integer, default=1)
    response_time_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)
    
    # Cost tracking
    cost = Column(Float, nullable=True)
    credits_used = Column(Integer, nullable=True)
    
    # Time tracking
    recorded_date = Column(DateTime(timezone=True), default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_api_usage_name_date', 'api_name', 'recorded_date'),
        Index('idx_api_usage_status', 'status_code'),
    )
    
    def __repr__(self):
        return f"<APIUsage(api_name='{self.api_name}', request_count={self.request_count}, recorded_date='{self.recorded_date}')>"


# Database utility functions
def create_all_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """Drop all tables from the database"""
    Base.metadata.drop_all(bind=engine)


def get_table_names():
    """Get list of all table names"""
    return [table.name for table in Base.metadata.tables.values()]
