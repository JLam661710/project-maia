import asyncio
import os
import uuid
import logging
import websockets
from dotenv import load_dotenv

# Load env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

VOLC_APP_ID = os.getenv("VOLC_APP_ID")
VOLC_ACCESS_TOKEN = os.getenv("VOLC_ACCESS_TOKEN")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger("Probe")

RESOURCE_IDS = [
    "volc.seedasr.sauc.duration",   # 2.0 Duration
    "volc.seedasr.sauc.concurrent", # 2.0 Concurrent
    "volc.bigasr.sauc.duration",    # 1.0 Duration (Baseline)
]

ENDPOINTS = [
    "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel",
    "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async",
]

async def probe(resource_id, endpoint):
    headers = {
        "X-Api-App-Key": VOLC_APP_ID,
        "X-Api-Access-Key": VOLC_ACCESS_TOKEN,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
    
    logger.info(f"Probing Resource: {resource_id} | Endpoint: {endpoint.split('/')[-1]}")
    
    try:
        async with websockets.connect(endpoint, additional_headers=headers) as ws:
            logger.info(f"✅ SUCCESS: Connected to {resource_id} @ {endpoint}")
            await ws.close()
            return True
    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"❌ FAILED: {e.status_code} - {resource_id}")
        return False
    except Exception as e:
        logger.error(f"❌ ERROR: {e} - {resource_id}")
        return False

async def main():
    logger.info(f"App ID: {VOLC_APP_ID}")
    
    for resource_id in RESOURCE_IDS:
        for endpoint in ENDPOINTS:
            await probe(resource_id, endpoint)
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
