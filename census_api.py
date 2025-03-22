"""
Census Bureau API Integration Module

This module provides functions to interact with the Census Bureau API for retrieving
demographic data for Clark County, Nevada (FIPS code 32003).
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

class CensusBureauAPI:
    """
    Class for interacting with the Census Bureau API.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the Census Bureau API client.
        
        Args:
            api_key (str, optional): Census Bureau API key. If not provided, will look for CENSUS_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get('CENSUS_API_KEY')
        if not self.api_key:
            logger.warning("No Census Bureau API key provided. Set CENSUS_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://api.census.gov/data"
        self.clark_county_fips = "32003"  # FIPS code for Clark County, Nevada
        self.rate_limit = 500  # Requests per day (adjust based on API documentation)
        self.request_timestamps = []
    
    def _check_rate_limit(self):
        """
        Check if we're within rate limits and wait if necessary.
        """
        now = time.time()
        # Remove timestamps older than 24 hours
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 86400]
        
        if len(self.request_timestamps) >= self.rate_limit:
            logger.error("Census Bureau API daily rate limit reached.")
            raise Exception("Census Bureau API daily rate limit reached.")
        
        # Add current timestamp
        self.request_timestamps.append(time.time())
    
    def get_demographic_data(self, year=2020, dataset="acs/acs5", variables=None, tract=None, block_group=None):
        """
        Get demographic data for Clark County, Nevada.
        
        Args:
            year (int, optional): Census year. Defaults to 2020.
            dataset (str, optional): Census dataset. Defaults to "acs/acs5" (5-year American Community Survey).
            variables (list, optional): List of Census variables to retrieve. If None, retrieves basic demographics.
            tract (str, optional): Census tract code within Clark County.
            block_group (str, optional): Census block group within tract.
            
        Returns:
            dict: Demographic data.
        """
        self._check_rate_limit()
        
        # Default variables if none provided
        if variables is None:
            variables = [
                "NAME",                # Area name
                "B01001_001E",         # Total population
                "B19013_001E",         # Median household income
                "B25077_001E",         # Median home value
                "B25064_001E",         # Median gross rent
                "B15003_022E",         # Bachelor's degree
                "B15003_023E",         # Master's degree
                "B15003_024E",         # Professional degree
                "B15003_025E",         # Doctorate degree
                "B25002_001E",         # Total housing units
                "B25002_002E",         # Occupied housing units
                "B25002_003E"          # Vacant housing units
            ]
        
        # Construct the API URL
        url = f"{self.base_url}/{year}/{dataset}"
        
        # Construct the geographic filter
        if tract and block_group:
            geo_filter = f"block%20group:{block_group}&in=state:32&in=county:003&in=tract:{tract}"
        elif tract:
            geo_filter = f"tract:{tract}&in=state:32&in=county:003"
        else:
            geo_filter = "county:003&in=state:32"
        
        # Construct the query parameters
        params = {
            "get": ",".join(variables),
            "for": geo_filter,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Convert to a more usable format
            headers = data[0]
            values = data[1:]
            
            result = []
            for row in values:
                result.append(dict(zip(headers, row)))
            
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching demographic data: {e}")
            return {"error": str(e)}
    
    def get_income_data(self, year=2020, tract=None):
        """
        Get income distribution data for Clark County, Nevada.
        
        Args:
            year (int, optional): Census year. Defaults to 2020.
            tract (str, optional): Census tract code within Clark County.
            
        Returns:
            dict: Income distribution data.
        """
        variables = [
            "NAME",
            "B19001_001E",  # Total households
            "B19001_002E",  # Less than $10,000
            "B19001_003E",  # $10,000 to $14,999
            "B19001_004E",  # $15,000 to $19,999
            "B19001_005E",  # $20,000 to $24,999
            "B19001_006E",  # $25,000 to $29,999
            "B19001_007E",  # $30,000 to $34,999
            "B19001_008E",  # $35,000 to $39,999
            "B19001_009E",  # $40,000 to $44,999
            "B19001_010E",  # $45,000 to $49,999
            "B19001_011E",  # $50,000 to $59,999
            "B19001_012E",  # $60,000 to $74,999
            "B19001_013E",  # $75,000 to $99,999
            "B19001_014E",  # $100,000 to $124,999
            "B19001_015E",  # $125,000 to $149,999
            "B19001_016E",  # $150,000 to $199,999
            "B19001_017E"   # $200,000 or more
        ]
        
        return self.get_demographic_data(year=year, variables=variables, tract=tract)
    
    def get_housing_data(self, year=2020, tract=None):
        """
        Get housing data for Clark County, Nevada.
        
        Args:
            year (int, optional): Census year. Defaults to 2020.
            tract (str, optional): Census tract code within Clark County.
            
        Returns:
            dict: Housing data.
        """
        variables = [
            "NAME",
            "B25002_001E",  # Total housing units
            "B25002_002E",  # Occupied housing units
            "B25002_003E",  # Vacant housing units
            "B25003_001E",  # Tenure (total)
            "B25003_002E",  # Owner occupied
            "B25003_003E",  # Renter occupied
            "B25077_001E",  # Median home value
            "B25064_001E",  # Median gross rent
            "B25034_001E",  # Year structure built (total)
            "B25034_002E",  # Built 2014 or later
            "B25034_003E",  # Built 2010 to 2013
            "B25034_004E",  # Built 2000 to 2009
            "B25034_005E",  # Built 1990 to 1999
            "B25034_006E",  # Built 1980 to 1989
            "B25034_007E",  # Built 1970 to 1979
            "B25034_008E",  # Built 1960 to 1969
            "B25034_009E",  # Built 1950 to 1959
            "B25034_010E",  # Built 1940 to 1949
            "B25034_011E"   # Built 1939 or earlier
        ]
        
        return self.get_demographic_data(year=year, variables=variables, tract=tract)
    
    def get_education_data(self, year=2020, tract=None):
        """
        Get education data for Clark County, Nevada.
        
        Args:
            year (int, optional): Census year. Defaults to 2020.
            tract (str, optional): Census tract code within Clark County.
            
        Returns:
            dict: Education data.
        """
        variables = [
            "NAME",
            "B15003_001E",  # Total population 25 years and over
            "B15003_002E",  # No schooling completed
            "B15003_003E",  # Nursery school
            "B15003_004E",  # Kindergarten
            "B15003_005E",  # 1st grade
            "B15003_006E",  # 2nd grade
            "B15003_007E",  # 3rd grade
            "B15003_008E",  # 4th grade
            "B15003_009E",  # 5th grade
            "B15003_010E",  # 6th grade
            "B15003_011E",  # 7th grade
            "B15003_012E",  # 8th grade
            "B15003_013E",  # 9th grade
            "B15003_014E",  # 10th grade
            "B15003_015E",  # 11th grade
            "B15003_016E",  # 12th grade, no diploma
            "B15003_017E",  # Regular high school diploma
            "B15003_018E",  # GED or alternative credential
            "B15003_019E",  # Some college, less than 1 year
            "B15003_020E",  # Some college, 1 or more years, no degree
            "B15003_021E",  # Associate's degree
            "B15003_022E",  # Bachelor's degree
            "B15003_023E",  # Master's degree
            "B15003_024E",  # Professional school degree
            "B15003_025E"   # Doctorate degree
        ]
        
        return self.get_demographic_data(year=year, variables=variables, tract=tract)
    
    def get_commuting_data(self, year=2020, tract=None):
        """
        Get commuting data for Clark County, Nevada.
        
        Args:
            year (int, optional): Census year. Defaults to 2020.
            tract (str, optional): Census tract code within Clark County.
            
        Returns:
            dict: Commuting data.
        """
        variables = [
            "NAME",
            "B08301_001E",  # Total workers 16 years and over
            "B08301_002E",  # Car, truck, or van - drove alone
            "B08301_003E",  # Car, truck, or van - carpooled
            "B08301_004E",  # Public transportation (excluding taxicab)
            "B08301_010E",  # Walked
            "B08301_016E",  # Taxicab, motorcycle, bicycle, or other means
            "B08301_021E",  # Worked from home
            "B08303_001E",  # Total travel time to work
            "B08303_002E",  # Less than 5 minutes
            "B08303_003E",  # 5 to 9 minutes
            "B08303_004E",  # 10 to 14 minutes
            "B08303_005E",  # 15 to 19 minutes
            "B08303_006E",  # 20 to 24 minutes
            "B08303_007E",  # 25 to 29 minutes
            "B08303_008E",  # 30 to 34 minutes
            "B08303_009E",  # 35 to 39 minutes
            "B08303_010E",  # 40 to 44 minutes
            "B08303_011E",  # 45 to 59 minutes
            "B08303_012E",  # 60 to 89 minutes
            "B08303_013E"   # 90 or more minutes
        ]
        
        return self.get_demographic_data(year=year, variables=variables, tract=tract)
    
    def get_migration_data(self, year=2020, tract=None):
        """
        Get migration data for Clark County, Nevada.
        
        Args:
            year (int, optional): Census year. Defaults to 2020.
            tract (str, optional): Census tract code within Clark County.
            
        Returns:
            dict: Migration data.
        """
        variables = [
            "NAME",
            "B07001_001E",  # Total population
            "B07001_017E",  # Moved within same county
            "B07001_033E",  # Moved from different county, same state
            "B07001_049E",  # Moved from different state
            "B07001_065E",  # Moved from abroad
            "B07001_081E"   # Same house 1 year ago
        ]
        
        return self.get_demographic_data(year=year, variables=variables, tract=tract)
    
    def get_census_tract_for_address(self, address, city="Las Vegas", state="NV", zip_code=None):
        """
        Get Census tract for a given address using the Census Geocoding API.
        
        Args:
            address (str): Street address.
            city (str, optional): City name. Defaults to "Las Vegas".
            state (str, optional): State code. Defaults to "NV".
            zip_code (str, optional): ZIP code.
            
        Returns:
            dict: Census tract information.
        """
        self._check_rate_limit()
        
        # Construct the address string
        address_str = f"{address}, {city}, {state}"
        if zip_code:
            address_str += f" {zip_code}"
        
        # URL encode the address
        address_encoded = requests.utils.quote(address_str)
        
        # Construct the API URL
        url = f"https://geocoding.geo.census.gov/geocoder/geographies/address?street={address_encoded}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we got a match
            if data.get("result", {}).get("addressMatches", []):
                match = data["result"]["addressMatches"][0]
                geographies = match.get("geographies", {})
                
                # Extract Census tract information
                census_tracts = geographies.get("Census Tracts", [])
                if census_tracts:
                    tract_info = census_tracts[0]
                    return {
                        "tract": tract_info.get("TRACT"),
                        "county": tract_info.get("COUNTY"),
                        "state": tract_info.get("STATE"),
                        "geoid": tract_info.get("GEOID"),
                        "name": tract_info.get("NAME"),
                        "coordinates": {
                            "x": match.get("coordinates", {}).get("x"),
                            "y": match.get("coordinates", {}).get("y")
                        }
                    }
                else:
                    return {"error": "No Census tract found for this address"}
            else:
                return {"error": "Address not found"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error geocoding address: {e}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # For testing purposes
    census = CensusBureauAPI()
    
    # Example: Get demographic data for Clark County
    demographic_data = census.get_demographic_data()
    print(json.dumps(demographic_data, indent=2))
    
    # Example: Get Census tract for an address
    tract_info = census.get_census_tract_for_address(
        address="123 Main St",
        city="Las Vegas",
        state="NV",
        zip_code="89101"
    )
    print(json.dumps(tract_info, indent=2))
    
    # Example: Get demographic data for a specific tract
    if "tract" in tract_info:
        tract_demographic_data = census.get_demographic_data(tract=tract_info["tract"])
        print(json.dumps(tract_demographic_data, indent=2))
