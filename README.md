## Rapid MD API

Rapid MD is a FastAPI-based backend for uploading, storing, and managing files (including markdown, images, documents, and zip archives) in a database.

### Features

- Upload files (single or zip archive)
- Store file content as base64 in a relational database
- File metadata: UUID, filename, creation date, type (markdown, image, document)
- List all uploaded files
- Delete files by ID
- API key protection for upload endpoint

### API Endpoints

#### Upload a file
`POST /upload-file`

**Headers:**
- `x-api-key`: API key (required)

**Body (JSON):**
```
{
	"filepath": "relative/path/to/file.md",
	"content_base64": "...base64-encoded content..."
}
```

If the file is a zip archive, all contained files will be extracted and stored individually.

#### List files
`GET /files`

Returns a list of all uploaded files with metadata.

#### Delete a file
`DELETE /files/{file_id}`

Deletes the file with the given UUID.

### Database

Uses SQLAlchemy ORM and Alembic for migrations. The `uploaded_files` table contains:
- `id` (UUID, primary key)
- `filename` (string)
- `content` (base64 string)
- `created_at` (datetime)
- `filetype` (enum: markdown, image, document)

### Environment variables

- `RAPID_MD_API_KEY`: API key required for upload
- `DATABASE_URL`: SQLAlchemy database URL (default: SQLite)

---
See source code for further details and customization.
