"""
This module provides a client for interacting with the SpaceX API v4.
It handles data fetching, error handling, and basic caching.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SpaceXAPIClient:
    """Client for interacting with the SpaceX API v4."""
    
    BASE_URL = "https://api.spacexdata.com/v4"
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache")
    
    def __init__(self, cache_dir: Optional[str], cache_expiry: int = 3600, max_cache_age_days: int = 1):
        """
        Initialize the SpaceX API client.
        
        Args:
            cache_dir: Directory to store cached data. Defaults to ".cache" in the project directory.
            cache_expiry: Cache expiry time in seconds. Defaults to 1 hour.
            max_cache_age_days: Maximum age for cache files in days before they're removed.
        """
        self.cache_dir = cache_dir or self.CACHE_DIR
        self.cache_expiry = cache_expiry
        self.max_cache_age_days = max_cache_age_days
    
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Invalidate old cache files on startup
        self.invalidate_old_cache(max_cache_age_days)
        
    def _get_cache_path(self, endpoint: str) -> str:
        """
        Get the cache file path for an endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Path to the cache file
        """
        # Create a safe filename from the endpoint
        safe_endpoint = endpoint.replace("/", "_").strip("_")
        return os.path.join(self.cache_dir, f"{safe_endpoint}.json")
    
    def _read_cache(self, endpoint: str) -> Optional[Dict]:
        """
        Read data from cache if available and not expired.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Cached data if available, None otherwise
        """
        cache_path = self._get_cache_path(endpoint)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
                
            # Check if cache is expired
            timestamp = cached_data.get('timestamp', 0)
            if time.time() - timestamp > self.cache_expiry:
                logger.debug(f"Cache expired for {endpoint}")
                return None
                
            logger.debug(f"Cache hit for {endpoint}")
            return cached_data.get('data')
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error reading cache for {endpoint}: {e}")
            return None
            
    def _write_cache(self, endpoint: str, data: Any) -> None:
        """
        Write data to cache.
        
        Args:
            endpoint: API endpoint
            data: Data to cache
        """
        cache_path = self._get_cache_path(endpoint)
        cache_data = {
            'timestamp': time.time(),
            'data': data
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            logger.debug(f"Cached data for {endpoint}")
        except (IOError, OSError) as e:
            logger.warning(f"Failed to write cache for {endpoint}: {e}")
        
    def clear_cache(self, endpoint: Optional[str] = None) -> None:
        """
        Clear cache for a specific endpoint or all endpoints.
        
        Args:
            endpoint: API endpoint to clear cache for. If None, clear all cache.
        """
        if endpoint:
            cache_path = self._get_cache_path(endpoint)
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"Cleared cache for {endpoint}")
        else:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
            logger.info("Cleared all cache")
            
        # After clearing cache, invalidate any remaining old files
        self.invalidate_old_cache(self.max_cache_age_days)
    
    def periodic_cleanup(self) -> None:
        """
        Perform periodic cache maintenance.
        Call this method regularly for long-running applications.
        """
        # Invalidate old cache files
        self.invalidate_old_cache(self.max_cache_age_days)
        
        # Log cache statistics
        total_files = len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])
        logger.info(f"Cache status: {total_files} files in cache")
    
    def _make_request(self, endpoint: str, use_cache: bool = True) -> Any:
        """
        Make a request to the SpaceX API with caching and error handling.
        
        Args:
            endpoint: API endpoint (without base URL)
            use_cache: Whether to use cached data if available
            
        Returns:
            API response data
            
        Raises:
            RequestException: If the API request fails after retries
        """
        if use_cache:
            cached_data = self._read_cache(endpoint)
            if cached_data is not None:
                return cached_data
        
        url = f"{self.BASE_URL}{endpoint}"
        logger.info(f"Fetching data from {url}")
        
        # Try the request with one retry
        for attempt in range(2):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Cache the successful response
                if use_cache:
                    self._write_cache(endpoint, data)
                    
                return data
                
            except RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/2): {e}")
                if attempt == 1:  # Last attempt failed
                    raise
                time.sleep(1)  # Short delay before retry
    
    def get_all_launches(self) -> List[Dict]:
        """
        Get all SpaceX launches.
        
        Returns:
            List of launch data
        """
        return self._make_request("/launches")
    
    def get_past_launches(self) -> List[Dict]:
        """
        Get past SpaceX launches.
        
        Returns:
            List of past launch data
        """
        return self._make_request("/launches/past")
    
    def get_upcoming_launches(self) -> List[Dict]:
        """
        Get upcoming SpaceX launches.
        
        Returns:
            List of upcoming launch data
        """
        return self._make_request("/launches/upcoming")
    
    def get_launch_by_id(self, launch_id: str) -> Dict:
        """
        Get a specific launch by ID.
        
        Args:
            launch_id: Launch ID
            
        Returns:
            Launch data
        """
        return self._make_request(f"/launches/{launch_id}")
    
    def get_all_rockets(self) -> List[Dict]:
        """
        Get all SpaceX rockets.
        
        Returns:
            List of rocket data
        """
        return self._make_request("/rockets")
    
    def get_rocket_by_id(self, rocket_id: str) -> Dict:
        """
        Get a specific rocket by ID.
        
        Args:
            rocket_id: Rocket ID
            
        Returns:
            Rocket data
        """
        return self._make_request(f"/rockets/{rocket_id}")
    
    def get_all_launchpads(self) -> List[Dict]:
        """
        Get all SpaceX launchpads.
        
        Returns:
            List of launchpad data
        """
        return self._make_request("/launchpads")
    
    def get_launchpad_by_id(self, launchpad_id: str) -> Dict:
        """
        Get a specific launchpad by ID.
        
        Args:
            launchpad_id: Launchpad ID
            
        Returns:
            Launchpad data
        """
        return self._make_request(f"/launchpads/{launchpad_id}")
    
    def clear_cache(self, endpoint: Optional[str] = None) -> None:
        """
        Clear cache for a specific endpoint or all endpoints.
        
        Args:
            endpoint: API endpoint to clear cache for. If None, clear all cache.
        """
        if endpoint:
            cache_path = self._get_cache_path(endpoint)
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"Cleared cache for {endpoint}")
        else:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
            logger.info("Cleared all cache")

    def invalidate_old_cache(self, max_age_days: int = 7) -> None:
        """
        Invalidate cache files older than the specified number of days.
        
        Args:
            max_age_days: Maximum age of cache files in days
        """
        cutoff_time = time.time() - (max_age_days * 86400)
        
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed old cache file: {filename}")
                except OSError as e:
                    logger.warning(f"Failed to remove old cache file {filename}: {e}")