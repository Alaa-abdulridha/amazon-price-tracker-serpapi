# Amazon Price Tracker with SerpApi 🛍️

A powerful, intelligent Amazon price tracking application that monitors product prices, analyzes trends, and sends smart notifications when great deals are found. Built with SerpApi for reliable product data and enhanced with AI-powered insights.

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![SerpApi](https://img.shields.io/badge/SerpApi-powered-green.svg)
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

### Installation

```bash
# Clone the repository
git clone https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi.git
cd amazon-price-tracker-serpapi

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your SerpApi key and other settings
```

### Configuration

Create a `.env` file with your settings:

```env
# Required: SerpApi configuration
SERPAPI_KEY=your_serpapi_key_here

# Optional: Email notifications
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Optional: Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Optional: Database (defaults to SQLite)
DATABASE_URL=sqlite:///./amazontracker.db

# Optional: Monitoring settings
DEFAULT_CHECK_INTERVAL=2h
MAX_CONCURRENT_CHECKS=5
PRICE_DROP_THRESHOLD=5.0
```

### Usage Examples

#### Web Dashboard (Beginner-Friendly)
```bash
# Start the web dashboard
python main.py web

# Open browser and go to: http://localhost:8000
```

#### Command Line Interface
```bash
# Add a product by search query
python cli.py add --query "iPhone 15 Pro Max" --target-price 999.99

# Add a product by ASIN (more accurate)
python cli.py add --asin B0C1J2Z3K4 --target-price 299.99

# List all tracked products
python cli.py list

# Check prices now
python cli.py check

# Start background monitoring
python cli.py monitor
```

#### Python API
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

# Get AI predictions
from amazontracker.ai.prediction import PricePredictionEngine
predictor = PricePredictionEngine()
prediction = predictor.predict_price(product.id, days_ahead=7)
print(f"Predicted price in 7 days: ${prediction['predicted_price']}")
```

## 🧠 AI Features

### Price Predictions
- **Machine Learning Models**: Random Forest and Linear Regression
- **Confidence Scores**: Know how reliable predictions are
- **Seasonal Patterns**: Detect holiday sales and seasonal trends
- **Market Analysis**: Understand price volatility and trends

### Smart Alerts
- **Intelligent Thresholds**: AI suggests optimal price targets
- **Trend Detection**: Get notified of significant trend changes
- **Deal Scoring**: Products are ranked by deal quality
- **Personalized Recommendations**: Based on your tracking history

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

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=amazontracker --cov-report=html

# Run specific test category
python -m pytest tests/test_serpapi_client.py -v
```

## 🚀 Deployment

### Docker (Recommended)
```bash
# Build and run
docker build -t amazon-price-tracker .
docker run -d \
  --name price-tracker \
  -p 8000:8000 \
  -e SERPAPI_KEY=your_key_here \
  amazon-price-tracker
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SERPAPI_KEY=your_key_here
export DATABASE_URL=postgresql://user:pass@host/db

# Run application
python main.py web --host 0.0.0.0 --port 8000
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

- **[SerpApi](https://serpapi.com/)** - For providing reliable Amazon data scraping
- **FastAPI** - For the modern web framework
- **Plotly** - For beautiful interactive charts
- **Python Community** - For the amazing ecosystem of libraries

## 📞 Support

- 📧 **Email:** alaa@serpapi.com
- 🐛 **Issues:** [GitHub Issues](https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi/discussions)

---

**Made with ❤️ by [Alaa Abdulridha](https://github.com/Alaa-abdulridha) for [SerpApi](https://serpapi.com/)**
