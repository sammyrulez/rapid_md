from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from rapid_md.models import FileTypeEnum

class FileResponse(BaseModel):
    id: UUID
    filename: str
    created_at: datetime
    filetype: str

class FilesListResponse(BaseModel):
    files: List[FileResponse]

class FileDeleteResponse(BaseModel):
    message: str
    id: str

class FileUploadRequest(BaseModel):
    filepath: str = Field(..., description="Relative path of the file to save")
    content_base64: str = Field(..., description="File content encoded in base64")

class SingleFileUploadResponse(BaseModel):
    message: str
    id: str
    filename: str
    filetype: str

class ZipFileUploadResponse(BaseModel):
    message: str
    files: List[FileResponse]