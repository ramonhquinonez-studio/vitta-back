import io
import tempfile
import unittest
from pathlib import Path

from starlette.datastructures import Headers
from fastapi import UploadFile

from app.core.config import settings
from app.core.storage import save_upload


def _upload_file(data: bytes, *, filename: str, content_type: str) -> UploadFile:
    return UploadFile(
        io.BytesIO(data),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


class SaveUploadTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._original_uploads_dir = settings.UPLOADS_DIR
        settings.UPLOADS_DIR = self._tmp_dir.name

    def tearDown(self):
        settings.UPLOADS_DIR = self._original_uploads_dir
        self._tmp_dir.cleanup()

    async def test_saves_file_and_returns_url(self):
        file = _upload_file(b"fake video bytes", filename="clip.mp4", content_type="video/mp4")

        url, content_type = await save_upload(file, subfolder="workout_plans/owner1/videos")

        self.assertTrue(url.startswith("/uploads/workout_plans/owner1/videos/"))
        self.assertTrue(url.endswith(".mp4"))
        self.assertEqual(content_type, "video/mp4")
        saved_path = Path(self._tmp_dir.name) / url.removeprefix("/uploads/")
        self.assertEqual(saved_path.read_bytes(), b"fake video bytes")

    async def test_rejects_a_file_over_the_size_limit(self):
        file = _upload_file(b"x" * 100, filename="clip.mp4", content_type="video/mp4")

        with self.assertRaises(ValueError):
            await save_upload(file, subfolder="workout_plans/owner1/videos", max_size_bytes=50)

    async def test_allows_a_file_within_the_size_limit(self):
        file = _upload_file(b"x" * 50, filename="clip.mp4", content_type="video/mp4")

        url, _content_type = await save_upload(
            file, subfolder="workout_plans/owner1/videos", max_size_bytes=50
        )

        self.assertTrue(url.startswith("/uploads/workout_plans/owner1/videos/"))

    async def test_ignores_a_spoofed_filename_extension_and_uses_content_type_instead(self):
        # A malicious filename shouldn't decide the saved extension: /uploads is
        # served by StaticFiles, which infers Content-Type from the extension —
        # trusting the filename here would let an attacker get an uploaded file
        # served back as e.g. text/html (stored XSS) regardless of its real
        # content type.
        file = _upload_file(b"<script>evil()</script>", filename="x.html", content_type="image/jpeg")

        url, content_type = await save_upload(file, subfolder="measurements/patient1")

        self.assertTrue(url.endswith(".jpg"))
        self.assertEqual(content_type, "image/jpeg")

    async def test_falls_back_to_a_safe_extension_for_an_unrecognized_content_type(self):
        file = _upload_file(b"data", filename="whatever.exe", content_type="application/x-msdownload")

        url, _content_type = await save_upload(file, subfolder="measurements/patient1")

        self.assertTrue(url.endswith(".bin"))
