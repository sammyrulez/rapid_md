import uuid
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class FileTypeEnum(str, enum.Enum):
    markdown = "markdown"
    image = "image"
    document = "document"

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    filename = Column(String, nullable=False)
    content = Column(String, nullable=False)  # base64 o testo
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    filetype = Column(Enum(FileTypeEnum), nullable=False)
