"""
FRED/BLS Economic Data API Integration Module

This module provides functions to interact with the Federal Reserve Economic Data (FRED)
and Bureau of Labor Statistics (BLS) APIs for retrieving economic indicators relevant
to the real estate market in Clark County, Nevada.
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EconomicDataAPI:
    """
    Class for interacting with FRED and BLS APIs for economic data.
    """
    
    def __init__(self, fred_api_key=None, bls_api_key=None):
        """
        Initialize the Economic Data API client.
        
        Args:
            fred_api_key (str, optional): FRED API key. If not provided, will look for FRED_API_KEY environment variable.
            bls_api_key (str, optional): BLS API key. If not provided, will look for BLS_API_KEY environment variable.
        """
        self.fred_api_key = fred_api_key or os.environ.get('FRED_API_KEY')
        if not self.fred_api_key:
            logger.warning("No FRED API key provided. Set FRED_API_KEY environment variable or pass fred_api_key parameter.")
        
        self.bls_api_key = bls_api_key or os.environ.get('BLS_API_KEY')
        if not self.bls_api_key:
            logger.warning("No BLS API key provided. Set BLS_API_KEY environment variable or pass bls_api_key parameter.")
        
        self.fred_base_url = "https://api.stlouisfed.org/fred"
        self.bls_base_url = "https://api.bls.gov/publicAPI/v2"
        
        # Rate limits
        self.fred_rate_limit = 120  # Requests per minute
        self.bls_rate_limit = 500   # Requests per day
        
        self.fred_request_timestamps = []
        self.bls_request_timestamps = []
        
        # Common FRED series IDs for real estate and economic indicators
        self.series_ids = {
            "mortgage_30yr": "MORTGAGE30US",       # 30-Year Fixed Rate Mortgage Average
            "mortgage_15yr": "MORTGAGE15US",       # 15-Year Fixed Rate Mortgage Average
            "unemployment_national": "UNRATE",     # Unemployment Rate
            "unemployment_nevada": "NVUR",         # Unemployment Rate in Nevada
            "unemployment_las_vegas": "LASV832URN",# Unemployment Rate in Las Vegas-Henderson-Paradise, NV
            "housing_starts": "HOUST",             # Housing Starts: Total: New Privately Owned Housing Units Started
            "home_price_index": "CSUSHPINSA",      # S&P/Case-Shiller U.S. National Home Price Index
            "las_vegas_home_price": "LVXRNSA",     # S&P/Case-Shiller NV-Las Vegas Home Price Index
            "gdp_growth": "A191RL1Q225SBEA",       # Real Gross Domestic Product
            "inflation": "CPIAUCSL",               # Consumer Price Index for All Urban Consumers
            "construction_spending": "TTLCONS",    # Total Construction Spending
            "building_permits": "PERMIT",          # New Private Housing Units Authorized by Building Permits
            "median_household_income": "MEHOINUSA646N", # Median Household Income in the United States
            "population_growth": "POPTHM",         # Population
            "rental_vacancy": "RRVRUSQ156N",       # Rental Vacancy Rate for the United States
            "homeownership_rate": "RHORUSQ156N",   # Homeownership Rate for the United States
            "housing_inventory": "MSACSR",         # Monthly Supply of Houses in the United States
            "new_home_sales": "HSN1F",             # New One Family Houses Sold: United States
            "existing_home_sales": "EXHOSLUSM495S" # Existing Home Sales
        }
        
        # Common BLS series IDs for real estate and economic indicators
        self.bls_series_ids = {
            "cpi_housing": "CUUR0000SAH",          # Consumer Price Index for Housing
            "cpi_rent": "CUUR0000SEHA",            # Consumer Price Index for Rent of Primary Residence
            "cpi_owners_equivalent": "CUUR0000SEHC", # Consumer Price Index for Owners' Equivalent Rent of Residences
            "employment_construction": "CES2000000001", # Employment in Construction
            "employment_real_estate": "CES5553000001", # Employment in Real Estate
            "wages_construction": "CES2000000030",  # Average Hourly Earnings of Production and Nonsupervisory Employees, Construction
            "wages_real_estate": "CES5553000030",   # Average Hourly Earnings of Production and Nonsupervisory Employees, Real Estate
            "ppi_construction": "WPUIP2300001",     # Producer Price Index by Industry: New Warehouse Building Construction
            "ppi_materials": "WPUIP2310001"         # Producer Price Index by Industry: New School Building Construction
        }
    
    def _check_fred_rate_limit(self):
        """
        Check if we're within FRED API rate limits and wait if necessary.
        """
        now = time.time()
        # Remove timestamps older than 1 minute
        self.fred_request_timestamps = [ts for ts in self.fred_request_timestamps if now - ts < 60]
        
        if len(self.fred_request_timestamps) >= self.fred_rate_limit:
            # Wait until we're under the rate limit
            sleep_time = 60 - (now - self.fred_request_timestamps[0])
            if sleep_time > 0:
                logger.info(f"FRED API rate limit reached. Waiting {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
        
        # Add current timestamp
        self.fred_request_timestamps.append(time.time())
    
    def _check_bls_rate_limit(self):
        """
        Check if we're within BLS API rate limits and wait if necessary.
        """
        now = time.time()
        # Remove timestamps older than 24 hours
        self.bls_request_timestamps = [ts for ts in self.bls_request_timestamps if now - ts < 86400]
        
        if len(self.bls_request_timestamps) >= self.bls_rate_limit:
            logger.error("BLS API daily rate limit reached.")
            raise Exception("BLS API daily rate limit reached.")
        
        # Add current timestamp
        self.bls_request_timestamps.append(time.time())
    
    def get_fred_series(self, series_id, start_date=None, end_date=None, frequency=None):
        """
        Get time series data from FRED.
        
        Args:
            series_id (str): FRED series ID.
            start_date (str, optional): Start date in 'YYYY-MM-DD' format.
            end_date (str, optional): End date in 'YYYY-MM-DD' format.
            frequency (str, optional): Data frequency ('d', 'w', 'bw', 'm', 'q', 'sa', 'a').
            
        Returns:
            dict: Time series data.
        """
        self._check_fred_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "series_id": series_id,
            "api_key": self.fred_api_key,
            "file_type": "json"
        }
        
        if start_date:
            params["observation_start"] = start_date
        
        if end_date:
            params["observation_end"] = end_date
        
        if frequency:
            params["frequency"] = frequency
        
        try:
            response = requests.get(
                f"{self.fred_base_url}/series/observations",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}")
            return {"error": str(e)}
    
    def get_bls_series(self, series_ids, start_year=None, end_year=None):
        """
        Get time series data from BLS.
        
        Args:
            series_ids (list): List of BLS series IDs.
            start_year (int, optional): Start year.
            end_year (int, optional): End year.
            
        Returns:
            dict: Time series data.
        """
        self._check_bls_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Set default years if not provided
        if not start_year:
            start_year = datetime.now().year - 10
        
        if not end_year:
            end_year = datetime.now().year
        
        data = {
            "seriesid": series_ids,
            "startyear": str(start_year),
            "endyear": str(end_year),
            "registrationkey": self.bls_api_key
        }
        
        try:
            response = requests.post(
                f"{self.bls_base_url}/timeseries/data/",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching BLS series: {e}")
            return {"error": str(e)}
    
    def get_mortgage_rates(self, months=12):
        """
        Get mortgage rate trends.
        
        Args:
            months (int, optional): Number of months of data to retrieve. Defaults to 12.
            
        Returns:
            dict: Mortgage rate trends.
        """
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30.44)  # Approximate days per month
        
        # Get 30-year and 15-year mortgage rates
        mortgage_30yr = self.get_fred_series(
            self.series_ids["mortgage_30yr"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        mortgage_15yr = self.get_fred_series(
            self.series_ids["mortgage_15yr"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Check for errors
        if "error" in mortgage_30yr or "error" in mortgage_15yr:
            return {"error": "Error fetching mortgage rates"}
        
        # Process the data
        rates_30yr = mortgage_30yr.get("observations", [])
        rates_15yr = mortgage_15yr.get("observations", [])
        
        # Calculate current rates (most recent)
        current_30yr = float(rates_30yr[-1]["value"]) if rates_30yr and rates_30yr[-1]["value"] != "." else None
        current_15yr = float(rates_15yr[-1]["value"]) if rates_15yr and rates_15yr[-1]["value"] != "." else None
        
        # Calculate average rates
        valid_rates_30yr = [float(r["value"]) for r in rates_30yr if r["value"] != "."]
        valid_rates_15yr = [float(r["value"]) for r in rates_15yr if r["value"] != "."]
        
        avg_30yr = sum(valid_rates_30yr) / len(valid_rates_30yr) if valid_rates_30yr else None
        avg_15yr = sum(valid_rates_15yr) / len(valid_rates_15yr) if valid_rates_15yr else None
        
        # Calculate min and max rates
        min_30yr = min(valid_rates_30yr) if valid_rates_30yr else None
        max_30yr = max(valid_rates_30yr) if valid_rates_30yr else None
        min_15yr = min(valid_rates_15yr) if valid_rates_15yr else None
        max_15yr = max(valid_rates_15yr) if valid_rates_15yr else None
        
        # Calculate trend (positive means increasing rates)
        trend_30yr = valid_rates_30yr[-1] - valid_rates_30yr[0] if len(valid_rates_30yr) > 1 else 0
        trend_15yr = valid_rates_15yr[-1] - valid_rates_15yr[0] if len(valid_rates_15yr) > 1 else 0
        
        return {
            "current_rates": {
                "30_year_fixed": current_30yr,
                "15_year_fixed": current_15yr
            },
            "average_rates": {
                "30_year_fixed": avg_30yr,
                "15_year_fixed": avg_15yr
            },
            "min_rates": {
                "30_year_fixed": min_30yr,
                "15_year_fixed": min_15yr
            },
            "max_rates": {
                "30_year_fixed": max_30yr,
                "15_year_fixed": max_15yr
            },
            "trends": {
                "30_year_fixed": trend_30yr,
                "15_year_fixed": trend_15yr
            },
            "data": {
                "30_year_fixed": rates_30yr,
                "15_year_fixed": rates_15yr
            }
        }
    
    def get_unemployment_data(self, months=12):
        """
        Get unemployment rate data for the US and Nevada.
        
        Args:
            months (int, optional): Number of months of data to retrieve. Defaults to 12.
            
        Returns:
            dict: Unemployment rate data.
        """
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30.44)  # Approximate days per month
        
        # Get unemployment rates
        unemployment_national = self.get_fred_series(
            self.series_ids["unemployment_national"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        unemployment_nevada = self.get_fred_series(
            self.series_ids["unemployment_nevada"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        unemployment_las_vegas = self.get_fred_series(
            self.series_ids["unemployment_las_vegas"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Check for errors
        if "error" in unemployment_national or "error" in unemployment_nevada or "error" in unemployment_las_vegas:
            return {"error": "Error fetching unemployment data"}
        
        # Process the data
        rates_national = unemployment_national.get("observations", [])
        rates_nevada = unemployment_nevada.get("observations", [])
        rates_las_vegas = unemployment_las_vegas.get("observations", [])
        
        # Calculate current rates (most recent)
        current_national = float(rates_national[-1]["value"]) if rates_national and rates_national[-1]["value"] != "." else None
        current_nevada = float(rates_nevada[-1]["value"]) if rates_nevada and rates_nevada[-1]["value"] != "." else None
        current_las_vegas = float(rates_las_vegas[-1]["value"]) if rates_las_vegas and rates_las_vegas[-1]["value"] != "." else None
        
        # Calculate trends
        valid_rates_national = [float(r["value"]) for r in rates_national if r["value"] != "."]
        valid_rates_nevada = [float(r["value"]) for r in rates_nevada if r["value"] != "."]
        valid_rates_las_vegas = [float(r["value"]) for r in rates_las_vegas if r["value"] != "."]
        
        trend_national = valid_rates_national[-1] - valid_rates_national[0] if len(valid_rates_national) > 1 else 0
        trend_nevada = valid_rates_nevada[-1] - valid_rates_nevada[0] if len(valid_rates_nevada) > 1 else 0
        trend_las_vegas = valid_rates_las_vegas[-1] - valid_rates_las_vegas[0] if len(valid_rates_las_vegas) > 1 else 0
        
        return {
            "current_rates": {
                "national": current_national,
                "nevada": current_nevada,
                "las_vegas": current_las_vegas
            },
            "trends": {
                "national": trend_national,
                "nevada": trend_nevada,
                "las_vegas": trend_las_vegas
            },
            "data": {
                "national": rates_national,
                "nevada": rates_nevada,
                "las_vegas": rates_las_vegas
            }
        }
    
    def get_home_price_trends(self, months=60):
        """
        Get home price trends for the US and Las Vegas.
        
        Args:
            months (int, optional): Number of months of data to retrieve. Defaults to 60 (5 years).
            
        Returns:
            dict: Home price trends.
        """
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30.44)  # Approximate days per month
        
        # Get home price indices
        home_price_index = self.get_fred_series(
            self.series_ids["home_price_index"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        las_vegas_home_price = self.get_fred_series(
            self.series_ids["las_vegas_home_price"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Check for errors
        if "error" in home_price_index or "error" in las_vegas_home_price:
            return {"error": "Error fetching home price data"}
        
        # Process the data
        prices_national = home_price_index.get("observations", [])
        prices_las_vegas = las_vegas_home_price.get("observations", [])
        
        # Calculate current indices (most recent)
        current_national = float(prices_national[-1]["value"]) if prices_national and prices_national[-1]["value"] != "." else None
        current_las_vegas = float(prices_las_vegas[-1]["value"]) if prices_las_vegas and prices_las_vegas[-1]["value"] != "." else None
        
        # Calculate year-over-year changes
        valid_prices_national = [(r["date"], float(r["value"])) for r in prices_national if r["value"] != "."]
        valid_prices_las_vegas = [(r["date"], float(r["value"])) for r in prices_las_vegas if r["value"] != "."]
        
        # Calculate 1-year change
        one_year_ago_national = None
        one_year_ago_las_vegas = None
        
        if len(valid_prices_national) > 12:
            one_year_ago_national = valid_prices_national[-13][1]  # Approximately 1 year ago
        
        if len(valid_prices_las_vegas) > 12:
            one_year_ago_las_vegas = valid_prices_las_vegas[-13][1]  # Approximately 1 year ago
        
        yoy_change_national = ((current_national / one_year_ago_national) - 1) * 100 if current_national and one_year_ago_national else None
        yoy_change_las_vegas = ((current_las_vegas / one_year_ago_las_vegas) - 1) * 100 if current_las_vegas and one_year_ago_las_vegas else None
        
        # Calculate 5-year change
        five_years_ago_national = None
        five_years_ago_las_vegas = None
        
        if len(valid_prices_national) > 60:
            five_years_ago_national = valid_prices_national[-61][1]  # Approximately 5 years ago
        
        if len(valid_prices_las_vegas) > 60:
            five_years_ago_las_vegas = valid_prices_las_vegas[-61][1]  # Approximately 5 years ago
        
        five_year_change_national = ((current_national / five_years_ago_national) - 1) * 100 if current_national and five_years_ago_national else None
        five_year_change_las_vegas = ((current_las_vegas / five_years_ago_las_vegas) - 1) * 100 if current_las_vegas and five_years_ago_las_vegas else None
        
        return {
            "current_indices": {
                "national": current_national,
                "las_vegas": current_las_vegas
            },
            "year_over_year_change": {
                "national": yoy_change_national,
                "las_vegas": yoy_change_las_vegas
            },
            "five_year_change": {
                "national": five_year_change_national,
                "las_vegas": five_year_change_las_vegas
            },
            "data": {
                "national": prices_national,
                "las_vegas": prices_las_vegas
            }
        }
    
    def get_housing_supply_data(self, months=24):
        """
        Get housing supply data including inventory, new home sales, and existing home sales.
        
        Args:
            months (int, optional): Number of months of data to retrieve. Defaults to 24 (2 years).
            
        Returns:
            dict: Housing supply data.
        """
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30.44)  # Approximate days per month
        
        # Get housing supply data
        housing_inventory = self.get_fred_series(
            self.series_ids["housing_inventory"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        new_home_sales = self.get_fred_series(
            self.series_ids["new_home_sales"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        existing_home_sales = self.get_fred_series(
            self.series_ids["existing_home_sales"],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Check for errors
        if "error" in housing_inventory or "error" in new_home_sales or "error" in existing_home_sales:
            return {"error": "Error fetching housing supply data"}
        
        # Process the data
        inventory_data = housing_inventory.get("observations", [])
        new_sales_data = new_home_sales.get("observations", [])
        existing_sales_data = existing_home_sales.get("observations", [])
        
        # Calculate current values (most recent)
        current_inventory = float(inventory_data[-1]["value"]) if inventory_data and inventory_data[-1]["value"] != "." else None
        current_new_sales = float(new_sales_data[-1]["value"]) if new_sales_data and new_sales_data[-1]["value"] != "." else None
        current_existing_sales = float(existing_sales_data[-1]["value"]) if existing_sales_data and existing_sales_data[-1]["value"] != "." else None
        
        # Calculate trends
        valid_inventory = [float(r["value"]) for r in inventory_data if r["value"] != "."]
        valid_new_sales = [float(r["value"]) for r in new_sales_data if r["value"] != "."]
        valid_existing_sales = [float(r["value"]) for r in existing_sales_data if r["value"] != "."]
        
        trend_inventory = valid_inventory[-1] - valid_inventory[0] if len(valid_inventory) > 1 else 0
        trend_new_sales = valid_new_sales[-1] - valid_new_sales[0] if len(valid_new_sales) > 1 else 0
        trend_existing_sales = valid_existing_sales[-1] - valid_existing_sales[0] if len(valid_existing_sales) > 1 else 0
        
        # Calculate absorption rate (months of supply)
        absorption_rate = current_inventory
        
        return {
            "current_values": {
                "inventory_months_supply": current_inventory,
                "new_home_sales": current_new_sales,
                "existing_home_sales": current_existing_sales
            },
            "trends": {
                "inventory": trend_inventory,
                "new_home_sales": trend_new_sales,
                "existing_home_sales": trend_existing_sales
            },
            "absorption_rate": absorption_rate,
            "market_condition": self._interpret_absorption_rate(absorption_rate),
            "data": {
                "inventory": inventory_data,
                "new_home_sales": new_sales_data,
                "existing_home_sales": existing_sales_data
            }
        }
    
    def get_economic_indicators(self):
        """
        Get a comprehensive set of economic indicators relevant to real estate.
        
        Returns:
            dict: Economic indicators data.
        """
        # Get various economic indicators
        mortgage_rates = self.get_mortgage_rates()
        unemployment_data = self.get_unemployment_data()
        home_price_trends = self.get_home_price_trends()
        housing_supply = self.get_housing_supply_data()
        
        # Check for errors
        if any("error" in data for data in [mortgage_rates, unemployment_data, home_price_trends, housing_supply]):
            return {"error": "Error fetching economic indicators"}
        
        # Get inflation data (last 12 months)
        inflation_data = self.get_fred_series(
            self.series_ids["inflation"],
            start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )
        
        # Calculate inflation rate (year-over-year)
        inflation_rate = None
        if "observations" in inflation_data and len(inflation_data["observations"]) > 12:
            current_cpi = float(inflation_data["observations"][-1]["value"])
            year_ago_cpi = float(inflation_data["observations"][-13]["value"])
            inflation_rate = ((current_cpi / year_ago_cpi) - 1) * 100
        
        # Get GDP growth data (last 4 quarters)
        gdp_data = self.get_fred_series(
            self.series_ids["gdp_growth"],
            start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )
        
        # Get latest GDP growth rate
        gdp_growth_rate = None
        if "observations" in gdp_data and gdp_data["observations"]:
            gdp_growth_rate = float(gdp_data["observations"][-1]["value"])
        
        # Compile all indicators
        return {
            "mortgage_rates": {
                "current_30yr": mortgage_rates["current_rates"]["30_year_fixed"],
                "current_15yr": mortgage_rates["current_rates"]["15_year_fixed"],
                "trend_30yr": mortgage_rates["trends"]["30_year_fixed"],
                "trend_15yr": mortgage_rates["trends"]["15_year_fixed"]
            },
            "unemployment": {
                "national": unemployment_data["current_rates"]["national"],
                "nevada": unemployment_data["current_rates"]["nevada"],
                "las_vegas": unemployment_data["current_rates"]["las_vegas"],
                "trend_national": unemployment_data["trends"]["national"],
                "trend_nevada": unemployment_data["trends"]["nevada"],
                "trend_las_vegas": unemployment_data["trends"]["las_vegas"]
            },
            "home_prices": {
                "national_yoy_change": home_price_trends["year_over_year_change"]["national"],
                "las_vegas_yoy_change": home_price_trends["year_over_year_change"]["las_vegas"],
                "national_5yr_change": home_price_trends["five_year_change"]["national"],
                "las_vegas_5yr_change": home_price_trends["five_year_change"]["las_vegas"]
            },
            "housing_supply": {
                "inventory_months": housing_supply["current_values"]["inventory_months_supply"],
                "market_condition": housing_supply["market_condition"],
                "new_home_sales_trend": housing_supply["trends"]["new_home_sales"],
                "existing_home_sales_trend": housing_supply["trends"]["existing_home_sales"]
            },
            "macroeconomic": {
                "inflation_rate": inflation_rate,
                "gdp_growth_rate": gdp_growth_rate
            },
            "market_outlook": self._generate_market_outlook({
                "mortgage_rates": mortgage_rates,
                "unemployment": unemployment_data,
                "home_prices": home_price_trends,
                "housing_supply": housing_supply,
                "inflation_rate": inflation_rate,
                "gdp_growth_rate": gdp_growth_rate
            })
        }
    
    def _interpret_absorption_rate(self, months_supply):
        """
        Interpret the absorption rate (months of supply) to determine market condition.
        
        Args:
            months_supply (float): Months of housing supply.
            
        Returns:
            str: Market condition interpretation.
        """
        if months_supply is None:
            return "Unknown"
        elif months_supply < 3:
            return "Strong Seller's Market"
        elif months_supply < 4:
            return "Seller's Market"
        elif months_supply < 6:
            return "Balanced Market"
        elif months_supply < 7:
            return "Buyer's Market"
        else:
            return "Strong Buyer's Market"
    
    def _generate_market_outlook(self, indicators):
        """
        Generate a market outlook based on economic indicators.
        
        Args:
            indicators (dict): Economic indicators data.
            
        Returns:
            dict: Market outlook assessment.
        """
        # Initialize scores
        price_growth_score = 0
        affordability_score = 0
        market_activity_score = 0
        economic_health_score = 0
        
        # Evaluate price growth potential
        if indicators["home_prices"]["las_vegas_yoy_change"] is not None:
            yoy_change = indicators["home_prices"]["las_vegas_yoy_change"]
            if yoy_change > 10:
                price_growth_score = 5  # Very high growth
            elif yoy_change > 7:
                price_growth_score = 4  # High growth
            elif yoy_change > 4:
                price_growth_score = 3  # Moderate growth
            elif yoy_change > 1:
                price_growth_score = 2  # Slow growth
            elif yoy_change > -2:
                price_growth_score = 1  # Stable
            else:
                price_growth_score = 0  # Declining
        
        # Evaluate affordability
        if indicators["mortgage_rates"]["current_30yr"] is not None:
            rate = indicators["mortgage_rates"]["current_30yr"]
            if rate < 3.5:
                affordability_score = 5  # Very affordable
            elif rate < 4.5:
                affordability_score = 4  # Affordable
            elif rate < 5.5:
                affordability_score = 3  # Moderate
            elif rate < 6.5:
                affordability_score = 2  # Less affordable
            elif rate < 7.5:
                affordability_score = 1  # Expensive
            else:
                affordability_score = 0  # Very expensive
        
        # Evaluate market activity
        if indicators["housing_supply"]["inventory_months"] is not None:
            months_supply = indicators["housing_supply"]["inventory_months"]
            if months_supply < 2:
                market_activity_score = 5  # Very active
            elif months_supply < 3:
                market_activity_score = 4  # Active
            elif months_supply < 4:
                market_activity_score = 3  # Moderate
            elif months_supply < 6:
                market_activity_score = 2  # Slow
            elif months_supply < 8:
                market_activity_score = 1  # Very slow
            else:
                market_activity_score = 0  # Stagnant
        
        # Evaluate economic health
        unemployment_score = 0
        if indicators["unemployment"]["las_vegas"] is not None:
            unemployment = indicators["unemployment"]["las_vegas"]
            if unemployment < 3:
                unemployment_score = 5  # Very low unemployment
            elif unemployment < 4:
                unemployment_score = 4  # Low unemployment
            elif unemployment < 5:
                unemployment_score = 3  # Moderate unemployment
            elif unemployment < 6:
                unemployment_score = 2  # High unemployment
            elif unemployment < 8:
                unemployment_score = 1  # Very high unemployment
            else:
                unemployment_score = 0  # Severe unemployment
        
        gdp_score = 0
        if indicators["gdp_growth_rate"] is not None:
            gdp_growth = indicators["gdp_growth_rate"]
            if gdp_growth > 3:
                gdp_score = 5  # Strong growth
            elif gdp_growth > 2:
                gdp_score = 4  # Good growth
            elif gdp_growth > 1:
                gdp_score = 3  # Moderate growth
            elif gdp_growth > 0:
                gdp_score = 2  # Slow growth
            elif gdp_growth > -1:
                gdp_score = 1  # Stagnant
            else:
                gdp_score = 0  # Recession
        
        # Average economic health scores
        economic_health_score = (unemployment_score + gdp_score) / 2 if unemployment_score > 0 and gdp_score > 0 else max(unemployment_score, gdp_score)
        
        # Calculate overall market outlook score (0-100)
        overall_score = (price_growth_score + affordability_score + market_activity_score + economic_health_score) / 20 * 100
        
        # Determine market outlook
        if overall_score >= 80:
            outlook = "Very Positive"
        elif overall_score >= 60:
            outlook = "Positive"
        elif overall_score >= 40:
            outlook = "Neutral"
        elif overall_score >= 20:
            outlook = "Negative"
        else:
            outlook = "Very Negative"
        
        return {
            "overall_score": round(overall_score, 1),
            "outlook": outlook,
            "price_growth_potential": price_growth_score,
            "affordability": affordability_score,
            "market_activity": market_activity_score,
            "economic_health": economic_health_score
        }
    
    def get_insurance_rate_trends(self):
        """
        Get insurance rate trends for homeowners in Nevada.
        
        Note: This is a simulated function as there's no direct FRED/BLS API for insurance rates.
        In a real implementation, this would connect to insurance comparison APIs or use web scraping.
        
        Returns:
            dict: Insurance rate trends.
        """
        # Simulated data based on industry reports
        # In a real implementation, this would be replaced with actual API calls
        
        # Base annual premium for a $300,000 home in Las Vegas
        base_premium = 1250
        
        # Year-over-year increase (national average is around 3-7%)
        yoy_increase = 5.8
        
        # Factors affecting rates in Nevada
        factors = {
            "wildfire_risk": "Moderate",
            "flood_risk": "Low to Moderate",
            "crime_rate_impact": "Moderate",
            "construction_costs": "High",
            "claims_history": "Average"
        }
        
        # Premium ranges by home value
        premium_ranges = {
            "200000": {"min": 850, "avg": 1050, "max": 1350},
            "300000": {"min": 1050, "avg": 1250, "max": 1650},
            "400000": {"min": 1250, "avg": 1450, "max": 1950},
            "500000": {"min": 1450, "avg": 1750, "max": 2350},
            "750000": {"min": 1950, "avg": 2450, "max": 3250},
            "1000000": {"min": 2650, "avg": 3350, "max": 4450}
        }
        
        # Premium variations by ZIP code (sample of Clark County ZIP codes)
        zip_code_factors = {
            "89101": 1.15,  # Downtown Las Vegas
            "89102": 1.10,
            "89103": 1.05,
            "89104": 1.20,
            "89106": 1.25,
            "89107": 1.10,
            "89108": 1.05,
            "89109": 1.00,  # The Strip
            "89110": 1.15,
            "89113": 0.95,
            "89117": 0.90,  # Summerlin
            "89118": 1.00,
            "89119": 1.10,
            "89120": 1.00,
            "89121": 1.05,
            "89122": 1.15,
            "89123": 0.95,
            "89128": 0.90,
            "89129": 0.90,
            "89130": 0.95,
            "89131": 0.90,
            "89134": 0.85,  # Sun City Summerlin
            "89135": 0.85,
            "89138": 0.85,
            "89139": 0.95,
            "89141": 0.90,
            "89142": 1.10,
            "89143": 0.90,
            "89144": 0.85,
            "89145": 0.90,
            "89146": 1.00,
            "89147": 0.95,
            "89148": 0.90,
            "89149": 0.90,
            "89156": 1.05,
            "89166": 0.90,
            "89178": 0.90,
            "89179": 0.90,
            "89183": 0.95,
            "89191": 1.00
        }
        
        # Historical trend (simulated)
        historical_trend = [
            {"year": datetime.now().year - 5, "avg_premium": base_premium * 0.85},
            {"year": datetime.now().year - 4, "avg_premium": base_premium * 0.88},
            {"year": datetime.now().year - 3, "avg_premium": base_premium * 0.92},
            {"year": datetime.now().year - 2, "avg_premium": base_premium * 0.96},
            {"year": datetime.now().year - 1, "avg_premium": base_premium * 0.98},
            {"year": datetime.now().year, "avg_premium": base_premium}
        ]
        
        # Projected trend (simulated)
        projected_trend = [
            {"year": datetime.now().year + 1, "avg_premium": base_premium * (1 + yoy_increase/100)},
            {"year": datetime.now().year + 2, "avg_premium": base_premium * (1 + yoy_increase/100) * (1 + yoy_increase/100)},
            {"year": datetime.now().year + 3, "avg_premium": base_premium * (1 + yoy_increase/100) * (1 + yoy_increase/100) * (1 + yoy_increase/100)}
        ]
        
        return {
            "current_avg_premium": base_premium,
            "yoy_increase_percent": yoy_increase,
            "risk_factors": factors,
            "premium_ranges_by_home_value": premium_ranges,
            "zip_code_factors": zip_code_factors,
            "historical_trend": historical_trend,
            "projected_trend": projected_trend
        }

# Example usage
if __name__ == "__main__":
    # For testing purposes
    economic = EconomicDataAPI()
    
    # Example: Get mortgage rates
    mortgage_rates = economic.get_mortgage_rates()
    print(json.dumps(mortgage_rates, indent=2))
    
    # Example: Get economic indicators
    indicators = economic.get_economic_indicators()
    print(json.dumps(indicators, indent=2))
    
    # Example: Get insurance rate trends
    insurance_trends = economic.get_insurance_rate_trends()
    print(json.dumps(insurance_trends, indent=2))
