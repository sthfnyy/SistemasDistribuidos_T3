import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, BigInteger, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Audio(Base):
    __tablename__ = "audios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    original_name = Column(String(255), nullable=False)
    original_ext = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    duration_sec = Column(Float, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bitrate = Column(Integer, nullable=True)
    processing_type = Column(String(100), nullable=False)
    processing_params = Column(Text, nullable=True)  # JSON codificado como string
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    path_original = Column(String(500), nullable=False)
    path_processed = Column(String(500), nullable=False)
    path_waveform = Column(String(500), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "original_name": self.original_name,
            "original_ext": self.original_ext,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "duration_sec": self.duration_sec,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bitrate": self.bitrate,
            "processing_type": self.processing_type,
            "processing_params": self.processing_params,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "path_original": self.path_original,
            "path_processed": self.path_processed,
            "path_waveform": self.path_waveform,
            "is_deleted": self.is_deleted,
        }

