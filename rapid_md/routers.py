from fastapi import Query, Response
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from typing import List
from pydantic import BaseModel
import base64
import os
import io
import zipfile
from sqlalchemy.orm import Session
from datetime import datetime
from rapid_md.models import UploadedFile, FileTypeEnum
from rapid_md.db import get_db
import markdown as mdlib



router = APIRouter()

@router.get("/files", response_model=List[dict])
def list_files(
    db: Session = Depends(get_db),
    x_api_key: str = Header(None)
):
    api_key = get_api_key_from_env()
    if x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    files = db.query(UploadedFile).all()
    return [
        {
            "id": str(f.id),
            "filename": f.filename,
            "created_at": f.created_at.isoformat(),
            "filetype": f.filetype.value
        }
        for f in files
    ]

@router.delete("/files/{file_id}")
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    x_api_key: str = Header(None)
):
    api_key = get_api_key_from_env()
    if x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    db.delete(file)
    db.commit()
    return {"message": "File deleted", "id": file_id}

API_KEY_ENV = "RAPID_MD_API_KEY"

class FileUploadRequest(BaseModel):
    filepath: str  # relative path of the file to save
    content_base64: str  # file content encoded in base64

def get_api_key_from_env():
    api_key = os.getenv(API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"Environment variable {API_KEY_ENV} not set")
    return api_key


def guess_filetype(filename: str) -> FileTypeEnum:
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".md", ".markdown"}:
        return FileTypeEnum.markdown
    elif ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"}:
        return FileTypeEnum.image
    else:
        return FileTypeEnum.document


def save_uploaded_file(db: Session, filename: str, content_b64: str, filetype: FileTypeEnum):
    uploaded = UploadedFile(
        filename=filename,
        content=content_b64,
        created_at=datetime.utcnow(),
        filetype=filetype
    )
    db.add(uploaded)
    db.commit()
    db.refresh(uploaded)
    return uploaded


@router.post("/upload-file")
async def upload_file(
    request: Request,
    body: FileUploadRequest,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    api_key = get_api_key_from_env()
    if x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    try:
        filename = os.path.basename(body.filepath)
        filetype = guess_filetype(filename)
        results = []
        if filename.lower().endswith('.zip'):
            # Decode the zip content and process each file
            file_bytes = base64.b64decode(body.content_base64)
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                for zipinfo in z.infolist():
                    if zipinfo.is_dir():
                        continue
                    inner_filename = os.path.basename(zipinfo.filename)
                    inner_filetype = guess_filetype(inner_filename)
                    with z.open(zipinfo) as f:
                        inner_content = f.read()
                        inner_content_b64 = base64.b64encode(inner_content).decode('utf-8')
                        uploaded = save_uploaded_file(db, inner_filename, inner_content_b64, inner_filetype)
                        results.append({
                            "id": str(uploaded.id),
                            "filename": inner_filename,
                            "filetype": inner_filetype.value
                        })
            return {"message": "Zip file extracted and files saved to database", "files": results}
        else:
            uploaded = save_uploaded_file(db, filename, body.content_base64, filetype)
            return {
                "message": "File saved to database",
                "id": str(uploaded.id),
                "filename": filename,
                "filetype": filetype.value
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# List and delete endpoints at the end for clarity
@router.get("/files", response_model=List[dict])
def list_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).all()
    return [
        {
            "id": str(f.id),
            "filename": f.filename,
            "created_at": f.created_at.isoformat(),
            "filetype": f.filetype.value
        }
        for f in files
    ]

@router.delete("/files/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    db.delete(file)
    db.commit()
    return {"message": "File deleted", "id": file_id}
