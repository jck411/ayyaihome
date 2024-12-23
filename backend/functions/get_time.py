import pytz
from datetime import datetime, timedelta

# ---------------------
# Schema for get_time
# ---------------------
get_time_schema = {
    "name": "get_time",
    "description": "Returns the current date, time, or both in a specified format.",
    "parameters": {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "The timezone for the current time (e.g., UTC, EST, PST). Defaults to Orlando, FL time if not provided."
            },
            "time_format": {
                "type": "string",
                "description": "The format for the time: 12-hour or 24-hour.",
                "enum": ["24-hour", "12-hour"]
            },
            "date_format": {
                "type": "string",
                "description": "The format for the date: MM/DD/YYYY, YYYY-MM-DD, or DD/MM/YYYY.",
                "enum": ["MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY"]
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
}

# ---------------------
# Function Implementation
# ---------------------
from datetime import datetime, timedelta
import pytz

def get_time(
    timezone="America/New_York",
    time_format="12-hour",
    date_format="MM/DD/YYYY",
    date_shift=0,
    response_type="both"
):
    """
    Returns the current date, time, or both based on the specified
    timezone, format, and date shift. Default behavior for 'America/New_York'
    is to use 'Orlando' as the location name but still recognize the timezone.
    """

    timezone_mappings = {
        "PST": "America/Los_Angeles",
        "CST": "America/Chicago",
        "EST": "America/New_York",
        "MST": "America/Denver"
    }

    # Check shorthand timezone mappings
    if timezone.upper() in timezone_mappings:
        timezone = timezone_mappings[timezone.upper()]

    # Handle invalid timezones
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        timezone = "America/New_York"
        tz = pytz.timezone("America/New_York")

    now = datetime.now(tz) + timedelta(days=date_shift)

    # Format time
    formatted_time = now.strftime("%I:%M:%S %p") if time_format == "12-hour" else now.strftime("%H:%M:%S")

    # Format date
    if date_format == "MM/DD/YYYY":
        formatted_date = now.strftime("%m/%d/%Y")
    elif date_format == "YYYY-MM-DD":
        formatted_date = now.strftime("%Y-%m-%d")
    elif date_format == "DD/MM/YYYY":
        formatted_date = now.strftime("%d/%m/%Y")
    else:
        return f"Invalid date format: {date_format}"

    # Determine location name
    location_name = "Orlando" if timezone == "America/New_York" else timezone.split("/")[-1].replace("_", " ")

    # Handle response types
    if response_type == "time":
        return f"The time in {location_name} is {formatted_time}."
    elif response_type == "date":
        return f"The date in {location_name} is {formatted_date}."
    elif response_type == "timezone":
        return f"The official timezone name is {timezone}."
    else:
        return f"The time in {location_name} is {formatted_time} and the date is {formatted_date}."
