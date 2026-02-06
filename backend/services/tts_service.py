import asyncio
import json
import logging
import os
import uuid
from typing import AsyncGenerator, Optional

import websockets
from dotenv import load_dotenv

from backend.utils.volc_protocol import (
    EventType,
    MsgType,
    full_client_request,
    receive_message,
)

load_dotenv()

logger = logging.getLogger(__name__)


class VolcTTSService:
    def __init__(self):
        self.appid = os.getenv("VOLC_APP_ID")
        self.token = os.getenv("VOLC_ACCESS_TOKEN")
        self.resource_id = os.getenv("VOLC_TTS_RESOURCE_ID", "seed-tts-2.0")
        self.voice_type = os.getenv("VOLC_TTS_VOICE_TYPE", "zh_male_m191_uranus_bigtts")
        self.endpoint = os.getenv(
            "VOLC_TTS_ENDPOINT",
            "wss://openspeech.bytedance.com/api/v3/tts/unidirectional/stream",
        )

        if not all([self.appid, self.token]):
            logger.warning(
                "Volcengine TTS credentials missing in environment variables."
            )

    async def stream_tts(
        self, text: str, format: str = "pcm"
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS audio from Volcengine.
        Yields audio chunks (bytes).
        """
        if not text:
            return

        headers = {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }

        try:
            async with websockets.connect(
                self.endpoint, additional_headers=headers, max_size=10 * 1024 * 1024
            ) as websocket:
                logger.info(
                    f"Connected to TTS server: {websocket.response.headers.get('x-tt-logid', 'unknown')}"
                )

                # Prepare request
                request_payload = {
                    "user": {
                        "uid": str(uuid.uuid4()),
                    },
                    "req_params": {
                        "speaker": self.voice_type,
                        "audio_params": {
                            "format": format,
                            "sample_rate": 24000,
                            "enable_timestamp": False,  # Timestamp not needed for now
                        },
                        "text": text,
                        "additions": json.dumps(
                            {
                                "disable_markdown_filter": False,
                            }
                        ),
                    },
                }

                # Send request
                await full_client_request(
                    websocket, json.dumps(request_payload).encode()
                )

                # Receive loop
                while True:
                    msg = await receive_message(websocket)

                    if msg.type == MsgType.FullServerResponse:
                        if msg.event == EventType.SessionFinished:
                            logger.info("TTS Session Finished")
                            break
                        elif msg.event == EventType.TaskFailed:  # Handle failure
                            logger.error(
                                f"TTS Task Failed: {msg.error_code} - {msg.payload}"
                            )
                            break
                    elif msg.type == MsgType.AudioOnlyServer:
                        if msg.payload:
                            yield msg.payload
                    elif msg.type == MsgType.Error:
                        logger.error(f"TTS Error: {msg.error_code} - {msg.payload}")
                        break
                    else:
                        # Ignore other message types for now or log them
                        logger.debug(f"Received other message type: {msg.type}")

        except Exception as e:
            logger.error(f"TTS Streaming Error: {e}")
            raise


# Simple test block
if __name__ == "__main__":

    async def test():
        logging.basicConfig(level=logging.INFO)
        service = VolcTTSService()
        text = "你好，我是 Maia。很高兴见到你。"
        print(f"Synthesizing: {text}")

        with open("test_tts.mp3", "wb") as f:
            async for chunk in service.stream_tts(text):
                f.write(chunk)
                print(".", end="", flush=True)
        print("\nDone. Saved to test_tts.mp3")

    asyncio.run(test())
