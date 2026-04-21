"""Bootstrap Google Drive OAuth and write data/drive_token.json.

Run inside the backend container:
    docker exec -it buddy-backend-1 python -m app.scripts.auth_drive

The script prints a URL. Open it in your browser, complete the consent flow,
and the redirect to http://localhost:8080 will be caught by the local server
running inside the container (port 8080 is exposed in docker-compose.dev.yml).
"""
from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import settings
from app.services.drive import SCOPES, DriveService

OAUTH_PORT = 8080


def main() -> None:
    svc = DriveService(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        token_path="data/drive_token.json",
    )
    flow = InstalledAppFlow.from_client_config(svc._client_config(), SCOPES)
    creds = flow.run_local_server(
        host="localhost", bind_addr="0.0.0.0", port=OAUTH_PORT, open_browser=False
    )
    svc._save_creds(creds)
    print(f"\nToken saved to {svc.token_path}")


if __name__ == "__main__":
    main()
