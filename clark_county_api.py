"""
Clark County Assessor API Integration Module

This module provides functions to interact with the Clark County Assessor's data
for retrieving property tax records and assessment information for properties in Clark County, Nevada.
"""

import os
import requests
import json
import time
from datetime import datetime
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClarkCountyAssessorAPI:
    """
    Class for interacting with the Clark County Assessor's data.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the Clark County Assessor API client.
        
        Args:
            api_key (str, optional): API key if required. If not provided, will look for CLARK_COUNTY_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get('CLARK_COUNTY_API_KEY')
        self.base_url = "https://www.clarkcountynv.gov/assessor/api"
        self.rate_limit = 60  # Requests per minute
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
    
    def get_property_by_apn(self, apn):
        """
        Get property details by Assessor's Parcel Number (APN).
        
        Args:
            apn (str): Assessor's Parcel Number.
            
        Returns:
            dict: Property details from Clark County Assessor.
        """
        if not apn:
            raise ValueError("APN must be provided")
        
        # Format APN to match Clark County format (e.g., 123-45-678-901)
        apn = self._format_apn(apn)
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.get(
                f"{self.base_url}/property/{apn}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property by APN: {e}")
            return {"error": str(e)}
    
    def get_property_by_address(self, street_number, street_name, city="Las Vegas", zip_code=None):
        """
        Get property details by address.
        
        Args:
            street_number (str): Street number.
            street_name (str): Street name.
            city (str, optional): City name. Defaults to "Las Vegas".
            zip_code (str, optional): ZIP code.
            
        Returns:
            dict: Property details from Clark County Assessor.
        """
        if not street_number or not street_name:
            raise ValueError("Street number and street name must be provided")
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        params = {
            "streetNumber": street_number,
            "streetName": street_name,
            "city": city
        }
        
        if zip_code:
            params["zipCode"] = zip_code
        
        try:
            response = requests.get(
                f"{self.base_url}/property/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property by address: {e}")
            return {"error": str(e)}
    
    def get_property_tax_history(self, apn):
        """
        Get property tax history by Assessor's Parcel Number (APN).
        
        Args:
            apn (str): Assessor's Parcel Number.
            
        Returns:
            dict: Property tax history from Clark County Assessor.
        """
        if not apn:
            raise ValueError("APN must be provided")
        
        # Format APN to match Clark County format
        apn = self._format_apn(apn)
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.get(
                f"{self.base_url}/property/{apn}/tax-history",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property tax history: {e}")
            return {"error": str(e)}
    
    def get_property_assessment_history(self, apn):
        """
        Get property assessment history by Assessor's Parcel Number (APN).
        
        Args:
            apn (str): Assessor's Parcel Number.
            
        Returns:
            dict: Property assessment history from Clark County Assessor.
        """
        if not apn:
            raise ValueError("APN must be provided")
        
        # Format APN to match Clark County format
        apn = self._format_apn(apn)
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.get(
                f"{self.base_url}/property/{apn}/assessment-history",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property assessment history: {e}")
            return {"error": str(e)}
    
    def get_property_sales_history(self, apn):
        """
        Get property sales history by Assessor's Parcel Number (APN).
        
        Args:
            apn (str): Assessor's Parcel Number.
            
        Returns:
            dict: Property sales history from Clark County Assessor.
        """
        if not apn:
            raise ValueError("APN must be provided")
        
        # Format APN to match Clark County format
        apn = self._format_apn(apn)
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.get(
                f"{self.base_url}/property/{apn}/sales-history",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property sales history: {e}")
            return {"error": str(e)}
    
    def get_neighborhood_properties(self, apn, radius_miles=0.5, limit=50):
        """
        Get properties in the neighborhood of a given property.
        
        Args:
            apn (str): Assessor's Parcel Number of the central property.
            radius_miles (float, optional): Radius in miles to search. Defaults to 0.5.
            limit (int, optional): Maximum number of properties to return. Defaults to 50.
            
        Returns:
            dict: Neighborhood properties from Clark County Assessor.
        """
        if not apn:
            raise ValueError("APN must be provided")
        
        # Format APN to match Clark County format
        apn = self._format_apn(apn)
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        params = {
            "radius": radius_miles,
            "limit": limit
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/property/{apn}/neighborhood",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching neighborhood properties: {e}")
            return {"error": str(e)}
    
    def search_properties(self, params):
        """
        Search for properties with various criteria.
        
        Args:
            params (dict): Search parameters, which may include:
                - owner_name (str): Property owner name.
                - min_value (float): Minimum property value.
                - max_value (float): Maximum property value.
                - min_sqft (float): Minimum square footage.
                - max_sqft (float): Maximum square footage.
                - min_year_built (int): Minimum year built.
                - max_year_built (int): Maximum year built.
                - property_type (str): Property type.
                - zip_code (str): ZIP code.
                - limit (int): Maximum number of results.
            
        Returns:
            dict: Search results from Clark County Assessor.
        """
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Convert parameter keys to the format expected by the API
        api_params = {}
        param_mapping = {
            "owner_name": "ownerName",
            "min_value": "minValue",
            "max_value": "maxValue",
            "min_sqft": "minSqft",
            "max_sqft": "maxSqft",
            "min_year_built": "minYearBuilt",
            "max_year_built": "maxYearBuilt",
            "property_type": "propertyType",
            "zip_code": "zipCode",
            "limit": "limit"
        }
        
        for key, value in params.items():
            if key in param_mapping and value is not None:
                api_params[param_mapping[key]] = value
        
        try:
            response = requests.get(
                f"{self.base_url}/property/search",
                headers=headers,
                params=api_params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching properties: {e}")
            return {"error": str(e)}
    
    def get_property_tax_rate(self, apn=None, zip_code=None):
        """
        Get property tax rate for a specific property or ZIP code.
        
        Args:
            apn (str, optional): Assessor's Parcel Number.
            zip_code (str, optional): ZIP code.
            
        Returns:
            dict: Property tax rate information.
        """
        if not apn and not zip_code:
            raise ValueError("Either APN or ZIP code must be provided")
        
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        params = {}
        if apn:
            params["apn"] = self._format_apn(apn)
        if zip_code:
            params["zipCode"] = zip_code
        
        try:
            response = requests.get(
                f"{self.base_url}/tax-rates",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property tax rate: {e}")
            return {"error": str(e)}
    
    def _format_apn(self, apn):
        """
        Format APN to match Clark County format (e.g., 123-45-678-901).
        
        Args:
            apn (str): Assessor's Parcel Number in any format.
            
        Returns:
            str: Formatted APN.
        """
        # Remove any non-numeric characters
        digits = re.sub(r'[^0-9]', '', apn)
        
        # Clark County APNs are typically 11 digits
        if len(digits) != 11:
            logger.warning(f"APN {apn} does not have 11 digits. Returning as is.")
            return apn
        
        # Format as 123-45-678-901
        return f"{digits[0:3]}-{digits[3:5]}-{digits[5:8]}-{digits[8:11]}"

# Example usage
if __name__ == "__main__":
    # For testing purposes
    assessor = ClarkCountyAssessorAPI()
    
    # Example: Get property by APN
    property_details = assessor.get_property_by_apn("123456789012")
    print(json.dumps(property_details, indent=2))
    
    # Example: Get property by address
    address_search = assessor.get_property_by_address(
        street_number="123",
        street_name="Main St",
        city="Las Vegas",
        zip_code="89101"
    )
    print(json.dumps(address_search, indent=2))
