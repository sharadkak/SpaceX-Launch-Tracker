# SpaceX Launch Tracker

A Python application that tracks and analyzes SpaceX launches using their public API. The application helps users understand launch history, track statistics, and monitor mission details.

## Features

- **Data Fetching**: Retrieve data from the SpaceX API v4 with built-in caching for improved performance
- **Launch Tracking**: View and filter SpaceX launches by date range, rocket name, success/failure, and launch site
- **Statistics Generation**: Analyze success rates by rocket, track launch frequency, and monitor launch site usage
- **Interactive Dashboard**: Explore data through a user-friendly Streamlit interface
- **Data Export**: Export filtered launch data to CSV or JSON format
- **Caching System**: Minimize API calls with a local caching mechanism, implemented through json file for every endpoint

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/sharadkak/SpaceX-Launch-Tracker.git
   cd SpaceX-Launch-Tracker
   ```

2. Create a virtual environment and activate it:
   ```
   conda create --name spacex python=3.10
   conda activate spacex
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Project Structure

```
spacex_tracker/
├── spacex/
│   ├── __init__.py
│   ├── api_client.py       # API interaction with caching
│   ├── models.py           # Data models
│   ├── filters.py          # Launch filtering functions
│   └── statistics.py       # Statistics calculation
├── tests/
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_filters.py
│   └── test_statistics.py
├── streamlit_app.py        # Streamlit dashboard implementation
├── dashboard.py            # Dashboard entry point
├── main_app.py             # Command line interface
├── requirements.txt
└── README.md
```

## Usage

### Command Line Interface

The application provides a command-line interface for filtering and displaying launch data:

```
python main.py --show-launches --rocket "Falcon 9" --success yes
```

Available options:

- `--refresh`: Force refresh data from API (clears cache and loads fresh data)
- `--clear-cache`: Clear cache storage without loading data (maintenance operation)
- `--start-date`: Filter launches from this date (YYYY-MM-DD)
- `--end-date`: Filter launches until this date (YYYY-MM-DD)
- `--rocket`: Filter by rocket name
- `--success`: Filter by launch success/failure (yes/no)
- `--site`: Filter by launch site name
- `--show-launches`: Show launch list
- `--show-success-rates`: Show success rates by rocket
- `--show-sites`: Show launch statistics by site
- `--show-time`: Show launch statistics by time period
- `--show-summary`: Show launch summary
- `--export-json`: Export to JSON file
- `--export-csv`: Export to CSV file

### Streamlit Dashboard

The streamlit dashboard is deployed and can be accessed from here <br>
https://spacex-launch-tracker.streamlit.app/

The dashboard provides:

- Interactive filtering with multi-select options
- Visual analytics with charts and graphs
- Tabular data views
- Export capabilities

## API Details

The application uses the SpaceX API v4:
- Base URL: https://api.spacexdata.com/v4
- Key endpoints:
  - `/launches` - Fetch details about all SpaceX launches
  - `/rockets` - Retrieve rocket specifications
  - `/launchpads` - Get launch sites information

## Data Caching

The application implements file-based caching to minimize API calls:

- Cache is stored in a .cache directory
- Default expiry time is 1 hour for most data
- Cache is automatically cleaned up to remove files older than one day
- Cache can be manually cleared using command-line arguments

## Testing

Run the tests using pytest:

```
pytest
```

## License

[MIT License](LICENSE)