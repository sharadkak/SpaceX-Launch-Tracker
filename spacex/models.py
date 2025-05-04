"""
This module defines data models for SpaceX launches, rockets, and launchpads.
These models provide a clean interface to work with the API data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union, Any


@dataclass
class Rocket:
    """Model representing a SpaceX rocket."""
    
    id: str
    name: str
    type: str
    active: bool
    stages: int
    boosters: int
    success_rate_pct: int
    first_flight: str
    description: Optional[str] = None
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Rocket':
        """
        Create a Rocket instance from API data.
        
        Args:
            data: Rocket data from the API
            
        Returns:
            Rocket instance
        """
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            active=data['active'],
            stages=data['stages'],
            boosters=data['boosters'],
            success_rate_pct=data['success_rate_pct'],
            first_flight=data['first_flight'],
            description=data.get('description')
        )


@dataclass
class Launchpad:
    """Model representing a SpaceX launchpad."""
    
    id: str
    name: str
    full_name: str
    locality: str
    region: str
    latitude: float
    longitude: float
    launch_attempts: int
    launch_successes: int
    status: str
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Launchpad':
        """
        Create a Launchpad instance from API data.
        
        Args:
            data: Launchpad data from the API
            
        Returns:
            Launchpad instance
        """
        return cls(
            id=data['id'],
            name=data['name'],
            full_name=data['full_name'],
            locality=data['locality'],
            region=data['region'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            launch_attempts=data['launch_attempts'],
            launch_successes=data['launch_successes'],
            status=data['status']
        )


@dataclass
class Launch:
    """Model representing a SpaceX launch."""
    
    id: str
    name: str
    date_utc: datetime
    date_unix: int
    success: Optional[bool]
    rocket_id: str
    launchpad_id: str
    flight_number: int
    upcoming: bool
    rocket_name: Optional[str] = None
    launchpad_name: Optional[str] = None
    details: Optional[str] = None
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any], 
                     rockets: Optional[Dict[str, Rocket]] = None,
                     launchpads: Optional[Dict[str, Launchpad]] = None) -> 'Launch':
        """
        Create a Launch instance from API data.
        
        Args:
            data: Launch data from the API
            rockets: Optional dictionary of rockets by ID for name resolution
            launchpads: Optional dictionary of launchpads by ID for name resolution
            
        Returns:
            Launch instance
        """
        # Parse the date string to datetime
        try:
            date_utc = datetime.fromisoformat(data['date_utc'].replace('Z', '+00:00'))
        except (ValueError, KeyError):
            # Fallback to current time if date parsing fails
            date_utc = datetime.utcnow()
        
        # Get rocket and launchpad names if available
        rocket_name = None
        if rockets and data.get('rocket') in rockets:
            rocket_name = rockets[data['rocket']].name
            
        launchpad_name = None
        if launchpads and data.get('launchpad') in launchpads:
            launchpad_name = launchpads[data['launchpad']].name
        
        return cls(
            id=data['id'],
            name=data['name'],
            date_utc=date_utc,
            date_unix=data['date_unix'],
            success=data.get('success'),  # May be None for upcoming launches
            rocket_id=data.get('rocket', ''),
            launchpad_id=data.get('launchpad', ''),
            flight_number=data['flight_number'],
            upcoming=data['upcoming'],
            rocket_name=rocket_name,
            launchpad_name=launchpad_name,
            details=data.get('details')
        )


class DataRepository:
    """Repository for accessing and relating SpaceX data."""
    
    def __init__(self):
        """Initialize empty data containers."""
        self.launches: List[Launch] = []
        self.rockets: Dict[str, Rocket] = {}
        self.launchpads: Dict[str, Launchpad] = {}
        
    def add_rocket(self, rocket_data: Dict[str, Any]) -> None:
        """
        Add a rocket to the repository.
        
        Args:
            rocket_data: Rocket data from the API
        """
        rocket = Rocket.from_api_data(rocket_data)
        self.rockets[rocket.id] = rocket
        
    def add_launchpad(self, launchpad_data: Dict[str, Any]) -> None:
        """
        Add a launchpad to the repository.
        
        Args:
            launchpad_data: Launchpad data from the API
        """
        launchpad = Launchpad.from_api_data(launchpad_data)
        self.launchpads[launchpad.id] = launchpad
        
    def add_launch(self, launch_data: Dict[str, Any]) -> None:
        """
        Add a launch to the repository.
        
        Args:
            launch_data: Launch data from the API
        """
        launch = Launch.from_api_data(launch_data, self.rockets, self.launchpads)
        self.launches.append(launch)
    
    def load_rockets(self, rockets_data: List[Dict[str, Any]]) -> None:
        """
        Load multiple rockets into the repository.
        
        Args:
            rockets_data: List of rocket data from the API
        """
        for rocket_data in rockets_data:
            self.add_rocket(rocket_data)
    
    def load_launchpads(self, launchpads_data: List[Dict[str, Any]]) -> None:
        """
        Load multiple launchpads into the repository.
        
        Args:
            launchpads_data: List of launchpad data from the API
        """
        for launchpad_data in launchpads_data:
            self.add_launchpad(launchpad_data)
    
    def load_launches(self, launches_data: List[Dict[str, Any]]) -> None:
        """
        Load multiple launches into the repository.
        
        Args:
            launches_data: List of launch data from the API
        """
        for launch_data in launches_data:
            self.add_launch(launch_data)