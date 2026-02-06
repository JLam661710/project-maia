import asyncio
import os
import uuid
import logging
import websockets
from dotenv import load_dotenv

# Load env from Project_Maia root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

VOLC_APP_ID = os.getenv("VOLC_APP_ID")
VOLC_ACCESS_TOKEN = os.getenv("VOLC_ACCESS_TOKEN")
VOLC_ASR_RESOURCE_ID = "volc.bigasr.sauc.duration"
VOLC_ASR_ENDPOINT = os.getenv("VOLC_ASR_ENDPOINT", "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugConnect")

async def test_connect():
    headers = {
        "X-Api-App-Key": VOLC_APP_ID,
        "X-Api-Access-Key": VOLC_ACCESS_TOKEN,
        "X-Api-Resource-Id": VOLC_ASR_RESOURCE_ID,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
    
    logger.info(f"Connecting to {VOLC_ASR_ENDPOINT}")
    logger.info(f"Headers: {headers}")
    
    try:
        async with websockets.connect(VOLC_ASR_ENDPOINT, additional_headers=headers) as ws:
            logger.info("Successfully connected!")
            await ws.close()
    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"Connection failed with status code: {e.status_code}")
        logger.error(f"Headers: {e.headers}")
        # Sometimes body is not available in exception, but let's try
        logger.error(f"Message: {e}")
    except Exception as e:
        logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connect())
