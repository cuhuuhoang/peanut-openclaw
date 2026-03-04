import os
import json
import time
from pathlib import Path
import requests

from peanut_bridge.env import load_env

load_env()


def _resolve_data_dir() -> Path:
    env_dir = os.getenv("DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return Path(__file__).resolve().parents[1] / "data"


TOKEN_FILE = _resolve_data_dir() / "tokens.json"

CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "consumers")
ACCESS_TOKEN = os.getenv("MICROSOFT_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("MICROSOFT_REFRESH_TOKEN", "")


def _load_tokens_from_file():
    if TOKEN_FILE.exists():
        try:
            data = json.loads(TOKEN_FILE.read_text())
            return data.get("access_token", ""), data.get("refresh_token", ""), data.get("expires_at", 0)
        except Exception:
            return "", "", 0
    return "", "", 0


def _save_tokens_to_file(access_token: str, refresh_token: str, expires_in: int):
    expires_at = int(time.time()) + max(int(expires_in) - 60, 0)
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(
        json.dumps(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
            },
            indent=2,
        )
    )


def _get_tokens():
    file_access, file_refresh, file_expires_at = _load_tokens_from_file()
    env_access, env_refresh = ACCESS_TOKEN, REFRESH_TOKEN

    if env_refresh:
        if env_refresh != file_refresh:
            return env_access, env_refresh, 0
        if env_access and not _valid_token(file_access, file_expires_at):
            return env_access, env_refresh, 0
    if file_refresh:
        return file_access, file_refresh, file_expires_at
    if env_access or env_refresh:
        return env_access, env_refresh, 0
    return "", "", 0


def _valid_token(access_token: str, expires_at: int) -> bool:
    return bool(access_token) and time.time() < (expires_at or 0)


def refresh_access_token(refresh_token: str):
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "scope": "Tasks.ReadWrite offline_access",
    }
    if CLIENT_SECRET:
        data["client_secret"] = CLIENT_SECRET

    resp = requests.post(token_url, data=data, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Token refresh failed ({resp.status_code}): {resp.text}")

    payload = resp.json()
    new_access = payload["access_token"]
    new_refresh = payload.get("refresh_token", refresh_token)
    expires_in = int(payload.get("expires_in", 3600))

    _save_tokens_to_file(new_access, new_refresh, expires_in)
    return new_access, new_refresh, int(time.time()) + expires_in - 60


def get_valid_access_token():
    access, refresh, expires_at = _get_tokens()
    if not _valid_token(access, expires_at):
        if not refresh:
            raise RuntimeError(
                "No valid Microsoft tokens available. Set MICROSOFT_ACCESS_TOKEN and MICROSOFT_REFRESH_TOKEN in .env."
            )
        access, refresh, expires_at = refresh_access_token(refresh)
    return access
