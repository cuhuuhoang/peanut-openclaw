import requests
from peanut_bridge.token_manager import get_valid_access_token, _get_tokens, refresh_access_token


def _graph_headers(access_token: str):
    return {"Authorization": f"Bearer {access_token}"}


def graph_get(url: str, access_token: str):
    return requests.get(url, headers=_graph_headers(access_token), timeout=30)


def graph_post(url: str, access_token: str, json_body: dict):
    return requests.post(
        url,
        headers={**_graph_headers(access_token), "Content-Type": "application/json"},
        json=json_body,
        timeout=30,
    )


def graph_patch_beta(url: str, access_token: str, json_body: dict):
    return requests.patch(
        url,
        headers={**_graph_headers(access_token), "Content-Type": "application/json"},
        json=json_body,
        timeout=30,
    )


def with_auto_refresh(request_fn, *args, **kwargs):
    access = get_valid_access_token()
    resp = request_fn(*args, access, **kwargs)
    if resp.status_code == 401:
        _, refresh, _ = _get_tokens()
        new_access, _, _ = refresh_access_token(refresh)
        resp = request_fn(*args, new_access, **kwargs)
    return resp
