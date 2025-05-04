"""
Main module that ties together the API client, data models, filters, and statistics.
Provides a command-line interface for interacting with the application.
"""

import argparse
import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from spacex.api_client import SpaceXAPIClient
from spacex.models import DataRepository, Launch
from spacex.filters import filter_launches, parse_date
from spacex.statistics import (
    calculate_success_rate_by_rocket,
    count_launches_by_site,
    calculate_monthly_frequency,
    calculate_yearly_frequency,
    generate_launch_summary
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpaceXTracker:
    """Main class for the SpaceX Launch Tracker application."""
    
    def __init__(self, cache_dir: Optional[str] = None, cache_expiry: int = 3600):
        """
        Initialize the SpaceX Tracker.
        
        Args:
            cache_dir: Directory to store cached data
            cache_expiry: Cache expiry time in seconds
        """
        self.api_client = SpaceXAPIClient(cache_dir, cache_expiry)
        self.data_repo = DataRepository()
        
    def load_data(self, force_refresh: bool = False) -> None:
        """
        Load data from the SpaceX API.
        
        Args:
            force_refresh: Whether to force a refresh from the API
        """
        logger.info("Loading data from SpaceX API...")
        
        # Clear cache if force refresh
        if force_refresh:
            self.api_client.clear_cache()
        
        # Load rockets
        try:
            rockets_data = self.api_client.get_all_rockets()
            self.data_repo.load_rockets(rockets_data)
            logger.info(f"Loaded {len(rockets_data)} rockets")
        except Exception as e:
            logger.error(f"Failed to load rockets: {e}")
            
        # Load launchpads
        try:
            launchpads_data = self.api_client.get_all_launchpads()
            self.data_repo.load_launchpads(launchpads_data)
            logger.info(f"Loaded {len(launchpads_data)} launchpads")
        except Exception as e:
            logger.error(f"Failed to load launchpads: {e}")
            
        # Load launches
        try:
            launches_data = self.api_client.get_all_launches()
            self.data_repo.load_launches(launches_data)
            logger.info(f"Loaded {len(launches_data)} launches")
        except Exception as e:
            logger.error(f"Failed to load launches: {e}")
            
    def get_filtered_launches(self, 
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             rocket_name: Optional[str] = None,
                             success: Optional[bool] = None,
                             site_name: Optional[str] = None) -> List[Launch]:
        """
        Get filtered launches based on criteria.
        
        Args:
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            rocket_name: Optional rocket name
            success: Optional success status
            site_name: Optional launch site name
            
        Returns:
            Filtered list of launches
        """
        start_date_dt = parse_date(start_date) if start_date else None
        end_date_dt = parse_date(end_date) if end_date else None
        
        return filter_launches(
            self.data_repo.launches,
            start_date=start_date_dt,
            end_date=end_date_dt,
            rocket_name=rocket_name,
            success=success,
            site_name=site_name
        )
        
    def display_launches(self, launches: List[Launch]) -> None:
        """
        Display launches in a formatted table.
        
        Args:
            launches: List of launches to display
        """
        if not launches:
            print("No launches found matching the criteria.")
            return
            
        # Print header
        print("\nLAUNCH LIST")
        print("-" * 80)
        print(f"{'DATE':<12} {'MISSION':<30} {'ROCKET':<15} {'SUCCESS':<10} {'SITE':<20}")
        print("-" * 80)
        
        # Print each launch
        for launch in sorted(launches, key=lambda x: x.date_unix):
            date_str = launch.date_utc.strftime("%Y-%m-%d")
            success_str = "SUCCESS" if launch.success else "FAILURE" if launch.success is False else "UPCOMING"
            print(f"{date_str:<12} {launch.name[:28]:<30} {(launch.rocket_name or '')[:15]:<15} "
                  f"{success_str:<10} {(launch.launchpad_name or '')[:20]:<20}")
                  
    def display_success_rates(self, launches: List[Launch]) -> None:
        """
        Display success rates by rocket.
        
        Args:
            launches: List of launches to analyze
        """
        success_rates = calculate_success_rate_by_rocket(launches)
        
        if not success_rates:
            print("No success rate data available.")
            return
            
        print("\nSUCCESS RATES BY ROCKET")
        print("-" * 50)
        print(f"{'ROCKET':<20} {'SUCCESS RATE':<15} {'LAUNCHES':<10}")
        print("-" * 50)
        
        # Count launches by rocket
        rocket_counts = {}
        for launch in launches:
            if launch.rocket_name and not launch.upcoming:
                rocket_counts[launch.rocket_name] = rocket_counts.get(launch.rocket_name, 0) + 1
        
        # Print each rocket's success rate
        for rocket_name, rate in sorted(success_rates.items(), key=lambda x: x[1], reverse=True):
            count = rocket_counts.get(rocket_name, 0)
            print(f"{rocket_name[:20]:<20} {rate:.1f}%{' ':8} {count:<10}")
            
    def display_site_statistics(self, launches: List[Launch]) -> None:
        """
        Display launch statistics by site.
        
        Args:
            launches: List of launches to analyze
        """
        site_counts = count_launches_by_site(launches)
        
        if not site_counts:
            print("No launch site data available.")
            return
            
        print("\nLAUNCHES BY SITE")
        print("-" * 50)
        print(f"{'LAUNCH SITE':<30} {'LAUNCHES':<10}")
        print("-" * 50)
        
        # Print each site's launch count
        for site_name, count in sorted(site_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{site_name[:30]:<30} {count:<10}")
            
    def display_time_statistics(self, launches: List[Launch]) -> None:
        """
        Display launch statistics by time period.
        
        Args:
            launches: List of launches to analyze
        """
        monthly_freq = calculate_monthly_frequency(launches)
        yearly_freq = calculate_yearly_frequency(launches)
        
        # Display yearly statistics
        print("\nLAUNCHES BY YEAR")
        print("-" * 30)
        print(f"{'YEAR':<10} {'LAUNCHES':<10}")
        print("-" * 30)
        
        for year, count in yearly_freq.items():
            print(f"{year:<10} {count:<10}")
            
        # Display monthly statistics
        print("\nLAUNCHES BY MONTH")
        print("-" * 30)
        print(f"{'MONTH':<10} {'LAUNCHES':<10}")
        print("-" * 30)
        
        for month, count in monthly_freq.items():
            print(f"{month[:10]:<10} {count:<10}")
            
    def display_summary(self, launches: List[Launch]) -> None:
        """
        Display a summary of launch statistics.
        
        Args:
            launches: List of launches to analyze
        """
        summary = generate_launch_summary(launches)
        
        print("\nLAUNCH SUMMARY")
        print("-" * 50)
        print(f"Total launches: {summary['total_launches']}")
        print(f"Upcoming launches: {summary['upcoming_launches']}")
        print(f"Completed launches: {summary['completed_launches']}")
        print(f"Successful launches: {summary['successful_launches']}")
        print(f"Failed launches: {summary['failed_launches']}")
        print(f"Overall success rate: {summary['success_rate']:.1f}%")
        print(f"Most used rocket: {summary['most_used_rocket']} ({summary['most_used_rocket_count']} launches)")
        print(f"Busiest launch site: {summary['busiest_launch_site']} ({summary['busiest_launch_site_count']} launches)")
        
    def export_to_json(self, launches: List[Launch], filename: str) -> None:
        """
        Export launches to a JSON file.
        
        Args:
            launches: List of launches to export
            filename: Output filename
        """
        # Convert launches to dictionaries
        launch_dicts = []
        for launch in launches:
            launch_dict = {
                "id": launch.id,
                "name": launch.name,
                "date_utc": launch.date_utc.isoformat(),
                "date_unix": launch.date_unix,
                "success": launch.success,
                "rocket_id": launch.rocket_id,
                "rocket_name": launch.rocket_name,
                "launchpad_id": launch.launchpad_id,
                "launchpad_name": launch.launchpad_name,
                "flight_number": launch.flight_number,
                "upcoming": launch.upcoming,
                "details": launch.details
            }
            launch_dicts.append(launch_dict)
            
        # Write to file
        try:
            with open(filename, 'w') as f:
                json.dump(launch_dicts, f, indent=2)
            logger.info(f"Exported {len(launches)} launches to {filename}")
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            
    def export_to_csv(self, launches: List[Launch], filename: str) -> None:
        """
        Export launches to a CSV file.
        
        Args:
            launches: List of launches to export
            filename: Output filename
        """
        # Define CSV fields
        fieldnames = [
            "id", "name", "date_utc", "success", "rocket_name", 
            "launchpad_name", "flight_number", "upcoming", "details"
        ]
        
        # Convert launches to dictionaries
        launch_dicts = []
        for launch in launches:
            launch_dict = {
                "id": launch.id,
                "name": launch.name,
                "date_utc": launch.date_utc.isoformat(),
                "success": "Yes" if launch.success else "No" if launch.success is False else "Upcoming",
                "rocket_name": launch.rocket_name or "",
                "launchpad_name": launch.launchpad_name or "",
                "flight_number": launch.flight_number,
                "upcoming": "Yes" if launch.upcoming else "No",
                "details": launch.details or ""
            }
            launch_dicts.append(launch_dict)
            
        # Write to file
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(launch_dicts)
            logger.info(f"Exported {len(launches)} launches to {filename}")
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="SpaceX Launch Tracker")
    
    # Data loading options
    parser.add_argument("--refresh", action="store_true", help="Force refresh data from API")
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached data")
    
    # Filtering options
    parser.add_argument("--start-date", help="Filter launches from this date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Filter launches until this date (YYYY-MM-DD)")
    parser.add_argument("--rocket", help="Filter by rocket name")
    parser.add_argument("--success", choices=["yes", "no"], help="Filter by launch success/failure")
    parser.add_argument("--site", help="Filter by launch site name")
    
    # Display options
    parser.add_argument("--show-launches", action="store_true", help="Show launch list")
    parser.add_argument("--show-success-rates", action="store_true", help="Show success rates by rocket")
    parser.add_argument("--show-sites", action="store_true", help="Show launch statistics by site")
    parser.add_argument("--show-time", action="store_true", help="Show launch statistics by time period")
    parser.add_argument("--show-summary", action="store_true", help="Show launch summary")
    
    # Export options
    parser.add_argument("--export-json", help="Export to JSON file, provide filename")
    parser.add_argument("--export-csv", help="Export to CSV file, provide filename")
    
    args = parser.parse_args()
    
    # Initialize tracker
    tracker = SpaceXTracker()

    # Handle cache-related operations
    if args.clear_cache:
        tracker.api_client.clear_cache()
        print("All cache data cleared.")
    
    # Load data
    tracker.load_data(force_refresh=args.refresh)
    
    # Apply filters
    success_filter = None
    if args.success == "yes":
        success_filter = True
    elif args.success == "no":
        success_filter = False
        
    filtered_launches = tracker.get_filtered_launches(
        start_date=args.start_date,
        end_date=args.end_date,
        rocket_name=args.rocket,
        success=success_filter,
        site_name=args.site
    )
    
    # Show data based on options
    if args.show_launches:
        tracker.display_launches(filtered_launches)
        
    if args.show_success_rates:
        tracker.display_success_rates(filtered_launches)
        
    if args.show_sites:
        tracker.display_site_statistics(filtered_launches)
        
    if args.show_time:
        tracker.display_time_statistics(filtered_launches)
        
    if args.show_summary:
        tracker.display_summary(filtered_launches)
        
    # Export data if requested
    if args.export_json:
        tracker.export_to_json(filtered_launches, args.export_json)
        
    if args.export_csv:
        tracker.export_to_csv(filtered_launches, args.export_csv)
        
    # If no display/export options were selected, show summary
    if not any([
        args.show_launches, args.show_success_rates, args.show_sites,
        args.show_time, args.show_summary, args.export_json, args.export_csv
    ]):
        tracker.display_summary(filtered_launches)
        

if __name__ == "__main__":
    main()