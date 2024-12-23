# /home/jack/ayyaihome/backend/text_generation/function_dispatcher.py

import json
from .logging_config import logger

# Import your local function definitions as needed
from backend.functions.get_time import get_time
from backend.functions.get_weather import get_weather

async def _call_function_locally(function_name: str, arguments: dict) -> str:
    """
    Dispatches the detected function call to a local Python function by name.
    """
    logger.info(f"Calling local function '{function_name}' with arguments: {arguments}")
    try:
        if function_name == "get_time":
            timezone = arguments.get("timezone", "America/New_York")
            format_value = arguments.get("format", "12-hour")
            date_shift = arguments.get("date_shift", 0)
            response_type = arguments.get("response_type", "both")

            time_format = "12-hour"
            date_format = "MM/DD/YYYY"

            # Validate time/date formats
            if format_value in ["12-hour", "24-hour"]:
                time_format = format_value
            elif format_value in ["MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY"]:
                date_format = format_value

            return get_time(
                timezone=timezone,
                time_format=time_format,
                date_format=date_format,
                date_shift=date_shift,
                response_type=response_type,
            )

        elif function_name == "get_weather":
            # Parse parameters for get_weather
            lat = arguments.get("lat")
            lon = arguments.get("lon")
            exclude = arguments.get("exclude", "minutely")  # Default to exclude minutely data
            units = arguments.get("units", "imperial")  # Default to Fahrenheit

            # Call the get_weather function
            return get_weather(lat=lat, lon=lon, exclude=exclude, units=units)

        # Fallback or unknown function
        logger.warning(f"No suitable function found or function '{function_name}' not implemented.")
        return "No suitable function found or function not implemented."

    except Exception as e:
        logger.error(f"Error while calling function '{function_name}': {e}", exc_info=True)
        return "An error occurred while executing the function."
