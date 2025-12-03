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
    
    def _create_textile_prophet_model(self, data_points: int = 90, date_span_days: int = 90) -> Prophet:
        """
        Create Prophet model optimized for textile sales data.
        Adjusts configuration based on available data points and date span for better accuracy.
        
        Args:
            data_points: Number of data records available
            date_span_days: Number of days the data spans (for seasonality decisions)
        """
        # Adjust parameters based on data availability
        # Less data = simpler model to avoid overfitting
        if data_points < 14 or date_span_days < 14:
            # Very limited data - use simplest model
            return Prophet(
                growth='flat',                    # Flat growth for very limited data
                weekly_seasonality=False,         # Disable - not enough data
                yearly_seasonality=False,         # Disable - not enough data  
                daily_seasonality=False,
                changepoint_prior_scale=0.001,    # Very rigid - avoid overfitting
                seasonality_prior_scale=0.01,     # Minimal seasonality
                interval_width=0.95,              # Wider confidence intervals
                mcmc_samples=0,
                uncertainty_samples=500,
            )
        elif data_points < 30 or date_span_days < 30:
            # Limited data - simplified model
            return Prophet(
                growth='linear',
                weekly_seasonality=date_span_days >= 14,  # Need at least 2 weeks for weekly
                yearly_seasonality=False,         # Not enough data for yearly
                daily_seasonality=False,
                changepoint_prior_scale=0.01,     # More rigid
                seasonality_prior_scale=1.0,      # Reduced seasonality influence
                interval_width=0.9,               # Wider confidence intervals
                mcmc_samples=0,
                uncertainty_samples=500,
            )
        elif data_points < 90 or date_span_days < 90:
            # Moderate data - balanced model
            return Prophet(
                growth='linear',
                weekly_seasonality=True,
                yearly_seasonality=False,         # Need 2+ years for this
                daily_seasonality=False,
                changepoint_prior_scale=0.03,     # Slightly rigid
                seasonality_prior_scale=5.0,      # Moderate seasonality
                interval_width=0.85,
                mcmc_samples=0,
                uncertainty_samples=800,
            )
        else:
            # Sufficient data - full model
            return Prophet(
                growth='linear',
                weekly_seasonality=True,          # Weekly shopping patterns
                yearly_seasonality=date_span_days >= 365,  # Only if we have 1+ year of DATE SPAN
                daily_seasonality=False,          # Daily patterns less relevant
                changepoint_prior_scale=0.05,     # Standard flexibility
                seasonality_prior_scale=10.0,     # Strong seasonal patterns
                holidays_prior_scale=10.0,        # Holiday shopping effects
                interval_width=0.8,               # 80% confidence intervals
                mcmc_samples=0,
                uncertainty_samples=1000,
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
        
        # Initialize warnings list for tracking data quality issues
        warnings = []
        
        # Enhanced data validation for textile forecasting
        # Allow minimum 5 data points (reduced from 10) for flexibility
        if len(df) < 5:
            raise ValueError(f"Insufficient data: {len(df)} records (minimum 5 required)")
        elif len(df) < 10:
            warnings.append({
                "type": "data_points",
                "severity": "high",
                "message": f"Very limited data: only {len(df)} data points. Minimum recommended is 30 for reliable forecasts."
            })
        
        # Check for seasonal patterns
        date_span = (df['ds'].max() - df['ds'].min()).days
        if date_span < 7:
            warnings.append({
                "type": "date_range",
                "severity": "critical",
                "message": f"Extremely limited date range: only {date_span} days. Forecasts will have very low accuracy."
            })
        elif date_span < 30:
            warnings.append({
                "type": "date_range",
                "severity": "high", 
                "message": f"Limited date range: {date_span} days. Recommend at least 30 days for basic forecasting."
            })
        elif date_span < 90:
            warnings.append({
                "type": "date_range",
                "severity": "medium",
                "message": f"Moderate date range: {date_span} days. Recommend 90+ days for accurate seasonal patterns."
            })
        
        # Check for data consistency
        if df['y'].std() / df['y'].mean() > 2.0:
            warnings.append({
                "type": "variance",
                "severity": "medium",
                "message": "High variance detected in data - forecasts may be less stable."
            })
        
        # Store warnings in DataFrame metadata for access later
        df.attrs['preprocessing_warnings'] = warnings
        df.attrs['date_span_days'] = date_span
        df.attrs['original_size'] = original_size
        
        # Log preprocessing results
        if warnings:
            logger.warning(f"Preprocessed with warnings: {len(warnings)} issues found")
            for w in warnings:
                logger.warning(f"  [{w['severity'].upper()}] {w['message']}")
        
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
        
        # Create and fit new model with data-aware configuration
        data_points = len(df)
        date_span_days = (df['ds'].max() - df['ds'].min()).days if len(df) > 1 else 0
        logger.info(f"Creating new Prophet model for hash {data_hash[:8]} with {data_points} data points spanning {date_span_days} days")
        model = self._create_textile_prophet_model(data_points=data_points, date_span_days=date_span_days)
        
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
        Optimized sales forecasting with caching and textile-specific enhancements.
        Now supports forecasting with limited data while providing accuracy warnings.
        """
        try:
            # Preprocess data
            processed_df = self._preprocess_textile_data(df.copy())
            
            # Extract preprocessing warnings and metadata
            preprocessing_warnings = processed_df.attrs.get('preprocessing_warnings', [])
            date_span_days = processed_df.attrs.get('date_span_days', 0)
            
            # Get cached model
            model = self.get_cached_model(processed_df)
            
            # Store historical stats for post-processing
            historical_mean = processed_df['y'].mean()
            historical_max = processed_df['y'].max()
            historical_min = processed_df['y'].min()
            
            # Generate forecast
            start_time = time.time()
            future = model.make_future_dataframe(periods=periods, freq=freq)
            
            # Note: floor/cap only work with growth='logistic', so we use post-processing instead
            forecast = model.predict(future)
            forecast_time = time.time() - start_time
            
            # Extract relevant forecast data and ensure non-negative values
            forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).copy()
            
            # CRITICAL: Clamp all predictions to be non-negative (revenue/sales can't be negative)
            # Use historical_min as a reasonable floor - predictions shouldn't go below observed minimum
            reasonable_floor = max(0, historical_min * 0.5)  # 50% of historical minimum, but never negative
            forecast_data['yhat'] = forecast_data['yhat'].clip(lower=reasonable_floor)
            forecast_data['yhat_lower'] = forecast_data['yhat_lower'].clip(lower=0)  # Lower bound can be 0
            forecast_data['yhat_upper'] = forecast_data['yhat_upper'].clip(lower=reasonable_floor)
            
            # Cap unrealistic predictions (> 5x historical max)
            reasonable_cap = max(historical_max * 5, historical_mean * 10)
            forecast_data['yhat'] = forecast_data['yhat'].clip(upper=reasonable_cap)
            forecast_data['yhat_upper'] = forecast_data['yhat_upper'].clip(upper=reasonable_cap * 1.5)
            
            # For very limited data, use a more conservative approach:
            # blend prediction with historical average to avoid wild extrapolations
            if date_span_days < 30:
                blend_factor = max(0.3, date_span_days / 30)  # 30% to 100% model weight
                forecast_data['yhat'] = (forecast_data['yhat'] * blend_factor + 
                                         historical_mean * (1 - blend_factor))
                forecast_data['yhat_lower'] = forecast_data['yhat_lower'] * blend_factor
                forecast_data['yhat_upper'] = (forecast_data['yhat_upper'] * blend_factor + 
                                               historical_mean * (1 - blend_factor) * 1.5)
                # Ensure after blending values are still non-negative
                forecast_data['yhat'] = forecast_data['yhat'].clip(lower=0)
                forecast_data['yhat_lower'] = forecast_data['yhat_lower'].clip(lower=0)
                forecast_data['yhat_upper'] = forecast_data['yhat_upper'].clip(lower=0)
                logger.info(f"Applied conservative blending (factor={blend_factor:.2f}) for limited data")
            
            # Calculate data quality score and determine accuracy level
            data_quality_score, accuracy_level, accuracy_warnings = self._calculate_data_quality_score_detailed(processed_df)
            
            # Combine all warnings
            all_warnings = preprocessing_warnings + accuracy_warnings
            
            # Determine if forecast should show low accuracy warning
            has_low_accuracy_warning = any(w.get('severity') in ['critical', 'high'] for w in all_warnings)
            
            # Add performance metrics with enhanced warning information
            metrics = {
                'forecast_period_days': periods,
                'data_points_used': len(processed_df),
                'historical_days': date_span_days,
                'forecast_time_seconds': forecast_time,
                'model_cached': True,
                'data_quality_score': data_quality_score,
                'accuracy_level': accuracy_level,
                'has_low_accuracy_warning': has_low_accuracy_warning,
                'warnings': all_warnings,
                'minimum_recommended_days': 90,
                'minimum_required_days': 7
            }
            
            logger.info(f"Forecast generated in {forecast_time:.2f}s for {periods} periods "
                       f"(accuracy: {accuracy_level}, quality: {data_quality_score:.1f}%)")
            
            return forecast_data, metrics
            
        except Exception as e:
            logger.error(f"Forecast error: {str(e)}")
            raise
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """
        Calculate data quality score (0-100) for textile forecasting.
        Legacy method for backward compatibility.
        """
        score, _, _ = self._calculate_data_quality_score_detailed(df)
        return score
    
    def _calculate_data_quality_score_detailed(self, df: pd.DataFrame) -> Tuple[float, str, List[Dict]]:
        """
        Calculate detailed data quality score (0-100) for textile forecasting.
        Returns: (score, accuracy_level, warnings)
        
        Score breakdown:
        - Data quantity: 0-40 points
        - Data consistency: 0-30 points  
        - Date span/seasonality: 0-30 points
        """
        score = 0.0
        warnings = []
        
        # Data quantity scoring (0-40 points)
        data_points = len(df)
        if data_points >= 365:
            score += 40
        elif data_points >= 180:
            score += 35
        elif data_points >= 90:
            score += 30
        elif data_points >= 60:
            score += 25
        elif data_points >= 30:
            score += 20
        elif data_points >= 14:
            score += 12
            warnings.append({
                "type": "data_quantity",
                "severity": "high",
                "message": f"Only {data_points} data points available. Forecast accuracy may be limited."
            })
        elif data_points >= 7:
            score += 8
            warnings.append({
                "type": "data_quantity",
                "severity": "critical",
                "message": f"Very few data points ({data_points}). Forecast is highly speculative."
            })
        else:
            score += 5
            warnings.append({
                "type": "data_quantity",
                "severity": "critical",
                "message": f"Extremely limited data ({data_points} points). Forecasts will be unreliable."
            })
        
        # Data consistency scoring (0-30 points)
        cv = df['y'].std() / df['y'].mean() if df['y'].mean() > 0 else 0  # Coefficient of variation
        if cv <= 0.3:
            score += 30
        elif cv <= 0.5:
            score += 25
        elif cv <= 0.8:
            score += 20
        elif cv <= 1.0:
            score += 15
        elif cv <= 1.5:
            score += 10
            warnings.append({
                "type": "consistency",
                "severity": "medium",
                "message": "Sales data shows moderate variability which may affect forecast stability."
            })
        else:
            score += 5
            warnings.append({
                "type": "consistency",
                "severity": "high",
                "message": "High sales variability detected. Consider this when using forecast data."
            })
        
        # Date span/Seasonality scoring (0-30 points)
        date_span = (df['ds'].max() - df['ds'].min()).days
        if date_span >= 365:
            score += 30
        elif date_span >= 270:
            score += 27
        elif date_span >= 180:
            score += 23
        elif date_span >= 90:
            score += 18
        elif date_span >= 60:
            score += 14
            warnings.append({
                "type": "date_span",
                "severity": "medium",
                "message": f"Only {date_span} days of history. Seasonal patterns may not be captured."
            })
        elif date_span >= 30:
            score += 10
            warnings.append({
                "type": "date_span",
                "severity": "high",
                "message": f"Limited history ({date_span} days). Forecast relies on short-term trends only."
            })
        elif date_span >= 14:
            score += 6
            warnings.append({
                "type": "date_span",
                "severity": "critical",
                "message": f"Very limited history ({date_span} days). Forecast accuracy will be significantly reduced."
            })
        else:
            score += 3
            warnings.append({
                "type": "date_span",
                "severity": "critical",
                "message": f"Minimal history ({date_span} days). This forecast should be used with extreme caution."
            })
        
        # Determine accuracy level based on final score
        if score >= 80:
            accuracy_level = "High"
        elif score >= 60:
            accuracy_level = "Medium"
        elif score >= 40:
            accuracy_level = "Low"
        else:
            accuracy_level = "Very Low"
        
        return min(score, 100.0), accuracy_level, warnings
    
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
