"""
XGBoost Model Architecture for Home Valuation

This module implements the XGBoost model architecture for home valuation in Clark County, Nevada.
It includes feature engineering, model training, hyperparameter tuning, and prediction functionality.
"""

import os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import joblib
import json
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HomeValuationModel:
    """
    XGBoost model for home valuation in Clark County, Nevada.
    """
    
    def __init__(self, model_dir='/home/ubuntu/xgboost-valuation/models'):
        """
        Initialize the home valuation model.
        
        Args:
            model_dir (str, optional): Directory to store model files.
        """
        self.model_dir = model_dir
        self.models = {}  # Dictionary to store models for different property types
        self.preprocessors = {}  # Dictionary to store preprocessors for different property types
        self.feature_importances = {}  # Dictionary to store feature importances
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
        # Define property types
        self.property_types = [
            'single_family',
            'condo',
            'townhouse',
            'multi_family'
        ]
        
        # Define feature groups
        self.feature_groups = {
            'property_features': [
                'bedrooms', 'bathrooms', 'square_feet', 'lot_size', 'year_built', 
                'stories', 'pool', 'garage_spaces', 'has_view', 'has_fireplace',
                'has_basement', 'renovation_year', 'quality_score', 'condition_score'
            ],
            'location_features': [
                'zip_code', 'latitude', 'longitude', 'school_rating', 'crime_score',
                'distance_to_strip', 'distance_to_airport', 'distance_to_downtown',
                'distance_to_freeway', 'distance_to_hospital'
            ],
            'neighborhood_features': [
                'median_income', 'population_density', 'percent_college_educated',
                'percent_owner_occupied', 'median_age', 'walkability_score',
                'avg_commute_time'
            ],
            'market_features': [
                'days_on_market', 'list_price', 'price_per_sqft', 'price_drops',
                'absorption_rate', 'inventory_months', 'median_market_time'
            ],
            'economic_features': [
                'mortgage_rate_30yr', 'unemployment_rate', 'gdp_growth_rate',
                'inflation_rate', 'housing_starts', 'building_permits',
                'home_price_index_change'
            ],
            'temporal_features': [
                'month_of_year', 'quarter', 'year', 'days_since_last_sale',
                'previous_sale_price', 'price_change_since_last_sale'
            ]
        }
    
    def prepare_data(self, data, property_type='single_family', train=True):
        """
        Prepare data for model training or prediction.
        
        Args:
            data (pandas.DataFrame): Input data.
            property_type (str, optional): Property type. Defaults to 'single_family'.
            train (bool, optional): Whether this is for training. Defaults to True.
            
        Returns:
            tuple: Prepared features and target (if train=True).
        """
        if property_type not in self.property_types:
            raise ValueError(f"Invalid property type: {property_type}. Must be one of {self.property_types}")
        
        # Make a copy of the data to avoid modifying the original
        df = data.copy()
        
        # Extract target variable if training
        if train:
            if 'sale_price' not in df.columns:
                raise ValueError("Data must contain 'sale_price' column for training")
            y = df['sale_price'].values
            df = df.drop('sale_price', axis=1)
        
        # Identify numeric and categorical columns
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Remove any target-related columns that might be in the data
        for col in ['sale_price', 'log_sale_price']:
            if col in numeric_cols:
                numeric_cols.remove(col)
        
        # Create or use preprocessor
        if train or property_type not in self.preprocessors:
            # Create preprocessor
            numeric_transformer = Pipeline(steps=[
                ('scaler', StandardScaler())
            ])
            
            categorical_transformer = Pipeline(steps=[
                ('onehot', OneHotEncoder(handle_unknown='ignore'))
            ])
            
            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', numeric_transformer, numeric_cols),
                    ('cat', categorical_transformer, categorical_cols)
                ]
            )
            
            if train:
                self.preprocessors[property_type] = preprocessor
        
        # Apply preprocessing
        if train:
            X = self.preprocessors[property_type].fit_transform(df)
            return X, y
        else:
            X = self.preprocessors[property_type].transform(df)
            return X
    
    def engineer_features(self, data):
        """
        Engineer features for the model.
        
        Args:
            data (pandas.DataFrame): Input data.
            
        Returns:
            pandas.DataFrame: Data with engineered features.
        """
        # Make a copy of the data to avoid modifying the original
        df = data.copy()
        
        # Handle missing values
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown')
        
        # Create derived features
        
        # Price per square foot
        if 'square_feet' in df.columns and df['square_feet'].min() > 0:
            if 'sale_price' in df.columns:
                df['price_per_sqft'] = df['sale_price'] / df['square_feet']
            elif 'list_price' in df.columns:
                df['price_per_sqft'] = df['list_price'] / df['square_feet']
        
        # Property age
        if 'year_built' in df.columns:
            current_year = datetime.now().year
            df['property_age'] = current_year - df['year_built']
        
        # Years since renovation
        if 'renovation_year' in df.columns:
            current_year = datetime.now().year
            df['years_since_renovation'] = current_year - df['renovation_year']
            # If renovation_year is 0 or null, use year_built
            if 'year_built' in df.columns:
                mask = (df['renovation_year'] == 0) | df['renovation_year'].isna()
                df.loc[mask, 'years_since_renovation'] = current_year - df.loc[mask, 'year_built']
        
        # Total rooms
        if 'bedrooms' in df.columns and 'bathrooms' in df.columns:
            df['total_rooms'] = df['bedrooms'] + df['bathrooms']
        
        # Bedroom to bathroom ratio
        if 'bedrooms' in df.columns and 'bathrooms' in df.columns and (df['bathrooms'] > 0).all():
            df['bed_bath_ratio'] = df['bedrooms'] / df['bathrooms']
        
        # Living area ratio (square feet per bedroom)
        if 'square_feet' in df.columns and 'bedrooms' in df.columns and (df['bedrooms'] > 0).all():
            df['living_area_ratio'] = df['square_feet'] / df['bedrooms']
        
        # Lot to house ratio
        if 'lot_size' in df.columns and 'square_feet' in df.columns and (df['square_feet'] > 0).all():
            df['lot_to_house_ratio'] = df['lot_size'] / df['square_feet']
        
        # Temporal features
        if 'sale_date' in df.columns:
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            df['month_of_year'] = df['sale_date'].dt.month
            df['quarter'] = df['sale_date'].dt.quarter
            df['year'] = df['sale_date'].dt.year
            df['day_of_week'] = df['sale_date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['is_summer'] = df['month_of_year'].isin([6, 7, 8]).astype(int)
            df['is_winter'] = df['month_of_year'].isin([12, 1, 2]).astype(int)
        
        # Previous sale features
        if 'previous_sale_date' in df.columns and 'previous_sale_price' in df.columns:
            df['previous_sale_date'] = pd.to_datetime(df['previous_sale_date'])
            if 'sale_date' in df.columns:
                df['days_since_last_sale'] = (df['sale_date'] - df['previous_sale_date']).dt.days
            
            if 'sale_price' in df.columns:
                df['price_change_since_last_sale'] = df['sale_price'] - df['previous_sale_price']
                df['price_change_pct'] = (df['sale_price'] - df['previous_sale_price']) / df['previous_sale_price'] * 100
        
        # Location-based features
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Las Vegas Strip coordinates
            strip_lat, strip_lon = 36.1147, -115.1728
            
            # McCarran International Airport coordinates
            airport_lat, airport_lon = 36.0840, -115.1537
            
            # Downtown Las Vegas coordinates
            downtown_lat, downtown_lon = 36.1699, -115.1398
            
            # Calculate distances
            df['distance_to_strip'] = self._haversine_distance(
                df['latitude'], df['longitude'], strip_lat, strip_lon
            )
            
            df['distance_to_airport'] = self._haversine_distance(
                df['latitude'], df['longitude'], airport_lat, airport_lon
            )
            
            df['distance_to_downtown'] = self._haversine_distance(
                df['latitude'], df['longitude'], downtown_lat, downtown_lon
            )
        
        # Neighborhood quality score (combined score)
        if all(col in df.columns for col in ['school_rating', 'crime_score', 'walkability_score']):
            # Normalize each score to 0-10 range if needed
            school_rating = df['school_rating'] if df['school_rating'].max() <= 10 else df['school_rating'] / 10
            crime_score = df['crime_score'] if df['crime_score'].max() <= 10 else df['crime_score'] / 10
            walkability_score = df['walkability_score'] if df['walkability_score'].max() <= 10 else df['walkability_score'] / 10
            
            # Invert crime score (higher is better)
            crime_score_inverted = 10 - crime_score
            
            # Calculate neighborhood quality score (weighted average)
            df['neighborhood_quality'] = (
                school_rating * 0.4 +
                crime_score_inverted * 0.4 +
                walkability_score * 0.2
            )
        
        # Economic indicators
        if 'mortgage_rate_30yr' in df.columns and 'unemployment_rate' in df.columns:
            # Affordability index (inverse relationship with mortgage rate)
            df['affordability_index'] = 10 - (df['mortgage_rate_30yr'] / 10 * 10)
            
            # Economic health index (inverse relationship with unemployment)
            df['economic_health_index'] = 10 - (df['unemployment_rate'] / 10 * 10)
        
        # Log transform of target variable (if present)
        if 'sale_price' in df.columns:
            df['log_sale_price'] = np.log1p(df['sale_price'])
        
        # Log transform of numeric features with skewed distributions
        skewed_features = ['square_feet', 'lot_size', 'price_per_sqft']
        for feature in skewed_features:
            if feature in df.columns:
                df[f'log_{feature}'] = np.log1p(df[feature])
        
        # One-hot encoding for categorical variables
        # This will be handled by the preprocessor in prepare_data()
        
        return df
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the Haversine distance between two points in kilometers.
        
        Args:
            lat1 (float or Series): Latitude of first point.
            lon1 (float or Series): Longitude of first point.
            lat2 (float): Latitude of second point.
            lon2 (float): Longitude of second point.
            
        Returns:
            float or Series: Distance in kilometers.
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Radius of Earth in kilometers
        
        return c * r
    
    def train_model(self, data, property_type='single_family', tune_hyperparams=True):
        """
        Train an XGBoost model for home valuation.
        
        Args:
            data (pandas.DataFrame): Training data.
            property_type (str, optional): Property type. Defaults to 'single_family'.
            tune_hyperparams (bool, optional): Whether to tune hyperparameters. Defaults to True.
            
        Returns:
            dict: Training results.
        """
        logger.info(f"Training model for property type: {property_type}")
        
        # Filter data for the specific property type
        if 'property_type' in data.columns:
            property_data = data[data['property_type'] == property_type].copy()
            if len(property_data) == 0:
                logger.warning(f"No data found for property type: {property_type}")
                return {"error": f"No data found for property type: {property_type}"}
        else:
            property_data = data.copy()
        
        # Engineer features
        property_data = self.engineer_features(property_data)
        
        # Prepare data
        X, y = self.prepare_data(property_data, property_type=property_type, train=True)
        
        # Split data into train and validation sets
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Create DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)
        
        # Define base parameters
        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'eta': 0.1,
            'max_depth': 6,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 1,
            'gamma': 0,
            'seed': 42
        }
        
        # Tune hyperparameters if requested
        if tune_hyperparams:
            logger.info("Tuning hyperparameters...")
            best_params = self._tune_hyperparameters(X_train, y_train)
            params.update(best_params)
            logger.info(f"Best hyperparameters: {best_params}")
        
        # Train the model
        logger.info("Training XGBoost model...")
        evallist = [(dtrain, 'train'), (dval, 'validation')]
        num_round = 1000
        
        # Early stopping
        early_stopping_rounds = 50
        
        # Train the model
        bst = xgb.train(
            params,
            dtrain,
            num_round,
            evallist,
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=100
        )
        
        # Save the model
        model_path = os.path.join(self.model_dir, f"{property_type}_model.json")
        bst.save_model(model_path)
        
        # Save the model in memory
        self.models[property_type] = bst
        
        # Get feature importances
        importance = bst.get_score(importance_type='gain')
        self.feature_importances[property_type] = importance
        
        # Save feature importances
        importance_path = os.path.join(self.model_dir, f"{property_type}_feature_importance.json")
        with open(importance_path, 'w') as f:
            json.dump(importance, f)
        
        # Evaluate the model
        y_pred_train = bst.predict(dtrain)
        y_pred_val = bst.predict(dval)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
        
        train_mae = mean_absolute_error(y_train, y_pred_train)
        val_mae = mean_absolute_error(y_val, y_pred_val)
        
        train_r2 = r2_score(y_train, y_pred_train)
        val_r2 = r2_score(y_val, y_pred_val)
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        train_mape = np.mean(np.abs((y_train - y_pred_train) / y_train)) * 100
        val_mape = np.mean(np.abs((y_val - y_pred_val) / y_val)) * 100
        
        logger.info(f"Training RMSE: {train_rmse:.2f}")
        logger.info(f"Validation RMSE: {val_rmse:.2f}")
        logger.info(f"Training MAE: {train_mae:.2f}")
        logger.info(f"Validation MAE: {val_mae:.2f}")
        logger.info(f"Training R²: {train_r2:.4f}")
        logger.info(f"Validation R²: {val_r2:.4f}")
        logger.info(f"Training MAPE: {train_mape:.2f}%")
        logger.info(f"Validation MAPE: {val_mape:.2f}%")
        
        # Create evaluation plots
        self._create_evaluation_plots(y_val, y_pred_val, property_type)
        
        # Return training results
        return {
            "property_type": property_type,
            "model_path": model_path,
            "feature_importance_path": importance_path,
            "metrics": {
                "train_rmse": train_rmse,
                "val_rmse": val_rmse,
                "train_mae": train_mae,
                "val_mae": val_mae,
                "train_r2": train_r2,
                "val_r2": val_r2,
                "train_mape": train_mape,
                "val_mape": val_mape
            },
            "params": params,
            "top_features": sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def _tune_hyperparameters(self, X_train, y_train):
        """
        Tune hyperparameters using cross-validation.
        
        Args:
            X_train (numpy.ndarray): Training features.
            y_train (numpy.ndarray): Training target.
            
        Returns:
            dict: Best hyperparameters.
        """
        # Create parameter grid
        param_grid = {
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1, 0.2],
            'n_estimators': [100, 200, 300],
            'subsample': [0.6, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0],
            'min_child_weight': [1, 3, 5],
            'gamma': [0, 0.1, 0.2]
        }
        
        # Create XGBoost regressor
        xgb_model = xgb.XGBRegressor(
            objective='reg:squarederror',
            eval_metric='rmse',
            seed=42
        )
        
        # Create cross-validation
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        
        # Create grid search
        grid_search = GridSearchCV(
            estimator=xgb_model,
            param_grid=param_grid,
            scoring='neg_mean_squared_error',
            cv=cv,
            verbose=1,
            n_jobs=-1
        )
        
        # Fit grid search
        grid_search.fit(X_train, y_train)
        
        # Get best parameters
        best_params = grid_search.best_params_
        
        # Convert to XGBoost API format
        xgb_params = {
            'max_depth': best_params['max_depth'],
            'eta': best_params['learning_rate'],
            'subsample': best_params['subsample'],
            'colsample_bytree': best_params['colsample_bytree'],
            'min_child_weight': best_params['min_child_weight'],
            'gamma': best_params['gamma']
        }
        
        return xgb_params
    
    def _create_evaluation_plots(self, y_true, y_pred, property_type):
        """
        Create evaluation plots for model performance.
        
        Args:
            y_true (numpy.ndarray): True values.
            y_pred (numpy.ndarray): Predicted values.
            property_type (str): Property type.
        """
        # Create directory for plots
        plots_dir = os.path.join(self.model_dir, 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        
        # Scatter plot of predicted vs actual values
        plt.figure(figsize=(10, 6))
        plt.scatter(y_true, y_pred, alpha=0.5)
        plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--')
        plt.xlabel('Actual Values')
        plt.ylabel('Predicted Values')
        plt.title(f'Actual vs Predicted Values - {property_type}')
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, f'{property_type}_scatter.png'))
        plt.close()
        
        # Residual plot
        residuals = y_true - y_pred
        plt.figure(figsize=(10, 6))
        plt.scatter(y_pred, residuals, alpha=0.5)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Predicted Values')
        plt.ylabel('Residuals')
        plt.title(f'Residual Plot - {property_type}')
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, f'{property_type}_residuals.png'))
        plt.close()
        
        # Distribution of residuals
        plt.figure(figsize=(10, 6))
        sns.histplot(residuals, kde=True)
        plt.xlabel('Residuals')
        plt.ylabel('Frequency')
        plt.title(f'Distribution of Residuals - {property_type}')
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, f'{property_type}_residuals_dist.png'))
        plt.close()
        
        # Feature importance plot (if available)
        if property_type in self.feature_importances:
            importance = self.feature_importances[property_type]
            importance_df = pd.DataFrame({
                'Feature': list(importance.keys()),
                'Importance': list(importance.values())
            })
            importance_df = importance_df.sort_values('Importance', ascending=False).head(20)
            
            plt.figure(figsize=(12, 8))
            sns.barplot(x='Importance', y='Feature', data=importance_df)
            plt.title(f'Feature Importance - {property_type}')
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, f'{property_type}_feature_importance.png'))
            plt.close()
    
    def load_model(self, property_type='single_family'):
        """
        Load a trained model.
        
        Args:
            property_type (str, optional): Property type. Defaults to 'single_family'.
            
        Returns:
            bool: Whether the model was loaded successfully.
        """
        model_path = os.path.join(self.model_dir, f"{property_type}_model.json")
        
        if not os.path.exists(model_path):
            logger.warning(f"Model not found for property type: {property_type}")
            return False
        
        # Load the model
        bst = xgb.Booster()
        bst.load_model(model_path)
        self.models[property_type] = bst
        
        # Load feature importances if available
        importance_path = os.path.join(self.model_dir, f"{property_type}_feature_importance.json")
        if os.path.exists(importance_path):
            with open(importance_path, 'r') as f:
                self.feature_importances[property_type] = json.load(f)
        
        return True
    
    def predict(self, data, property_type='single_family'):
        """
        Make predictions using the trained model.
        
        Args:
            data (pandas.DataFrame): Input data.
            property_type (str, optional): Property type. Defaults to 'single_family'.
            
        Returns:
            numpy.ndarray: Predicted values.
        """
        # Check if model is loaded
        if property_type not in self.models:
            loaded = self.load_model(property_type)
            if not loaded:
                raise ValueError(f"Model not found for property type: {property_type}")
        
        # Engineer features
        data = self.engineer_features(data)
        
        # Prepare data
        X = self.prepare_data(data, property_type=property_type, train=False)
        
        # Create DMatrix
        dtest = xgb.DMatrix(X)
        
        # Make predictions
        predictions = self.models[property_type].predict(dtest)
        
        return predictions
    
    def predict_with_confidence(self, data, property_type='single_family', confidence_level=0.95):
        """
        Make predictions with confidence intervals.
        
        Args:
            data (pandas.DataFrame): Input data.
            property_type (str, optional): Property type. Defaults to 'single_family'.
            confidence_level (float, optional): Confidence level. Defaults to 0.95.
            
        Returns:
            dict: Predictions with confidence intervals.
        """
        # Make point predictions
        predictions = self.predict(data, property_type)
        
        # Get model metrics (assuming model was trained and metrics were saved)
        metrics_path = os.path.join(self.model_dir, f"{property_type}_metrics.json")
        
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            # Get RMSE from metrics
            rmse = metrics.get('val_rmse', 0.1 * np.mean(predictions))
        else:
            # If metrics not available, use a percentage of the prediction as an approximation
            rmse = 0.1 * np.mean(predictions)
        
        # Calculate confidence intervals
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        margin_of_error = z_score * rmse
        
        lower_bound = predictions - margin_of_error
        upper_bound = predictions + margin_of_error
        
        # Ensure lower bound is not negative
        lower_bound = np.maximum(lower_bound, 0)
        
        # Calculate confidence interval width as a percentage of the prediction
        ci_width_pct = (upper_bound - lower_bound) / predictions * 100
        
        # Calculate prediction intervals (wider than confidence intervals)
        pi_z_score = stats.norm.ppf((1 + 0.9) / 2)  # 90% prediction interval
        pi_margin = pi_z_score * rmse * 1.5  # Wider than confidence interval
        
        pi_lower = predictions - pi_margin
        pi_upper = predictions + pi_margin
        
        # Ensure lower bound is not negative
        pi_lower = np.maximum(pi_lower, 0)
        
        return {
            'predictions': predictions,
            'confidence_intervals': {
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'confidence_level': confidence_level,
                'width_percentage': ci_width_pct
            },
            'prediction_intervals': {
                'lower_bound': pi_lower,
                'upper_bound': pi_upper,
                'confidence_level': 0.9
            }
        }
    
    def evaluate_model(self, data, property_type='single_family'):
        """
        Evaluate the model on test data.
        
        Args:
            data (pandas.DataFrame): Test data.
            property_type (str, optional): Property type. Defaults to 'single_family'.
            
        Returns:
            dict: Evaluation metrics.
        """
        # Check if model is loaded
        if property_type not in self.models:
            loaded = self.load_model(property_type)
            if not loaded:
                raise ValueError(f"Model not found for property type: {property_type}")
        
        # Filter data for the specific property type
        if 'property_type' in data.columns:
            property_data = data[data['property_type'] == property_type].copy()
            if len(property_data) == 0:
                logger.warning(f"No data found for property type: {property_type}")
                return {"error": f"No data found for property type: {property_type}"}
        else:
            property_data = data.copy()
        
        # Check if target variable exists
        if 'sale_price' not in property_data.columns:
            raise ValueError("Data must contain 'sale_price' column for evaluation")
        
        # Engineer features
        property_data = self.engineer_features(property_data)
        
        # Get target variable
        y_true = property_data['sale_price'].values
        
        # Make predictions
        y_pred = self.predict(property_data, property_type)
        
        # Calculate metrics
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        # Calculate residuals
        residuals = y_true - y_pred
        
        # Calculate residual statistics
        mean_residual = np.mean(residuals)
        std_residual = np.std(residuals)
        
        # Create evaluation plots
        self._create_evaluation_plots(y_true, y_pred, f"{property_type}_test")
        
        # Save metrics
        metrics = {
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "mape": mape,
            "mean_residual": mean_residual,
            "std_residual": std_residual
        }
        
        metrics_path = os.path.join(self.model_dir, f"{property_type}_metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)
        
        return metrics
    
    def get_feature_importance(self, property_type='single_family'):
        """
        Get feature importance for a trained model.
        
        Args:
            property_type (str, optional): Property type. Defaults to 'single_family'.
            
        Returns:
            dict: Feature importance.
        """
        if property_type not in self.feature_importances:
            # Try to load from file
            importance_path = os.path.join(self.model_dir, f"{property_type}_feature_importance.json")
            if os.path.exists(importance_path):
                with open(importance_path, 'r') as f:
                    self.feature_importances[property_type] = json.load(f)
            else:
                logger.warning(f"Feature importance not found for property type: {property_type}")
                return {}
        
        return self.feature_importances[property_type]
    
    def explain_valuation(self, data, property_type='single_family'):
        """
        Explain the valuation for a property.
        
        Args:
            data (pandas.DataFrame): Property data.
            property_type (str, optional): Property type. Defaults to 'single_family'.
            
        Returns:
            dict: Valuation explanation.
        """
        # Make prediction with confidence interval
        prediction_result = self.predict_with_confidence(data, property_type)
        
        # Get feature importance
        feature_importance = self.get_feature_importance(property_type)
        
        # Engineer features for the property
        engineered_data = self.engineer_features(data)
        
        # Get top features and their values
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        top_feature_names = [f[0] for f in top_features]
        
        # Get feature values for the property
        feature_values = {}
        for feature in top_feature_names:
            if feature in engineered_data.columns:
                feature_values[feature] = engineered_data[feature].values[0]
        
        # Calculate value drivers
        value_drivers = []
        for feature, importance in top_features:
            if feature in feature_values:
                value_drivers.append({
                    "feature": feature,
                    "importance": importance,
                    "value": feature_values.get(feature),
                    "impact_percentage": (importance / sum(feature_importance.values())) * 100
                })
        
        # Create explanation
        explanation = {
            "property_type": property_type,
            "predicted_value": prediction_result['predictions'][0],
            "confidence_interval": {
                "lower": prediction_result['confidence_intervals']['lower_bound'][0],
                "upper": prediction_result['confidence_intervals']['upper_bound'][0],
                "confidence_level": prediction_result['confidence_intervals']['confidence_level']
            },
            "value_drivers": value_drivers,
            "feature_importance": dict(top_features)
        }
        
        return explanation
    
    def train_all_models(self, data, tune_hyperparams=True):
        """
        Train models for all property types.
        
        Args:
            data (pandas.DataFrame): Training data.
            tune_hyperparams (bool, optional): Whether to tune hyperparameters. Defaults to True.
            
        Returns:
            dict: Training results for all property types.
        """
        results = {}
        
        for property_type in self.property_types:
            logger.info(f"Training model for property type: {property_type}")
            
            # Filter data for the specific property type
            if 'property_type' in data.columns:
                property_data = data[data['property_type'] == property_type].copy()
                if len(property_data) == 0:
                    logger.warning(f"No data found for property type: {property_type}")
                    results[property_type] = {"error": f"No data found for property type: {property_type}"}
                    continue
            else:
                property_data = data.copy()
            
            # Train model
            result = self.train_model(property_data, property_type, tune_hyperparams)
            results[property_type] = result
        
        return results
    
    def retrain_models(self, data, schedule='monthly'):
        """
        Schedule model retraining based on market conditions.
        
        Args:
            data (pandas.DataFrame): New training data.
            schedule (str, optional): Retraining schedule. Defaults to 'monthly'.
            
        Returns:
            dict: Retraining results.
        """
        # Get current date
        current_date = datetime.now()
        
        # Get last training date
        last_training_path = os.path.join(self.model_dir, 'last_training.json')
        
        if os.path.exists(last_training_path):
            with open(last_training_path, 'r') as f:
                last_training = json.load(f)
        else:
            last_training = {
                "date": (current_date - timedelta(days=365)).strftime('%Y-%m-%d'),
                "property_types": {}
            }
        
        # Convert last training date to datetime
        last_training_date = datetime.strptime(last_training['date'], '%Y-%m-%d')
        
        # Check if retraining is needed based on schedule
        retrain = False
        
        if schedule == 'daily':
            retrain = (current_date - last_training_date).days >= 1
        elif schedule == 'weekly':
            retrain = (current_date - last_training_date).days >= 7
        elif schedule == 'monthly':
            retrain = (current_date - last_training_date).days >= 30
        elif schedule == 'quarterly':
            retrain = (current_date - last_training_date).days >= 90
        elif schedule == 'market_change':
            # Check if market conditions have changed significantly
            # This would require additional logic to detect market changes
            retrain = True
        
        if not retrain:
            logger.info(f"Retraining not needed based on schedule: {schedule}")
            return {"status": "Retraining not needed"}
        
        # Retrain models
        logger.info("Retraining models...")
        results = self.train_all_models(data)
        
        # Update last training date
        last_training = {
            "date": current_date.strftime('%Y-%m-%d'),
            "property_types": {pt: results[pt].get('metrics', {}) for pt in self.property_types if pt in results}
        }
        
        with open(last_training_path, 'w') as f:
            json.dump(last_training, f)
        
        return {
            "status": "Models retrained",
            "results": results
        }

# Example usage
if __name__ == "__main__":
    # For testing purposes
    model = HomeValuationModel()
    
    # Create synthetic data for testing
    np.random.seed(42)
    n_samples = 1000
    
    data = pd.DataFrame({
        'bedrooms': np.random.randint(1, 6, n_samples),
        'bathrooms': np.random.uniform(1, 4, n_samples).round(1),
        'square_feet': np.random.randint(800, 4000, n_samples),
        'lot_size': np.random.randint(2000, 20000, n_samples),
        'year_built': np.random.randint(1950, 2023, n_samples),
        'property_type': np.random.choice(['single_family', 'condo', 'townhouse', 'multi_family'], n_samples),
        'zip_code': np.random.choice(['89101', '89102', '89103', '89104', '89109', '89117', '89128', '89134', '89144', '89148'], n_samples),
        'latitude': np.random.uniform(36.0, 36.3, n_samples),
        'longitude': np.random.uniform(-115.3, -115.0, n_samples),
        'school_rating': np.random.uniform(1, 10, n_samples).round(1),
        'crime_score': np.random.uniform(1, 10, n_samples).round(1),
        'walkability_score': np.random.uniform(1, 10, n_samples).round(1),
        'mortgage_rate_30yr': np.random.uniform(3, 7, n_samples).round(2),
        'unemployment_rate': np.random.uniform(3, 8, n_samples).round(1)
    })
    
    # Generate synthetic sale prices based on features
    sale_price = (
        100000 +
        data['bedrooms'] * 25000 +
        data['bathrooms'] * 15000 +
        data['square_feet'] * 100 +
        (2023 - data['year_built']) * -500 +
        data['school_rating'] * 10000 +
        (10 - data['crime_score']) * 5000 +
        data['walkability_score'] * 2000 +
        np.random.normal(0, 50000, n_samples)  # Add some noise
    )
    
    # Ensure sale prices are positive
    data['sale_price'] = np.maximum(sale_price, 100000)
    
    # Train model for single-family homes
    result = model.train_model(data, property_type='single_family', tune_hyperparams=False)
    print(json.dumps(result, indent=2))
    
    # Make predictions for a new property
    new_property = pd.DataFrame({
        'bedrooms': [4],
        'bathrooms': [2.5],
        'square_feet': [2500],
        'lot_size': [8000],
        'year_built': [2010],
        'zip_code': ['89117'],
        'latitude': [36.15],
        'longitude': [-115.25],
        'school_rating': [8.5],
        'crime_score': [3.0],
        'walkability_score': [7.0],
        'mortgage_rate_30yr': [5.5],
        'unemployment_rate': [4.5]
    })
    
    prediction = model.predict(new_property, property_type='single_family')
    print(f"Predicted value: ${prediction[0]:,.2f}")
    
    # Get prediction with confidence interval
    prediction_with_ci = model.predict_with_confidence(new_property, property_type='single_family')
    print(f"Prediction with 95% confidence interval: ${prediction_with_ci['predictions'][0]:,.2f} " +
          f"(${prediction_with_ci['confidence_intervals']['lower_bound'][0]:,.2f} - " +
          f"${prediction_with_ci['confidence_intervals']['upper_bound'][0]:,.2f})")
    
    # Explain valuation
    explanation = model.explain_valuation(new_property, property_type='single_family')
    print(json.dumps(explanation, indent=2))
