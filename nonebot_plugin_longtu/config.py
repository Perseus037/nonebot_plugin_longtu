from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class Config(BaseModel):
    max_dragons: int = Field(5, ge=1, le=50)
    longtu_mode: Literal["local", "remote"] = "local"
    longtu_local_dir: Path = Path(__file__).resolve().parent / "images"
    longtu_auto_download: bool = True
    longtu_remote_fallback: bool = True
    longtu_download_concurrency: int = Field(3, ge=1, le=8)
    longtu_download_interval: float = Field(0.1, ge=0)
    longtu_idle_seconds: float = Field(3.0, ge=0)
    longtu_startup_delay: float = Field(5.0, ge=0)
    longtu_timeout: float = Field(8.0, gt=0, le=60)
    longtu_request_timeout: float = Field(20.0, gt=0, le=120)
