import io
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.drive import DriveService, FileMetadata


GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
PDF_MIME = "application/pdf"


@pytest.fixture
def token_path(tmp_path):
    return tmp_path / "drive_token.json"


@pytest.fixture
def valid_creds_file(token_path):
    token_path.write_text(json.dumps({
        "token": "abc",
        "refresh_token": "ref",
        "client_id": "cid",
        "client_secret": "sec",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
    }))
    return token_path


def _make_service(token_path):
    return DriveService(
        client_id="cid",
        client_secret="sec",
        token_path=str(token_path),
    )


def test_list_files_returns_metadata(valid_creds_file):
    svc = _make_service(valid_creds_file)
    fake_api = MagicMock()
    fake_api.files.return_value.list.return_value.execute.return_value = {
        "files": [
            {"id": "1", "name": "notes.pdf", "mimeType": PDF_MIME,
             "modifiedTime": "2026-04-20T10:00:00Z", "md5Checksum": "aaa"},
            {"id": "2", "name": "doc", "mimeType": GOOGLE_DOC_MIME,
             "modifiedTime": "2026-04-20T11:00:00Z"},
        ]
    }
    with patch.object(svc, "_build_service", return_value=fake_api), \
         patch.object(svc, "_load_creds", return_value=MagicMock(valid=True)):
        files = svc.list_files("folder-xyz")

    assert len(files) == 2
    assert files[0] == FileMetadata(id="1", name="notes.pdf", mime_type=PDF_MIME,
                                    modified_time="2026-04-20T10:00:00Z", md5="aaa")
    assert files[1].md5 is None
    fake_api.files.return_value.list.assert_called_once()
    kwargs = fake_api.files.return_value.list.call_args.kwargs
    assert "folder-xyz" in kwargs["q"]


def test_download_file_returns_bytes(valid_creds_file):
    svc = _make_service(valid_creds_file)
    fake_api = MagicMock()

    def fake_downloader(fh, request):
        downloader = MagicMock()
        fh.write(b"PDFBYTES")
        downloader.next_chunk.return_value = (MagicMock(progress=lambda: 1.0), True)
        return downloader

    fake_api.files.return_value.get_media.return_value = MagicMock()

    with patch.object(svc, "_build_service", return_value=fake_api), \
         patch.object(svc, "_load_creds", return_value=MagicMock(valid=True)), \
         patch("app.services.drive.MediaIoBaseDownload", side_effect=fake_downloader):
        content = svc.download_file("file-1", mime_type=PDF_MIME)

    assert content == b"PDFBYTES"
    fake_api.files.return_value.get_media.assert_called_once_with(fileId="file-1")


def test_download_google_doc_uses_export(valid_creds_file):
    svc = _make_service(valid_creds_file)
    fake_api = MagicMock()

    def fake_downloader(fh, request):
        downloader = MagicMock()
        fh.write(b"exported text")
        downloader.next_chunk.return_value = (MagicMock(), True)
        return downloader

    fake_api.files.return_value.export_media.return_value = MagicMock()

    with patch.object(svc, "_build_service", return_value=fake_api), \
         patch.object(svc, "_load_creds", return_value=MagicMock(valid=True)), \
         patch("app.services.drive.MediaIoBaseDownload", side_effect=fake_downloader):
        content = svc.download_file("doc-1", mime_type=GOOGLE_DOC_MIME)

    assert content == b"exported text"
    fake_api.files.return_value.export_media.assert_called_once_with(
        fileId="doc-1", mimeType="text/plain"
    )
    fake_api.files.return_value.get_media.assert_not_called()


def test_get_file_metadata(valid_creds_file):
    svc = _make_service(valid_creds_file)
    fake_api = MagicMock()
    fake_api.files.return_value.get.return_value.execute.return_value = {
        "id": "x", "name": "thing.pdf", "mimeType": PDF_MIME,
        "modifiedTime": "2026-04-20T10:00:00Z", "md5Checksum": "bbb",
    }
    with patch.object(svc, "_build_service", return_value=fake_api), \
         patch.object(svc, "_load_creds", return_value=MagicMock(valid=True)):
        meta = svc.get_file_metadata("x")

    assert meta.id == "x"
    assert meta.mime_type == PDF_MIME
    assert meta.md5 == "bbb"


def test_token_persisted_after_refresh(valid_creds_file):
    svc = _make_service(valid_creds_file)
    expired_creds = MagicMock(valid=False, expired=True, refresh_token="r")
    expired_creds.to_json.return_value = json.dumps({"token": "new", "refresh_token": "r"})

    with patch("app.services.drive.Credentials.from_authorized_user_file",
               return_value=expired_creds), \
         patch("app.services.drive.Request"):
        creds = svc._load_creds()

    expired_creds.refresh.assert_called_once()
    saved = json.loads(valid_creds_file.read_text())
    assert saved["token"] == "new"
    assert creds is expired_creds


def test_authenticate_runs_oauth_when_no_token(tmp_path):
    token = tmp_path / "drive_token.json"
    svc = DriveService(client_id="cid", client_secret="sec", token_path=str(token))

    new_creds = MagicMock(valid=True)
    new_creds.to_json.return_value = json.dumps({"token": "fresh"})
    fake_flow = MagicMock()
    fake_flow.run_local_server.return_value = new_creds

    with patch("app.services.drive.InstalledAppFlow.from_client_config",
               return_value=fake_flow):
        svc.authenticate()

    fake_flow.run_local_server.assert_called_once()
    assert token.exists()
    assert json.loads(token.read_text())["token"] == "fresh"
