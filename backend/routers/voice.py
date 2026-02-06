import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.services.tts_service import VolcTTSService
from backend.services.asr_service import VolcASRService

router = APIRouter()
logger = logging.getLogger(__name__)
tts_service = VolcTTSService()
asr_service = VolcASRService()

@router.websocket("/ws/asr")
async def websocket_asr_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to ASR WebSocket")
    
    # Queue to buffer audio chunks from client
    audio_queue = asyncio.Queue()
    
    async def audio_generator():
        while True:
            chunk = await audio_queue.get()
            if chunk is None: # End signal
                break
            yield chunk

    # Task to receive audio from client
    async def receive_audio_from_client():
        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message:
                    data = message["bytes"]
                    if data:
                        await audio_queue.put(data)
                elif "text" in message:
                    text = message["text"]
                    if text == "STOP":
                        await audio_queue.put(None)
                        break
        except WebSocketDisconnect:
            await audio_queue.put(None)
        except Exception as e:
            logger.error(f"Error receiving audio from client: {e}")
            await audio_queue.put(None)

    # Task to stream ASR results back to client
    async def stream_results():
        try:
            async for result in asr_service.stream_asr(audio_generator()):
                await websocket.send_text(result)
        except Exception as e:
            logger.error(f"Error streaming ASR results: {e}")
            # Try to send error to client
            try:
                await websocket.send_text(json.dumps({"error": str(e)}))
            except:
                pass

    # Run tasks
    receiver = asyncio.create_task(receive_audio_from_client())
    sender = asyncio.create_task(stream_results())
    
    await asyncio.gather(receiver, sender)
    logger.info("ASR Session Ended")


@router.websocket("/ws/tts")
async def websocket_tts_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to TTS WebSocket")
    
    try:
        while True:
            # Expecting text input from client
            # Format: {"text": "Hello world", "format": "mp3"} or just raw text string?
            # Let's support JSON for extensibility
            data = await websocket.receive_text()
            
            try:
                payload = None
                try:
                    payload = websocket.client_state.json_loads(data) # Use internal json loads or standard json
                    import json
                    payload = json.loads(data)
                except:
                    # If not JSON, treat as raw text
                    payload = {"text": data}
                
                text = payload.get("text")
                audio_format = payload.get("format", "pcm")
                
                if not text:
                    continue
                
                logger.info(f"Received TTS request: {text[:20]}...")
                
                # Stream audio back
                async for chunk in tts_service.stream_tts(text, format=audio_format):
                    await websocket.send_bytes(chunk)
                
                # Send a text message to indicate completion? 
                # Or just let the client know by silence?
                # Better to send a control message if possible, but for raw audio stream, 
                # client usually just plays what it gets.
                # We can send a special JSON message to indicate end of sentence if needed.
                # For now, let's just stream audio.
                
                # Optional: Send a "done" message
                await websocket.send_text(json.dumps({"type": "status", "content": "done"}))
                
            except Exception as e:
                logger.error(f"Error processing TTS request: {e}")
                await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
                
    except WebSocketDisconnect:
        logger.info("Client disconnected from TTS WebSocket")
