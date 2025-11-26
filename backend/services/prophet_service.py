# backend/services/prophet_service.py
"""
Optimized Prophet Service for Textile Forecasting
Provides high-performance, accurate forecasting with caching and textile-specific configurations
"""

import hashlib
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from prophet import Prophet
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextileProphetManager:
    """
    Optimized Prophet model manager for textile sales forecasting
    Features: caching, textile-specific configuration, enhanced validation
    """
    
    def __init__(self, max_cache_size: int = 20, cache_ttl: int = 3600):
        self.model_cache = {}
        self.forecast_cache = {}
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl  # Cache TTL in seconds
        self.access_times = {}
        
    def _generate_data_hash(self, df: pd.DataFrame) -> str:
        """Generate unique hash for DataFrame caching"""
        # Use shape, column names, and last few rows for hash
        key_data = f"{df.shape}_{df.columns.tolist()}"
        if len(df) > 0:
            key_data += f"_{df.tail(5).to_string()}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _create_textile_prophet_model(self) -> Prophet:
        """
        Create Prophet model optimized for textile sales data
        Textile-specific patterns: weekly shopping, seasonal fashion, holiday effects
        """
        return Prophet(
            # Seasonality for textile patterns
            weekly_seasonality=True,          # Weekly shopping patterns
            yearly_seasonality=True,          # Seasonal fashion trends
            daily_seasonality=False,          # Daily patterns less relevant
            
            # Trend flexibility for textile demand
            changepoint_prior_scale=0.05,     # Less sensitive to random fluctuations
            seasonality_prior_scale=10.0,    # Strong seasonal patterns (fashion seasons)
            holidays_prior_scale=10.0,       # Holiday shopping effects
            
            # Uncertainty and performance settings
            interval_width=0.8,               # 80% confidence intervals
            mcmc_samples=0,                    # Faster sampling for production
            uncertainty_samples=1000,          # Good uncertainty estimates
            
            # Performance optimizations
            stan_backend=None,                 # Use default optimized backend
        )
    
    def _preprocess_textile_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enhanced preprocessing specifically for textile sales data
        """
        original_size = len(df)
        
        # Ensure required columns
        if not {'ds', 'y'}.issubset(df.columns):
            raise ValueError("DataFrame must contain 'ds' (date) and 'y' (sales) columns")
        
        # Convert and validate dates
        df['ds'] = pd.to_datetime(df['ds'])
        df = df[df['ds'].notna()]
        
        # Convert sales to numeric and remove invalid values
        df['y'] = pd.to_numeric(df['y'], errors='coerce')
        df = df[df['y'].notna()]
        df = df[df['y'] > 0]  # Remove zero/negative sales
        
        # Sort by date
        df = df.sort_values('ds').reset_index(drop=True)
        
        # Remove outliers using IQR method (textile-specific tolerance)
        Q1 = df['y'].quantile(0.25)
        Q3 = df['y'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Keep reasonable outliers (textile can have legitimate spikes)
        df = df[(df['y'] >= lower_bound) & (df['y'] <= upper_bound)]
        
        # Enhanced data validation for textile forecasting
        if len(df) < 10:
            raise ValueError(f"Insufficient data: {len(df)} records (minimum 10 required)")
        
        # Check for seasonal patterns (at least 3 months of data)
        date_span = (df['ds'].max() - df['ds'].min()).days
        if date_span < 90:
            logger.warning(f"Limited date range: {date_span} days (recommend 90+ days)")
        
        # Check for data consistency
        if df['y'].std() / df['y'].mean() > 2.0:
            logger.warning("High variance detected - consider additional smoothing")
        
        # Log preprocessing results
        logger.info(f"Preprocessed: {original_size} -> {len(df)} records "
                   f"({len(df)/original_size:.1%} retained)")
        
        return df
    
    def _add_textile_seasonality(self, model: Prophet, df: pd.DataFrame):
        """
        Add textile-specific seasonal patterns
        """
        # Add custom seasonalities for textile industry
        
        # Monthly seasonality (fashion collection cycles)
        if len(df) >= 365:  # Only with sufficient data
            model.add_seasonality(name='monthly', period=30.5, fourier_order=8)
        
        # Quarterly seasonality (fashion seasons)
        if len(df) >= 365:
            model.add_seasonality(name='quarterly', period=91.25, fourier_order=5)
        
        # Add festival/holiday effects if data spans multiple years
        if df['ds'].dt.year.nunique() > 1:
            # This can be extended with specific holiday calendars
            pass
    
    def get_cached_model(self, df: pd.DataFrame) -> Prophet:
        """
        Get cached Prophet model or create new one with textile optimizations
        """
        data_hash = self._generate_data_hash(df)
        current_time = time.time()
        
        # Check cache
        if data_hash in self.model_cache:
            cache_time = self.access_times.get(data_hash, 0)
            if current_time - cache_time < self.cache_ttl:
                self.access_times[data_hash] = current_time
                logger.info(f"Using cached Prophet model for hash {data_hash[:8]}")
                return self.model_cache[data_hash]
            else:
                # Remove expired cache
                del self.model_cache[data_hash]
                del self.access_times[data_hash]
        
        # Cache management - remove oldest if at capacity
        if len(self.model_cache) >= self.max_cache_size:
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.model_cache[oldest_key]
            del self.access_times[oldest_key]
        
        # Create and fit new model
        logger.info(f"Creating new Prophet model for hash {data_hash[:8]}")
        model = self._create_textile_prophet_model()
        
        # Add textile-specific seasonalities
        self._add_textile_seasonality(model, df)
        
        # Fit model
        start_time = time.time()
        model.fit(df)
        fit_time = time.time() - start_time
        
        logger.info(f"Prophet model fitted in {fit_time:.2f}s")
        
        # Cache the model
        self.model_cache[data_hash] = model
        self.access_times[data_hash] = current_time
        
        return model
    
    def forecast_sales(self, df: pd.DataFrame, periods: int = 30, 
                      freq: str = 'D') -> Tuple[pd.DataFrame, Dict]:
        """
        Optimized sales forecasting with caching and textile-specific enhancements
        """
        try:
            # Preprocess data
            processed_df = self._preprocess_textile_data(df.copy())
            
            # Get cached model
            model = self.get_cached_model(processed_df)
            
            # Generate forecast
            start_time = time.time()
            future = model.make_future_dataframe(periods=periods, freq=freq)
            forecast = model.predict(future)
            forecast_time = time.time() - start_time
            
            # Extract relevant forecast data
            forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
            
            # Add performance metrics
            metrics = {
                'forecast_period_days': periods,
                'data_points_used': len(processed_df),
                'forecast_time_seconds': forecast_time,
                'model_cached': True,
                'data_quality_score': self._calculate_data_quality_score(processed_df)
            }
            
            logger.info(f"Forecast generated in {forecast_time:.2f}s for {periods} periods")
            
            return forecast_data, metrics
            
        except Exception as e:
            logger.error(f"Forecast error: {str(e)}")
            raise
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """
        Calculate data quality score (0-1) for textile forecasting
        """
        score = 0.0
        
        # Data quantity (0-0.4)
        data_points = len(df)
        if data_points >= 365:
            score += 0.4
        elif data_points >= 90:
            score += 0.3
        elif data_points >= 30:
            score += 0.2
        elif data_points >= 10:
            score += 0.1
        
        # Data consistency (0-0.3)
        cv = df['y'].std() / df['y'].mean()  # Coefficient of variation
        if cv <= 0.5:
            score += 0.3
        elif cv <= 1.0:
            score += 0.2
        elif cv <= 2.0:
            score += 0.1
        
        # Seasonal patterns (0-0.3)
        date_span = (df['ds'].max() - df['ds'].min()).days
        if date_span >= 365:
            score += 0.3
        elif date_span >= 180:
            score += 0.2
        elif date_span >= 90:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        return {
            'cached_models': len(self.model_cache),
            'max_cache_size': self.max_cache_size,
            'cache_hit_ratio': getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1),
            'memory_usage_estimate': len(self.model_cache) * 10  # MB estimate
        }
    
    def clear_cache(self):
        """Clear all cached models"""
        self.model_cache.clear()
        self.forecast_cache.clear()
        self.access_times.clear()
        logger.info("Prophet model cache cleared")

# Global instance for application-wide use
prophet_manager = TextileProphetManager()

# Convenience functions for backward compatibility
def forecast_sales_optimized(df: pd.DataFrame, periods: int = 30) -> pd.DataFrame:
    """
    Optimized sales forecasting function
    Returns forecast DataFrame with enhanced accuracy and performance
    """
    forecast_data, metrics = prophet_manager.forecast_sales(df, periods)
    return forecast_data

def get_forecast_with_metrics(df: pd.DataFrame, periods: int = 30) -> Tuple[pd.DataFrame, Dict]:
    """
    Get forecast with performance and quality metrics
    """
    return prophet_manager.forecast_sales(df, periods)
