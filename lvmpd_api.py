"""
LVMPD Crime Statistics API Integration Module

This module provides functions to interact with the Las Vegas Metropolitan Police Department (LVMPD)
crime statistics data for retrieving crime information for neighborhoods in Clark County, Nevada.
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LVMPDCrimeAPI:
    """
    Class for interacting with the LVMPD crime statistics data.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the LVMPD Crime API client.
        
        Args:
            api_key (str, optional): API key if required. If not provided, will look for LVMPD_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get('LVMPD_API_KEY')
        self.base_url = "https://opendata.lvmpd.com/resource"
        self.rate_limit = 1000  # Requests per hour (adjust based on API documentation)
        self.request_timestamps = []
    
    def _check_rate_limit(self):
        """
        Check if we're within rate limits and wait if necessary.
        """
        now = time.time()
        # Remove timestamps older than 1 hour
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 3600]
        
        if len(self.request_timestamps) >= self.rate_limit:
            # Wait until we're under the rate limit
            sleep_time = 3600 - (now - self.request_timestamps[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
        
        # Add current timestamp
        self.request_timestamps.append(time.time())
    
    def get_crime_incidents(self, start_date=None, end_date=None, crime_type=None, 
                           area=None, zip_code=None, limit=1000):
        """
        Get crime incidents data.
        
        Args:
            start_date (str, optional): Start date in 'YYYY-MM-DD' format. Defaults to 30 days ago.
            end_date (str, optional): End date in 'YYYY-MM-DD' format. Defaults to today.
            crime_type (str, optional): Type of crime (e.g., "ASSAULT", "BURGLARY").
            area (str, optional): Area command (e.g., "DOWNTOWN", "NORTHEAST").
            zip_code (str, optional): ZIP code.
            limit (int, optional): Maximum number of results. Defaults to 1000.
            
        Returns:
            dict: Crime incidents data.
        """
        self._check_rate_limit()
        
        # Set default dates if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-App-Token"] = self.api_key
        
        # Construct the query
        query = f"date_occurred between '{start_date}' and '{end_date}'"
        
        if crime_type:
            query += f" AND crime_type='{crime_type}'"
        
        if area:
            query += f" AND area_command='{area}'"
        
        if zip_code:
            query += f" AND zip_code='{zip_code}'"
        
        params = {
            "$where": query,
            "$limit": limit,
            "$order": "date_occurred DESC"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/crime-incidents.json",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching crime incidents: {e}")
            return {"error": str(e)}
    
    def get_crime_stats_by_zip(self, zip_code, start_date=None, end_date=None):
        """
        Get crime statistics for a specific ZIP code.
        
        Args:
            zip_code (str): ZIP code.
            start_date (str, optional): Start date in 'YYYY-MM-DD' format. Defaults to 1 year ago.
            end_date (str, optional): End date in 'YYYY-MM-DD' format. Defaults to today.
            
        Returns:
            dict: Crime statistics for the ZIP code.
        """
        self._check_rate_limit()
        
        # Set default dates if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-App-Token"] = self.api_key
        
        # Construct the query
        query = f"date_occurred between '{start_date}' and '{end_date}' AND zip_code='{zip_code}'"
        
        params = {
            "$where": query,
            "$group": "crime_type",
            "$select": "crime_type, count(*) as count",
            "$order": "count DESC"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/crime-incidents.json",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            # Process the data to calculate statistics
            crime_data = response.json()
            
            # Calculate total crimes
            total_crimes = sum(int(item.get("count", 0)) for item in crime_data)
            
            # Calculate days in the date range
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            days = (end - start).days or 1  # Avoid division by zero
            
            # Calculate crimes per day
            crimes_per_day = total_crimes / days
            
            # Calculate crimes per month (approximate)
            crimes_per_month = crimes_per_day * 30.44  # Average days per month
            
            # Calculate crimes per year
            crimes_per_year = crimes_per_day * 365.25  # Average days per year
            
            return {
                "zip_code": zip_code,
                "start_date": start_date,
                "end_date": end_date,
                "total_crimes": total_crimes,
                "crimes_per_day": crimes_per_day,
                "crimes_per_month": crimes_per_month,
                "crimes_per_year": crimes_per_year,
                "crime_breakdown": crime_data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching crime statistics by ZIP: {e}")
            return {"error": str(e)}
    
    def get_crime_stats_by_coordinates(self, latitude, longitude, radius_miles=1.0, 
                                      start_date=None, end_date=None):
        """
        Get crime statistics for a specific location defined by coordinates and radius.
        
        Args:
            latitude (float): Latitude of the center point.
            longitude (float): Longitude of the center point.
            radius_miles (float, optional): Radius in miles. Defaults to 1.0.
            start_date (str, optional): Start date in 'YYYY-MM-DD' format. Defaults to 1 year ago.
            end_date (str, optional): End date in 'YYYY-MM-DD' format. Defaults to today.
            
        Returns:
            dict: Crime statistics for the area.
        """
        self._check_rate_limit()
        
        # Set default dates if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-App-Token"] = self.api_key
        
        # Convert miles to meters for the query
        radius_meters = radius_miles * 1609.34
        
        # Construct the query
        query = f"date_occurred between '{start_date}' and '{end_date}' AND within_circle(location, {latitude}, {longitude}, {radius_meters})"
        
        params = {
            "$where": query,
            "$group": "crime_type",
            "$select": "crime_type, count(*) as count",
            "$order": "count DESC"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/crime-incidents.json",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            # Process the data to calculate statistics
            crime_data = response.json()
            
            # Calculate total crimes
            total_crimes = sum(int(item.get("count", 0)) for item in crime_data)
            
            # Calculate days in the date range
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            days = (end - start).days or 1  # Avoid division by zero
            
            # Calculate crimes per day
            crimes_per_day = total_crimes / days
            
            # Calculate crimes per month (approximate)
            crimes_per_month = crimes_per_day * 30.44  # Average days per month
            
            # Calculate crimes per year
            crimes_per_year = crimes_per_day * 365.25  # Average days per year
            
            return {
                "latitude": latitude,
                "longitude": longitude,
                "radius_miles": radius_miles,
                "start_date": start_date,
                "end_date": end_date,
                "total_crimes": total_crimes,
                "crimes_per_day": crimes_per_day,
                "crimes_per_month": crimes_per_month,
                "crimes_per_year": crimes_per_year,
                "crime_breakdown": crime_data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching crime statistics by coordinates: {e}")
            return {"error": str(e)}
    
    def get_crime_heatmap_data(self, start_date=None, end_date=None, crime_type=None):
        """
        Get crime data suitable for generating a heatmap.
        
        Args:
            start_date (str, optional): Start date in 'YYYY-MM-DD' format. Defaults to 30 days ago.
            end_date (str, optional): End date in 'YYYY-MM-DD' format. Defaults to today.
            crime_type (str, optional): Type of crime (e.g., "ASSAULT", "BURGLARY").
            
        Returns:
            list: List of crime incidents with coordinates for heatmap generation.
        """
        self._check_rate_limit()
        
        # Set default dates if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-App-Token"] = self.api_key
        
        # Construct the query
        query = f"date_occurred between '{start_date}' and '{end_date}'"
        
        if crime_type:
            query += f" AND crime_type='{crime_type}'"
        
        params = {
            "$where": query,
            "$select": "latitude, longitude, crime_type, date_occurred",
            "$limit": 10000  # Adjust based on your needs
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/crime-incidents.json",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            # Filter out entries without valid coordinates
            crime_data = response.json()
            heatmap_data = [
                {
                    "latitude": float(item.get("latitude", 0)),
                    "longitude": float(item.get("longitude", 0)),
                    "crime_type": item.get("crime_type", ""),
                    "date_occurred": item.get("date_occurred", "")
                }
                for item in crime_data
                if item.get("latitude") and item.get("longitude")
            ]
            
            return heatmap_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching crime heatmap data: {e}")
            return {"error": str(e)}
    
    def get_crime_trend(self, zip_code=None, area=None, crime_type=None, months=12):
        """
        Get crime trend data over time.
        
        Args:
            zip_code (str, optional): ZIP code.
            area (str, optional): Area command (e.g., "DOWNTOWN", "NORTHEAST").
            crime_type (str, optional): Type of crime (e.g., "ASSAULT", "BURGLARY").
            months (int, optional): Number of months to analyze. Defaults to 12.
            
        Returns:
            dict: Crime trend data.
        """
        self._check_rate_limit()
        
        # Calculate start and end dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30.44)  # Approximate days per month
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-App-Token"] = self.api_key
        
        # Construct the query
        query = f"date_occurred between '{start_date.strftime('%Y-%m-%d')}' and '{end_date.strftime('%Y-%m-%d')}'"
        
        if zip_code:
            query += f" AND zip_code='{zip_code}'"
        
        if area:
            query += f" AND area_command='{area}'"
        
        if crime_type:
            query += f" AND crime_type='{crime_type}'"
        
        params = {
            "$where": query,
            "$select": "date_trunc_ym(date_occurred) as month, count(*) as count",
            "$group": "month",
            "$order": "month ASC"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/crime-incidents.json",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            trend_data = response.json()
            
            # Format the response
            result = {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "zip_code": zip_code,
                "area": area,
                "crime_type": crime_type,
                "trend": trend_data
            }
            
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching crime trend data: {e}")
            return {"error": str(e)}
    
    def get_safety_score(self, zip_code=None, latitude=None, longitude=None, radius_miles=1.0):
        """
        Calculate a safety score for a location based on crime statistics.
        
        Args:
            zip_code (str, optional): ZIP code.
            latitude (float, optional): Latitude of the center point.
            longitude (float, optional): Longitude of the center point.
            radius_miles (float, optional): Radius in miles. Defaults to 1.0.
            
        Returns:
            dict: Safety score and related statistics.
        """
        self._check_rate_limit()
        
        # Get crime statistics for the past year
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Get crime data based on provided parameters
        if zip_code:
            crime_stats = self.get_crime_stats_by_zip(zip_code, start_date, end_date)
        elif latitude and longitude:
            crime_stats = self.get_crime_stats_by_coordinates(latitude, longitude, radius_miles, start_date, end_date)
        else:
            return {"error": "Either zip_code or latitude/longitude must be provided"}
        
        # Check if there was an error
        if "error" in crime_stats:
            return crime_stats
        
        # Define crime severity weights (adjust based on your needs)
        crime_weights = {
            "HOMICIDE": 10.0,
            "SEXUAL ASSAULT": 9.0,
            "ROBBERY": 8.0,
            "AGGRAVATED ASSAULT": 7.0,
            "BURGLARY": 6.0,
            "MOTOR VEHICLE THEFT": 5.0,
            "LARCENY": 4.0,
            "VANDALISM": 3.0,
            "DRUG": 2.0,
            "OTHER": 1.0
        }
        
        # Calculate weighted crime score
        weighted_score = 0
        total_crimes = crime_stats.get("total_crimes", 0)
        
        if total_crimes > 0:
            for crime in crime_stats.get("crime_breakdown", []):
                crime_type = crime.get("crime_type", "OTHER")
                count = int(crime.get("count", 0))
                
                # Get weight for this crime type (default to 1.0 if not in our list)
                weight = crime_weights.get(crime_type, 1.0)
                
                # Add to weighted score
                weighted_score += count * weight
            
            # Normalize by total crimes
            weighted_score /= total_crimes
        
        # Calculate safety score (0-100, higher is safer)
        # This is a simple inverse relationship - adjust the formula as needed
        max_weighted_score = 10.0  # Maximum possible weighted score
        safety_score = max(0, min(100, 100 - (weighted_score / max_weighted_score * 100)))
        
        # Create safety rating
        if safety_score >= 80:
            safety_rating = "Very Safe"
        elif safety_score >= 60:
            safety_rating = "Safe"
        elif safety_score >= 40:
            safety_rating = "Moderate"
        elif safety_score >= 20:
            safety_rating = "Concerning"
        else:
            safety_rating = "Unsafe"
        
        # Return the results
        return {
            "safety_score": round(safety_score, 1),
            "safety_rating": safety_rating,
            "crime_stats": crime_stats,
            "weighted_crime_score": round(weighted_score, 2)
        }

# Example usage
if __name__ == "__main__":
    # For testing purposes
    lvmpd = LVMPDCrimeAPI()
    
    # Example: Get crime incidents for the past 30 days
    incidents = lvmpd.get_crime_incidents(limit=10)
    print(json.dumps(incidents, indent=2))
    
    # Example: Get crime statistics for a ZIP code
    zip_stats = lvmpd.get_crime_stats_by_zip("89101")
    print(json.dumps(zip_stats, indent=2))
    
    # Example: Get safety score for a ZIP code
    safety = lvmpd.get_safety_score(zip_code="89101")
    print(json.dumps(safety, indent=2))
