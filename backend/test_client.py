# test_client.py

import asyncio
import websockets
import json
import wave

async def send_audio():
    uri = "ws://localhost:8000/ws/chat"  # Adjust the port if your server runs on a different one
    async with websockets.connect(uri) as websocket:
        # Send initial API type
        await websocket.send(json.dumps({"api": "anthropic"}))
        print("Sent initial API type.")

        # Open a WAV file in 16kHz, mono, 16-bit PCM
        with wave.open("test_audio.wav", "rb") as wf:
            data = wf.readframes(4096)
            while data:
                await websocket.send(data)
                print(f"Sent audio chunk of {len(data)} bytes.")
                data = wf.readframes(4096)
                await asyncio.sleep(0.1)  # Simulate streaming

        # Optionally send 'stop' command
        await websocket.send("stop")
        print("Sent stop command.")

        # Receive messages
        try:
            async for message in websocket:
                print(f"Received: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed.")

if __name__ == "__main__":
    asyncio.run(send_audio())
