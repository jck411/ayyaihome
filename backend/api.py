# api.py

import uuid
import time
import asyncio
import logging
from typing import List

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse

from abc_classes import AIService, TTSService, AudioPlayerBase
from stream_manager import StreamManager
from config import Config

logger = logging.getLogger(__name__)

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
