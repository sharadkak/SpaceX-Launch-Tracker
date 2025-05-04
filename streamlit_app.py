"""
SpaceX Launch Tracker Dashboard

A Streamlit-based dashboard for the SpaceX Launch Tracker application.
This provides an interactive web interface to explore SpaceX launch data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
from typing import List

from spacex.api_client import SpaceXAPIClient
from spacex.models import DataRepository, Launch
from spacex.filters import filter_launches
from spacex.statistics import (
    calculate_success_rate_by_rocket,
    count_launches_by_site,
    calculate_monthly_frequency,
    calculate_yearly_frequency,
    generate_launch_summary
)


class SpaceXDashboard:
    """Streamlit dashboard for SpaceX Launch Tracker."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.api_client = SpaceXAPIClient(None)
        self.data_repo = DataRepository()
        
        # Use session state to store data
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        
        if 'filtered_launches' not in st.session_state:
            st.session_state.filtered_launches = []
        
        if 'data_repo' in st.session_state and st.session_state.data_loaded:
            self.data_repo = st.session_state.data_repo
            
    def load_data(self, force_refresh: bool = False) -> None:
        """
        Load data from the SpaceX API.
        
        Args:
            force_refresh: Whether to force a refresh from the API
        """
        # Show loading spinner
        with st.spinner("Loading data from SpaceX API..."):
            # Clear cache if force refresh
            if force_refresh:
                self.api_client.clear_cache()
            
            # Load rockets first
            try:
                rockets_data = self.api_client.get_all_rockets()
                self.data_repo.load_rockets(rockets_data)
                st.session_state.rockets_count = len(rockets_data)
            except Exception as e:
                st.error(f"Failed to load rockets: {str(e)}")
                return  # Exit early if we can't load rockets
                
            # Load launchpads second
            try:
                launchpads_data = self.api_client.get_all_launchpads()
                self.data_repo.load_launchpads(launchpads_data)
                st.session_state.launchpads_count = len(launchpads_data)
            except Exception as e:
                st.error(f"Failed to load launchpads: {str(e)}")
                return  # Exit early if we can't load launchpads
                
            # Load launches last (since they reference rockets and launchpads)
            try:
                launches_data = self.api_client.get_all_launches()
                self.data_repo.load_launches(launches_data)
                st.session_state.launches_count = len(launches_data)
            except Exception as e:
                st.error(f"Failed to load launches: {str(e)}")
                return  # Exit early if we can't load launches
            
            st.session_state.data_repo = self.data_repo
            # Set data loaded flag only if we have successfully loaded launches
            if hasattr(self.data_repo, 'launches') and self.data_repo.launches:
                st.session_state.data_loaded = True
                # Set initial filtered launches to all launches
                st.session_state.filtered_launches = list(self.data_repo.launches)
                # Show success message
                st.success(f"Data loaded successfully! {len(self.data_repo.launches)} launches, "
                        f"{len(self.data_repo.rockets)} rockets, "
                        f"{len(self.data_repo.launchpads)} launchpads.")
            else:
                st.error("Failed to load launch data. Please try again.")
                st.session_state.data_loaded = False
                
    def filter_data(self) -> None:
        # First ensure we have data to filter
        if not self.data_repo.launches:
            st.sidebar.warning("No data available to filter. Please load data first.")
            return
        
        # Initialize filtered_launches if not already in session state
        if 'filtered_launches' not in st.session_state:
            # Create a new list (not reference)
            st.session_state.filtered_launches = list(self.data_repo.launches)

        # Get filter values from sidebar
        st.sidebar.header("Filter Launches")
        
        # Create a form for filters
        with st.sidebar.form(key="filter_form"):
            # Date range filter
            st.subheader("Date Range")
            
            # Get min and max dates from launches
            all_dates = [launch.date_utc for launch in self.data_repo.launches]
            min_date = min(all_dates).date()
            max_date = max(all_dates).date()
            
            # Date range selector
            start_date = st.date_input(
                "Start Date",
                min_date,
                min_value=min_date,
                max_value=max_date
            )
            
            end_date = st.date_input(
                "End Date",
                max_date,
                min_value=min_date,
                max_value=max_date
            )
            
            # Rocket filter with multiselect
            st.subheader("Rockets")
            # Get unique rocket names
            unique_rockets = sorted(set(
                launch.rocket_name for launch in self.data_repo.launches 
                if launch.rocket_name
            ))
            # Default is all rockets selected
            selected_rockets = st.multiselect(
                "Select Rockets ",
                options=unique_rockets,
                default=[]
            )
            
            # Success filter
            st.subheader("Launch Outcome")
            success_options = ["All", "Successful", "Failed", "Upcoming"]
            selected_outcome = st.selectbox("Select Outcome", success_options)
            
            # Launch site filter with multiselect
            st.subheader("Launch Sites")
            # Get unique launch site names
            unique_sites = sorted(set(
                launch.launchpad_name for launch in self.data_repo.launches 
                if launch.launchpad_name
            ))
            # Default is all sites selected
            selected_sites = st.multiselect(
                "Select Launch Sites",
                options=unique_sites,
                default=[]
            )
            
            # Submit button within the form
            filter_submitted = st.form_submit_button(label="Apply Filters")
            
            if filter_submitted:
                # Convert dates to datetime
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                
                # Start with a fresh copy of all launches
                filtered = list(self.data_repo.launches)
                
                # Apply date filter
                filtered = filter_launches(
                    filtered,
                    start_date=start_datetime,
                    end_date=end_datetime
                )
                
                # Rocket filter - only apply if rockets are selected
                if selected_rockets:
                    # Keep only launches with rockets in the selected list
                    filtered = [
                        launch for launch in filtered
                        if launch.rocket_name in selected_rockets
                    ]
                
                # Success filter
                if selected_outcome == "Successful":
                    filtered = filter_launches(filtered, success=True)
                elif selected_outcome == "Failed":
                    filtered = filter_launches(filtered, success=False)
                elif selected_outcome == "Upcoming":
                    filtered = [launch for launch in filtered if launch.upcoming]
                
                # Launch site filter - only apply if sites are selected
                if selected_sites:
                    # Keep only launches with sites in the selected list
                    filtered = [
                        launch for launch in filtered
                        if launch.launchpad_name in selected_sites
                    ]
                
                # Update session state with filtered launches
                st.session_state.filtered_launches = list(filtered)
                
                # Show success message
                st.sidebar.success(f"Filters applied! Showing {len(filtered)} launches.")
        
        # Display filter summary outside the form
        st.sidebar.info(f"Currently showing {len(st.session_state.filtered_launches)} launches")
        
    def create_launch_dataframe(self, launches: List[Launch]) -> pd.DataFrame:
        """
        Create a pandas DataFrame from launch data.
        
        Args:
            launches: List of launches
            
        Returns:
            DataFrame containing launch data
        """
        data = []
        for launch in launches:
            data.append({
                "ID": launch.id,
                "Name": launch.name,
                "Date": launch.date_utc,
                "Rocket": launch.rocket_name or "Unknown",
                "Launch Site": launch.launchpad_name or "Unknown",
                "Success": "Yes" if launch.success else "No" if launch.success is False else "Upcoming",
                "Flight Number": launch.flight_number,
                "Details": launch.details or "No details available"
            })
        
        return pd.DataFrame(data)
        
    def display_launches_table(self, launches: List[Launch]) -> None:
        """
        Display a table of launches.
        
        Args:
            launches: List of launches to display
        """
        if not launches:
            st.info("No launches match the selected filters.")
            return
            
        df = self.create_launch_dataframe(launches)
        
        # Sort by date
        df = df.sort_values(by="Date", ascending=False)
        
        # Format the date column
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
        
        # Display the table
        st.dataframe(
            df,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Name": st.column_config.TextColumn("Mission Name"),
                "Date": st.column_config.TextColumn("Launch Date"),
                "Rocket": st.column_config.TextColumn("Rocket"),
                "Launch Site": st.column_config.TextColumn("Launch Site"),
                "Success": st.column_config.TextColumn("Outcome"),
                "Flight Number": st.column_config.NumberColumn("Flight #"),
                "Details": st.column_config.TextColumn("Details", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
        
    def display_success_rate_chart(self, launches: List[Launch], key_suffix: str = "") -> None:
        """
        Display a chart of rocket success rates.
        
        Args:
            launches: List of launches to analyze
            key_suffix: Suffix to make the chart key unique
        """
        if not launches:
            st.info("No data available for success rate chart.")
            return
            
        success_rates = calculate_success_rate_by_rocket(launches)
        
        if not success_rates:
            st.info("No success rate data available.")
            return
            
        # Create DataFrame for the chart
        data = []
        for rocket_name, rate in success_rates.items():
            data.append({
                "Rocket": rocket_name,
                "Success Rate (%)": rate
            })
            
        df = pd.DataFrame(data)
        
        # Sort by success rate
        df = df.sort_values(by="Success Rate (%)", ascending=False)
        
        # Create the chart
        fig = px.bar(
            df, 
            x="Rocket", 
            y="Success Rate (%)",
            title="Success Rate by Rocket",
            labels={"Rocket": "Rocket Type", "Success Rate (%)": "Success Rate (%)"},
            color="Success Rate (%)",
            color_continuous_scale="RdYlGn"
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Rocket Type",
            yaxis_title="Success Rate (%)",
            yaxis_range=[0, 100]
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"success_rate_chart_{key_suffix}")
        
    def display_launches_by_site_chart(self, launches: List[Launch], key_suffix: str = "") -> None:
        """
        Display a chart of launches by site.
        
        Args:
            launches: List of launches to analyze
            key_suffix: Suffix to make the chart key unique
        """
        if not launches:
            st.info("No data available for launches by site chart.")
            return
            
        site_counts = count_launches_by_site(launches)
        
        if not site_counts:
            st.info("No launch site data available.")
            return
            
        # Create DataFrame for the chart
        data = []
        for site_name, count in site_counts.items():
            data.append({
                "Launch Site": site_name,
                "Number of Launches": count
            })
            
        df = pd.DataFrame(data)
        
        # Sort by launch count
        df = df.sort_values(by="Number of Launches", ascending=False)
        
        # Create the chart
        fig = px.bar(
            df, 
            x="Launch Site", 
            y="Number of Launches",
            title="Launches by Site",
            labels={"Launch Site": "Launch Site", "Number of Launches": "Number of Launches"},
            color="Number of Launches",
            color_continuous_scale="Viridis"
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Launch Site",
            yaxis_title="Number of Launches"
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"site_chart_{key_suffix}")
        
    def display_launches_timeline(self, launches: List[Launch], key_suffix: str = "") -> None:
        """
        Display a timeline of launches.
        
        Args:
            launches: List of launches to display
            key_suffix: Suffix to make the chart key unique
        """
        if not launches:
            st.info("No data available for timeline chart.")
            return
            
        # Create DataFrame for the chart
        data = []
        for launch in launches:
            status = "Successful" if launch.success else "Failed" if launch.success is False else "Upcoming"
            data.append({
                "Date": launch.date_utc,
                "Mission": launch.name,
                "Rocket": launch.rocket_name or "Unknown",
                "Status": status
            })
            
        df = pd.DataFrame(data)
        
        # Sort by date
        df = df.sort_values(by="Date")
        
        # Create the chart
        fig = px.scatter(
            df,
            x="Date",
            y="Rocket",
            color="Status",
            hover_name="Mission",
            size_max=10,
            color_discrete_map={
                "Successful": "green",
                "Failed": "red",
                "Upcoming": "blue"
            },
            title="SpaceX Launch Timeline"
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Launch Date",
            yaxis_title="Rocket Type",
            hovermode="closest"
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"timeline_{key_suffix}")
        
    def display_yearly_trend(self, launches: List[Launch], key_suffix: str = "") -> None:
        """
        Display yearly launch trend.
        
        Args:
            launches: List of launches to analyze
            key_suffix: Suffix to make the chart key unique
        """
        if not launches:
            st.info("No data available for yearly trend chart.")
            return
            
        yearly_freq = calculate_yearly_frequency(launches)
        
        if not yearly_freq:
            st.info("No yearly frequency data available.")
            return
            
        # Create DataFrame for the chart
        data = []
        for year, count in yearly_freq.items():
            data.append({
                "Year": year,
                "Number of Launches": count
            })
            
        df = pd.DataFrame(data)
        
        # Create the chart
        fig = px.line(
            df,
            x="Year",
            y="Number of Launches",
            markers=True,
            title="Launches per Year",
            labels={"Year": "Year", "Number of Launches": "Number of Launches"}
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Number of Launches"
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"yearly_trend_{key_suffix}")
        
    def display_monthly_trend(self, launches: List[Launch], key_suffix: str = "") -> None:
        """
        Display monthly launch trend.
        
        Args:
            launches: List of launches to analyze
            key_suffix: Suffix to make the chart key unique
        """
        if not launches:
            st.info("No data available for monthly trend chart.")
            return
            
        monthly_freq = calculate_monthly_frequency(launches)
        
        if not monthly_freq:
            st.info("No monthly frequency data available.")
            return
            
        # Create DataFrame for the chart
        data = []
        for month, count in monthly_freq.items():
            data.append({
                "Month": month,
                "Number of Launches": count
            })
            
        df = pd.DataFrame(data)
        
        # Create the chart
        fig = px.bar(
            df,
            x="Month",
            y="Number of Launches",
            title="Launches per Month",
            labels={"Month": "Month", "Number of Launches": "Number of Launches"},
            color="Number of Launches",
            color_continuous_scale="Blues"
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Launches"
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"monthly_trend_{key_suffix}")
        
    def display_success_metrics(self, launches: List[Launch]) -> None:
        """
        Display success metrics.
        
        Args:
            launches: List of launches to analyze
        """
        if not launches:
            st.info("No data available for success metrics.")
            return
            
        # Generate summary
        summary = generate_launch_summary(launches)
        
        # Create metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Launches",
                summary["total_launches"]
            )
            
        with col2:
            st.metric(
                "Success Rate",
                f"{summary['success_rate']:.1f}%"
            )
            
        with col3:
            st.metric(
                "Upcoming Launches",
                summary["upcoming_launches"]
            )
            
        # Create second row of metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Successful Launches",
                summary["successful_launches"]
            )
            
        with col2:
            st.metric(
                "Failed Launches",
                summary["failed_launches"]
            )
            
        with col3:
            st.metric(
                "Most Used Rocket",
                summary["most_used_rocket"]
            )
            
    def run(self) -> None:
        """Run the dashboard."""
        # Configure page
        st.set_page_config(
            page_title="SpaceX Launch Tracker",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Title and description
        st.title("🚀 SpaceX Launch Tracker")
        st.markdown(
            "Explore SpaceX launch history, track statistics, and monitor mission details."
        )
        
        # Load data button in sidebar
        st.sidebar.title("SpaceX Data")
        if st.sidebar.button("Refresh Data", key="refresh_data"):
            st.session_state.data_loaded = False
            if 'filtered_launches' in st.session_state:
                del st.session_state.filtered_launches

        # Perform periodic cache maintenance
        self.api_client.periodic_cleanup()

        # Load data if not already loaded
        if not st.session_state.data_loaded:
            self.load_data()
        
        # Only show filters if data is loaded
        if st.session_state.data_loaded:
            # Add filters in sidebar
            self.filter_data()
            
            # Main content
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Dashboard", 
                "📋 Launch List", 
                "📈 Statistics",
                "⏱️ Timeline"
            ])
            
            with tab1:
                st.header("Launch Overview")
                
                # Display metrics
                self.display_success_metrics(st.session_state.filtered_launches)
                
                # Display charts with unique keys for tab1
                col1, col2 = st.columns(2)
                
                with col1:
                    self.display_success_rate_chart(st.session_state.filtered_launches, key_suffix="tab1")
                    
                with col2:
                    self.display_launches_by_site_chart(st.session_state.filtered_launches, key_suffix="tab1")
                    
                self.display_yearly_trend(st.session_state.filtered_launches, key_suffix="tab1")
                
            with tab2:
                st.header("Launch List")
                self.display_launches_table(st.session_state.filtered_launches)
                
                # Add export buttons
                if st.session_state.filtered_launches:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Export to CSV", key="export_csv"):
                            df = self.create_launch_dataframe(st.session_state.filtered_launches)
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name="spacex_launches.csv",
                                mime="text/csv",
                                key="download_csv"
                            )
                            
                    with col2:
                        if st.button("Export to JSON", key="export_json"):
                            # Convert launches to dictionaries
                            launch_dicts = []
                            for launch in st.session_state.filtered_launches:
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
                                
                            json_str = json.dumps(launch_dicts, indent=2, default=str)
                            st.download_button(
                                label="Download JSON",
                                data=json_str,
                                file_name="spacex_launches.json",
                                mime="application/json",
                                key="download_json"
                            )
                
            with tab3:
                st.header("Launch Statistics")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Use unique key for this instance of yearly trend chart
                    self.display_yearly_trend(st.session_state.filtered_launches, key_suffix="tab3_col1")
                    
                with col2:
                    self.display_monthly_trend(st.session_state.filtered_launches, key_suffix="tab3")
                    
                col1, col2 = st.columns(2)
                
                with col1:
                    # Use unique key for this instance of success rate chart
                    self.display_success_rate_chart(st.session_state.filtered_launches, key_suffix="tab3")
                    
                with col2:
                    # Use unique key for this instance of site chart
                    self.display_launches_by_site_chart(st.session_state.filtered_launches, key_suffix="tab3")
                    
            with tab4:
                st.header("Launch Timeline")
                self.display_launches_timeline(st.session_state.filtered_launches, key_suffix="tab4")
        else:
            st.info("Please click 'Refresh Data' to load data and view the dashboard.")