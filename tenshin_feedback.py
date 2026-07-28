"""Drop-in bug/feature reporter for Tenshin Arts games. Copy this ONE file into a game repo.

The game calls submit(...) server-side when a player files a report; it POSTs to the shared hub
(tenshinarts.com/feedback), authenticating with the same TENSHIN_SECRET the game already runs with.
One shared queue for every game — view + auto-fix at tenshinarts.com/admin/feedback.

    import tenshin_feedback
    ok, info = tenshin_feedback.submit(game="freight", kind="bug",
                                       title="Ship stuck at Mars", body="...", username="42")

Config (env): TENSHIN_HUB_URL (default https://tenshinarts.com), TENSHIN_SECRET (shared with the hub).
"""
import json
import os
import urllib.parse
import urllib.request

HUB = os.environ.get("TENSHIN_HUB_URL", "https://tenshinarts.com").rstrip("/")
SECRET = os.environ.get("TENSHIN_SECRET") or "dev-insecure-secret-change-me"


def submit(game, kind, title, body="", username="", meta=None, timeout=6):
    """Send a report to the shared hub. Returns (ok: bool, info: dict). NEVER raises —
    a down hub must not break the game."""
    data = urllib.parse.urlencode({
        "game": game, "kind": kind, "title": title, "body": body,
        "username": str(username or ""), "meta": json.dumps(meta) if meta else "",
        "secret": SECRET,
    }).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(HUB + "/feedback", data=data), timeout=timeout)
        return True, json.loads(r.read() or "{}")
    except Exception as e:
        return False, {"error": str(e)}
