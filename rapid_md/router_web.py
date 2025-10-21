from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
import base64
import markdown as mdlib
from rapid_md.models import UploadedFile, FileTypeEnum
from rapid_md.db import get_db
from pathlib import Path


render_router = APIRouter()


@render_router.get("/")
def home(db: Session = Depends(get_db)) -> Response:
    """
    Homepage endpoint che mostra la lista di tutti i file caricati
    """
    files = db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).all()

    # Read the template HTML
    template_path = Path(__file__).parent.parent / "template.html"
    with open(template_path, "r") as template_file:
        template_html = template_file.read()

    # Set page title and heading
    template_html = template_html.replace("__page_title__", "Home")
    template_html = template_html.replace("__title__", "Files Repository")
    template_html = template_html.replace(
        "__navigation__", "<!-- No navigation on home page -->"
    )
    template_html = template_html.replace("__tags__", "<!-- No tags on home page -->")

    if not files:
        content_html = '<div class="empty-message">No files uploaded yet.</div>'
    else:
        # Creiamo la tabella dei file
        table_html = """
        <table>
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Type</th>
                    <th>Created At</th>
                    <th>Tags</th>
                </tr>
            </thead>
            <tbody>
        """

        for file in files:
            # Formatta la data
            created_at = file.created_at.strftime("%Y-%m-%d %H:%M")

            # Genera l'HTML dei tag
            tags_html = '<div class="tags">'
            if file.tags:
                for key, value in file.tags.items():
                    if isinstance(value, (str, int, float, bool)):
                        tags_html += f'<span class="tag"><span class="tag-key">{key}</span>: <span class="tag-value">{value}</span></span>'
            else:
                tags_html += '<span style="color: #6a737d;">No tags</span>'
            tags_html += "</div>"

            # Determina l'icona in base al tipo di file
            filetype_class = f"filetype-{file.filetype.value}"

            # Aggiungi la riga alla tabella
            table_html += f"""
            <tr>
                <td><a href="/render/{file.filename}" class="{filetype_class}">{file.filename}</a></td>
                <td>{file.filetype.value}</td>
                <td>{created_at}</td>
                <td>{tags_html}</td>
            </tr>
            """

        table_html += """
            </tbody>
        </table>
        """

        content_html = table_html

    # Replace __content__ with the generated HTML
    rendered_html = template_html.replace("__content__", content_html)

    return Response(content=rendered_html, media_type="text/html")


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

        # Set page title and heading
        template_html = template_html.replace("__page_title__", f"Viewing {filename}")
        template_html = template_html.replace("__title__", filename)

        # Add navigation link back to home
        template_html = template_html.replace(
            "__navigation__", '<a href="/" class="back-link">Back to file list</a>'
        )

        # Generate HTML for tags if they exist
        tags_html = ""
        if file.tags:
            tags_html = "<h3>Tags:</h3>"
            for key, value in file.tags.items():
                if isinstance(value, (str, int, float, bool)):
                    tags_html += f'<span class="tag"><span class="tag-key">{key}</span>: <span class="tag-value">{value}</span></span>'
        else:
            tags_html = "<!-- No tags -->"

        # Replace __tags__ with the tags HTML
        template_html = template_html.replace("__tags__", tags_html)

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
        "stl": "text/stl",
    }
    mimetype = mimetypes.get(ext, "application/octet-stream")
    return Response(content=file_bytes, media_type=mimetype)
