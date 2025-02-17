import os
from pathlib import Path
from typing import Dict, Optional, Union
from dotenv import load_dotenv
import requests
import json

class DataFetcher:
    """
    A class to fetch and manage football data from football-data.org API.
    """
    def __init__(self, current_season: int, league: str):
        """
        Initialize the DataFetcher with season and league information.
        
        Args:
            current_season (int): The season year to fetch data for
            league (str): League identifier (e.g., 'PD' for La Liga)
        """
        load_dotenv(override=True)
        self.current_season = str(current_season)
        self.league = league
        self.base_url = "https://api.football-data.org/v4/competitions/{league}/{endpoint}/?season={current_season}"
        self.headers = {"X-Auth-Token": os.getenv("X_AUTH_TOKEN")}
        self.data_dir = Path("local_data")
        self.data_dir.mkdir(exist_ok=True)

    def get_data(self, endpoint: str) -> Optional[Dict]:
        """
        Fetch data from the API for a given endpoint.
        
        Args:
            endpoint (str): API endpoint (e.g., 'standings', 'matches')
            
        Returns:
            Optional[Dict]: JSON response data or None if request fails
        """
        url = self.base_url.format(
            endpoint=endpoint,
            league=self.league,
            current_season=self.current_season
        )
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data: {str(e)}")
            print(f"Response: {response.text if 'response' in locals() else 'No response'}")
            return None

    def load_data(self, endpoint: str) -> Optional[Dict]:
        """
        Load data from local JSON file.
        
        Args:
            endpoint (str): Data type to load (e.g., 'standings', 'matches')
            
        Returns:
            Optional[Dict]: Loaded JSON data or None if file doesn't exist
        """
        file_path = self.data_dir / f"{self.league}_{endpoint}_{self.current_season}.json"
        try:
            with open(file_path) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"No local data found for {endpoint} in season {self.current_season}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {file_path}")
            return None

    def save_data(self, endpoint: str, data: Dict) -> bool:
        """
        Save data to local JSON file.
        
        Args:
            endpoint (str): Data type to save
            data (Dict): Data to save
            
        Returns:
            bool: True if save successful, False otherwise
        """
        file_path = self.data_dir / f"{self.league}_{endpoint}_{self.current_season}.json"
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except (IOError, TypeError) as e:
            print(f"Error saving data: {str(e)}")
            return False

