from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class AudioResponse(BaseModel):
    id: str
    original_name: str
    original_ext: str
    mime_type: str
    size_bytes: int
    duration_sec: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bitrate: Optional[int] = None
    processing_type: str
    processing_params: Optional[str] = None
    created_at: Optional[str] = None
    is_deleted: bool = False
    urls: Optional[Dict[str, str]] = None

    model_config = ConfigDict(from_attributes=True)

class AudioListResponse(BaseModel):
    total: int
    audios: List[AudioResponse]

