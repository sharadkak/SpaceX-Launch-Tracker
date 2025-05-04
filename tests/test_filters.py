"""
Tests for the SpaceX filters module using pytest.
"""

from datetime import datetime

import pytest

from spacex.filters import (
    filter_by_date_range,
    filter_by_rocket_name,
    filter_by_success,
    filter_by_launch_site,
    filter_launches,
    parse_date
)
from spacex.models import Launch


@pytest.fixture
def sample_launches():
    """Create test launch data."""
    return [
        Launch(
            id="1",
            name="Test Launch 1",
            date_utc=datetime(2020, 1, 1),
            date_unix=1577836800,
            success=True,
            rocket_id="falcon9",
            launchpad_id="ksc",
            flight_number=1,
            upcoming=False,
            rocket_name="Falcon 9",
            launchpad_name="Kennedy Space Center",
            details="Test launch details"
        ),
        Launch(
            id="2",
            name="Test Launch 2",
            date_utc=datetime(2020, 2, 1),
            date_unix=1580515200,
            success=False,
            rocket_id="falcon9",
            launchpad_id="vafb",
            flight_number=2,
            upcoming=False,
            rocket_name="Falcon 9",
            launchpad_name="Vandenberg",
            details="Test launch details"
        ),
        Launch(
            id="3",
            name="Test Launch 3",
            date_utc=datetime(2020, 3, 1),
            date_unix=1583020800,
            success=None,
            rocket_id="falconheavy",
            launchpad_id="ksc",
            flight_number=3,
            upcoming=True,
            rocket_name="Falcon Heavy",
            launchpad_name="Kennedy Space Center",
            details="Test launch details"
        ),
        Launch(
            id="4",
            name="Test Launch 4",
            date_utc=datetime(2021, 1, 1),
            date_unix=1609459200,
            success=True,
            rocket_id="starship",
            launchpad_id="boca",
            flight_number=4,
            upcoming=False,
            rocket_name="Starship",
            launchpad_name="Boca Chica",
            details="Test launch details"
        )
    ]


def test_filter_by_date_range_both_dates(sample_launches):
    """Test filtering by date range with both start and end dates."""
    start_date = datetime(2020, 1, 15)
    end_date = datetime(2020, 3, 15)
    
    filtered = filter_by_date_range(sample_launches, start_date, end_date)
    
    assert len(filtered) == 2
    assert filtered[0].id == "2"
    assert filtered[1].id == "3"


def test_filter_by_date_range_start_date_only(sample_launches):
    """Test filtering by date range with only start date."""
    start_date = datetime(2020, 2, 15)
    
    filtered = filter_by_date_range(sample_launches, start_date)
    
    assert len(filtered) == 2
    assert filtered[0].id == "3"
    assert filtered[1].id == "4"


def test_filter_by_date_range_end_date_only(sample_launches):
    """Test filtering by date range with only end date."""
    end_date = datetime(2020, 2, 15)
    
    filtered = filter_by_date_range(sample_launches, end_date=end_date)
    
    assert len(filtered) == 2
    assert filtered[0].id == "1"
    assert filtered[1].id == "2"


def test_filter_by_rocket_name(sample_launches):
    """Test filtering by rocket name."""
    filtered = filter_by_rocket_name(sample_launches, "falcon")
    
    assert len(filtered) == 3
    assert filtered[0].id == "1"
    assert filtered[1].id == "2"
    assert filtered[2].id == "3"


def test_filter_by_rocket_name_case_insensitive(sample_launches):
    """Test filtering by rocket name is case insensitive."""
    filtered = filter_by_rocket_name(sample_launches, "FALCON")
    
    assert len(filtered) == 3


def test_filter_by_success_true(sample_launches):
    """Test filtering by success=True."""
    filtered = filter_by_success(sample_launches, True)
    
    assert len(filtered) == 2
    assert filtered[0].id == "1"
    assert filtered[1].id == "4"


def test_filter_by_success_false(sample_launches):
    """Test filtering by success=False."""
    filtered = filter_by_success(sample_launches, False)
    
    assert len(filtered) == 1
    assert filtered[0].id == "2"


def test_filter_by_success_none(sample_launches):
    """Test filtering by success=None returns all launches."""
    filtered = filter_by_success(sample_launches, None)
    
    assert len(filtered) == 4


def test_filter_by_launch_site(sample_launches):
    """Test filtering by launch site."""
    filtered = filter_by_launch_site(sample_launches, "Kennedy")
    
    assert len(filtered) == 2
    assert filtered[0].id == "1"
    assert filtered[1].id == "3"


def test_filter_by_launch_site_case_insensitive(sample_launches):
    """Test filtering by launch site is case insensitive."""
    filtered = filter_by_launch_site(sample_launches, "kennedy")
    
    assert len(filtered) == 2


def test_filter_launches_multiple_criteria(sample_launches):
    """Test filtering launches with multiple criteria."""
    filtered = filter_launches(
        sample_launches,
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 12, 31),
        rocket_name="Falcon",
        success=True,
        site_name="Kennedy"
    )
    
    assert len(filtered) == 1
    assert filtered[0].id == "1"


def test_parse_date_valid():
    """Test parsing a valid date string."""
    date = parse_date("2020-01-01")
    
    assert date == datetime(2020, 1, 1)


def test_parse_date_invalid():
    """Test parsing an invalid date string."""
    date = parse_date("invalid-date")
    
    assert date is None


def test_empty_launch_list():
    """Test handling empty launch list."""
    empty_list = []
    
    # All filter functions should handle empty lists gracefully
    assert filter_by_date_range(empty_list) == []
    assert filter_by_rocket_name(empty_list, "Falcon") == []
    assert filter_by_success(empty_list, True) == []
    assert filter_by_launch_site(empty_list, "Kennedy") == []
    assert filter_launches(empty_list) == []


def test_filter_no_matches(sample_launches):
    """Test filtering with criteria that match no launches."""
    filtered = filter_launches(
        sample_launches,
        rocket_name="Nonexistent Rocket",
        site_name="Nonexistent Site"
    )
    
    assert filtered == []


@pytest.mark.parametrize("rocket_name,expected_count", [
    ("Falcon", 3),
    ("Heavy", 1),
    ("Starship", 1),
    ("Nonexistent", 0)
])
def test_filter_by_rocket_name_parametrized(sample_launches, rocket_name, expected_count):
    """Test filtering by various rocket names using parametrization."""
    filtered = filter_by_rocket_name(sample_launches, rocket_name)
    assert len(filtered) == expected_count


@pytest.mark.parametrize("site_name,expected_count", [
    ("Kennedy", 2),
    ("Vandenberg", 1),
    ("Boca", 1),
    ("Nonexistent", 0)
])
def test_filter_by_site_name_parametrized(sample_launches, site_name, expected_count):
    """Test filtering by various site names using parametrization."""
    filtered = filter_by_launch_site(sample_launches, site_name)
    assert len(filtered) == expected_count