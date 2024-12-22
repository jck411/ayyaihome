import os
import json
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import pytz
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------------------------------------------
# 1) ENV & CLIENT SETUP
# --------------------------------------------------------------------------------

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OPENAI_API_KEY found in environment.")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()


# Allow CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "*"  # Allow all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --------------------------------------------------------------------------------
# 2) THE FUNCTION + SCHEMA
# --------------------------------------------------------------------------------

functions = [
    {
        "name": "get_time",
        "description": "Returns the current date, time, or both in a specified format.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": (
                        "Timezone for the current time (e.g., UTC, EST, PST). "
                        "Defaults to Orlando, FL if not provided."
                    )
                },
                "format": {
                    "type": "string",
                    "description": (
                        "Format for the date/time (e.g., '24-hour', '12-hour', "
                        "'MM/DD/YYYY', 'YYYY-MM-DD')."
                    )
                },
                "date_shift": {
                    "type": "integer",
                    "description": "Days to shift the date (1=tomorrow, -1=yesterday)."
                },
                "response_type": {
                    "type": "string",
                    "description": (
                        "What to return: 'time', 'date', or 'both' (default)."
                    ),
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
    timezone_mappings = {
        "PST": "America/Los_Angeles",
        "CST": "America/Chicago",
        "EST": "America/New_York",
        "MST": "America/Denver"
    }

    # Remap abbreviations
    if timezone.upper() in timezone_mappings:
        timezone = timezone_mappings[timezone.upper()]

    # Validate/fallback timezone
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        timezone = "America/New_York"
        tz = pytz.timezone("America/New_York")

    now = datetime.now(tz) + timedelta(days=date_shift)

    # Time format
    if time_format == "12-hour":
        formatted_time = now.strftime("%I:%M:%S %p")
    elif time_format == "24-hour":
        formatted_time = now.strftime("%H:%M:%S")
    else:
        return f"Invalid time format: {time_format}"

    # Date format
    if date_format == "MM/DD/YYYY":
        formatted_date = now.strftime("%m/%d/%Y")
    elif date_format == "YYYY-MM-DD":
        formatted_date = now.strftime("%Y-%m-%d")
    elif date_format == "DD/MM/YYYY":
        formatted_date = now.strftime("%d/%m/%Y")
    else:
        return f"Invalid date format: {date_format}"

    # Extract location
    if timezone == "America/New_York":
        location_name = "Orlando"
    else:
        if "/" in timezone:
            location_name = timezone.split("/")[-1].replace("_", " ")
        else:
            location_name = timezone

    # Build final string
    if response_type == "time":
        return f"The time in {location_name} is {formatted_time}."
    elif response_type == "date":
        return f"The date in {location_name} is {formatted_date}."
    else:
        return f"The time in {location_name} is {formatted_time} and the date is {formatted_date}."

# --------------------------------------------------------------------------------
# 3) CHUNK PROCESSING & UTILITIES
# --------------------------------------------------------------------------------

def extract_content_from_openai_chunk(chunk: Any) -> Optional[str]:
    try:
        return chunk.choices[0].delta.content
    except (IndexError, AttributeError):
        return None

def extract_function_call_from_chunk(chunk: Any) -> Optional[Dict[str, str]]:
    try:
        function_call = chunk.choices[0].delta.function_call
        if function_call:
            return {
                "name": function_call.get("name", ""),
                "arguments": function_call.get("arguments", "")
            }
    except (IndexError, AttributeError):
        pass
    return None

def compile_delimiter_pattern(delimiters: List[str]) -> Optional[re.Pattern]:
    if not delimiters:
        return None
    sorted_delimiters = sorted(delimiters, key=len, reverse=True)
    escaped_delimiters = map(re.escape, sorted_delimiters)
    return re.compile("|".join(escaped_delimiters))

async def process_chunks(
    chunk_queue: asyncio.Queue,
    phrase_queue: asyncio.Queue,
    delimiter_pattern: Optional[re.Pattern],
    use_segmentation: bool,
    character_max: int
):
    working_string = ""
    chars_processed = 0
    segmentation_active = use_segmentation

    while True:
        chunk = await chunk_queue.get()
        if chunk is None:
            # End of stream
            if working_string.strip():
                await phrase_queue.put(working_string.strip())
            await phrase_queue.put(None)  # signal end
            break

        content_part = extract_content_from_openai_chunk(chunk)
        if content_part:
            working_string += content_part

            if segmentation_active and delimiter_pattern:
                while True:
                    match = delimiter_pattern.search(working_string)
                    if match:
                        end_index = match.end()
                        phrase = working_string[:end_index].strip()
                        if phrase:
                            await phrase_queue.put(phrase)
                            chars_processed += len(phrase)
                        working_string = working_string[end_index:]

                        if chars_processed >= character_max:
                            segmentation_active = False
                            break
                    else:
                        break

# --------------------------------------------------------------------------------
# 4) STREAMING COMPLETION WITH FUNCTION HANDLING
# --------------------------------------------------------------------------------

async def stream_openai_completion(
    messages: List[Dict[str, Union[str, Any]]],
    phrase_queue: asyncio.Queue,
    client: AsyncOpenAI,
    delimiters: Optional[List[str]] = None,
    use_segmentation: bool = False,
    character_max: int = 10_000,
) -> AsyncIterator[str]:

    delimiter_pattern = compile_delimiter_pattern(delimiters or [])
    chunk_queue = asyncio.Queue()
    chunk_processor = asyncio.create_task(
        process_chunks(chunk_queue, phrase_queue, delimiter_pattern, use_segmentation, character_max)
    )

    function_name = None
    function_arguments_accumulator = ""
    function_call_in_progress = False

    try:
        # 1) Make the first streaming request
        response = await client.chat.completions.create(
            model="gpt-4-0613",
            messages=messages,
            functions=functions,
            function_call="auto",
            stream=True
        )

        async for chunk in response:
            choice = chunk.choices[0]
            finish_reason = choice.finish_reason

            fc_data = extract_function_call_from_chunk(chunk)
            if fc_data:
                if fc_data["name"]:
                    function_name = fc_data["name"]
                    function_call_in_progress = True
                function_arguments_accumulator += fc_data["arguments"]

            content_part = extract_content_from_openai_chunk(chunk)
            if content_part:
                yield content_part

            await chunk_queue.put(chunk)

            if finish_reason == "function_call":
                break

            if finish_reason in ("stop", "length"):
                pass

        # 2) If a function call occurred, parse and run it
        if function_call_in_progress and function_name:
            try:
                parsed_args = json.loads(function_arguments_accumulator.strip())
            except (json.JSONDecodeError, TypeError):
                parsed_args = {}

            tz = parsed_args.get("timezone", "America/New_York")
            format_value = parsed_args.get("format", "12-hour")
            date_shift = parsed_args.get("date_shift", 0)
            response_type = parsed_args.get("response_type", "both")

            time_format = "12-hour"
            date_format = "MM/DD/YYYY"
            if format_value in ["12-hour", "24-hour"]:
                time_format = format_value
            elif format_value in ["MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY"]:
                date_format = format_value

            function_result = get_time(
                timezone=tz,
                time_format=time_format,
                date_format=date_format,
                date_shift=date_shift,
                response_type=response_type
            )

            messages.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(function_result)
            })

            messages.append({
                "role": "system",
                "content": "Use the function result above to answer the user's question."
            })

            followup_resp = await client.chat.completions.create(
                model="gpt-4-0613",
                messages=messages,
                functions=functions,
                function_call="none",
                stream=True
            )

            async for followup_chunk in followup_resp:
                choice = followup_chunk.choices[0]
                finish_reason = choice.finish_reason

                followup_content = extract_content_from_openai_chunk(followup_chunk)
                if followup_content:
                    yield followup_content

                await chunk_queue.put(followup_chunk)

                if finish_reason in ("stop", "length"):
                    pass

        await chunk_queue.put(None)
        await chunk_processor

    except Exception as e:
        logger.exception(f"Error during streaming: {e}")
        await chunk_queue.put(None)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {e}"
        )

# --------------------------------------------------------------------------------
# 5) FASTAPI ENDPOINT
# --------------------------------------------------------------------------------

@app.post("/api/openai")
async def chat_endpoint(payload: dict):
    user_messages = payload.get("messages", [])
    if not isinstance(user_messages, list):
        raise HTTPException(400, "Invalid messages format. Must be a list.")

    delimiters = payload.get("delimiters") or []
    use_segmentation = payload.get("use_segmentation", False)
    character_max = payload.get("character_max", 10_000)

    phrase_queue = asyncio.Queue()

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for token in stream_openai_completion(
                messages=user_messages,
                phrase_queue=phrase_queue,
                client=openai_client,
                delimiters=delimiters,
                use_segmentation=use_segmentation,
                character_max=character_max,
            ):
                yield token
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.exception(f"Unhandled error in event_stream: {e}")
            raise HTTPException(500, f"Internal Server Error: {str(e)}")

    return StreamingResponse(event_stream(), media_type="text/plain")

# --------------------------------------------------------------------------------
# 6) MAIN ENTRY POINT (SERVER)
# --------------------------------------------------------------------------------

if __name__ == "__main__":
    # Run the app using Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
