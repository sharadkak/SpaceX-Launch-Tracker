"""
This module provides filtering functions for SpaceX launches based on various criteria.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Callable

from .models import Launch

def filter_by_date_range(launches: List[Launch], 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Launch]:
    """
    Filter launches by date range.
    
    Args:
        launches: List of launches to filter
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        Filtered list of launches
    """
    filtered_launches = launches
    
    if start_date:
        start_date = start_date.replace(tzinfo=timezone.utc)
        filtered_launches = [
            launch for launch in filtered_launches
            if launch.date_utc >= start_date
        ]
        
    if end_date:
        end_date = end_date.replace(tzinfo=timezone.utc)
        filtered_launches = [
            launch for launch in filtered_launches
            if launch.date_utc <= end_date
        ]
        
    return filtered_launches


def filter_by_rocket_name(launches: List[Launch], rocket_name: str) -> List[Launch]:
    """
    Filter launches by rocket name.
    
    Args:
        launches: List of launches to filter
        rocket_name: Rocket name to filter by 
        
    Returns:
        Filtered list of launches
    """
    rocket_name_lower = rocket_name.lower()
    return [
        launch for launch in launches
        if launch.rocket_name and rocket_name_lower in launch.rocket_name.lower()
    ]


def filter_by_success(launches: List[Launch], success: Optional[bool] = None) -> List[Launch]:
    """
    Filter launches by success status.
    
    Args:
        launches: List of launches to filter
        success: Success status to filter by (None for all launches)
        
    Returns:
        Filtered list of launches
    """
    if success is None:
        return launches
        
    return [
        launch for launch in launches
        if launch.success is not None and launch.success == success
    ]


def filter_by_launch_site(launches: List[Launch], site_name: str) -> List[Launch]:
    """
    Filter launches by launch site name.
    
    Args:
        launches: List of launches to filter
        site_name: Site name to filter by 
        
    Returns:
        Filtered list of launches
    """
    site_name_lower = site_name.lower()
    return [
        launch for launch in launches
        if launch.launchpad_name and site_name_lower in launch.launchpad_name.lower()
    ]


def filter_launches(launches: List[Launch], 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   rocket_name: Optional[str] = None,
                   success: Optional[bool] = None,
                   site_name: Optional[str] = None) -> List[Launch]:
    """
    Filter launches by multiple criteria.
    
    Args:
        launches: List of launches to filter
        start_date: Optional start date (inclusive)
        end_date: Optional end date (inclusive)
        rocket_name: Optional rocket name to filter by
        success: Optional success status to filter by
        site_name: Optional site name to filter by
        
    Returns:
        Filtered list of launches
    """
    filtered = launches
    
    # Apply filters sequentially
    if start_date or end_date:
        filtered = filter_by_date_range(filtered, start_date, end_date)
        
    if rocket_name:
        filtered = filter_by_rocket_name(filtered, rocket_name)
        
    if success is not None:
        filtered = filter_by_success(filtered, success)
        
    if site_name:
        filtered = filter_by_launch_site(filtered, site_name)
        
    return filtered


def apply_custom_filter(launches: List[Launch], 
                        filter_func: Callable[[Launch], bool]) -> List[Launch]:
    """
    Apply a custom filter function to launches.
    
    Args:
        launches: List of launches to filter
        filter_func: Function that takes a Launch and returns a boolean
        
    Returns:
        Filtered list of launches
    """
    return [launch for launch in launches if filter_func(launch)]


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string into a datetime object.
    
    Args:
        date_str: Date string in ISO format (YYYY-MM-DD)
        
    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None