# /home/jack/ayyaihome/backend/functions/function_schemas.py

import pytz
from datetime import datetime, timedelta
import json

# Example function definitions
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
                    "description": "The format for the date or time (e.g., 24-hour, 12-hour, MM/DD/YYYY, YYYY-MM-DD)."
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
            "required": []
        }
    }
]

def get_time(
    timezone="America/New_York",
    time_format="12-hour",
    date_format="MM/DD/YYYY",
    date_shift=0,
    response_type="both"
):
    # Map common abbreviations
    timezone_mappings = {
        "PST": "America/Los_Angeles",
        "CST": "America/Chicago",
        "EST": "America/New_York",
        "MST": "America/Denver"
    }

    # Handle common timezone abbreviations
    if timezone.upper() in timezone_mappings:
        timezone = timezone_mappings[timezone.upper()]

    # Attempt to use the provided timezone, fallback to Orlando if invalid
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        timezone = "America/New_York"
        tz = pytz.timezone("America/New_York")

    now = datetime.now(tz) + timedelta(days=date_shift)

    # Determine time format
    if time_format == "12-hour":
        formatted_time = now.strftime("%I:%M:%S %p")
    else:  # "24-hour"
        formatted_time = now.strftime("%H:%M:%S")

    # Determine date format
    if date_format == "MM/DD/YYYY":
        formatted_date = now.strftime("%m/%d/%Y")
    elif date_format == "YYYY-MM-DD":
        formatted_date = now.strftime("%Y-%m-%d")
    elif date_format == "DD/MM/YYYY":
        formatted_date = now.strftime("%d/%m/%Y")
    else:
        return f"Invalid date format: {date_format}"

    # Handle location name
    if timezone == "America/New_York":
        location_name = "Orlando"
    else:
        # e.g. "Europe/Amsterdam" -> "Amsterdam"
        if "/" in timezone:
            location_name = timezone.split("/")[-1].replace("_", " ")
        else:
            location_name = timezone

    # Format response
    if response_type == "time":
        return f"The time in {location_name} is {formatted_time}."
    elif response_type == "date":
        return f"The date in {location_name} is {formatted_date}."
    else:  # response_type == "both"
        return f"The time in {location_name} is {formatted_time} and the date is {formatted_date}."
