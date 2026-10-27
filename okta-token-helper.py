#!/usr/bin/env python3
"""apiKeyHelper for Claude Code + Okta PKCE. Prints a single access token to stdout."""
import os
import sys
import json
import time
import base64
import hashlib
import secrets
import socket
import ssl
import webbrowser
import urllib.parse
import urllib.request
import urllib.error

# --- Okta configuration (override via env vars; do not hardcode real values here) ---
OKTA_DOMAIN = os.environ.get("OKTA_DOMAIN", "https://your-org.okta.com")
CLIENT_ID = os.environ.get("OKTA_CLIENT_ID", "0oa1b2c3d4YourClientId")
REDIRECT_PORT = int(os.environ.get("OKTA_REDIRECT_PORT", "9876"))
AUDIENCE = os.environ.get("OKTA_AUDIENCE", "api://default")
AUTH_SERVER = os.environ.get("OKTA_AUTH_SERVER", "default")
# Optional: path to a CA bundle (PEM) to trust in addition to the system default,
# for environments behind a TLS-inspecting (MITM) proxy whose root CA isn't in
# Python's own trust store even though the OS/browser already trusts it.
CA_BUNDLE = os.environ.get("OKTA_CA_BUNDLE")
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
SCOPES = "openid profile email offline_access"
CALLBACK_TIMEOUT_SECS = 120

CACHE_DIR = os.path.expanduser("~/.claude/okta-cache")
CACHE_FILE = os.path.join(CACHE_DIR, "tokens.json")
LOCK_DIR = os.path.join(CACHE_DIR, "auth.lock")
LOCK_TIMEOUT_SECS = 30

BASE_URL = f"{OKTA_DOMAIN}/oauth2/{AUTH_SERVER}/v1"
AUTH_ENDPOINT = f"{BASE_URL}/authorize"
TOKEN_ENDPOINT = f"{BASE_URL}/token"

def log(msg: str) -> None:
    sys.stderr.write(f"[okta-auth] {msg}\n")


if CA_BUNDLE:
    if not os.path.isfile(CA_BUNDLE):
        log(f"ERROR: OKTA_CA_BUNDLE={CA_BUNDLE!r} is set but no such file exists.")
        sys.exit(1)
    log(f"Using custom CA bundle: {CA_BUNDLE}")
    SSL_CONTEXT = ssl.create_default_context(cafile=CA_BUNDLE)
else:
    SSL_CONTEXT = None


def die(msg: str) -> None:
    log(f"ERROR: {msg}")
    sys.exit(1)


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(token_data: dict) -> None:
    os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
    cache = load_cache()
    cache.update(token_data)
    if "expires_in" in token_data:
        cache["expires_at"] = time.time() + int(token_data["expires_in"]) - 60
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)
    os.chmod(CACHE_FILE, 0o600)


def acquire_lock():
    os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
    waited = 0.0
    while True:
        try:
            os.mkdir(LOCK_DIR)
            return
        except FileExistsError:
            time.sleep(0.5)
            waited += 0.5
            if waited > LOCK_TIMEOUT_SECS:
                log("Lock timeout, removing stale lock")
                try:
                    os.rmdir(LOCK_DIR)
                except OSError:
                    pass


def release_lock() -> None:
    try:
        os.rmdir(LOCK_DIR)
    except OSError:
        pass


def access_token_valid(cache: dict) -> str | None:
    tok = cache.get("access_token")
    exp = cache.get("expires_at", 0)
    if tok and exp and time.time() < exp:
        return tok
    return None


def refresh_access_token(refresh_token: str) -> str | None:
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": refresh_token,
        "scope": SCOPES,
    }).encode("utf-8")
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data, method="POST")
    try:
        log("Attempting silent refresh...")
        with urllib.request.urlopen(req, context=SSL_CONTEXT) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            save_cache(res_body)
            log("Token refreshed successfully.")
            return res_body.get("access_token")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        log(f"Refresh token error: HTTP {e.code} {e.reason} - {body}")
        return None
    except (urllib.error.URLError, Exception) as e:
        log(f"Refresh token error: {e}")
        return None


def wait_for_callback(expected_state: str) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", REDIRECT_PORT))
    sock.listen(1)
    sock.settimeout(CALLBACK_TIMEOUT_SECS)

    html_ok = b"<html><body><h2>Authenticated! Close this tab.</h2><script>window.close();</script></body></html>"
    html_err = b"<html><body><h2>Authentication failed.</h2></body></html>"

    try:
        conn, _ = sock.accept()
    except socket.timeout:
        die("Timed out waiting for callback.")

    try:
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        request_line = data.decode(errors="replace").split("\r\n")[0]
        path = request_line.split(" ")[1] if " " in request_line else "/"
        params = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]
        error = params.get("error", [None])[0]
        ok = bool(code) and state == expected_state and not error

        conn.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
            + (html_ok if ok else html_err)
        )
        conn.close()
    finally:
        sock.close()

    if not ok:
        if error:
            die(f"Okta returned an error: {error}")
        die("No authorization code received.")
    return code


def run_pkce_flow() -> str:
    code_verifier = b64url(secrets.token_bytes(32))
    code_challenge = b64url(hashlib.sha256(code_verifier.encode("utf-8")).digest())
    state = secrets.token_hex(16)

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "audience": AUDIENCE,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    url = f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"
    log("Opening browser for Okta login...")
    log(f"If the browser doesn't open, visit: {url}")
    webbrowser.open(url)

    log(f"Waiting for callback on {REDIRECT_URI} ...")
    auth_code = wait_for_callback(state)
    log("Authorization code received. Exchanging for tokens...")

    exchange_data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }).encode("utf-8")

    req = urllib.request.Request(TOKEN_ENDPOINT, data=exchange_data, method="POST")
    try:
        with urllib.request.urlopen(req, context=SSL_CONTEXT) as resp:
            tokens = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        die(f"Token exchange failed: HTTP {e.code} {e.reason} - {body}")
    except urllib.error.URLError as e:
        die(f"Token exchange failed: {e}")

    if "access_token" not in tokens:
        die("No access_token in response.")

    save_cache(tokens)
    log("Authentication successful. Token cached.")
    return tokens["access_token"]


def main() -> None:
    acquire_lock()
    try:
        cache = load_cache()

        tok = access_token_valid(cache)
        if tok:
            sys.stdout.write(tok)
            return

        if cache.get("refresh_token"):
            tok = refresh_access_token(cache["refresh_token"])
            if tok:
                sys.stdout.write(tok)
                return

        tok = run_pkce_flow()
        sys.stdout.write(tok)
    finally:
        release_lock()


if __name__ == "__main__":
    main()
