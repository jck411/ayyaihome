import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------------
# Schema for get_weather
# ---------------------
get_weather_schema = {
    "name": "get_weather",
    "description": "Fetches current and forecast weather information from the OpenWeather One Call 3.0 API. Defaults to Orlando, FL in Fahrenheit.",
    "parameters": {
        "type": "object",
        "properties": {
            "lat": {
                "type": "number",
                "description": "Latitude of the location. Defaults to 28.5383 if not provided."
            },
            "lon": {
                "type": "number",
                "description": "Longitude of the location. Defaults to -81.3792 if not provided."
            },
            "exclude": {
                "type": "string",
                "description": "Comma-delimited list of parts to exclude from API response (e.g., 'minutely,hourly,daily,alerts')."
            },
            "units": {
                "type": "string",
                "description": "Units of measurement: standard or imperial. Defaults to 'imperial'.",
                "enum": ["standard", "imperial"]
            }
        },
        "required": [],
        "additionalProperties": False,
        "strict": True
    }
}

# ---------------------
# Function Implementation
# ---------------------
def get_weather(
    lat: float = None,
    lon: float = None,
    exclude: str = "minutely",  # Default to exclude minutely data
    units: str = "imperial"
):
    """
    Calls the OpenWeather One Call 3.0 API to get current weather 
    and forecast data for a given location. Defaults to Orlando, FL 
    (lat=28.5383, lon=-81.3792) with Fahrenheit units (imperial).
    Excludes minutely data by default.
    """

    # Retrieve API key from environment variable
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    if not OPENWEATHER_API_KEY:
        raise ValueError("Missing OpenWeather API key. Ensure it is set in the .env file.")

    # Default to Orlando if no lat/lon provided
    if lat is None:
        lat = 28.5383
    if lon is None:
        lon = -81.3792

    # Validate inputs (optional improvement)
    VALID_EXCLUDES = {"current", "minutely", "hourly", "daily", "alerts"}
    VALID_UNITS = {"standard", "imperial", "metric"}

    if exclude:
        invalid_excludes = [part for part in exclude.split(",") if part.strip() not in VALID_EXCLUDES]
        if invalid_excludes:
            raise ValueError(f"Invalid exclude parts: {', '.join(invalid_excludes)}")

    if units not in VALID_UNITS:
        raise ValueError(f"Invalid units: {units}. Must be one of {', '.join(VALID_UNITS)}.")

    # Prepare the API request
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "exclude": exclude,
        "units": units,
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return f"An error occurred while calling OpenWeather: {e}"

    return data
