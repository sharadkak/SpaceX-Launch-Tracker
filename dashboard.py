"""
SpaceX Launch Tracker Dashboard

Entry point for the Streamlit dashboard application.
"""

from streamlit_app import SpaceXDashboard

if __name__ == "__main__":
    dashboard = SpaceXDashboard()
    dashboard.run()