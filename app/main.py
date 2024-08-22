from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
from datetime import datetime, UTC
from typing import Dict
from app.models import DeviceInfo
from app.config import Config
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
config = Config("config/config.json")
device_data: Dict[str, DeviceInfo] = {}
firmware_path = "data/firmware/"


def get_current_time() -> datetime:
    return datetime.now(UTC)


def validate_headers(request: Request) -> Dict[str, str]:
    """Validate custom headers and return device info."""
    mac = request.headers.get("_br_mac_")
    fw_version = request.headers.get("_br_fwv_")
    if not mac or not fw_version:
        raise HTTPException(status_code=400, detail="Missing custom headers")
    return {"mac": mac, "fw_version": fw_version}


@app.get("/version.txt")
async def get_version(request: Request) -> PlainTextResponse:
    """Return the current firmware version."""
    try:
        device_info = validate_headers(request)
        device = DeviceInfo(
            **device_info,
            last_seen_time=get_current_time()
        )
        await device.save()
        return PlainTextResponse(config.current_version)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in /version.txt endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/firmware.bin")
async def get_firmware(request: Request) -> FileResponse:
    """Return the firmware binary file."""
    try:
        device_info = validate_headers(request)
        device = DeviceInfo(
            **device_info,
            update_time=get_current_time()
        )
        await device.save()
        return FileResponse(f"{firmware_path}{config.current_version}.bin")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in /firmware.bin endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
