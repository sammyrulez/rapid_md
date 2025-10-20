from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
import base64
import markdown as mdlib
from rapid_md.models import UploadedFile, FileTypeEnum
from rapid_md.db import get_db
from pathlib import Path

API_KEY_ENV = "RAPID_MD_API_KEY"

render_router = APIRouter()


@render_router.get("/render/{filename:path}")
def render_file(filename: str, db: Session = Depends(get_db)) -> Response:
    file = db.query(UploadedFile).filter(UploadedFile.filename == filename).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    file_bytes = base64.b64decode(file.content)
    if file.filetype == FileTypeEnum.markdown:
        # Convert markdown to HTML
        html_content = mdlib.markdown(file_bytes.decode("utf-8"))

        # Read the template HTML
        template_path = Path(__file__).parent.parent / "template.html"
        with open(template_path, "r") as template_file:
            template_html = template_file.read()

        # Replace __content__ with the rendered HTML
        rendered_html = template_html.replace("__content__", html_content)

        return Response(content=rendered_html, media_type="text/html")
    ext = filename.split(".")[-1].lower()
    mimetypes = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
        "txt": "text/plain",
        "md": "text/markdown",
        "html": "text/html",
    }
    mimetype = mimetypes.get(ext, "application/octet-stream")
    return Response(content=file_bytes, media_type=mimetype)
