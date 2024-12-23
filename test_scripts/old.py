# /home/jack/ayyaihome/backend/functions/function_schemas.py

import pytz
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv  # <-- Load environment variables
import requests  # <-- For making our API call to OpenWeather

# Load .env file
load_dotenv()

# ------------------
# Existing get_time
# ------------------
def get_time(
    timezone="America/New_York",
    time_format="12-hour",
    date_format="MM/DD/YYYY",
    date_shift=0,
    response_type="both"
):
    timezone_mappings = {
        "PST": "America/Los_Angeles",
        "CST": "America/Chicago",
        "EST": "America/New_York",
        "MST": "America/Denver"
    }

    if timezone.upper() in timezone_mappings:
        timezone = timezone_mappings[timezone.upper()]

    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        timezone = "America/New_York"
        tz = pytz.timezone("America/New_York")

    now = datetime.now(tz) + timedelta(days=date_shift)

    if time_format == "12-hour":
        formatted_time = now.strftime("%I:%M:%S %p")
    else:
        formatted_time = now.strftime("%H:%M:%S")

    if date_format == "MM/DD/YYYY":
        formatted_date = now.strftime("%m/%d/%Y")
    elif date_format == "YYYY-MM-DD":
        formatted_date = now.strftime("%Y-%m-%d")
    elif date_format == "DD/MM/YYYY":
        formatted_date = now.strftime("%d/%m/%Y")
    else:
        return f"Invalid date format: {date_format}"

    if timezone == "America/New_York":
        location_name = "Orlando"
    else:
        if "/" in timezone:
            location_name = timezone.split("/")[-1].replace("_", " ")
        else:
            location_name = timezone

    if response_type == "time":
        return f"The time in {location_name} is {formatted_time}."
    elif response_type == "date":
        return f"The date in {location_name} is {formatted_date}."
    else:
        return f"The time in {location_name} is {formatted_time} and the date is {formatted_date}."

# ----------------------
# New get_weather
# ----------------------
def get_weather(
    lat: float = None,
    lon: float = None,
    exclude: str = "",
    units: str = "imperial"
):
    """
    Calls the OpenWeather One Call 3.0 API to get current weather 
    and forecast data for a given location. Defaults to Orlando, FL 
    (lat=28.5383, lon=-81.3792) with Fahrenheit units (imperial).
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

    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "exclude": "minutely",
        "units": units,  # default "imperial" for Fahrenheit
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return f"An error occurred while calling OpenWeather: {e}"

    # Return the raw JSON response for now. You can process this as needed.
    return data

# -------------------------------
# Updated function schema list
# -------------------------------
functions = [
    {
        "name": "get_time",
        "description": "Returns the current date, time, or both in a specified format.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "The timezone for the current time (e.g., UTC, EST, PST). Defaults to Orlando, FL time if not provided."
                },
                "format": {
                    "type": "string",
                    "description": "The format for the date or time (e.g., 24-hour, 12-hour, MM/DD/YYYY, YYYY-MM-DD).",
                    "enum": ["24-hour", "12-hour", "MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY"]
                },
                "date_shift": {
                    "type": "integer",
                    "description": "Number of days to shift the date (e.g., 1 for tomorrow, -1 for yesterday). Defaults to 0 (today)."
                },
                "response_type": {
                    "type": "string",
                    "description": "Specifies what to return: 'time', 'date', or 'both'. Defaults to 'both'.",
                    "enum": ["time", "date", "both"]
                }
            },
            "required": ["response_type"],
            "additionalProperties": False,
            "strict": True
        }
    },
    {
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
]
