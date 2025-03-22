"""
Zillow Bridge API Integration Module

This module provides functions to interact with the Zillow Bridge API for retrieving
property details and Zestimates for properties in Clark County, Nevada.
"""

import os
import requests
import json
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZillowAPI:
    """
    Class for interacting with the Zillow Bridge API.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the Zillow API client.
        
        Args:
            api_key (str, optional): Zillow API key. If not provided, will look for ZILLOW_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get('ZILLOW_API_KEY')
        if not self.api_key:
            logger.warning("No Zillow API key provided. Set ZILLOW_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://api.bridgedataoutput.com/api/v2/zestimates"
        self.rate_limit = 100  # Requests per minute (adjust based on your API tier)
        self.request_timestamps = []
    
    def _check_rate_limit(self):
        """
        Check if we're within rate limits and wait if necessary.
        """
        now = time.time()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 60]
        
        if len(self.request_timestamps) >= self.rate_limit:
            # Wait until we're under the rate limit
            sleep_time = 60 - (now - self.request_timestamps[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
        
        # Add current timestamp
        self.request_timestamps.append(time.time())
    
    def get_property_details(self, address=None, zipcode=None, zpid=None):
        """
        Get property details from Zillow.
        
        Args:
            address (str, optional): Property address.
            zipcode (str, optional): Property zipcode.
            zpid (str, optional): Zillow Property ID.
            
        Returns:
            dict: Property details from Zillow.
        """
        if not any([address, zpid]):
            raise ValueError("Either address or zpid must be provided")
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        params = {}
        if address:
            params["address"] = address
            if zipcode:
                params["zipcode"] = zipcode
        if zpid:
            params["zpid"] = zpid
        
        try:
            response = requests.get(
                f"{self.base_url}/property",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property details: {e}")
            return {"error": str(e)}
    
    def get_zestimate(self, zpid):
        """
        Get Zestimate for a property.
        
        Args:
            zpid (str): Zillow Property ID.
            
        Returns:
            dict: Zestimate data.
        """
        if not zpid:
            raise ValueError("zpid must be provided")
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{zpid}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Zestimate: {e}")
            return {"error": str(e)}
    
    def search_properties(self, address=None, city="Las Vegas", state="NV", zipcode=None, 
                          min_price=None, max_price=None, beds=None, baths=None, 
                          property_type=None, limit=10):
        """
        Search for properties in Clark County, Nevada.
        
        Args:
            address (str, optional): Partial address to search for.
            city (str, optional): City name. Defaults to "Las Vegas".
            state (str, optional): State code. Defaults to "NV".
            zipcode (str, optional): ZIP code.
            min_price (int, optional): Minimum price.
            max_price (int, optional): Maximum price.
            beds (int, optional): Number of bedrooms.
            baths (int, optional): Number of bathrooms.
            property_type (str, optional): Property type (e.g., "Single Family", "Condo").
            limit (int, optional): Maximum number of results. Defaults to 10.
            
        Returns:
            dict: Search results.
        """
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        params = {
            "limit": limit,
            "city": city,
            "state": state,
            "countyFIPS": "32003"  # Clark County, Nevada FIPS code
        }
        
        if address:
            params["address"] = address
        if zipcode:
            params["zipcode"] = zipcode
        if min_price:
            params["minPrice"] = min_price
        if max_price:
            params["maxPrice"] = max_price
        if beds:
            params["beds"] = beds
        if baths:
            params["baths"] = baths
        if property_type:
            params["propertyType"] = property_type
        
        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching properties: {e}")
            return {"error": str(e)}
    
    def get_comparable_properties(self, zpid, count=10):
        """
        Get comparable properties for a given property.
        
        Args:
            zpid (str): Zillow Property ID.
            count (int, optional): Number of comparable properties to return. Defaults to 10.
            
        Returns:
            dict: Comparable properties data.
        """
        if not zpid:
            raise ValueError("zpid must be provided")
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        params = {
            "count": count
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{zpid}/comps",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching comparable properties: {e}")
            return {"error": str(e)}
    
    def get_property_timeline(self, zpid):
        """
        Get historical timeline data for a property.
        
        Args:
            zpid (str): Zillow Property ID.
            
        Returns:
            dict: Property timeline data.
        """
        if not zpid:
            raise ValueError("zpid must be provided")
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{zpid}/timeline",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property timeline: {e}")
            return {"error": str(e)}
    
    def get_property_value_history(self, zpid):
        """
        Get historical value data for a property.
        
        Args:
            zpid (str): Zillow Property ID.
            
        Returns:
            dict: Property value history data.
        """
        if not zpid:
            raise ValueError("zpid must be provided")
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{zpid}/history",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property value history: {e}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # For testing purposes
    zillow = ZillowAPI()
    
    # Example: Get property details by address
    property_details = zillow.get_property_details(
        address="123 Main St",
        zipcode="89101"
    )
    print(json.dumps(property_details, indent=2))
    
    # Example: Search for properties
    search_results = zillow.search_properties(
        city="Las Vegas",
        min_price=300000,
        max_price=500000,
        beds=3,
        property_type="Single Family"
    )
    print(json.dumps(search_results, indent=2))
