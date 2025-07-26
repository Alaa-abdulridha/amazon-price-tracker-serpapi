"""
Configuration management for Amazon Price Tracker
Handles environment variables, settings validation, and configuration loading
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import validator, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and type checking"""
    
    # SerpApi Configuration
    serpapi_key: str
    serpapi_timeout: int = 30
    serpapi_retries: int = 3
    serpapi_retry_delay: float = 1.0
    
    # Database Configuration
    database_url: str = "sqlite:///./amazontracker.db"
    
    # Notification Settings
    email_enabled: bool = True
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    
    desktop_notifications_enabled: bool = True
    
    # Monitoring Configuration
    default_check_interval: str = "1h"
    max_concurrent_checks: int = 5
    price_change_threshold: float = 5.0
    deal_threshold_percentage: float = 10.0
    
    # AI/ML Configuration
    ml_prediction_enabled: bool = True
    ml_model_update_interval: str = "24h"
    ml_confidence_threshold: float = 0.7
    
    # Security
    secret_key: str
    debug: bool = False
    
    # Data Storage
    data_dir: str = "data"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/amazontracker.log"
    log_rotation: str = "daily"
    log_max_size: str = "10MB"
    
    # Web Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    burst_limit: int = 10
    requests_per_minute: int = Field(
        default=20,
        ge=1,
        description="Maximum requests per minute for SerpApi"
    )
    
    # Monitoring intervals
    default_check_interval: str = Field(
        default="1h",
        description="Default price check interval (e.g., '30m', '1h', '6h')"
    )
    min_check_interval: str = Field(
        default="15m",
        description="Minimum allowed check interval"
    )
    
    # Price alert thresholds
    default_price_drop_threshold: float = Field(
        default=5.0,
        ge=0.0,
        description="Default price drop percentage threshold for alerts"
    )
    max_price_difference_percent: float = Field(
        default=50.0,
        ge=0.0,
        description="Maximum price difference to consider valid"
    )
    
    # Email settings
    email_enabled: bool = Field(default=False, description="Enable email notifications")
    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP server")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    email_username: str = Field(default="", description="Email username")
    email_password: str = Field(default="", description="Email password")
    email_from: str = Field(default="", description="From email address")
    
    # Slack settings
    slack_enabled: bool = Field(default=False, description="Enable Slack notifications")
    slack_webhook_url: str = Field(default="", description="Slack webhook URL")
    slack_channel: str = Field(default="#general", description="Slack channel")
    slack_username: str = Field(default="Amazon Tracker", description="Slack username")
    slack_icon_emoji: str = Field(default=":shopping_bags:", description="Slack icon emoji")
    
    # Desktop notifications
    desktop_notifications_enabled: bool = Field(default=True, description="Enable desktop notifications")
    
    # Auto-start monitoring
    auto_start_monitoring: bool = Field(default=False, description="Auto-start monitoring on startup")
    
    # Backup Configuration
    backup_enabled: bool = True
    backup_interval: str = "24h"
    backup_retention_days: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator("serpapi_key")
    def validate_serpapi_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Valid SerpApi key is required")
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class DatabaseConfig:
    """Database-specific configuration"""
    
    @staticmethod
    def get_engine_config(database_url: str) -> dict:
        """Get SQLAlchemy engine configuration based on database URL"""
        config = {
            "echo": False,
            "pool_pre_ping": True,
        }
        
        if database_url.startswith("sqlite"):
            config.update({
                "connect_args": {"check_same_thread": False}
            })
        elif database_url.startswith("postgresql"):
            config.update({
                "pool_size": 20,
                "max_overflow": 30,
                "pool_recycle": 3600,
            })
        
        return config


class LoggingConfig:
    """Logging configuration"""
    
    @staticmethod
    def get_logging_config(settings: Settings) -> dict:
        """Get comprehensive logging configuration"""
        log_dir = Path(settings.log_file).parent
        log_dir.mkdir(exist_ok=True, parents=True)
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                },
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": settings.log_level,
                    "formatter": "simple",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": settings.log_level,
                    "formatter": "detailed",
                    "filename": settings.log_file,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": str(log_dir / "errors.log"),
                    "maxBytes": 10485760,
                    "backupCount": 3
                }
            },
            "loggers": {
                "amazontracker": {
                    "level": settings.log_level,
                    "handlers": ["console", "file", "error_file"],
                    "propagate": False
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console", "file"],
                    "propagate": False
                },
                "sqlalchemy": {
                    "level": "WARNING",
                    "handlers": ["file"],
                    "propagate": False
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "file"]
            }
        }


# Global settings instance
settings = Settings()

# Ensure log directory exists
log_dir = Path(settings.log_file).parent
log_dir.mkdir(exist_ok=True, parents=True)

# Environment-specific configurations
DEVELOPMENT = settings.debug
PRODUCTION = not settings.debug

# API Rate limiting configurations
RATE_LIMITS = {
    "serpapi": {
        "requests_per_minute": 100,
        "burst_limit": 10,
        "retry_after": 60
    },
    "web_api": {
        "requests_per_minute": settings.rate_limit_per_minute,
        "burst_limit": settings.burst_limit
    }
}

# Monitoring intervals in seconds
INTERVALS = {
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "6h": 21600,
    "12h": 43200,
    "24h": 86400
}

def get_interval_seconds(interval_str: str) -> int:
    """Convert interval string to seconds"""
    return INTERVALS.get(interval_str, 3600)  # Default to 1 hour


def validate_configuration() -> List[str]:
    """Validate the current configuration and return any issues"""
    issues = []
    
    # Check required environment variables
    if not settings.serpapi_key:
        issues.append("SERPAPI_KEY is required")
    
    if settings.email_enabled and not settings.email_username:
        issues.append("EMAIL_USERNAME is required when email notifications are enabled")
    
    if settings.slack_enabled and not settings.slack_webhook_url:
        issues.append("SLACK_WEBHOOK_URL is required when Slack notifications are enabled")
    
    # Check file permissions
    try:
        log_dir = Path(settings.log_file).parent
        log_dir.mkdir(exist_ok=True, parents=True)
        test_file = log_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        issues.append(f"Cannot write to log directory: {e}")
    
    return issues


# Configuration validation on import
config_issues = validate_configuration()
if config_issues and not settings.debug:
    raise RuntimeError(f"Configuration issues: {config_issues}")
