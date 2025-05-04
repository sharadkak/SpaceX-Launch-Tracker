"""
Tests for the SpaceX API client using pytest.
"""

import os
import tempfile
import time
from unittest import mock

import pytest
import requests

from spacex.api_client import SpaceXAPIClient

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after tests
    for filename in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, filename))
    os.rmdir(temp_dir)


@pytest.fixture
def api_client(temp_cache_dir):
    """Create an API client for testing."""
    return SpaceXAPIClient(cache_dir=temp_cache_dir, cache_expiry=60)


def test_make_request_success(api_client):
    """Test successful API request."""
    # Setup mock response
    with mock.patch('requests.get') as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        # Execute the request
        result = api_client._make_request("/test")
        
        # Verify request was made correctly
        mock_get.assert_called_once_with(
            "https://api.spacexdata.com/v4/test", 
            timeout=10
        )
        
        # Verify the result
        assert result == {"test": "data"}


def test_make_request_with_retry(api_client):
    """Test API request with retry on failure."""
    # Setup mock responses
    with mock.patch('requests.get') as mock_get:
        fail_response = mock.Mock()
        fail_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error")
        
        success_response = mock.Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"test": "data"}
        
        # First call fails, second one succeeds
        mock_get.side_effect = [fail_response, success_response]
        
        # Execute the request
        result = api_client._make_request("/test")
        
        # Verify request was made twice
        assert mock_get.call_count == 2
        
        # Verify the result
        assert result == {"test": "data"}


def test_make_request_all_retries_fail(api_client):
    """Test API request when all retries fail."""
    # Setup mock response to always fail
    with mock.patch('requests.get') as mock_get:
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error")
        mock_get.return_value = mock_response
        
        # Execute the request and expect exception
        with pytest.raises(requests.exceptions.RequestException):
            api_client._make_request("/test")
        
        # Verify request was made twice (initial + retry)
        assert mock_get.call_count == 2


def test_cache_writing_and_reading(api_client):
    """Test writing to and reading from cache."""
    endpoint = "/test-cache"
    test_data = {"test": "cache_data"}
    
    # Write to cache
    api_client._write_cache(endpoint, test_data)
    
    # Read from cache
    cached_data = api_client._read_cache(endpoint)
    
    assert cached_data == test_data


def test_cache_expiry(temp_cache_dir):
    """Test cache expiry functionality."""
    endpoint = "/test-expiry"
    test_data = {"test": "expiry_data"}
    
    # Create client with very short expiry
    short_expiry_client = SpaceXAPIClient(cache_dir=temp_cache_dir, cache_expiry=1)
    
    # Write to cache
    short_expiry_client._write_cache(endpoint, test_data)
    
    # Read immediately should succeed
    cached_data = short_expiry_client._read_cache(endpoint)
    assert cached_data == test_data
    
    # Wait for cache to expire
    time.sleep(1.1)
    
    # Read after expiry should fail
    expired_data = short_expiry_client._read_cache(endpoint)
    assert expired_data is None


def test_clear_cache_specific(api_client):
    """Test clearing cache for a specific endpoint."""
    endpoint1 = "/test-clear1"
    endpoint2 = "/test-clear2"
    test_data = {"test": "clear_data"}
    
    # Write to both caches
    api_client._write_cache(endpoint1, test_data)
    api_client._write_cache(endpoint2, test_data)
    
    # Clear just the first cache
    api_client.clear_cache(endpoint1)
    
    # First cache should be gone, second should remain
    assert api_client._read_cache(endpoint1) is None
    assert api_client._read_cache(endpoint2) == test_data


def test_clear_cache_all(api_client):
    """Test clearing all cache."""
    endpoint1 = "/test-clear-all1"
    endpoint2 = "/test-clear-all2"
    test_data = {"test": "clear_all_data"}
    
    # Write to both caches
    api_client._write_cache(endpoint1, test_data)
    api_client._write_cache(endpoint2, test_data)
    
    # Clear all cache
    api_client.clear_cache()
    
    # Both caches should be gone
    assert api_client._read_cache(endpoint1) is None
    assert api_client._read_cache(endpoint2) is None


def test_get_all_launches(api_client):
    """Test get_all_launches method."""
    with mock.patch.object(api_client, '_make_request') as mock_request:
        mock_request.return_value = [{"id": "1", "name": "Test Launch"}]
        
        launches = api_client.get_all_launches()
        
        mock_request.assert_called_once_with("/launches")
        assert launches == [{"id": "1", "name": "Test Launch"}]


def test_get_all_rockets(api_client):
    """Test get_all_rockets method."""
    with mock.patch.object(api_client, '_make_request') as mock_request:
        mock_request.return_value = [{"id": "1", "name": "Falcon 9"}]
        
        rockets = api_client.get_all_rockets()
        
        mock_request.assert_called_once_with("/rockets")
        assert rockets == [{"id": "1", "name": "Falcon 9"}]


def test_get_all_launchpads(api_client):
    """Test get_all_launchpads method."""
    with mock.patch.object(api_client, '_make_request') as mock_request:
        mock_request.return_value = [{"id": "1", "name": "KSC"}]
        
        launchpads = api_client.get_all_launchpads()
        
        mock_request.assert_called_once_with("/launchpads")
        assert launchpads == [{"id": "1", "name": "KSC"}]


def test_cache_path_creation(api_client):
    """Test the cache path is created correctly."""
    endpoint = "/test/endpoint"
    expected_path = os.path.join(api_client.cache_dir, "test_endpoint.json")
    
    assert api_client._get_cache_path(endpoint) == expected_path


def test_invalidate_old_cache(api_client, monkeypatch):
    """Test invalidation of old cache files."""
    # Create test cache files
    test_data = {"test": "data"}
    api_client._write_cache("/test1", test_data)
    api_client._write_cache("/test2", test_data)
    
    # Mock os.path.getmtime to make one file appear old
    original_getmtime = os.path.getmtime
    
    def mock_getmtime(path):
        if "test1" in path:
            # Return a time that's 10 days old
            return time.time() - (10 * 86400)
        return original_getmtime(path)
    
    monkeypatch.setattr(os.path, "getmtime", mock_getmtime)
    
    # Run the invalidation with 7 days as max age
    api_client.invalidate_old_cache(max_age_days=7)
    
    # test1 should be removed, test2 should remain
    assert api_client._read_cache("/test1") is None
    assert api_client._read_cache("/test2") == test_data