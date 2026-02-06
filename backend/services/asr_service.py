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
    MsgTypeFlagBits,
    full_client_request,
    audio_only_client,
    receive_message,
)

load_dotenv()

logger = logging.getLogger(__name__)


class VolcASRService:
    def __init__(self):
        self.appid = os.getenv("VOLC_APP_ID")
        self.token = os.getenv("VOLC_ACCESS_TOKEN")
        self.resource_id = os.getenv("VOLC_ASR_RESOURCE_ID", "volc.seedasr.sauc.duration")
        self.endpoint = os.getenv(
            "VOLC_ASR_ENDPOINT",
            "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async",
        )

        if not all([self.appid, self.token]):
            logger.warning(
                "Volcengine ASR credentials missing in environment variables."
            )

    async def stream_asr(
        self, audio_generator: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[str, None]:
        """
        Stream audio to Volcengine ASR and yield recognized text.
        audio_generator: yields PCM bytes (16k, 16bit, mono)
        """
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
                logger.info("Connected to ASR server")

                # 1. Send Init Request (FullClientRequest)
                req_payload = {
                    "user": {"uid": "maia_user"},
                    "audio": {
                        "format": "pcm",
                        "rate": 16000,
                        "bits": 16,
                        "channel": 1,
                    },
                    "request": {
                        "model_name": "bigmodel",
                        "enable_itn": True,
                        "enable_punc": True,
                        "enable_ddc": True,
                    }
                }
                await full_client_request(websocket, json.dumps(req_payload).encode("utf-8"))

                # 2. Create Tasks for Sending and Receiving
                
                # Task: Send Audio
                async def send_audio():
                    try:
                        async for chunk in audio_generator:
                            if chunk:
                                await audio_only_client(websocket, chunk, MsgTypeFlagBits.NoSeq)
                        # End of stream
                        await audio_only_client(websocket, b"", MsgTypeFlagBits.LastNoSeq)
                        logger.info("Sent all audio data")
                    except Exception as e:
                        logger.error(f"Error sending audio to ASR: {e}")
                        # We don't raise here to let receive_results handle close

                # Task: Receive Results
                async def receive_results():
                    try:
                        while True:
                            msg = await receive_message(websocket)
                            if msg.type == MsgType.FullServerResponse:
                                if msg.payload:
                                    try:
                                        resp = json.loads(msg.payload)
                                        # Yield full response for now, or just text?
                                        # The verification demo showed {"result": {"text": "..."}}
                                        # Let's yield the text if available
                                        if "result" in resp and "text" in resp["result"]:
                                            yield json.dumps(resp) # Send full JSON for frontend to parse (inc. partial)
                                        
                                        # Check for end of session (sequence < 0 or specific flags)
                                        # But usually we rely on "is_last_package" in payload if checking manually
                                        # Or just keep running until connection closes
                                    except Exception as e:
                                        logger.error(f"Failed to parse ASR response: {e}")
                                
                                # Check if sequence indicates end (NegativeSeq)
                                if msg.flag == MsgTypeFlagBits.NegativeSeq or msg.flag == MsgTypeFlagBits.LastNoSeq:
                                    break
                            elif msg.type == MsgType.Error:
                                logger.error(f"ASR Error: {msg.error_code} - {msg.payload}")
                                break
                    except Exception as e:
                        logger.error(f"Error receiving ASR results: {e}")
                        raise

                send_task = asyncio.create_task(send_audio())
                
                try:
                    async for result in receive_results():
                        yield result
                finally:
                    # Ensure send task is cancelled if receive stops
                    if not send_task.done():
                        send_task.cancel()
                        try:
                            await send_task
                        except asyncio.CancelledError:
                            pass

        except Exception as e:
            logger.error(f"ASR Connection Error: {e}")
            raise
