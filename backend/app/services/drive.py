import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.logging_config import get_logger

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
GOOGLE_SLIDES_MIME = "application/vnd.google-apps.presentation"
EXPORT_AS_TEXT = {
    GOOGLE_DOC_MIME: "text/plain",
    GOOGLE_SHEET_MIME: "text/csv",
    GOOGLE_SLIDES_MIME: "text/plain",
}

log = get_logger("app.services.drive")


@dataclass(frozen=True)
class FileMetadata:
    id: str
    name: str
    mime_type: str
    modified_time: str
    md5: Optional[str] = None


class DriveService:
    def __init__(self, client_id: str, client_secret: str, token_path: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_path = Path(token_path)

    def _client_config(self) -> dict:
        return {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }

    def _save_creds(self, creds: Credentials) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(creds.to_json())

    def _load_creds(self) -> Credentials:
        if not self.token_path.exists():
            return self.authenticate()

        creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        if creds.valid:
            return creds

        if creds.expired and creds.refresh_token:
            log.info("token_refresh", category="auth", action="token_refresh")
            creds.refresh(Request())
            self._save_creds(creds)
            return creds

        log.info("token_expired", category="auth", action="token_expired")
        return self.authenticate()

    def authenticate(self) -> Credentials:
        log.info("oauth_start", category="auth", action="oauth_start")
        flow = InstalledAppFlow.from_client_config(self._client_config(), SCOPES)
        creds = flow.run_local_server(port=0)
        self._save_creds(creds)
        log.info("oauth_callback", category="auth", action="oauth_callback")
        return creds

    def _build_service(self, creds: Credentials):
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def list_files(self, folder_id: str) -> list[FileMetadata]:
        creds = self._load_creds()
        api = self._build_service(creds)
        query = f"'{folder_id}' in parents and trashed = false"
        fields = "files(id,name,mimeType,modifiedTime,md5Checksum)"
        resp = api.files().list(q=query, fields=fields, pageSize=1000).execute()
        return [self._to_metadata(f) for f in resp.get("files", [])]

    def get_file_metadata(self, file_id: str) -> FileMetadata:
        creds = self._load_creds()
        api = self._build_service(creds)
        fields = "id,name,mimeType,modifiedTime,md5Checksum"
        resp = api.files().get(fileId=file_id, fields=fields).execute()
        return self._to_metadata(resp)

    def download_file(self, file_id: str, mime_type: str) -> bytes:
        creds = self._load_creds()
        api = self._build_service(creds)

        if mime_type in EXPORT_AS_TEXT:
            request = api.files().export_media(
                fileId=file_id, mimeType=EXPORT_AS_TEXT[mime_type]
            )
        else:
            request = api.files().get_media(fileId=file_id)

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _status, done = downloader.next_chunk()
        return buf.getvalue()

    @staticmethod
    def _to_metadata(f: dict) -> FileMetadata:
        return FileMetadata(
            id=f["id"],
            name=f["name"],
            mime_type=f["mimeType"],
            modified_time=f.get("modifiedTime", ""),
            md5=f.get("md5Checksum"),
        )
