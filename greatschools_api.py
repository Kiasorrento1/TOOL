"""
GreatSchools.org API Integration Module

This module provides functions to interact with the GreatSchools.org API
for retrieving education quality metrics for schools in Clark County, Nevada.
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

class GreatSchoolsAPI:
    """
    Class for interacting with the GreatSchools.org API.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the GreatSchools.org API client.
        
        Args:
            api_key (str, optional): GreatSchools API key. If not provided, will look for GREATSCHOOLS_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get('GREATSCHOOLS_API_KEY')
        if not self.api_key:
            logger.warning("No GreatSchools API key provided. Set GREATSCHOOLS_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://api.greatschools.org/schools"
        self.rate_limit = 100  # Requests per day (adjust based on your API tier)
        self.request_timestamps = []
    
    def _check_rate_limit(self):
        """
        Check if we're within rate limits and wait if necessary.
        """
        now = time.time()
        # Remove timestamps older than 24 hours
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 86400]
        
        if len(self.request_timestamps) >= self.rate_limit:
            logger.error("GreatSchools API daily rate limit reached.")
            raise Exception("GreatSchools API daily rate limit reached.")
        
        # Add current timestamp
        self.request_timestamps.append(time.time())
    
    def get_schools_near_location(self, latitude, longitude, distance=5, school_types=None, limit=10):
        """
        Get schools near a specific location.
        
        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            distance (int, optional): Distance in miles. Defaults to 5.
            school_types (list, optional): List of school types (e.g., ["public", "charter", "private"]).
            limit (int, optional): Maximum number of results. Defaults to 10.
            
        Returns:
            dict: Schools near the location.
        """
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        params = {
            "lat": latitude,
            "lon": longitude,
            "distance": distance,
            "limit": limit,
            "state": "NV"  # Nevada
        }
        
        if school_types:
            params["schoolType"] = ",".join(school_types)
        
        try:
            response = requests.get(
                f"{self.base_url}/nearby",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching schools near location: {e}")
            return {"error": str(e)}
    
    def get_schools_by_zip(self, zip_code, school_types=None, limit=10):
        """
        Get schools in a specific ZIP code.
        
        Args:
            zip_code (str): ZIP code.
            school_types (list, optional): List of school types (e.g., ["public", "charter", "private"]).
            limit (int, optional): Maximum number of results. Defaults to 10.
            
        Returns:
            dict: Schools in the ZIP code.
        """
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        params = {
            "zip": zip_code,
            "limit": limit,
            "state": "NV"  # Nevada
        }
        
        if school_types:
            params["schoolType"] = ",".join(school_types)
        
        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching schools by ZIP: {e}")
            return {"error": str(e)}
    
    def get_school_details(self, school_id):
        """
        Get detailed information about a specific school.
        
        Args:
            school_id (str): GreatSchools school ID.
            
        Returns:
            dict: School details.
        """
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{school_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching school details: {e}")
            return {"error": str(e)}
    
    def get_school_ratings(self, school_id):
        """
        Get ratings for a specific school.
        
        Args:
            school_id (str): GreatSchools school ID.
            
        Returns:
            dict: School ratings.
        """
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{school_id}/ratings",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching school ratings: {e}")
            return {"error": str(e)}
    
    def get_school_reviews(self, school_id, limit=10):
        """
        Get reviews for a specific school.
        
        Args:
            school_id (str): GreatSchools school ID.
            limit (int, optional): Maximum number of reviews. Defaults to 10.
            
        Returns:
            dict: School reviews.
        """
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        params = {
            "limit": limit
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{school_id}/reviews",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching school reviews: {e}")
            return {"error": str(e)}
    
    def get_school_test_scores(self, school_id):
        """
        Get test scores for a specific school.
        
        Args:
            school_id (str): GreatSchools school ID.
            
        Returns:
            dict: School test scores.
        """
        self._check_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/{school_id}/test-scores",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching school test scores: {e}")
            return {"error": str(e)}
    
    def calculate_education_score(self, zip_code=None, latitude=None, longitude=None, distance=2):
        """
        Calculate an education score for a location based on nearby schools.
        
        Args:
            zip_code (str, optional): ZIP code.
            latitude (float, optional): Latitude of the location.
            longitude (float, optional): Longitude of the location.
            distance (int, optional): Distance in miles. Defaults to 2.
            
        Returns:
            dict: Education score and related statistics.
        """
        # Get schools based on provided parameters
        if zip_code:
            schools_data = self.get_schools_by_zip(zip_code, limit=20)
        elif latitude and longitude:
            schools_data = self.get_schools_near_location(latitude, longitude, distance=distance, limit=20)
        else:
            return {"error": "Either zip_code or latitude/longitude must be provided"}
        
        # Check if there was an error
        if "error" in schools_data:
            return schools_data
        
        # Extract schools from the response
        schools = schools_data.get("schools", [])
        
        if not schools:
            return {
                "education_score": 0,
                "education_rating": "No Data",
                "schools_count": 0,
                "schools": []
            }
        
        # Calculate average rating
        total_rating = 0
        rated_schools = 0
        
        elementary_schools = []
        middle_schools = []
        high_schools = []
        
        for school in schools:
            rating = school.get("rating", {}).get("overall", 0)
            if rating > 0:
                total_rating += rating
                rated_schools += 1
            
            # Categorize schools by level
            level = school.get("level", "").lower()
            if "elementary" in level:
                elementary_schools.append(school)
            elif "middle" in level:
                middle_schools.append(school)
            elif "high" in level:
                high_schools.append(school)
        
        # Calculate average rating (1-10 scale)
        avg_rating = total_rating / rated_schools if rated_schools > 0 else 0
        
        # Convert to 0-100 scale
        education_score = avg_rating * 10
        
        # Create education rating
        if education_score >= 80:
            education_rating = "Excellent"
        elif education_score >= 70:
            education_rating = "Very Good"
        elif education_score >= 60:
            education_rating = "Good"
        elif education_score >= 50:
            education_rating = "Above Average"
        elif education_score >= 40:
            education_rating = "Average"
        elif education_score >= 30:
            education_rating = "Below Average"
        elif education_score > 0:
            education_rating = "Poor"
        else:
            education_rating = "No Data"
        
        # Return the results
        return {
            "education_score": round(education_score, 1),
            "education_rating": education_rating,
            "average_rating": round(avg_rating, 1),
            "schools_count": len(schools),
            "rated_schools_count": rated_schools,
            "elementary_schools_count": len(elementary_schools),
            "middle_schools_count": len(middle_schools),
            "high_schools_count": len(high_schools),
            "top_schools": sorted(schools, key=lambda x: x.get("rating", {}).get("overall", 0), reverse=True)[:5] if schools else []
        }

# Example usage
if __name__ == "__main__":
    # For testing purposes
    greatschools = GreatSchoolsAPI()
    
    # Example: Get schools near a location
    schools_near = greatschools.get_schools_near_location(
        latitude=36.1699,
        longitude=-115.1398,  # Las Vegas coordinates
        distance=5
    )
    print(json.dumps(schools_near, indent=2))
    
    # Example: Calculate education score for a ZIP code
    education_score = greatschools.calculate_education_score(zip_code="89101")
    print(json.dumps(education_score, indent=2))
