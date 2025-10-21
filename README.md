## Rapid MD API

[![Tests](https://github.com/sammyrulez/rapid_md/actions/workflows/python-tests.yml/badge.svg)](https://github.com/sammyrulez/rapid_md/actions/workflows/python-tests.yml)

Rapid MD is a FastAPI-based backend for uploading, storing, and managing files (including markdown, images, documents, and zip archives) in a database.

### Features

- Upload files (single or zip archive)
- Store file content as base64 in a relational database
- File metadata: UUID, filename, creation date, type (markdown, image, document), tags
- List all uploaded files
- Delete files by ID
- API key protection for management endpoints
- Public endpoint for rendering and displaying files
- Beautiful HTML template for rendering markdown files
- Home page with files organized by upload session and tags
- Tracking of upload sessions for grouped files (especially from ZIP archives)

### API Endpoints

#### Upload a file
`POST /upload-file`

**Headers:**
- `x-api-key`: API key (required)

**Body (JSON):**
```
{
	"filepath": "relative/path/to/file.md",
	"content_base64": "...base64-encoded content...",
	"tags": { "key1": "value1", "key2": "value2" }  // opzionale
}
```

If the file is a zip archive, all contained files will be extracted and stored individually.

#### List files
`GET /files`

Returns a list of all uploaded files with metadata.

#### Delete a file
`DELETE /files/{file_id}`

Deletes the file with the given UUID.

#### Home Page (Public endpoint)
`GET /`

Displays a web interface showing all uploaded files organized by:
- **Upload Session**: Groups files that were uploaded together (especially useful for ZIP uploads)
- **Tags**: Groups files by their tag values
- **All Files**: A comprehensive list of all files

This is a **public endpoint** that doesn't require an API key.

#### Render file (Public endpoint)
`GET /render/{filename}`

Renders and displays the content of the file. This is a **public endpoint** that doesn't require an API key.

- For markdown files: renders the content as HTML using a styled template
- For images: displays the image directly in the browser
- For other files: serves the raw file with appropriate MIME type

### Database

Uses SQLAlchemy ORM and Alembic for migrations. The `uploaded_files` table contains:
- `id` (UUID, primary key)
- `filename` (string)
- `content` (base64 string)
- `created_at` (datetime)
- `filetype` (enum: markdown, image, document)
- `tags` (JSON, optional): metadati personalizzati per il file
- `upload_session` (UUID): identificativo della sessione di upload, condiviso tra file caricati insieme

### Environment variables

- `RAPID_MD_API_KEY`: API key required for upload
- `DATABASE_URL`: SQLAlchemy database URL (default: SQLite)

### Docker

You can run the application in a container using the provided `Dockerfile`.

**Build the image:**
```sh
docker build -t rapid-md .
```

**Run the container:**
```sh
docker run -e RAPID_MD_API_KEY=yourkey -e DATABASE_URL=sqlite:///./test.db -p 8000:8000 rapid-md
```

On startup, Alembic migrations are applied automatically before the API server starts.

You can override the environment variables as needed for production (e.g. PostgreSQL connection string for `DATABASE_URL`).

---
See source code for further details and customization.
