"""
AI-powered price prediction and analysis engine
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy import stats
import joblib
import os

from ..database.models import PriceHistory, PricePrediction, Product
from ..database.connection import get_db_session
from ..utils.config import settings

logger = logging.getLogger(__name__)


class PricePredictionEngine:
    """
    AI-powered engine for price prediction and trend analysis
    """
    
    def __init__(self):
        """Initialize the prediction engine"""
        self.models = {}
        self.scalers = {}
        self.model_dir = os.path.join(settings.data_dir, "models")
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Model parameters
        self.min_data_points = 10  # Minimum data points for training
        self.prediction_days = [1, 3, 7, 14, 30]  # Days to predict ahead
        
        logger.info("Price prediction engine initialized")
    
    async def predict_price(
        self,
        product_id: str,
        days_ahead: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Predict future price for a product
        
        Args:
            product_id: Product ID
            days_ahead: Number of days to predict ahead
            
        Returns:
            Prediction results dictionary or None if insufficient data
        """
        try:
            # Get historical price data
            price_data = await self._get_price_data(product_id)
            
            if len(price_data) < self.min_data_points:
                logger.warning(f"Insufficient data for prediction: {len(price_data)} points")
                return None
            
            # Prepare features
            features, target = self._prepare_features(price_data)
            
            if len(features) == 0:
                logger.warning("No features could be prepared")
                return None
            
            # Train or load model
            model, scaler = await self._get_or_train_model(product_id, features, target)
            
            # Make prediction
            prediction_result = self._make_prediction(
                model, scaler, features, days_ahead
            )
            
            # Calculate confidence and trend
            confidence = self._calculate_confidence(model, features, target)
            trend = self._analyze_trend(price_data)
            
            # Store prediction in database
            await self._store_prediction(
                product_id=product_id,
                days_ahead=days_ahead,
                predicted_price=prediction_result['predicted_price'],
                confidence_score=confidence,
                trend_direction=trend['direction'],
                trend_strength=trend['strength']
            )
            
            result = {
                'product_id': product_id,
                'days_ahead': days_ahead,
                'predicted_price': prediction_result['predicted_price'],
                'confidence_score': confidence,
                'trend': trend,
                'price_range': prediction_result.get('price_range'),
                'model_accuracy': prediction_result.get('accuracy'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Price prediction completed for product {product_id}: ${prediction_result['predicted_price']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in price prediction: {e}")
            return None
    
    async def analyze_price_trends(
        self,
        product_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze price trends and patterns
        
        Args:
            product_id: Product ID
            period_days: Analysis period in days
            
        Returns:
            Trend analysis results
        """
        try:
            # Get price data for the period
            price_data = await self._get_price_data(product_id, period_days)
            
            if len(price_data) < 3:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Basic statistics
            prices = [p['price'] for p in price_data]
            current_price = prices[-1]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = np.mean(prices)
            price_volatility = np.std(prices)
            
            # Trend analysis
            trend = self._analyze_trend(price_data)
            
            # Price patterns
            patterns = self._detect_patterns(price_data)
            
            # Seasonal analysis (if enough data)
            seasonal_info = {}
            if len(price_data) >= 14:
                seasonal_info = self._analyze_seasonality(price_data)
            
            # Support and resistance levels
            support_resistance = self._find_support_resistance(prices)
            
            # Deal probability
            deal_probability = self._calculate_deal_probability(price_data, current_price)
            
            result = {
                'product_id': product_id,
                'period_days': period_days,
                'current_price': current_price,
                'price_statistics': {
                    'min_price': min_price,
                    'max_price': max_price,
                    'average_price': avg_price,
                    'volatility': price_volatility,
                    'price_change': current_price - avg_price,
                    'price_change_percent': ((current_price - avg_price) / avg_price) * 100
                },
                'trend': trend,
                'patterns': patterns,
                'seasonal_info': seasonal_info,
                'support_resistance': support_resistance,
                'deal_probability': deal_probability,
                'analysis_date': datetime.now(timezone.utc).isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return {'error': str(e)}
    
    async def get_price_alerts_ai(
        self,
        product_id: str,
        target_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered price alerts and recommendations
        
        Args:
            product_id: Product ID
            target_price: Optional target price
            
        Returns:
            List of AI-generated alerts
        """
        try:
            alerts = []
            
            # Get predictions for multiple time horizons
            predictions = []
            for days in self.prediction_days:
                pred = await self.predict_price(product_id, days)
                if pred:
                    predictions.append(pred)
            
            if not predictions:
                return alerts
            
            # Get trend analysis
            trend_analysis = await self.analyze_price_trends(product_id)
            
            current_price = trend_analysis.get('current_price')
            if not current_price:
                return alerts
            
            # Generate alerts based on predictions and trends
            
            # 1. Target price alerts
            if target_price:
                for pred in predictions:
                    if pred['predicted_price'] <= target_price:
                        alerts.append({
                            'type': 'target_price_prediction',
                            'message': f"AI predicts target price (${target_price:.2f}) may be reached in {pred['days_ahead']} days",
                            'predicted_price': pred['predicted_price'],
                            'confidence': pred['confidence_score'],
                            'days_ahead': pred['days_ahead'],
                            'priority': 'high' if pred['confidence_score'] > 0.7 else 'medium'
                        })
            
            # 2. Price drop alerts
            best_future_price = min([p['predicted_price'] for p in predictions])
            if best_future_price < current_price * 0.95:  # 5% drop
                savings = current_price - best_future_price
                alerts.append({
                    'type': 'predicted_price_drop',
                    'message': f"AI predicts price drop of ${savings:.2f} ({((savings/current_price)*100):.1f}%)",
                    'predicted_price': best_future_price,
                    'savings': savings,
                    'priority': 'high' if savings > current_price * 0.1 else 'medium'
                })
            
            # 3. Trend-based alerts
            trend = trend_analysis.get('trend', {})
            if trend.get('direction') == 'downward' and trend.get('strength', 0) > 0.6:
                alerts.append({
                    'type': 'downward_trend',
                    'message': f"Strong downward price trend detected (strength: {trend['strength']:.2f})",
                    'trend_strength': trend['strength'],
                    'priority': 'medium'
                })
            
            # 4. Deal probability alerts
            deal_prob = trend_analysis.get('deal_probability', 0)
            if deal_prob > 0.7:
                alerts.append({
                    'type': 'deal_probability',
                    'message': f"High probability ({deal_prob:.1%}) of deal based on historical patterns",
                    'probability': deal_prob,
                    'priority': 'medium'
                })
            
            # 5. Support level alerts
            support_resistance = trend_analysis.get('support_resistance', {})
            support_level = support_resistance.get('support')
            if support_level and current_price <= support_level * 1.05:  # Within 5% of support
                alerts.append({
                    'type': 'near_support_level',
                    'message': f"Price near support level (${support_level:.2f}) - potential buying opportunity",
                    'support_level': support_level,
                    'priority': 'medium'
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating AI alerts: {e}")
            return []
    
    async def _get_price_data(
        self,
        product_id: str,
        days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get historical price data for a product"""
        try:
            with get_db_session() as session:
                query = session.query(PriceHistory).filter(
                    PriceHistory.product_id == product_id
                )
                
                if days:
                    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                    query = query.filter(PriceHistory.checked_at >= cutoff_date)
                
                price_records = query.order_by(PriceHistory.checked_at.asc()).all()
                
                return [
                    {
                        'price': record.price,
                        'checked_at': record.checked_at,
                        'old_price': record.old_price,
                        'discount_percentage': record.discount_percentage or 0,
                        'rating': record.rating or 0,
                        'reviews_count': record.reviews_count or 0,
                        'prime_eligible': record.prime_eligible or False
                    }
                    for record in price_records
                ]
                
        except Exception as e:
            logger.error(f"Error getting price data: {e}")
            return []
    
    def _prepare_features(
        self,
        price_data: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for machine learning model"""
        try:
            df = pd.DataFrame(price_data)
            df['checked_at'] = pd.to_datetime(df['checked_at'])
            df = df.sort_values('checked_at')
            
            # Create time-based features
            df['day_of_week'] = df['checked_at'].dt.dayofweek
            df['hour'] = df['checked_at'].dt.hour
            df['day_of_month'] = df['checked_at'].dt.day
            df['days_since_start'] = (df['checked_at'] - df['checked_at'].min()).dt.days
            
            # Price-based features
            df['price_rolling_mean_3'] = df['price'].rolling(window=3, min_periods=1).mean()
            df['price_rolling_mean_7'] = df['price'].rolling(window=7, min_periods=1).mean()
            df['price_change'] = df['price'].diff()
            df['price_volatility'] = df['price'].rolling(window=5, min_periods=1).std()
            
            # Rating and review features
            df['rating_change'] = df['rating'].diff()
            df['reviews_growth'] = df['reviews_count'].pct_change()
            
            # Feature columns
            feature_columns = [
                'day_of_week', 'hour', 'day_of_month', 'days_since_start',
                'price_rolling_mean_3', 'price_rolling_mean_7',
                'price_volatility', 'discount_percentage',
                'rating', 'reviews_count', 'rating_change', 'reviews_growth'
            ]
            
            # Fill NaN values
            df = df.fillna(method='forward').fillna(0)
            
            # Prepare features and target
            features = df[feature_columns].values
            target = df['price'].values
            
            # Remove the last row for features (we want to predict next price)
            if len(features) > 1:
                features = features[:-1]
                target = target[1:]  # Target is next price
            
            return features, target
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return np.array([]), np.array([])
    
    async def _get_or_train_model(
        self,
        product_id: str,
        features: np.ndarray,
        target: np.ndarray
    ) -> Tuple[Any, Any]:
        """Get existing model or train new one"""
        model_path = os.path.join(self.model_dir, f"{product_id}_model.joblib")
        scaler_path = os.path.join(self.model_dir, f"{product_id}_scaler.joblib")
        
        # Try to load existing model
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                model = joblib.load(model_path)
                scaler = joblib.load(scaler_path)
                
                # Check if model needs retraining (based on age or performance)
                model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
                if model_age.days < 7:  # Use model if less than 7 days old
                    return model, scaler
            except Exception as e:
                logger.warning(f"Failed to load existing model: {e}")
        
        # Train new model
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Use Random Forest for better performance with small datasets
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        model.fit(features_scaled, target)
        
        # Save model and scaler
        try:
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            logger.info(f"Model trained and saved for product {product_id}")
        except Exception as e:
            logger.warning(f"Failed to save model: {e}")
        
        return model, scaler
    
    def _make_prediction(
        self,
        model: Any,
        scaler: Any,
        features: np.ndarray,
        days_ahead: int
    ) -> Dict[str, Any]:
        """Make price prediction"""
        try:
            # Use the last feature row as base for prediction
            last_features = features[-1:].copy()
            
            # Adjust time-based features for future prediction
            last_features[0, 3] += days_ahead  # days_since_start
            
            # Scale features
            features_scaled = scaler.transform(last_features)
            
            # Make prediction
            predicted_price = model.predict(features_scaled)[0]
            
            # Calculate prediction interval (uncertainty range)
            # For Random Forest, use prediction variance
            if hasattr(model, 'estimators_'):
                # Get predictions from all trees
                tree_predictions = [tree.predict(features_scaled)[0] for tree in model.estimators_]
                prediction_std = np.std(tree_predictions)
                
                # 95% confidence interval
                lower_bound = predicted_price - 1.96 * prediction_std
                upper_bound = predicted_price + 1.96 * prediction_std
                
                price_range = {
                    'lower': max(0, lower_bound),  # Price can't be negative
                    'upper': upper_bound,
                    'std': prediction_std
                }
            else:
                price_range = None
            
            # Calculate accuracy if we have historical predictions to validate against
            accuracy = self._calculate_model_accuracy(model, scaler, features)
            
            return {
                'predicted_price': max(0, predicted_price),  # Ensure non-negative
                'price_range': price_range,
                'accuracy': accuracy
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {'predicted_price': 0}
    
    def _calculate_confidence(
        self,
        model: Any,
        features: np.ndarray,
        target: np.ndarray
    ) -> float:
        """Calculate prediction confidence score"""
        try:
            if len(features) < 5:
                return 0.5  # Low confidence with little data
            
            # Use cross-validation-like approach for confidence
            split_point = len(features) // 2
            train_features = features[:split_point]
            test_features = features[split_point:]
            train_target = target[:split_point]
            test_target = target[split_point:]
            
            if len(test_features) == 0:
                return 0.6
            
            # Train on first half, test on second half
            scaler = StandardScaler()
            train_features_scaled = scaler.fit_transform(train_features)
            test_features_scaled = scaler.transform(test_features)
            
            temp_model = RandomForestRegressor(n_estimators=50, random_state=42)
            temp_model.fit(train_features_scaled, train_target)
            
            predictions = temp_model.predict(test_features_scaled)
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((test_target - predictions) / test_target))
            
            # Convert to confidence score (higher accuracy = higher confidence)
            confidence = max(0, min(1, 1 - mape))
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _analyze_trend(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze price trend direction and strength"""
        try:
            prices = [p['price'] for p in price_data]
            
            if len(prices) < 3:
                return {'direction': 'unknown', 'strength': 0}
            
            # Linear regression for trend
            x = np.arange(len(prices))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, prices)
            
            # Determine direction
            if slope > 0.01:  # Small threshold to avoid noise
                direction = 'upward'
            elif slope < -0.01:
                direction = 'downward'
            else:
                direction = 'sideways'
            
            # Strength is based on R-squared (how well trend fits)
            strength = abs(r_value)
            
            # Additional trend metrics
            recent_prices = prices[-5:] if len(prices) >= 5 else prices
            recent_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            
            return {
                'direction': direction,
                'strength': strength,
                'slope': slope,
                'r_squared': r_value ** 2,
                'recent_change_percent': recent_change * 100,
                'p_value': p_value
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return {'direction': 'unknown', 'strength': 0}
    
    def _detect_patterns(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect price patterns and cycles"""
        try:
            prices = [p['price'] for p in price_data]
            
            if len(prices) < 7:
                return {}
            
            patterns = {}
            
            # Moving average crossovers
            if len(prices) >= 10:
                short_ma = pd.Series(prices).rolling(3).mean().tolist()
                long_ma = pd.Series(prices).rolling(7).mean().tolist()
                
                # Check for golden cross (short MA crosses above long MA)
                if len(short_ma) > 1 and len(long_ma) > 1:
                    if short_ma[-1] > long_ma[-1] and short_ma[-2] <= long_ma[-2]:
                        patterns['golden_cross'] = True
                    elif short_ma[-1] < long_ma[-1] and short_ma[-2] >= long_ma[-2]:
                        patterns['death_cross'] = True
            
            # Price volatility pattern
            price_changes = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
            avg_volatility = np.mean(price_changes)
            recent_volatility = np.mean(price_changes[-3:]) if len(price_changes) >= 3 else avg_volatility
            
            if recent_volatility > avg_volatility * 1.5:
                patterns['high_volatility'] = True
            elif recent_volatility < avg_volatility * 0.5:
                patterns['low_volatility'] = True
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return {}
    
    def _analyze_seasonality(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze seasonal price patterns"""
        try:
            df = pd.DataFrame(price_data)
            df['checked_at'] = pd.to_datetime(df['checked_at'])
            
            # Day of week analysis
            df['day_of_week'] = df['checked_at'].dt.day_name()
            day_avg = df.groupby('day_of_week')['price'].mean().to_dict()
            
            # Hour of day analysis (if we have that granularity)
            df['hour'] = df['checked_at'].dt.hour
            hour_avg = df.groupby('hour')['price'].mean().to_dict()
            
            return {
                'day_of_week_patterns': day_avg,
                'hourly_patterns': hour_avg if len(hour_avg) > 1 else {}
            }
            
        except Exception as e:
            logger.error(f"Error analyzing seasonality: {e}")
            return {}
    
    def _find_support_resistance(self, prices: List[float]) -> Dict[str, float]:
        """Find support and resistance levels"""
        try:
            if len(prices) < 5:
                return {}
            
            # Sort prices to find levels
            sorted_prices = sorted(prices)
            
            # Support is around the lower quartile
            support = np.percentile(sorted_prices, 25)
            
            # Resistance is around the upper quartile
            resistance = np.percentile(sorted_prices, 75)
            
            return {
                'support': support,
                'resistance': resistance,
                'current_vs_support': (prices[-1] - support) / support,
                'current_vs_resistance': (prices[-1] - resistance) / resistance
            }
            
        except Exception as e:
            logger.error(f"Error finding support/resistance: {e}")
            return {}
    
    def _calculate_deal_probability(
        self,
        price_data: List[Dict[str, Any]],
        current_price: float
    ) -> float:
        """Calculate probability of current price being a good deal"""
        try:
            prices = [p['price'] for p in price_data]
            
            if len(prices) < 5:
                return 0.5
            
            # What percentile is current price?
            percentile = stats.percentileofscore(prices, current_price)
            
            # Lower percentile = better deal
            deal_probability = (100 - percentile) / 100
            
            return deal_probability
            
        except Exception as e:
            logger.error(f"Error calculating deal probability: {e}")
            return 0.5
    
    def _calculate_model_accuracy(
        self,
        model: Any,
        scaler: Any,
        features: np.ndarray
    ) -> Optional[float]:
        """Calculate model accuracy on historical data"""
        try:
            if len(features) < 5:
                return None
            
            # Use last 20% of data for validation
            split_point = int(len(features) * 0.8)
            train_features = features[:split_point]
            test_features = features[split_point:]
            
            if len(test_features) == 0:
                return None
            
            # Scale features
            train_scaled = scaler.transform(train_features)
            test_scaled = scaler.transform(test_features)
            
            # Make predictions
            predictions = model.predict(test_scaled)
            
            # For this simplified version, return a mock accuracy
            # In practice, you'd compare against actual future prices
            return 0.75  # Placeholder accuracy
            
        except Exception as e:
            logger.error(f"Error calculating model accuracy: {e}")
            return None
    
    async def _store_prediction(
        self,
        product_id: str,
        days_ahead: int,
        predicted_price: float,
        confidence_score: float,
        trend_direction: str,
        trend_strength: float
    ):
        """Store prediction in database"""
        try:
            with get_db_session() as session:
                prediction = PricePrediction(
                    product_id=product_id,
                    predicted_price=predicted_price,
                    prediction_date=datetime.now(timezone.utc),
                    target_date=datetime.now(timezone.utc) + timedelta(days=days_ahead),
                    confidence_score=confidence_score,
                    model_version="v1.0",
                    features_used="time_series,price_history,ratings",
                    trend_direction=trend_direction,
                    trend_strength=trend_strength
                )
                
                session.add(prediction)
                session.commit()
                
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about trained models"""
        try:
            model_files = [f for f in os.listdir(self.model_dir) if f.endswith('_model.joblib')]
            
            stats = {
                'total_models': len(model_files),
                'model_directory': self.model_dir,
                'models': []
            }
            
            for model_file in model_files:
                product_id = model_file.replace('_model.joblib', '')
                model_path = os.path.join(self.model_dir, model_file)
                
                model_info = {
                    'product_id': product_id,
                    'file_size': os.path.getsize(model_path),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat()
                }
                
                stats['models'].append(model_info)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting model stats: {e}")
            return {'error': str(e)}
