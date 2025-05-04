"""
This module provides functions for calculating statistics about SpaceX launches.
"""

from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any

from .models import Launch


def calculate_success_rate_by_rocket(launches: List[Launch]) -> Dict[str, float]:
    """
    Calculate the success rate for each rocket type.
    
    Args:
        launches: List of launches
        
    Returns:
        Dictionary mapping rocket names to success rates (0-100%)
    """
    if not launches:
        return {}
    
    rocket_attempts = defaultdict(int)
    rocket_successes = defaultdict(int)
    
    for launch in launches:
        if launch.rocket_name and not launch.upcoming:
            rocket_attempts[launch.rocket_name] += 1
            if launch.success:
                rocket_successes[launch.rocket_name] += 1
    
    success_rates = {}
    for rocket_name, attempts in rocket_attempts.items():
        if attempts > 0:
            success_rates[rocket_name] = (rocket_successes[rocket_name] / attempts) * 100
        else:
            success_rates[rocket_name] = 0.0
            
    return success_rates


def count_launches_by_site(launches: List[Launch]) -> Dict[str, int]:
    """
    Count the number of launches for each launch site.
    
    Args:
        launches: List of launches
        
    Returns:
        Dictionary mapping site names to launch counts
    """
    site_counts = defaultdict(int)
    
    for launch in launches:
        if launch.launchpad_name:
            site_counts[launch.launchpad_name] += 1
            
    return dict(site_counts)


def calculate_monthly_frequency(launches: List[Launch]) -> Dict[str, int]:
    """
    Calculate the launch frequency by month.
    
    Args:
        launches: List of launches
        
    Returns:
        Dictionary mapping month names to launch counts
    """
    month_counts = defaultdict(int)
    
    for launch in launches:
        month_name = launch.date_utc.strftime("%B")
        month_counts[month_name] += 1
    
    # Sort by month number to get chronological order
    month_order = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    
    return {
        month: month_counts[month]
        for month in sorted(month_counts.keys(), key=lambda m: month_order.get(m, 13))
    }


def calculate_yearly_frequency(launches: List[Launch]) -> Dict[int, int]:
    """
    Calculate the launch frequency by year.
    
    Args:
        launches: List of launches
        
    Returns:
        Dictionary mapping years to launch counts
    """
    year_counts = defaultdict(int)
    
    for launch in launches:
        year = launch.date_utc.year
        year_counts[year] += 1
    
    # Sort by year
    return {
        year: year_counts[year]
        for year in sorted(year_counts.keys())
    }


def get_most_launched_rocket(launches: List[Launch]) -> Tuple[str, int]:
    """
    Get the most frequently launched rocket.
    
    Args:
        launches: List of launches
        
    Returns:
        Tuple of (rocket_name, launch_count)
    """
    rocket_counts = defaultdict(int)
    
    for launch in launches:
        if launch.rocket_name:
            rocket_counts[launch.rocket_name] += 1
    
    if not rocket_counts:
        return ("Unknown", 0)
    
    most_common_rocket = max(rocket_counts.items(), key=lambda x: x[1])
    return most_common_rocket


def get_busiest_launch_site(launches: List[Launch]) -> Tuple[str, int]:
    """
    Get the busiest launch site.
    
    Args:
        launches: List of launches
        
    Returns:
        Tuple of (site_name, launch_count)
    """
    site_counts = count_launches_by_site(launches)
    
    if not site_counts:
        return ("Unknown", 0)
    
    busiest_site = max(site_counts.items(), key=lambda x: x[1])
    return busiest_site


def get_launch_success_trend(launches: List[Launch]) -> Dict[int, float]:
    """
    Get the trend of launch success rates by year.
    
    Args:
        launches: List of launches
        
    Returns:
        Dictionary mapping years to success rates (0-100%)
    """
    if not launches:
        return {}
    
    year_attempts = defaultdict(int)
    year_successes = defaultdict(int)
    
    for launch in launches:
        if not launch.upcoming:
            year = launch.date_utc.year
            year_attempts[year] += 1
            if launch.success:
                year_successes[year] += 1
    
    success_rates = {}
    for year, attempts in year_attempts.items():
        if attempts > 0:
            success_rates[year] = (year_successes[year] / attempts) * 100
        else:
            success_rates[year] = 0.0
    
    # Sort by year
    return {
        year: success_rates[year]
        for year in sorted(success_rates.keys())
    }


def generate_launch_summary(launches: List[Launch]) -> Dict[str, Any]:
    """
    Generate a comprehensive summary of launch statistics.
    
    Args:
        launches: List of launches
        
    Returns:
        Dictionary containing various statistics
    """
    if not launches:
        return {
            "total_launches": 0,
            "successful_launches": 0,
            "failed_launches": 0,
            "success_rate": 0.0,
            "most_used_rocket": "Unknown",
            "busiest_launch_site": "Unknown"
        }
    
    # Count launches
    completed_launches = [launch for launch in launches if not launch.upcoming]
    successful_launches = [launch for launch in completed_launches if launch.success]
    failed_launches = [launch for launch in completed_launches if launch.success is False]
    
    # Calculate overall success rate
    total_completed = len(completed_launches)
    success_rate = (len(successful_launches) / total_completed * 100) if total_completed > 0 else 0.0
    
    # Get most used rocket and busiest site
    most_used_rocket, rocket_count = get_most_launched_rocket(launches)
    busiest_site, site_count = get_busiest_launch_site(launches)
    
    return {
        "total_launches": len(launches),
        "upcoming_launches": len([l for l in launches if l.upcoming]),
        "completed_launches": total_completed,
        "successful_launches": len(successful_launches),
        "failed_launches": len(failed_launches),
        "success_rate": success_rate,
        "most_used_rocket": most_used_rocket,
        "most_used_rocket_count": rocket_count,
        "busiest_launch_site": busiest_site,
        "busiest_launch_site_count": site_count
    }