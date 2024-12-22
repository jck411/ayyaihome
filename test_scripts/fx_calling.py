import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
from openai import AsyncOpenAI
import asyncio

# Load environment variables (containing OPENAI_API_KEY)
load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the function schema
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
    else:
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

    # Determine the location name from the timezone
    if timezone == "America/New_York":
        location_name = "Orlando"
    else:
        # Extract the part after the slash, replace underscores with spaces
        # e.g., "Europe/Amsterdam" -> "Amsterdam"
        if "/" in timezone:
            location_name = timezone.split("/")[-1].replace("_", " ")
        else:
            # If no slash, just use the timezone as-is
            location_name = timezone

    # Handle response type
    if response_type == "time":
        return f"The time in {location_name} is {formatted_time}."
    elif response_type == "date":
        return f"The date in {location_name} is {formatted_date}."
    else:  # response_type == "both"
        return f"The time in {location_name} is {formatted_time} and the date is {formatted_date}."

async def main():
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    print("Type your message below. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            print("Exiting. Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        # Make a streaming request for the initial assistant response
        # We still allow function calls, but we won't print them as they stream.
        response_stream = await client.chat.completions.create(
            model="gpt-4-0613",
            messages=messages,
            functions=functions,
            function_call="auto",
            stream=True
        )

        full_reply = ""
        function_arguments_accumulator = ""
        function_name = None
        function_call_finished = False

        print("\nAssistant:", end=" ")

        # Stream only the text content of the assistant response
        # (do not stream the function call chunks)
        async for part in response_stream:
            delta = part.choices[0].delta

            # If there's actual content, print it
            if hasattr(delta, "content") and delta.content:
                print(delta.content, end="", flush=True)
                full_reply += delta.content

            # Check if there's a function_call piece (we do not print it)
            if hasattr(delta, "function_call") and delta.function_call is not None:
                # Store the function name if present
                if delta.function_call.name:
                    function_name = delta.function_call.name

                # Accumulate arguments if provided
                if delta.function_call.arguments:
                    function_arguments_accumulator += delta.function_call.arguments

            # If the finish_reason indicates a function call is complete
            if part.choices[0].finish_reason == "function_call":
                function_call_finished = True
                break

        print()  # newline after assistant response
        messages.append({"role": "assistant", "content": full_reply})

        # If a function call was made, handle it now (without streaming partial calls)
        if function_call_finished:
            # Parse the accumulated function call arguments
            try:
                arguments = json.loads(function_arguments_accumulator.strip())
            except (json.JSONDecodeError, TypeError):
                arguments = {}

            # Extract arguments
            timezone = arguments.get("timezone", "America/New_York")
            format_value = arguments.get("format", "12-hour")
            date_shift = arguments.get("date_shift", 0)
            response_type = arguments.get("response_type", "both")

            # Determine time/date formats
            time_format = "12-hour"
            date_format = "MM/DD/YYYY"

            # If 'format' is time or date, map accordingly
            if format_value in ["12-hour", "24-hour"]:
                time_format = format_value
            elif format_value in ["MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY"]:
                date_format = format_value

            # Call our function
            function_result = get_time(
                timezone=timezone,
                time_format=time_format,
                date_format=date_format,
                date_shift=date_shift,
                response_type=response_type
            )

            # Add the function call result as a new message
            messages.append({
                "role": "function",
                "name": function_name if function_name else "get_time",
                "content": json.dumps(function_result)
            })

            # Add a system message directing the assistant to use the function's result
            messages.append({"role": "system", "content": "Use the function result to answer the user clearly."})

            # Make a follow-up request using the function result (forcing no function calls here)
            follow_up_stream = await client.chat.completions.create(
                model="gpt-4-0613",
                messages=messages,
                functions=functions,
                function_call="none",
                stream=True
            )

            print("\nAssistant:", end=" ")
            full_follow_up_reply = ""
            async for part in follow_up_stream:
                delta = part.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    print(delta.content, end="", flush=True)
                    full_follow_up_reply += delta.content
            print()

            # Append the follow-up response to messages
            messages.append({"role": "assistant", "content": full_follow_up_reply})

# Run the async main loop
asyncio.run(main())
