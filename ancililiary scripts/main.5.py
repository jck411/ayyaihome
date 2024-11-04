import asyncio
import os
import uuid
import re
import logging
import time

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Type, AsyncIterator

from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

import pyaudio
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from openai import AsyncOpenAI

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Abstract Base Classes
class AIService(ABC):
    @abstractmethod
    async def stream_completion(
        self, 
        messages: List[dict], 
        phrase_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ) -> AsyncIterator[str]:
        """Streams AI completion."""
        pass

class TTSService(ABC):
    @abstractmethod
    async def process(
        self, 
        phrase_queue: asyncio.Queue, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ):
        """Processes text to speech."""
        pass

class AudioPlayerBase(ABC):
    @abstractmethod
    async def play(
        self, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str, 
        start_time: float
    ):
        """Plays audio."""
        pass

    @abstractmethod
    def terminate(self):
        """Terminates the audio player."""
        pass

# Configuration Dataclasses
@dataclass
class AIServiceConfig:
    SERVICE: str = "openai"  # Options: 'openai', 'anthropic', etc.
    DEFAULT_RESPONSE_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 1.0
    TOP_P: float = 1.0
    FREQUENCY_PENALTY: float = 0.0
    PRESENCE_PENALTY: float = 0.0
    MAX_TOKENS: int = 1000
    STOP: Optional[List[str]] = None
    LOGIT_BIAS: Optional[Dict[str, Any]] = None
    SYSTEM_PROMPT: Dict[str, str] = field(default_factory=lambda: {
        "role": "system",
        "content": "You are a helpful but witty and dry assistant"
    })

@dataclass
class TTSServiceConfig:
    SERVICE: str = "openai"  # Options: 'openai', 'azure', etc.
    DEFAULT_TTS_MODEL: str = "tts-1"
    DEFAULT_VOICE: str = "alloy"  # other options: echo, fable, onyx, nova, shimmer
    RESPONSE_FORMAT: str = "pcm"  # options: "mp3", "opus", "aac", "flac"

@dataclass
class ResponseFormatConfig:
    SUPPORTED_FORMATS: List[str] = field(default_factory=lambda: ["pcm", "mp3", "opus", "aac", "flac"])

@dataclass
class Config:
    # General Configurations
    MINIMUM_PHRASE_LENGTH: int = 50
    TTS_CHUNK_SIZE: int = 1024
    AUDIO_FORMAT: int = pyaudio.paInt16
    CHANNELS: int = 1
    RATE: int = 24000
    TTS_SPEED: float = 1.0
    DELIMITERS: List[str] = field(default_factory=lambda: [".", "?", "!"])

    # Service Selection
    AI_SERVICE: str = "openai"        # Options: 'openai', 'anthropic', etc.
    TTS_SERVICE: str = "openai"       # Options: 'openai', 'azure', etc.
    AUDIO_PLAYER: str = "pyaudio"     # Options: 'pyaudio', 'sounddevice', etc.

    # Service-Specific Configurations
    ai_service: AIServiceConfig = field(default_factory=AIServiceConfig)
    tts_service: TTSServiceConfig = field(default_factory=TTSServiceConfig)
    response_format: ResponseFormatConfig = field(default_factory=ResponseFormatConfig)

    # Dynamically create the regex pattern based on DELIMITERS
    DELIMITER_REGEX: str = field(init=False)
    DELIMITER_PATTERN: re.Pattern = field(init=False)

    def __post_init__(self):
        escaped_delimiters = ''.join(re.escape(d) for d in self.DELIMITERS)
        self.DELIMITER_REGEX = f"[{escaped_delimiters}]"
        self.DELIMITER_PATTERN = re.compile(self.DELIMITER_REGEX)

    def get_ai_service_class(self) -> Type[AIService]:
        service_map = {
            'openai': OpenAIService,
            'anthropic': AnthropicService,
            # Add other AI services here
        }
        service_class = service_map.get(self.AI_SERVICE.lower())
        if not service_class:
            raise ValueError(f"Unsupported AI_SERVICE: {self.AI_SERVICE}")
        return service_class

    def get_tts_service_class(self) -> Type[TTSService]:
        service_map = {
            'openai': OpenAITTSService,
            'azure': AzureTTSService,
            # Add other TTS services here
        }
        service_class = service_map.get(self.TTS_SERVICE.lower())
        if not service_class:
            raise ValueError(f"Unsupported TTS_SERVICE: {self.TTS_SERVICE}")
        return service_class

    def get_audio_player_class(self) -> Type[AudioPlayerBase]:
        service_map = {
            'pyaudio': PyAudioPlayer,
            'sounddevice': SoundDevicePlayer,
            # Add other audio players here
        }
        service_class = service_map.get(self.AUDIO_PLAYER.lower())
        if not service_class:
            raise ValueError(f"Unsupported AUDIO_PLAYER: {self.AUDIO_PLAYER}")
        return service_class

# Utility Functions
def find_next_phrase_end(text: str, config: Config) -> int:
    """
    Finds the end position of the next phrase based on delimiters using regex.

    Args:
        text (str): The text to search within.
        config (Config): Configuration instance.

    Returns:
        int: The index of the delimiter if found after the minimum phrase length; otherwise, -1.
    """
    match = config.DELIMITER_PATTERN.search(text, pos=config.MINIMUM_PHRASE_LENGTH)
    return match.start() if match else -1

# AI Service Implementations
class OpenAIService(AIService):
    def __init__(self, api_key: str, config: Config):
        self.client = AsyncOpenAI(api_key=api_key)
        self.config = config

    async def stream_completion(
        self, 
        messages: List[dict], 
        phrase_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ) -> AsyncIterator[str]:
        try:
            response = await self.client.chat.completions.create(
                model=self.config.ai_service.DEFAULT_RESPONSE_MODEL,
                messages=messages,
                stream=True,
                temperature=self.config.ai_service.TEMPERATURE,
                top_p=self.config.ai_service.TOP_P,
                frequency_penalty=self.config.ai_service.FREQUENCY_PENALTY,
                presence_penalty=self.config.ai_service.PRESENCE_PENALTY,
                max_tokens=self.config.ai_service.MAX_TOKENS,
                stop=self.config.ai_service.STOP,
                logit_bias=self.config.ai_service.LOGIT_BIAS,
            )

            working_string, in_code_block = "", False
            async for chunk in response:
                if stop_event.is_set():
                    logger.info(f"Stop event set for stream ID: {stream_id}. Terminating stream_completion.")
                    await phrase_queue.put(None)
                    break

                content = getattr(chunk.choices[0].delta, 'content', "") if chunk.choices else ""
                if content:
                    yield content
                    working_string += content

                    while True:
                        if in_code_block:
                            code_block_end = working_string.find("\n```", 3)
                            if code_block_end != -1:
                                working_string = working_string[code_block_end + 3:]
                                await phrase_queue.put("Code presented on screen")
                                in_code_block = False
                            else:
                                break
                        else:
                            code_block_start = working_string.find("```")
                            if code_block_start != -1:
                                phrase, working_string = working_string[:code_block_start], working_string[code_block_start:]
                                if phrase.strip():
                                    await phrase_queue.put(phrase.strip())
                                in_code_block = True
                            else:
                                next_phrase_end = find_next_phrase_end(working_string, self.config)
                                if next_phrase_end == -1:
                                    break
                                phrase, working_string = working_string[:next_phrase_end + 1].strip(), working_string[next_phrase_end + 1:]
                                await phrase_queue.put(phrase)

            if working_string.strip() and not in_code_block:
                logger.info(f"Final working_string for stream ID {stream_id}: {working_string.strip()}")
                await phrase_queue.put(working_string.strip())
            await phrase_queue.put(None)

        except Exception as e:
            logger.error(f"Error in stream_completion (Stream ID: {stream_id}): {e}")
            await phrase_queue.put(None)
            yield f"Error: {e}"

        finally:
            logger.info(f"Stream completion ended for stream ID: {stream_id}")

# Placeholder for AnthropicService
class AnthropicService(AIService):
    def __init__(self, api_key: str, config: Config):
        # Initialize the Anthropic client
        pass

    async def stream_completion(
        self, 
        messages: List[dict], 
        phrase_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ) -> AsyncIterator[str]:
        # Implement the Anthropic streaming completion logic
        pass

# TTS Service Implementations
class OpenAITTSService(TTSService):
    def __init__(self, client: AIService, config: Config):
        self.client = client  # This should be an instance of AIService
        self.config = config

    async def process(
        self, 
        phrase_queue: asyncio.Queue, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ):
        try:
            while not stop_event.is_set():
                phrase = await phrase_queue.get()
                if phrase is None:
                    await audio_queue.put(None)
                    break

                try:
                    if self.config.tts_service.RESPONSE_FORMAT not in self.config.response_format.SUPPORTED_FORMATS:
                        raise ValueError(f"Unsupported response format: {self.config.tts_service.RESPONSE_FORMAT}")

                    async with self.client.client.audio.speech.with_streaming_response.create(
                        model=self.config.tts_service.DEFAULT_TTS_MODEL,
                        voice=self.config.tts_service.DEFAULT_VOICE,
                        input=phrase,
                        speed=self.config.TTS_SPEED,
                        response_format=self.config.tts_service.RESPONSE_FORMAT
                    ) as response:
                        async for audio_chunk in response.iter_bytes(self.config.TTS_CHUNK_SIZE):
                            if stop_event.is_set():
                                break
                            await audio_queue.put(audio_chunk)
                    await audio_queue.put(b'\x00' * 2400)
                except Exception as e:
                    logger.error(f"Error in TTS processing (Stream ID: {stream_id}): {e}")
                    await audio_queue.put(None)
                    break
        finally:
            await audio_queue.put(None)

class AzureTTSService(TTSService):
    def __init__(self, client: AIService, config: Config):
        # Initialize the Azure TTS client
        pass

    async def process(
        self, 
        phrase_queue: asyncio.Queue, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ):
        # Implement the Azure TTS processing logic
        pass

# Audio Player Implementations
class PyAudioPlayer(AudioPlayerBase):
    def __init__(self, config: Config):
        self.pyaudio_instance = pyaudio.PyAudio()
        self.config = config

    async def play(
        self, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str, 
        start_time: float
    ):
        stream = None
        try:
            stream = self.pyaudio_instance.open(
                format=self.config.AUDIO_FORMAT,
                channels=self.config.CHANNELS,
                rate=self.config.RATE,
                output=True,
                frames_per_buffer=2048
            )
            await asyncio.to_thread(stream.write, b'\x00' * 2048)

            first_audio = True  # Flag to check for the first audio chunk

            while not stop_event.is_set():
                audio_data = await audio_queue.get()
                if audio_data is None:
                    break

                # Measure time when the first audio data is processed
                if first_audio:
                    elapsed_time = time.time() - start_time
                    logger.info(f"Time taken for the first audio to be heard: {elapsed_time:.2f} seconds")
                    first_audio = False  # Reset the flag after the first chunk is processed

                await asyncio.to_thread(stream.write, audio_data)
        except Exception as e:
            logger.error(f"Error in audio player (Stream ID: {stream_id}): {e}")
        finally:
            if stream:
                await asyncio.to_thread(stream.stop_stream)
                await asyncio.to_thread(stream.close)

    def terminate(self):
        self.pyaudio_instance.terminate()

class SoundDevicePlayer(AudioPlayerBase):
    def __init__(self, config: Config):
        self.config = config
        # Initialize sounddevice stream or other necessary components

    async def play(
        self, 
        audio_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str, 
        start_time: float
    ):
        try:
            import sounddevice as sd
            from io import BytesIO
            import numpy as np

            # Example setup for sounddevice (adjust parameters as needed)
            stream = sd.OutputStream(
                samplerate=self.config.RATE,
                channels=self.config.CHANNELS,
                dtype='int16'
            )
            stream.start()

            first_audio = True

            while not stop_event.is_set():
                audio_data = await audio_queue.get()
                if audio_data is None:
                    break

                if first_audio:
                    elapsed_time = time.time() - start_time
                    logger.info(f"Time taken for the first audio to be heard: {elapsed_time:.2f} seconds")
                    first_audio = False

                # Convert bytes to numpy array
                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                stream.write(audio_np)
        except Exception as e:
            logger.error(f"Error in sounddevice player (Stream ID: {stream_id}): {e}")
        finally:
            if 'stream' in locals() and stream.active:
                stream.stop()
                stream.close()

    def terminate(self):
        # Terminate sounddevice or other resources if needed
        pass

# Stream Manager
class StreamManager:
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, asyncio.Event | asyncio.Task]] = {}
        self.lock = asyncio.Lock()

    async def add_stream(self, stream_id: str, stop_event: asyncio.Event, task: asyncio.Task):
        async with self.lock:
            self.active_streams[stream_id] = {
                "stop_event": stop_event,
                "task": task
            }

    async def remove_stream(self, stream_id: str):
        async with self.lock:
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
                logger.info(f"Cleaned up stream with ID: {stream_id}")

    async def stop_all(self):
        async with self.lock:
            if not self.active_streams:
                logger.info("No active streams to stop.")
                return

            logger.info("Stopping all active streams...")
            for stream_id, stream_info in self.active_streams.items():
                logger.info(f"Setting stop_event for stream ID: {stream_id}")
                stream_info["stop_event"].set()
                stream_info["task"].cancel()

            await asyncio.sleep(0.1)
            self.active_streams.clear()
            logger.info("All active streams have been stopped.")

    async def stop_stream(self, stream_id: str):
        async with self.lock:
            if stream_id not in self.active_streams:
                logger.warning(f"Attempted to stop non-existent stream ID: {stream_id}")
                return False

            logger.info(f"Stopping specific stream with ID: {stream_id}")
            stream_info = self.active_streams[stream_id]
            stream_info["stop_event"].set()
            stream_info["task"].cancel()
            await asyncio.sleep(0.1)
            if stream_id in self.active_streams:
                await self.remove_stream(stream_id)
            return True

# Application Lifecycle Manager
class AppLifecycle:
    def __init__(self, stream_manager: StreamManager, audio_player: AudioPlayerBase):
        self.stream_manager = stream_manager
        self.audio_player = audio_player

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        logger.info("Starting up application...")
        try:
            yield
        finally:
            logger.info("Shutting down application...")
            await self.stream_manager.stop_all()
            self.audio_player.terminate()
            logger.info("Shutdown complete.")

# API Routes
class API:
    def __init__(
        self, 
        app: FastAPI, 
        ai_service: AIService, 
        tts_service: TTSService,
        audio_player: AudioPlayerBase, 
        stream_manager: StreamManager, 
        config: Config
    ):
        self.app = app
        self.ai_service = ai_service
        self.tts_service = tts_service
        self.audio_player = audio_player
        self.stream_manager = stream_manager
        self.config = config

        self.setup_routes()

    def setup_routes(self):
        @self.app.post("/api/openai")
        async def openai_stream(request: Request):
            logger.info("Received new /api/openai request. Stopping all existing streams...")
            await self.stream_manager.stop_all()

            stream_id = str(uuid.uuid4())
            logger.info(f"Starting new stream with ID: {stream_id}")

            stop_event = asyncio.Event()

            try:
                data = await request.json()
            except Exception as e:
                logger.error(f"Invalid JSON payload: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON payload")

            messages = [{"role": msg["sender"], "content": msg["text"]} for msg in data.get("messages", [])]
            messages.insert(0, self.config.ai_service.SYSTEM_PROMPT)

            phrase_queue = asyncio.Queue()
            audio_queue = asyncio.Queue()

            start_time = time.time()  # Record the start time here

            tts_task = asyncio.create_task(
                self.tts_service.process(phrase_queue, audio_queue, stop_event, stream_id)
            )
            audio_task = asyncio.create_task(
                self.audio_player.play(audio_queue, stop_event, stream_id, start_time)  # Pass the start_time to AudioPlayer
            )
            process_task = asyncio.create_task(
                self.process_streams(tts_task, audio_task, stream_id)
            )

            await self.stream_manager.add_stream(stream_id, stop_event, process_task)

            return StreamingResponse(
                self.stream_completion_generator(messages, phrase_queue, stop_event, stream_id),
                media_type="text/plain"
            )

        @self.app.post("/api/stop_all")
        async def stop_all_streams_endpoint():
            await self.stream_manager.stop_all()
            return {"status": "All active streams have been stopped."}

        @self.app.post("/api/stop/{stream_id}")
        async def stop_specific_stream(stream_id: str):
            success = await self.stream_manager.stop_stream(stream_id)
            if not success:
                raise HTTPException(status_code=404, detail="Stream ID not found.")
            return {"status": f"Stream {stream_id} has been stopped."}

    async def process_streams(
        self, 
        tts_task: asyncio.Task, 
        audio_task: asyncio.Task, 
        stream_id: str
    ):
        try:
            await asyncio.gather(tts_task, audio_task)
        except asyncio.CancelledError:
            logger.info(f"Process streams tasks cancelled (Stream ID: {stream_id})")
        except Exception as e:
            logger.error(f"Error in process_streams (Stream ID: {stream_id}): {e}")
        finally:
            await self.stream_manager.remove_stream(stream_id)

    async def stream_completion_generator(
        self, 
        messages: List[dict], 
        phrase_queue: asyncio.Queue, 
        stop_event: asyncio.Event, 
        stream_id: str
    ):
        try:
            async for content in self.ai_service.stream_completion(messages, phrase_queue, stop_event, stream_id):
                yield content
        except Exception as e:
            logger.error(f"Error in stream_completion_generator (Stream ID: {stream_id}): {e}")
            yield f"Error: {e}"
        finally:
            logger.info(f"Stream completion generator ended for stream ID: {stream_id}")

# Main Application Setup
def create_app() -> FastAPI:
    config = Config()
    app = FastAPI()

    # Initialize services based on configuration
    # AI Service
    ai_service_class = config.get_ai_service_class()
    if config.AI_SERVICE.lower() == 'openai':
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY is not set in environment variables.")
            raise EnvironmentError("OPENAI_API_KEY is required.")
        ai_service = ai_service_class(api_key=openai_api_key, config=config)
    elif config.AI_SERVICE.lower() == 'anthropic':
        # Initialize AnthropicService
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY is not set in environment variables.")
            raise EnvironmentError("ANTHROPIC_API_KEY is required.")
        ai_service = ai_service_class(api_key=anthropic_api_key, config=config)
    else:
        raise ValueError(f"Unsupported AI_SERVICE: {config.AI_SERVICE}")

    # TTS Service
    tts_service_class = config.get_tts_service_class()
    if config.TTS_SERVICE.lower() == 'openai':
        tts_service = tts_service_class(client=ai_service, config=config)
    elif config.TTS_SERVICE.lower() == 'azure':
        # Initialize AzureTTSService
        azure_tts_api_key = os.getenv("AZURE_TTS_API_KEY")
        azure_tts_region = os.getenv("AZURE_TTS_REGION")
        if not azure_tts_api_key or not azure_tts_region:
            logger.error("AZURE_TTS_API_KEY and AZURE_TTS_REGION must be set in environment variables.")
            raise EnvironmentError("AZURE_TTS_API_KEY and AZURE_TTS_REGION are required for Azure TTS.")
        tts_service = tts_service_class(client=ai_service, config=config)
    else:
        raise ValueError(f"Unsupported TTS_SERVICE: {config.TTS_SERVICE}")

    # Audio Player
    audio_player_class = config.get_audio_player_class()
    if config.AUDIO_PLAYER.lower() == 'pyaudio':
        audio_player = audio_player_class(config=config)
    elif config.AUDIO_PLAYER.lower() == 'sounddevice':
        audio_player = audio_player_class(config=config)
    else:
        raise ValueError(f"Unsupported AUDIO_PLAYER: {config.AUDIO_PLAYER}")

    # Initialize Stream Manager
    stream_manager = StreamManager()

    # Initialize Application Lifecycle Manager
    lifecycle = AppLifecycle(stream_manager=stream_manager, audio_player=audio_player)

    # Initialize API Routes
    api = API(app, ai_service, tts_service, audio_player, stream_manager, config)

    # Add Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Update this as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup lifespan
    app.router.lifespan = lifecycle.lifespan

    return app

# Initialize the app
app = create_app()

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)