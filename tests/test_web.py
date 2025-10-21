import unittest
import base64
import uuid
from unittest.mock import patch
from datetime import datetime
import os
import tempfile
from typing import Generator

from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from rapid_md.router_web import render_router
from rapid_md.models import UploadedFile, FileTypeEnum, Base


class TestWebRoutes(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database for testing
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Create all tables in the database
        Base.metadata.create_all(self.engine)

        # Create a session factory
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Define dependency override for database session
        def override_get_db() -> Generator[Session, None, None]:
            db = TestingSessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        # Create a test app and override dependencies
        self.app = FastAPI()
        self.app.include_router(render_router)
        self.app.dependency_overrides = {"rapid_md.router_web.get_db": override_get_db}
        self.client = TestClient(self.app)

        # Get a session for test data setup
        self.db = TestingSessionLocal()

        # Create session ID for testing
        self.session_id_1 = uuid.uuid4()
        self.session_id_2 = uuid.uuid4()

        # Create test data directly in the database
        self.test_file_1 = UploadedFile(
            id=uuid.uuid4(),
            filename="test1.md",
            content=base64.b64encode(b"# Test Markdown").decode("utf-8"),
            created_at=datetime(2025, 10, 15, 10, 0),
            filetype=FileTypeEnum.markdown,
            tags={"category": "test", "priority": "high"},
            upload_session=self.session_id_1,
        )

        self.test_file_2 = UploadedFile(
            id=uuid.uuid4(),
            filename="test2.png",
            content=base64.b64encode(b"fake-image-data").decode("utf-8"),
            created_at=datetime(2025, 10, 16, 11, 0),
            filetype=FileTypeEnum.image,
            tags={"category": "test"},
            upload_session=self.session_id_1,  # Same session as file 1
        )

        self.test_file_3 = UploadedFile(
            id=uuid.uuid4(),
            filename="test3.pdf",
            content=base64.b64encode(b"fake-pdf-data").decode("utf-8"),
            created_at=datetime(2025, 10, 17, 12, 0),
            filetype=FileTypeEnum.document,
            tags={"priority": "low"},
            upload_session=self.session_id_2,  # Different session
        )

        # Add all test files to the database
        self.db.add(self.test_file_1)
        self.db.add(self.test_file_2)
        self.db.add(self.test_file_3)
        self.db.commit()

        # Template mock
        self.mock_template_content = """
        __navigation__
        <h1>__title__</h1>
        <div>__tags__</div>
        <div>__content__</div>
        """

        # Create a temporary template file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_path = os.path.join(self.temp_dir.name, "template.html")
        with open(self.template_path, "w") as f:
            f.write(self.mock_template_content)

    def tearDown(self):
        # Clean up the database by dropping all tables
        self.db.close()
        Base.metadata.drop_all(self.engine)

        # Clean up temporary files
        self.temp_dir.cleanup()

    @patch("pathlib.Path.__truediv__")
    def test_home_with_files(self, mock_path_div):
        # Setup - mock the template path to use our temporary file
        mock_path_div.return_value = self.template_path

        # Execute
        response = self.client.get("/")

        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/html; charset=utf-8")

        # Check content includes file names
        content = response.content.decode("utf-8")
        self.assertIn("test1.md", content)
        self.assertIn("test2.png", content)
        self.assertIn("test3.pdf", content)

        # Check content has sections
        self.assertIn("Files by Upload Session", content)
        self.assertIn("Files by Tag", content)
        self.assertIn("All Files", content)

        # Check tag grouping
        self.assertIn("category:test", content.replace(" ", ""))
        self.assertIn("priority:high", content.replace(" ", ""))
        self.assertIn("priority:low", content.replace(" ", ""))

        # Check upload session grouping - we can't test exact timestamps because we're using a real database
        self.assertIn("Upload Session", content)
        self.assertIn("2 files", content)  # First session has 2 files
        self.assertIn("1 files", content)  # Second session has 1 file

    @patch("pathlib.Path.__truediv__")
    def test_home_empty(self, mock_path_div):
        # Setup - mock the template path to use our temporary file
        mock_path_div.return_value = self.template_path

        # Clear the database
        self.db.query(UploadedFile).delete()
        self.db.commit()

        # Execute
        response = self.client.get("/")

        # Verify
        self.assertEqual(response.status_code, 200)

        # Check empty message
        content = response.content.decode("utf-8")
        self.assertIn("No files uploaded yet", content)

    @patch("pathlib.Path.__truediv__")
    def test_render_markdown_file(self, mock_path_div):
        # Setup - mock the template path to use our temporary file
        mock_path_div.return_value = self.template_path

        # Execute
        response = self.client.get("/render/test1.md")

        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/html; charset=utf-8")

        # Check content includes markdown rendered as HTML
        content = response.content.decode("utf-8")
        self.assertIn("<h1>Test Markdown</h1>", content)

        # Check template replacements
        self.assertIn("Back to file list", content)
        self.assertIn("test1.md", content)

        # Check tags are included
        self.assertIn("category", content)
        self.assertIn("test", content)
        self.assertIn("priority", content)
        self.assertIn("high", content)

    @patch("pathlib.Path.__truediv__")
    def test_render_image_file(self, mock_path_div):
        # Setup - mock the template path to use our temporary file
        mock_path_div.return_value = self.template_path

        # Execute
        response = self.client.get("/render/test2.png")

        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")

        # Check the raw content is returned
        self.assertEqual(response.content, b"fake-image-data")

    @patch("pathlib.Path.__truediv__")
    def test_render_document_file(self, mock_path_div):
        # Setup - mock the template path to use our temporary file
        mock_path_div.return_value = self.template_path

        # Execute
        response = self.client.get("/render/test3.pdf")

        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")

        # Check the raw content is returned
        self.assertEqual(response.content, b"fake-pdf-data")

    def test_render_file_not_found(self):
        # Execute and verify
        response = self.client.get("/render/nonexistent.md")
        self.assertEqual(response.status_code, 404)
        self.assertIn("File not found", response.json()["detail"])

    @patch("pathlib.Path.__truediv__")
    def test_render_file_unknown_extension(self, mock_path_div):
        # Setup - mock the template path to use our temporary file
        mock_path_div.return_value = self.template_path

        # Create unknown file type
        unknown_file = UploadedFile(
            id=uuid.uuid4(),
            filename="test.unknown",
            content=base64.b64encode(b"unknown-data").decode("utf-8"),
            created_at=datetime(2025, 10, 17, 12, 0),
            filetype=FileTypeEnum.document,
            tags=None,
            upload_session=uuid.uuid4(),
        )

        # Add to database
        self.db.add(unknown_file)
        self.db.commit()

        # Execute
        response = self.client.get("/render/test.unknown")

        # Verify - should use default mimetype
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/octet-stream")
        self.assertEqual(response.content, b"unknown-data")


if __name__ == "__main__":
    unittest.main()
