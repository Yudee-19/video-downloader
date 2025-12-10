from pydantic import BaseModel
from typing import Optional, List


class DownloadRequest(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    audio_only: Optional[bool] = False


class BatchItem(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class BatchDownloadRequest(BaseModel):
    items: Optional[List[BatchItem]] = None
    urls: Optional[List[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    audio_only: Optional[bool] = False


class DownloadResponse(BaseModel):
    file_id: str
    message: str


class BatchDownloadResponse(BaseModel):
    batch_id: str
    download_ids: List[str]
    message: str


class StatusResponse(BaseModel):
    ready: bool
    filename: Optional[str] = None
    error: Optional[str] = None
    progress: Optional[str] = None
    status: Optional[str] = None
    download_url: Optional[str] = None  # S3 presigned URL for batch downloads


class BatchStatusResponse(BaseModel):
    batch_id: str
    total: int
    completed: int
    failed: int
    in_progress: int
    downloads: List[dict]
