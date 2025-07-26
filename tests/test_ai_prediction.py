"""
Comprehensive tests for AI prediction engine functionality
Tests price prediction, trend analysis, and machine learning features
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from amazontracker.ai.prediction import PricePredictionEngine


class TestPricePredictionEngineInitialization:
    """Test prediction engine initialization and setup"""
    
    def test_engine_initialization(self, test_settings):
        """Test prediction engine initializes correctly"""
        with patch('amazontracker.ai.prediction.settings', test_settings):
            engine = PricePredictionEngine()
            
            assert engine.models == {}
            assert engine.scalers == {}
            assert engine.min_data_points == 10
            assert engine.prediction_days == [1, 3, 7, 14, 30]
    
    def test_model_directory_creation(self, test_settings):
        """Test model directory is created"""
        with patch('amazontracker.ai.prediction.settings', test_settings):
            with patch('os.makedirs') as mock_makedirs:
                engine = PricePredictionEngine()
                
                mock_makedirs.assert_called_once()
    
    def test_engine_with_custom_settings(self, test_settings):
        """Test engine with custom ML settings"""
        test_settings.ml_prediction_enabled = True
        test_settings.ml_confidence_threshold = 0.8
        
        with patch('amazontracker.ai.prediction.settings', test_settings):
            engine = PricePredictionEngine()
            
            assert engine.confidence_threshold == 0.8


class TestPricePredictionEnginePrediction:
    """Test price prediction functionality"""
    
    @pytest.mark.asyncio
    async def test_predict_price_success(self, temp_database, sample_price_history):
        """Test successful price prediction"""
        engine = PricePredictionEngine()
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            # Mock sufficient price history
            mock_history.return_value = pd.DataFrame([
                {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
                for data in sample_price_history * 3  # Ensure enough data
            ])
            
            with patch.object(engine, '_train_model') as mock_train:
                mock_model = Mock()
                mock_model.predict.return_value = np.array([899.99])
                mock_train.return_value = (mock_model, Mock(), 0.85)
                
                result = await engine.predict_price("test-product-id", days_ahead=7)
                
                assert result is not None
                assert result["predicted_price"] == 899.99
                assert result["confidence"] == 0.85
                assert result["days_ahead"] == 7
    
    @pytest.mark.asyncio
    async def test_predict_price_insufficient_data(self, temp_database):
        """Test prediction with insufficient data"""
        engine = PricePredictionEngine()
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            # Mock insufficient price history
            mock_history.return_value = pd.DataFrame([
                {"price": 999.99, "timestamp": pd.to_datetime("2025-07-26")}
            ])  # Only 1 data point, less than min_data_points
            
            result = await engine.predict_price("test-product-id", days_ahead=7)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_predict_price_model_training_failure(self, temp_database, sample_price_history):
        """Test prediction when model training fails"""
        engine = PricePredictionEngine()
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            mock_history.return_value = pd.DataFrame([
                {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
                for data in sample_price_history * 3
            ])
            
            with patch.object(engine, '_train_model') as mock_train:
                mock_train.side_effect = Exception("Training failed")
                
                result = await engine.predict_price("test-product-id", days_ahead=7)
                
                assert result is None
    
    @pytest.mark.asyncio
    async def test_predict_price_multiple_days(self, temp_database, sample_price_history):
        """Test prediction for multiple days ahead"""
        engine = PricePredictionEngine()
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            mock_history.return_value = pd.DataFrame([
                {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
                for data in sample_price_history * 3
            ])
            
            with patch.object(engine, '_train_model') as mock_train:
                mock_model = Mock()
                mock_model.predict.return_value = np.array([899.99])
                mock_train.return_value = (mock_model, Mock(), 0.85)
                
                results = []
                for days in [1, 7, 30]:
                    result = await engine.predict_price("test-product-id", days_ahead=days)
                    results.append(result)
                
                assert len(results) == 3
                assert all(r is not None for r in results)
                assert all(r["days_ahead"] in [1, 7, 30] for r in results)


class TestPricePredictionEngineTrendAnalysis:
    """Test trend analysis functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_price_trends_upward(self, temp_database):
        """Test analyzing upward price trends"""
        engine = PricePredictionEngine()
        
        # Mock upward trending data
        trending_data = pd.DataFrame([
            {"price": 900.0 + i * 10, "timestamp": pd.to_datetime(f"2025-07-{20+i}")}
            for i in range(5)
        ])
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            mock_history.return_value = trending_data
            
            result = await engine.analyze_price_trends("test-product-id", period_days=30)
            
            assert result is not None
            assert result["trend_direction"] == "upward"
            assert result["trend_strength"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_price_trends_downward(self, temp_database):
        """Test analyzing downward price trends"""
        engine = PricePredictionEngine()
        
        # Mock downward trending data
        trending_data = pd.DataFrame([
            {"price": 1000.0 - i * 15, "timestamp": pd.to_datetime(f"2025-07-{20+i}")}
            for i in range(5)
        ])
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            mock_history.return_value = trending_data
            
            result = await engine.analyze_price_trends("test-product-id", period_days=30)
            
            assert result is not None
            assert result["trend_direction"] == "downward"
            assert result["trend_strength"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_price_trends_stable(self, temp_database):
        """Test analyzing stable price trends"""
        engine = PricePredictionEngine()
        
        # Mock stable pricing data
        stable_data = pd.DataFrame([
            {"price": 999.99, "timestamp": pd.to_datetime(f"2025-07-{20+i}")}
            for i in range(5)
        ])
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            mock_history.return_value = stable_data
            
            result = await engine.analyze_price_trends("test-product-id", period_days=30)
            
            assert result is not None
            assert result["trend_direction"] == "stable"
            assert result["trend_strength"] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_trends_with_volatility(self, temp_database):
        """Test trend analysis includes volatility metrics"""
        engine = PricePredictionEngine()
        
        # Mock volatile pricing data
        volatile_data = pd.DataFrame([
            {"price": 1000 + (i % 2) * 100, "timestamp": pd.to_datetime(f"2025-07-{20+i}")}
            for i in range(10)
        ])
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            mock_history.return_value = volatile_data
            
            result = await engine.analyze_price_trends("test-product-id", period_days=30)
            
            assert result is not None
            assert "volatility" in result
            assert result["volatility"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_trends_insufficient_data(self, temp_database):
        """Test trend analysis with insufficient data"""
        engine = PricePredictionEngine()
        
        with patch.object(engine, '_get_price_history_data') as mock_history:
            mock_history.return_value = pd.DataFrame([
                {"price": 999.99, "timestamp": pd.to_datetime("2025-07-26")}
            ])  # Only 1 data point
            
            result = await engine.analyze_price_trends("test-product-id", period_days=30)
            
            assert result is None


class TestPricePredictionEngineModelTraining:
    """Test machine learning model training"""
    
    def test_train_model_random_forest(self, sample_price_history):
        """Test training Random Forest model"""
        engine = PricePredictionEngine()
        
        # Create sample training data
        data = pd.DataFrame([
            {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
            for data in sample_price_history * 5  # Ensure enough data
        ])
        
        with patch('sklearn.ensemble.RandomForestRegressor') as mock_rf:
            mock_model = Mock()
            mock_rf.return_value = mock_model
            mock_model.fit.return_value = None
            mock_model.score.return_value = 0.85
            
            model, scaler, confidence = engine._train_model(data, "random_forest")
            
            assert model == mock_model
            assert confidence == 0.85
            mock_model.fit.assert_called_once()
    
    def test_train_model_linear_regression(self, sample_price_history):
        """Test training Linear Regression model"""
        engine = PricePredictionEngine()
        
        data = pd.DataFrame([
            {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
            for data in sample_price_history * 5
        ])
        
        with patch('sklearn.linear_model.LinearRegression') as mock_lr:
            mock_model = Mock()
            mock_lr.return_value = mock_model
            mock_model.fit.return_value = None
            mock_model.score.return_value = 0.75
            
            model, scaler, confidence = engine._train_model(data, "linear_regression")
            
            assert model == mock_model
            assert confidence == 0.75
    
    def test_feature_engineering(self, sample_price_history):
        """Test feature engineering for model training"""
        engine = PricePredictionEngine()
        
        data = pd.DataFrame([
            {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
            for data in sample_price_history
        ])
        
        features = engine._engineer_features(data)
        
        # Check that features are created
        assert "day_of_week" in features.columns
        assert "hour_of_day" in features.columns
        assert "price_lag_1" in features.columns
        assert "price_moving_avg_3" in features.columns
    
    def test_model_validation(self, sample_price_history):
        """Test model validation and performance metrics"""
        engine = PricePredictionEngine()
        
        data = pd.DataFrame([
            {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
            for data in sample_price_history * 10  # More data for validation
        ])
        
        with patch.object(engine, '_train_model') as mock_train:
            mock_model = Mock()
            mock_model.predict.return_value = np.array([999.99] * 5)
            mock_train.return_value = (mock_model, Mock(), 0.85)
            
            metrics = engine._validate_model(data, mock_model, Mock())
            
            assert "mae" in metrics  # Mean Absolute Error
            assert "rmse" in metrics  # Root Mean Square Error
            assert "mape" in metrics  # Mean Absolute Percentage Error
    
    def test_model_persistence(self, temp_database):
        """Test saving and loading trained models"""
        engine = PricePredictionEngine()
        
        mock_model = Mock()
        mock_scaler = Mock()
        
        with patch('joblib.dump') as mock_dump:
            engine._save_model("test-product", mock_model, mock_scaler)
            
            # Should save both model and scaler
            assert mock_dump.call_count == 2
        
        with patch('joblib.load') as mock_load:
            mock_load.side_effect = [mock_model, mock_scaler]
            
            loaded_model, loaded_scaler = engine._load_model("test-product")
            
            assert loaded_model == mock_model
            assert loaded_scaler == mock_scaler


class TestPricePredictionEngineOptimization:
    """Test optimization and performance features"""
    
    def test_model_selection(self, sample_price_history):
        """Test automatic model selection based on performance"""
        engine = PricePredictionEngine()
        
        data = pd.DataFrame([
            {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
            for data in sample_price_history * 10
        ])
        
        with patch.object(engine, '_train_model') as mock_train:
            # Random Forest performs better
            mock_train.side_effect = [
                (Mock(), Mock(), 0.90),  # Random Forest
                (Mock(), Mock(), 0.75),  # Linear Regression
            ]
            
            best_model, best_scaler, best_score = engine._select_best_model(data)
            
            assert best_score == 0.90
    
    def test_model_retraining_trigger(self, temp_database):
        """Test triggering model retraining based on performance degradation"""
        engine = PricePredictionEngine()
        
        # Mock existing model with degraded performance
        with patch.object(engine, '_load_model') as mock_load:
            mock_model = Mock()
            mock_model.score.return_value = 0.5  # Low score
            mock_load.return_value = (mock_model, Mock())
            
            with patch.object(engine, '_get_price_history_data') as mock_history:
                mock_history.return_value = pd.DataFrame([
                    {"price": 999.99, "timestamp": pd.to_datetime("2025-07-26")}
                ] * 20)  # Sufficient data
                
                should_retrain = engine._should_retrain_model("test-product")
                
                assert should_retrain is True
    
    def test_hyperparameter_optimization(self, sample_price_history):
        """Test hyperparameter optimization for models"""
        engine = PricePredictionEngine()
        
        data = pd.DataFrame([
            {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
            for data in sample_price_history * 10
        ])
        
        with patch('sklearn.model_selection.GridSearchCV') as mock_grid:
            mock_search = Mock()
            mock_search.best_estimator_ = Mock()
            mock_search.best_score_ = 0.88
            mock_grid.return_value = mock_search
            mock_search.fit.return_value = None
            
            optimized_model = engine._optimize_hyperparameters(data, "random_forest")
            
            assert optimized_model == mock_search.best_estimator_
    
    def test_ensemble_prediction(self, sample_price_history):
        """Test ensemble prediction combining multiple models"""
        engine = PricePredictionEngine()
        
        # Mock multiple trained models
        models = {
            "random_forest": (Mock(), Mock(), 0.85),
            "linear_regression": (Mock(), Mock(), 0.75),
        }
        
        for model_name, (model, scaler, score) in models.items():
            model.predict.return_value = np.array([900.0 + score * 100])
            engine.models[f"test-product-{model_name}"] = (model, scaler, score)
        
        prediction = engine._ensemble_predict("test-product", np.array([[1, 2, 3]]))
        
        # Should combine predictions weighted by confidence
        assert prediction is not None
        assert 900 < prediction < 1000
    
    def test_prediction_confidence_calculation(self, sample_price_history):
        """Test confidence calculation for predictions"""
        engine = PricePredictionEngine()
        
        # Mock prediction with variance
        predictions = np.array([995, 1000, 1005, 999, 1001])
        
        confidence = engine._calculate_prediction_confidence(predictions)
        
        assert 0 <= confidence <= 1
        # Lower variance should result in higher confidence
    
    def test_seasonal_pattern_detection(self, temp_database):
        """Test detection of seasonal pricing patterns"""
        engine = PricePredictionEngine()
        
        # Mock data with weekly pattern
        dates = pd.date_range(start="2025-01-01", periods=100, freq="D")
        prices = [1000 + 50 * np.sin(2 * np.pi * i / 7) for i in range(100)]
        data = pd.DataFrame({"timestamp": dates, "price": prices})
        
        patterns = engine._detect_seasonal_patterns(data)
        
        assert "weekly_pattern" in patterns
        assert patterns["weekly_pattern"] is True


class TestPricePredictionEngineAlerts:
    """Test prediction-based alert generation"""
    
    @pytest.mark.asyncio
    async def test_price_drop_prediction_alert(self, temp_database):
        """Test alerts for predicted price drops"""
        engine = PricePredictionEngine()
        
        with patch.object(engine, 'predict_price') as mock_predict:
            mock_predict.return_value = {
                "predicted_price": 799.99,
                "confidence": 0.85,
                "current_price": 999.99
            }
            
            alert = await engine.generate_prediction_alert("test-product", target_price=850.00)
            
            assert alert is not None
            assert alert["alert_type"] == "predicted_price_drop"
            assert alert["predicted_price"] == 799.99
    
    @pytest.mark.asyncio
    async def test_price_spike_prediction_alert(self, temp_database):
        """Test alerts for predicted price spikes"""
        engine = PricePredictionEngine()
        
        with patch.object(engine, 'predict_price') as mock_predict:
            mock_predict.return_value = {
                "predicted_price": 1299.99,
                "confidence": 0.80,
                "current_price": 999.99
            }
            
            alert = await engine.generate_prediction_alert("test-product", spike_threshold=1200.00)
            
            assert alert is not None
            assert alert["alert_type"] == "predicted_price_spike"
    
    @pytest.mark.asyncio
    async def test_low_confidence_prediction_handling(self, temp_database):
        """Test handling of low confidence predictions"""
        engine = PricePredictionEngine()
        engine.confidence_threshold = 0.7
        
        with patch.object(engine, 'predict_price') as mock_predict:
            mock_predict.return_value = {
                "predicted_price": 799.99,
                "confidence": 0.5  # Below threshold
            }
            
            alert = await engine.generate_prediction_alert("test-product", target_price=850.00)
            
            assert alert is None  # Should not generate alert for low confidence


class TestPricePredictionEngineDataManagement:
    """Test data management and preprocessing"""
    
    def test_data_cleaning(self, temp_database):
        """Test data cleaning and outlier removal"""
        engine = PricePredictionEngine()
        
        # Data with outliers
        data = pd.DataFrame({
            "price": [999, 1000, 1001, 5000, 999, 998],  # 5000 is outlier
            "timestamp": pd.date_range(start="2025-07-20", periods=6)
        })
        
        cleaned_data = engine._clean_price_data(data)
        
        # Outlier should be removed or adjusted
        assert cleaned_data["price"].max() < 2000
    
    def test_data_normalization(self, sample_price_history):
        """Test data normalization for model training"""
        engine = PricePredictionEngine()
        
        data = pd.DataFrame([
            {"price": data["price"], "timestamp": pd.to_datetime(data["timestamp"])}
            for data in sample_price_history
        ])
        
        normalized_data, scaler = engine._normalize_data(data["price"].values.reshape(-1, 1))
        
        # Normalized data should have mean ~0 and std ~1
        assert abs(normalized_data.mean()) < 0.1
        assert abs(normalized_data.std() - 1.0) < 0.1
    
    def test_missing_data_handling(self, temp_database):
        """Test handling of missing price data"""
        engine = PricePredictionEngine()
        
        # Data with missing values
        data = pd.DataFrame({
            "price": [999, None, 1001, None, 998],
            "timestamp": pd.date_range(start="2025-07-20", periods=5)
        })
        
        filled_data = engine._handle_missing_data(data)
        
        # Missing values should be filled
        assert filled_data["price"].isna().sum() == 0
    
    def test_data_aggregation(self, temp_database):
        """Test aggregation of high-frequency data"""
        engine = PricePredictionEngine()
        
        # Hourly data to be aggregated daily
        dates = pd.date_range(start="2025-07-20", periods=48, freq="H")
        data = pd.DataFrame({
            "price": np.random.normal(1000, 10, 48),
            "timestamp": dates
        })
        
        daily_data = engine._aggregate_to_daily(data)
        
        # Should have 2 days of data
        assert len(daily_data) == 2
        assert "price_mean" in daily_data.columns
        assert "price_min" in daily_data.columns
        assert "price_max" in daily_data.columns
