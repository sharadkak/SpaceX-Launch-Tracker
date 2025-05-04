"""
Tests for the SpaceX statistics module using pytest.
"""

from datetime import datetime

import pytest

from spacex.models import Launch
from spacex.statistics import (
    calculate_success_rate_by_rocket,
    count_launches_by_site,
    calculate_monthly_frequency,
    calculate_yearly_frequency,
    get_most_launched_rocket,
    get_busiest_launch_site,
    get_launch_success_trend,
    generate_launch_summary
)


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
        ),
        Launch(
            id="5",
            name="Test Launch 5",
            date_utc=datetime(2021, 2, 1),
            date_unix=1612137600,
            success=True,
            rocket_id="falcon9",
            launchpad_id="ksc",
            flight_number=5,
            upcoming=False,
            rocket_name="Falcon 9",
            launchpad_name="Kennedy Space Center",
            details="Test launch details"
        ),
    ]


def test_calculate_success_rate_by_rocket(sample_launches):
    """Test calculating success rates by rocket."""
    success_rates = calculate_success_rate_by_rocket(sample_launches)
    
    # Expected: Falcon 9 has 2 successes out of 3 attempts (66.67%)
    # Starship has 1 success out of 1 attempt (100%)
    # Falcon Heavy has no completed launches (upcoming)
    assert len(success_rates) == 2
    assert abs(success_rates["Falcon 9"] - 66.67) < 0.1
    assert success_rates["Starship"] == 100.0
    assert "Falcon Heavy" not in success_rates  # Upcoming launches don't count


def test_count_launches_by_site(sample_launches):
    """Test counting launches by site."""
    site_counts = count_launches_by_site(sample_launches)
    
    assert len(site_counts) == 3
    assert site_counts["Kennedy Space Center"] == 3
    assert site_counts["Vandenberg"] == 1
    assert site_counts["Boca Chica"] == 1


def test_calculate_monthly_frequency(sample_launches):
    """Test calculating monthly launch frequency."""
    monthly_freq = calculate_monthly_frequency(sample_launches)
    
    # We should have January (2), February (2), and March (1)
    assert len(monthly_freq) == 3
    assert monthly_freq["January"] == 2
    assert monthly_freq["February"] == 2
    assert monthly_freq["March"] == 1


def test_calculate_yearly_frequency(sample_launches):
    """Test calculating yearly launch frequency."""
    yearly_freq = calculate_yearly_frequency(sample_launches)
    
    assert len(yearly_freq) == 2
    assert yearly_freq[2020] == 3
    assert yearly_freq[2021] == 2


def test_get_most_launched_rocket(sample_launches):
    """Test getting the most launched rocket."""
    rocket, count = get_most_launched_rocket(sample_launches)
    
    assert rocket == "Falcon 9"
    assert count == 3


def test_get_busiest_launch_site(sample_launches):
    """Test getting the busiest launch site."""
    site, count = get_busiest_launch_site(sample_launches)
    
    assert site == "Kennedy Space Center"
    assert count == 3


def test_get_launch_success_trend(sample_launches):
    """Test getting launch success trend by year."""
    trend = get_launch_success_trend(sample_launches)
    
    assert len(trend) == 2
    # 2020: 1 success out of 2 completed (50%)
    # 2021: 2 successes out of 2 completed (100%)
    assert abs(trend[2020] - 50.0) < 0.1
    assert trend[2021] == 100.0


def test_generate_launch_summary(sample_launches):
    """Test generating a comprehensive launch summary."""
    summary = generate_launch_summary(sample_launches)
    
    assert summary["total_launches"] == 5
    assert summary["upcoming_launches"] == 1
    assert summary["completed_launches"] == 4
    assert summary["successful_launches"] == 3
    assert summary["failed_launches"] == 1
    assert abs(summary["success_rate"] - 75.0) < 0.1
    assert summary["most_used_rocket"] == "Falcon 9"
    assert summary["most_used_rocket_count"] == 3
    assert summary["busiest_launch_site"] == "Kennedy Space Center"
    assert summary["busiest_launch_site_count"] == 3


def test_empty_launch_list():
    """Test statistics with empty launch list."""
    empty_list = []
    
    # All statistics functions should handle empty lists gracefully
    assert calculate_success_rate_by_rocket(empty_list) == {}
    assert count_launches_by_site(empty_list) == {}
    assert calculate_monthly_frequency(empty_list) == {}
    assert calculate_yearly_frequency(empty_list) == {}
    assert get_most_launched_rocket(empty_list) == ("Unknown", 0)
    assert get_busiest_launch_site(empty_list) == ("Unknown", 0)
    assert get_launch_success_trend(empty_list) == {}
    
    # Summary should have default values
    summary = generate_launch_summary(empty_list)
    assert summary["total_launches"] == 0
    assert summary["success_rate"] == 0.0


def test_all_upcoming_launches():
    """Test statistics with only upcoming launches."""
    # Create a list of only upcoming launches
    upcoming_launches = [
        Launch(
            id="1",
            name="Future Launch 1",
            date_utc=datetime(2025, 1, 1),
            date_unix=1735689600,
            success=None,
            rocket_id="falcon9",
            launchpad_id="ksc",
            flight_number=1,
            upcoming=True,
            rocket_name="Falcon 9",
            launchpad_name="Kennedy Space Center",
            details="Future launch"
        ),
        Launch(
            id="2",
            name="Future Launch 2",
            date_utc=datetime(2025, 2, 1),
            date_unix=1738368000,
            success=None,
            rocket_id="starship",
            launchpad_id="boca",
            flight_number=2,
            upcoming=True,
            rocket_name="Starship",
            launchpad_name="Boca Chica",
            details="Future launch"
        )
    ]
    
    # Test statistics
    assert calculate_success_rate_by_rocket(upcoming_launches) == {}
    
    site_counts = count_launches_by_site(upcoming_launches)
    assert site_counts["Kennedy Space Center"] == 1
    assert site_counts["Boca Chica"] == 1
    
    summary = generate_launch_summary(upcoming_launches)
    assert summary["total_launches"] == 2
    assert summary["upcoming_launches"] == 2
    assert summary["completed_launches"] == 0
    assert summary["success_rate"] == 0.0


@pytest.mark.parametrize("success_values,expected_rate", [
    ([True, True, True], 100.0),
    ([True, False, True], 66.67),
    ([False, False, False], 0.0),
    ([True, None, False], 50.0),  # None is upcoming, not counted
])
def test_success_rate_calculation(success_values, expected_rate):
    """Test success rate calculation with different patterns."""
    # Create launches with specified success values
    launches = []
    for i, success in enumerate(success_values):
        upcoming = success is None
        launches.append(
            Launch(
                id=str(i),
                name=f"Test Launch {i}",
                date_utc=datetime(2020, 1, i+1),
                date_unix=1577836800 + i*86400,
                success=success,
                rocket_id="falcon9",
                launchpad_id="ksc",
                flight_number=i+1,
                upcoming=upcoming,
                rocket_name="Falcon 9",
                launchpad_name="Kennedy Space Center",
                details="Test launch"
            )
        )
    
    # Calculate success rate
    success_rates = calculate_success_rate_by_rocket(launches)
    
    # Verify rate is as expected
    if "Falcon 9" in success_rates:
        assert abs(success_rates["Falcon 9"] - expected_rate) < 0.1
    else:
        # If there are no completed launches, the rocket won't be in the results
        assert all(success is None for success in success_values)