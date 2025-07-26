# Am![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![SerpApi](https://img.shields.io/badge/SerpApi-powered-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-modern-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)Tracker with SerpApi 🛍️

A powerful, intelligent Amazon price tracking application that monitors product prices, analyzes trends, and sends smart notifications when great deals are found. Built with SerpApi for reliable product data and enhanced with AI-powered insights.

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![SerpApi](https://img.shields.io/badge/SerpApi-powered-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-modern-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg) Price Tracker with SerpAPI �️

A powerful, intelligent Amazon price tracking application that monitors product prices, analyzes trends, and sends smart notifications when great deals are found. Built with SerpAPI for reliable product data and enhanced with AI-powered insights.

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![SerpAPI](https://img.shields.io/badge/SerpAPI-powered-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-modern-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 🔍 Powered by SerpApi
- **Reliable Data Source**: Uses SerpApi's robust Amazon scraping capabilities
- **Real-time Pricing**: Get accurate, up-to-date price information
- **Rich Product Data**: Access detailed product information, ratings, and reviews
- **Global Amazon Support**: Track products across different Amazon marketplaces

### 🧠 Smart Analytics
- **AI Price Predictions**: Machine learning models forecast future price trends
- **Intelligent Deal Detection**: Automatically identifies the best deals
- **Historical Analysis**: Track price patterns and market trends
- **Smart Alerts**: Get notified only when it matters

### 📊 Beautiful Dashboard
- **Interactive Charts**: Visualize price history with modern web interface
- **Product Portfolio**: Manage multiple products from one dashboard
- **Real-time Updates**: Live price monitoring and instant notifications
- **Mobile Responsive**: Access your dashboard from any device

### 🔔 Multi-Channel Notifications
- **Email Alerts**: Rich HTML emails with product details and charts
- **Slack Integration**: Team notifications for shared watchlists
- **Desktop Notifications**: Instant alerts on your computer
- **Webhook Support**: Integrate with any external service

### ⚙️ Easy Configuration
- **Simple Setup**: Get started in minutes with minimal configuration
- **Flexible Scheduling**: Set custom check intervals for each product
- **Environment Variables**: Secure configuration management
- **Auto-scaling**: Handles multiple products efficiently

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- SerpApi account ([Sign up for free](https://serpapi.com/users/sign_up))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi.git
   cd amazon-price-tracker-serpapi
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your SerpApi key:**
   - Sign up at [SerpApi.com](https://serpapi.com/users/sign_up)
   - Get your free API key from the dashboard
   - You get 100 free searches per month!

4. **Configure your environment:**
   ```bash
   # Create environment file
   cp .env.example .env
   
   # Edit .env file with your settings
   SERPAPI_KEY=your_serpapi_key_here
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```

5. **Run the application:**
   ```bash
   # Start web dashboard (recommended)
   python main.py web
   
   # Or use CLI for advanced users
   python cli.py --help
   ```

## 📖 Usage Examples

### Web Dashboard (Beginner-Friendly)
1. **Start the dashboard:**
   ```bash
   python main.py web
   ```
2. **Open your browser:** Go to `http://localhost:8000`
3. **Add products:** Click "Add Product" and enter:
   - Product search: "iPhone 15 Pro Max 256GB"
   - Target price: $999.99
   - Check interval: Every 2 hours
4. **Monitor:** View real-time price charts and get alerts!

### Command Line Interface (Advanced)
```bash
# Add a product by search query
python cli.py add --query "MacBook Pro M3" --target-price 1999.99 --interval 1h

# Add a product by ASIN (more accurate)
python cli.py add --asin B0C1J2Z3K4 --target-price 299.99 --interval 30m

# List all tracked products
python cli.py list

# Check prices now (manual)
python cli.py check

# View price history
python cli.py history --product-id "product-123" --days 30

# Get AI predictions
python cli.py predict --product-id "product-123" --days-ahead 7

# Start background monitoring
python cli.py monitor --interval 30m
```

### Python Integration
```python
from amazontracker import PriceTracker

# Initialize tracker
tracker = PriceTracker()

# Add a product
product = tracker.add_product(
    search_query="Nintendo Switch OLED",
    target_price=299.99,
    check_interval="2h"
)

# Check current price
price_info = tracker.check_product_price(product.id)
print(f"Current price: ${price_info.price}")

# Get price predictions
from amazontracker.ai.prediction import PricePredictionEngine
predictor = PricePredictionEngine()
prediction = predictor.predict_price(product.id, days_ahead=7)
print(f"Predicted price in 7 days: ${prediction['predicted_price']}")
```

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# SerpApi Configuration (Required)
SERPAPI_KEY=your_serpapi_key_here

# Email Notifications (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=Amazon Price Tracker <noreply@yoursite.com>

# Slack Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///./amazontracker.db

# Monitoring Settings
DEFAULT_CHECK_INTERVAL=2h
MAX_CONCURRENT_CHECKS=5
PRICE_DROP_THRESHOLD=5.0

# Web Dashboard
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

## 🔔 Notification Setup

### Email Notifications
1. **Gmail:** Use an App Password (not your regular password)
2. **Outlook:** Enable 2FA and create an app password
3. **Custom SMTP:** Any SMTP server works

### Slack Notifications
1. Create a Slack webhook URL
2. Add it to your `.env` file
3. Notifications will include product details and price charts

### Desktop Notifications
Works automatically on Windows, macOS, and Linux. No setup required!

## 📊 Dashboard Features

The web dashboard provides:

- **📈 Price History Charts:** Interactive graphs showing price trends
- **🎯 Deal Alerts:** Visual indicators for products meeting your criteria
- **📱 Mobile Responsive:** Access from any device
- **⚡ Real-time Updates:** Live price monitoring
- **📋 Bulk Management:** Add/remove multiple products easily
- **🤖 AI Insights:** Price predictions and trend analysis

## 🧠 AI Features

### Price Predictions
- **Machine Learning Models:** Random Forest and Linear Regression
- **Confidence Scores:** Know how reliable predictions are
- **Seasonal Patterns:** Detect holiday sales and seasonal trends
- **Market Analysis:** Understand price volatility and trends

### Smart Alerts
- **Intelligent Thresholds:** AI suggests optimal price targets
- **Trend Detection:** Get notified of significant trend changes
- **Deal Scoring:** Products are ranked by deal quality
- **Personalized Recommendations:** Based on your tracking history

## 🏗️ Architecture

```
amazon-price-tracker/
├── amazontracker/          # Main application package
│   ├── core/              # Core tracking logic
│   ├── services/          # SerpApi integration
│   ├── ai/                # Machine learning models
│   ├── notifications/     # Alert systems
│   ├── web/               # FastAPI dashboard
│   └── database/          # Data models
├── tests/                 # Comprehensive test suite
├── templates/             # HTML templates
└── static/                # CSS/JS assets
```

## 🔧 Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=amazontracker --cov-report=html

# Run specific test category
python -m pytest tests/test_serpapi_client.py -v
```

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run in development mode
export FLASK_ENV=development
python main.py web --debug

# Run linting
flake8 amazontracker/
black amazontracker/
```

## 🚀 Deployment

### Docker (Recommended)
```bash
# Build image
docker build -t amazon-price-tracker .

# Run container
docker run -d \
  --name price-tracker \
  -p 8000:8000 \
  -e SERPAPI_KEY=your_key_here \
  amazon-price-tracker
```

### Manual Deployment
```bash
# Install production dependencies
pip install -r requirements.txt

# Set production environment
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@host/db

# Run with gunicorn
gunicorn amazontracker.web.app:app --host 0.0.0.0 --port 8000
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[SerpAPI](https://serpapi.com/)** - For providing reliable Amazon data scraping
- **FastAPI** - For the modern web framework
- **Plotly** - For beautiful interactive charts
- **Python Community** - For the amazing ecosystem of libraries

## 📞 Support

- 📧 **Email:** alaa@serpapi.com
-  **Issues:** [GitHub Issues](https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi/discussions)

---

**Made with ❤️ by [Alaa Abdulridha](https://github.com/Alaa-abdulridha) for [SerpApi](https://serpapi.com/)**

# Add a product
product = tracker.add_product(
    name="Gaming Laptop",
    search_query="ASUS ROG gaming laptop",
    target_price=1200.00,
    check_interval="2h"
)

# Get price history
history = tracker.get_price_history(product.id)

# Get current best deals
deals = tracker.get_current_deals(max_price=1500)
```

### Advanced Monitoring

```python
from amazontracker.services import PriceMonitor
from amazontracker.ai import PredictionEngine

# Initialize services
monitor = PriceMonitor()
predictor = PredictionEngine()

# Start monitoring with AI predictions
monitor.start_monitoring(
    enable_predictions=True,
    prediction_days=7,
    confidence_threshold=0.8
)

# Get price predictions
future_prices = predictor.predict_prices(
    product_id="product_123",
    days_ahead=30
)
```

### Custom Notifications

```python
from amazontracker.notifications import NotificationManager

# Configure custom notification
notifier = NotificationManager()

notifier.add_webhook(
    name="custom_service",
    url="https://api.custom-service.com/webhook",
    headers={"Authorization": "Bearer your_token"},
    template="{product_name} dropped to ${current_price}!"
)

# Send test notification
notifier.send_test_notification("email")
```

## 🏗️ Architecture

### Core Components

```
amazontracker/
├── app/                    # FastAPI web application
│   ├── main.py            # Application entry point
│   ├── routers/           # API route handlers
│   ├── templates/         # Jinja2 HTML templates
│   └── static/            # CSS, JS, images
├── services/              # Business logic services
│   ├── price_monitor.py   # Main monitoring service
│   ├── serpapi_client.py  # SerpAPI integration
│   └── scheduler.py       # Task scheduling
├── ai/                    # AI and ML components
│   ├── prediction.py      # Price prediction models
│   ├── analysis.py        # Trend analysis
│   └── models/            # ML model storage
├── notifications/         # Notification systems
│   ├── email_sender.py    # Email notifications
│   ├── slack_sender.py    # Slack integration
│   └── desktop_notifier.py # Desktop notifications
├── database/              # Database models and operations
│   ├── models.py          # SQLAlchemy models
│   ├── operations.py      # Database operations
│   └── migrations/        # Database migrations
├── utils/                 # Utility functions
│   ├── config.py          # Configuration management
│   ├── logging.py         # Logging setup
│   └── helpers.py         # Helper functions
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test fixtures
└── scripts/               # Utility scripts
    ├── init_db.py         # Database initialization
    ├── backup.py          # Data backup
    └── migrate.py         # Database migration
```

### Data Flow

1. **Product Registration**: Users add products via web UI or API
2. **Scheduled Monitoring**: Cron jobs trigger price checks
3. **SerpAPI Integration**: Fetch current prices from Amazon
4. **AI Analysis**: ML models analyze trends and predict prices
5. **Deal Detection**: Algorithm identifies good deals
6. **Notification Dispatch**: Multi-channel alerts sent to users
7. **Data Storage**: All data persisted to database
8. **Dashboard Updates**: Real-time updates to web interface

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=amazontracker

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run performance tests
pytest tests/performance/
```

### Test Configuration
```bash
# Set test environment
export TESTING=true
export DATABASE_URL=sqlite:///./test.db

# Run tests with real API (use sparingly)
export TEST_WITH_REAL_API=true
pytest tests/integration/test_serpapi.py
```

## 📊 Monitoring and Analytics

### Built-in Metrics
- Price change frequency and magnitude
- API response times and error rates
- Notification delivery success rates
- User engagement metrics
- System performance indicators

### Health Checks
```bash
# Check system status
curl http://localhost:8000/health

# Detailed status with metrics
curl http://localhost:8000/health/detailed

# Check individual service status
curl http://localhost:8000/health/services
```

### Performance Monitoring
```python
from amazontracker.monitoring import MetricsCollector

metrics = MetricsCollector()

# Get performance stats
stats = metrics.get_performance_stats()
print(f"Average API response time: {stats.avg_response_time}ms")
print(f"Success rate: {stats.success_rate}%")
```

## 🔧 Advanced Configuration

### Custom Price Analysis
```python
# config/analysis.yaml
price_analysis:
  trend_detection:
    short_term_days: 7
    long_term_days: 30
    volatility_threshold: 0.15
  
  deal_scoring:
    historical_weight: 0.6
    trend_weight: 0.3
    volatility_weight: 0.1
    min_score_threshold: 0.7
  
  predictions:
    model_type: "ensemble"  # linear, polynomial, lstm, ensemble
    training_window_days: 90
    prediction_horizon_days: 30
    confidence_intervals: [0.68, 0.95]
```

### Custom Notification Templates
```html
<!-- templates/email/price_alert.html -->
<div class="price-alert">
    <h2>🎉 Great Deal Found!</h2>
    <div class="product-info">
        <img src="{{ product.image_url }}" alt="{{ product.name }}">
        <h3>{{ product.name }}</h3>
        <div class="price-info">
            <span class="current-price">${{ current_price }}</span>
            <span class="old-price">${{ previous_price }}</span>
            <span class="savings">Save ${{ savings }}</span>
        </div>
    </div>
    <div class="chart">
        <!-- Price history chart -->
        {{ price_chart_html | safe }}
    </div>
    <a href="{{ product_url }}" class="buy-button">Buy Now on Amazon</a>
</div>
```

### Custom Schedulers
```python
from amazontracker.services.scheduler import CustomScheduler

# Create custom monitoring schedule
scheduler = CustomScheduler()

# High-priority products - check every 30 minutes
scheduler.add_job(
    product_ids=["high_priority_1", "high_priority_2"],
    interval="30m",
    priority="high"
)

# Regular products - check every 2 hours
scheduler.add_job(
    product_ids="all_regular",
    interval="2h",
    priority="normal"
)

# Seasonal products - check more frequently during sales
scheduler.add_conditional_job(
    product_ids="seasonal",
    base_interval="1h",
    conditions={
        "black_friday": "15m",
        "prime_day": "10m",
        "holiday_season": "30m"
    }
)
```

## 🐳 Docker Deployment

### Development
```bash
# Build and run development environment
docker-compose up --build

# Run specific services
docker-compose up web db

# Execute commands in container
docker-compose exec web python -m scripts.init_db
```

### Production
```bash
# Build production image
docker build -f Dockerfile.prod -t amazontracker:prod .

# Run with production settings
docker run -d \
  --name amazontracker-prod \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/amazontracker \
  -e SERPAPI_KEY=your_key \
  amazontracker:prod
```

### Docker Compose (Production)
```yaml
version: '3.8'
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://tracker:password@db:5432/amazontracker
      - SERPAPI_KEY=${SERPAPI_KEY}
    depends_on:
      - db
      - redis
    
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: amazontracker
      POSTGRES_USER: tracker
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:6-alpine
    
  worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: python -m services.worker
    environment:
      - DATABASE_URL=postgresql://tracker:password@db:5432/amazontracker
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black amazontracker/
isort amazontracker/

# Run linting
flake8 amazontracker/
pylint amazontracker/

# Run type checking
mypy amazontracker/
```

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 90%
- Use meaningful variable and function names
- Include error handling for all external API calls

### Submitting Changes
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Run the test suite: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 API Documentation

### RESTful API Endpoints

#### Products
- `GET /api/products` - List all tracked products
- `POST /api/products` - Add new product to track
- `GET /api/products/{id}` - Get product details
- `PUT /api/products/{id}` - Update product settings
- `DELETE /api/products/{id}` - Stop tracking product

#### Price History
- `GET /api/products/{id}/prices` - Get price history
- `GET /api/products/{id}/prices/chart` - Get price chart data
- `GET /api/products/{id}/predictions` - Get price predictions

#### Notifications
- `GET /api/notifications` - List notification settings
- `POST /api/notifications/test` - Send test notification
- `PUT /api/notifications/{id}` - Update notification settings

#### Analytics
- `GET /api/analytics/dashboard` - Dashboard data
- `GET /api/analytics/deals` - Current best deals
- `GET /api/analytics/trends` - Market trends

### WebSocket API
```javascript
// Real-time price updates
const socket = new WebSocket('ws://localhost:8000/ws/prices');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Price update:', data);
};

// Subscribe to specific product updates
socket.send(JSON.stringify({
    action: 'subscribe',
    product_id: 'product_123'
}));
```

## 🚨 Troubleshooting

### Common Issues

#### SerpAPI Connection Issues
```python
# Verify your API key and increase retry delays
SERPAPI_RETRIES=5
SERPAPI_RETRY_DELAY=2
```

#### Database Connection Issues
```bash
# Check database connectivity
python -c "from database.connection import test_connection; test_connection()"

# Reset database
python -m scripts.reset_db --confirm
```

#### Memory Usage
```bash
# Monitor memory usage
python -m utils.monitor_memory

# Optimize database queries
export SQLALCHEMY_ECHO=true  # Debug SQL queries
```

#### Notification Delivery Issues
```python
# Test email configuration
python -m notifications.test_email

# Test Slack integration
python -m notifications.test_slack

# Check notification logs
tail -f logs/notifications.log
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with profiling
python -m cProfile -o profile.stats -m app.main
```

### Performance Optimization
```python
# Enable caching
REDIS_URL=redis://localhost:6379
CACHE_TTL=300

# Database optimization
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [SerpAPI](https://serpapi.com/) for providing excellent Amazon search API
- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [Plotly](https://plotly.com/) for beautiful data visualizations
- [SQLAlchemy](https://www.sqlalchemy.org/) for robust ORM capabilities

## 📞 Support

- 📧 **Email:** alaa@serpapi.com
-  **Issues:** [GitHub Issues](https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi/discussions)

---

**Made with ❤️ by [Alaa Abdulridha](https://github.com/Alaa-abdulridha) for [SerpApi](https://serpapi.com/)**
