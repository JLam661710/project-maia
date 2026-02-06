import asyncio
import json
import logging
import os
import uuid
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import websockets

# Load env from Project_Maia root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ASR_Verifier")

# Import protocol
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from protocol import (
    full_client_request,
    audio_only_client,
    receive_message,
    MsgType,
    MsgTypeFlagBits,
    EventType,
)

app = FastAPI()

# Configuration
VOLC_APP_ID = os.getenv("VOLC_APP_ID")
VOLC_ACCESS_TOKEN = os.getenv("VOLC_ACCESS_TOKEN")
VOLC_ASR_RESOURCE_ID = os.getenv("VOLC_ASR_RESOURCE_ID", "volc.seedasr.sauc.duration")
VOLC_ASR_ENDPOINT = os.getenv("VOLC_ASR_ENDPOINT", "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel")

logger.info(f"Loaded Config: APP_ID={VOLC_APP_ID}, RESOURCE_ID={VOLC_ASR_RESOURCE_ID}")

@app.get("/")
async def get():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "r") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(client_ws: WebSocket):
    await client_ws.accept()
    logger.info("Client connected")

    # Connect to Volc Engine
    headers = {
        "X-Api-App-Key": VOLC_APP_ID,
        "X-Api-Access-Key": VOLC_ACCESS_TOKEN,
        "X-Api-Resource-Id": VOLC_ASR_RESOURCE_ID,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
    
    try:
        async with websockets.connect(VOLC_ASR_ENDPOINT, additional_headers=headers) as volc_ws:
            logger.info("Connected to Volc Engine ASR")

            # 1. Send FullClientRequest (Init)
            req_payload = {
                "user": {"uid": "maia_verifier"},
                "audio": {
                    "format": "pcm",
                    "rate": 16000,
                    "bits": 16,
                    "channel": 1,
                },
                "request": {
                    "model_name": "bigmodel",
                    "enable_itn": True,
                }
            }
            await full_client_request(volc_ws, json.dumps(req_payload).encode("utf-8"))

            # 2. Task Loop
            async def forward_audio():
                try:
                    while True:
                        data = await client_ws.receive_bytes()
                        if len(data) == 0:  # Special signal or just keepalive
                            continue
                        
                        # Check for specific "END" signal if sent as bytes? 
                        # Or maybe client sends text "STOP"?
                        # Actually websocket.receive_bytes() will raise if text is sent but we expect bytes.
                        # Let's handle mixed types if possible or assume binary = audio.
                        
                        await audio_only_client(volc_ws, data, MsgTypeFlagBits.NoSeq)
                except Exception as e:
                    logger.info(f"Audio forwarding stopped: {e}")

            async def receive_results():
                try:
                    while True:
                        msg = await receive_message(volc_ws)
                        if msg.type == MsgType.FullServerResponse:
                            # Parse payload
                            try:
                                resp_json = json.loads(msg.payload)
                                await client_ws.send_json(resp_json)
                                
                                # Check if it's the end
                                # sequence < 0 usually means end in some protocols, 
                                # but here we look at the JSON content or message flags if needed.
                                # But for ASR, we just stream until client stops.
                            except Exception as e:
                                logger.error(f"Failed to parse response: {e}")
                except Exception as e:
                    logger.error(f"Result receiving stopped: {e}")

            # Start tasks
            # We need to handle "STOP" signal from client.
            # Simplified: Client sends binary audio. Client closes connection or sends specific frame to stop.
            # Better: Client sends text "STOP" to indicate end of speech.
            
            # Re-implementing client loop to handle mixed text/binary
            forward_task = None
            receive_task = asyncio.create_task(receive_results())

            try:
                while True:
                    message = await client_ws.receive()
                    if "bytes" in message:
                        data = message["bytes"]
                        if data:
                            await audio_only_client(volc_ws, data, MsgTypeFlagBits.NoSeq)
                    elif "text" in message:
                        text = message["text"]
                        if text == "STOP":
                            logger.info("Received STOP signal from client")
                            # Send last packet
                            await audio_only_client(volc_ws, b"", MsgTypeFlagBits.LastNoSeq)
                            break
            except WebSocketDisconnect:
                logger.info("Client disconnected")
            
            # Wait a bit for final results
            await asyncio.sleep(1) 
            receive_task.cancel()
            
    except Exception as e:
        logger.error(f"Volc Error: {e}")
        await client_ws.close()

