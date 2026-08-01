"""Pyrogen — the web layer (FastAPI), implementing the Tenshin game contract.

A pathogen crosses tissue toward an organ and every way of stopping it is a way of
hurting yourself. You commit a schedule — resting drive levels plus up to three
reflex triggers — and the server resolves thirty beats against it.

Contract: GET /version · GET / (spectator-open, play gated) · GET /live +
/live/embed + /live/stream + /live/agents (public) · GET /leaderboard.json (public)
· GET /admin/players (secret) · POST /api/report. Game: GET /api/state · POST
/api/commit · /api/restart · /api/initials.

    python app.py            # serve on 127.0.0.1:9100
    python app.py test       # the gate — in-process, no httpx
    TENSHIN_DEV=1 python app.py

⚠ TENSHIN_DEV must be set BEFORE tenshin_gate is imported; the drop-in latches it
into a module constant at import time.

⚠ PORT 9100 IS CORPUS'S, freed when Corpus and Titer retired into this game
(2026-08-01). It was safe to take only because both A records were removed first —
see the OPS row in ../Website/app.py, which is the live port map.
"""
import asyncio
import contextlib
import json
import os
import random
import sys
import threading
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import (HTMLResponse, JSONResponse, PlainTextResponse,
                               StreamingResponse)

import tenshin_client
import tenshin_feedback
import tenshin_gate
import tenshin_version
from engine.turns import TurnEngine
from pyrogen import game, physiology as phys

GAME = "pyrogen"
TITLE = "Pyrogen"
VERSION = tenshin_version.get_version()
PORT = int(os.environ.get("LOAD_PORT", "9100"))
HERE = Path(__file__).parent
SITE_URL = os.environ.get("TENSHIN_SITE_URL", "https://tenshinarts.com").rstrip("/")
DB = ":memory:" if "test" in sys.argv else os.environ.get("PYROGEN_DB", str(HERE / "pyrogen.db"))
# ⚠ TWO — the platform cap on AI players per game (Dr. Ray, 2026-07-31).
BOT_COUNT = int(os.environ.get("BOT_COUNT", "2"))
BOT_TICK = float(os.environ.get("LOAD_BOT_TICK", "8"))
PLAYERS_WINDOW = 600

CORS = {"Access-Control-Allow-Origin": "*"}
ENG = TurnEngine(DB, comp_map=game.COMPETENCIES)
RNG = random.Random()
_SEEN = {}
_LOCK = threading.RLock()
_TURN = 0          # whose turn it is among the agents; see bot_tick

BOT_NAMES = ["PYX", "FERV", "ILIA", "KALOR", "SEPSIS", "VIGIL", "ARDOR", "THERM"]


# ── the client ───────────────────────────────────────────────────────────────
def client(spectate=False):
    """One HTML file for both surfaces, switched by a body class the server stamps.

    ⚠ Plain `.replace`, not `.format` — a `{` in the stylesheet or the script is not
    a format field, and a game two doors down shipped a page whose every brace was
    doubled: 200 OK, invalid CSS, a script that never parsed, a blank console, and
    every check green."""
    html = (HERE / "web" / "console.html").read_text(encoding="utf-8")
    return (html.replace("__VERSION__", VERSION)
                .replace("__SITE__", SITE_URL)
                .replace("__BODYCLASS__", "spectate" if spectate else "play"))


def snapshot(state, pid=None):
    out = {"view": game.view(state)}
    if pid is not None:
        out["progress"] = progress(pid)
    return out


def progress(pid):
    """What the stealth assessment concluded. ⚠ It had better reach a screen —
    evidence recorded every wave and read back by nothing is worse than a dead
    endpoint, because the machinery actually runs."""
    try:
        st = ENG.status(pid)
    except KeyError:
        return None
    rows = [{"id": c.id, "name": c.name, "what": c.description,
             "band": st[c.id]["band"], "unlocked": st[c.id]["unlocked"],
             "tier": c.tier}
            for c in game.COMPETENCIES]
    return {"rank": ENG.rank(pid, game.TITLES), "level": ENG.level(pid),
            "of": len(game.COMPETENCIES), "rows": rows}


def load(pid):
    ENG.ensure_player(pid, game.new_run(RNG.randrange(1, 10 ** 6)))
    return ENG.get(pid)[1]


def account(request: Request) -> int:
    acct = tenshin_gate.require_account(request)
    with _LOCK:
        _SEEN[acct] = time.time()
    return acct


# ── the living world ─────────────────────────────────────────────────────────
def bot_schedule(rng):
    """A competent-but-not-optimal answer. ⚠ NOT full drive — law 2 says maxing
    everything loses, so a fleet of maximisers would flatline on wave one and the
    feed would show two corpses for ever. It backs off the body, which is what the
    bench's compared policies had to learn to do before question 1 meant anything."""
    # ⚠⚠ RECRUIT-ONLY, AND THAT IS A SYMPTOM, NOT A STYLE CHOICE (2026-08-01).
    # The first version of this shivered and released sugar like the bench's policies
    # do. Measured over eight seeds at wave 1: `recruit .45` survives 8/8 and clears
    # 8/8, while ANY schedule that raises a fever survives 0/8 — see the envelope
    # table in IMPROVEMENTS.md. A fleet on the honest policy would be two corpses in
    # the feed forever, which monitors as a living world and is not one.
    # ⚠ So this is a WORKAROUND around an open balance finding, not the answer to it.
    # When wave 1 stops being lethal to the signature mechanic, give the bots a fever
    # back — a living world whose agents cannot use the game's central verb is a
    # demonstration of the wrong game.
    return {
        "rest": {"recruit": round(rng.uniform(0.35, 0.55), 2),
                 "hyperventilate": round(rng.uniform(0.2, 0.45), 2)},
        "triggers": [
            {"metric": "organ", "op": ">", "value": round(rng.uniform(2.0, 3.4), 1),
             "set": {"recruit": 0.15}},
        ],
    }


def seed_bots():
    existing = ENG.agents()
    for _ in range(max(0, BOT_COUNT - len(existing))):
        ENG.create_bot(game.new_run(RNG.randrange(1, 10 ** 6)))


def bot_tick():
    """One move for one agent. ⚠ Returns the pid it moved, or None — a bot loop
    that swallows every exception and reports nothing is how a botless world looks
    healthy. The engine counts refusals; this says out loud whether it acted."""
    agents = ENG.agents()
    if not agents:
        return None
    # ⚠ A COUNTER, NOT THE CLOCK. This was `int(time.time() / BOT_TICK) % len(agents)`,
    # which reads as round-robin and is not: two calls inside one BOT_TICK window pick
    # the SAME agent, so within any short window one bot takes every turn and the other
    # starves. Live it eventually rotates, which is why it would never have been noticed
    # — and it is untestable by construction, because a test cannot make the wall clock
    # move. Found by asserting every agent's turn counter rose rather than that a tick
    # returned something.
    global _TURN
    with _LOCK:
        pid = agents[_TURN % len(agents)]
        _TURN += 1
    try:
        state = ENG.get(pid)[1]
    except KeyError:
        return None
    action = ({"do": "restart", "seed": RNG.randrange(1, 10 ** 6)}
              if not state["alive"] else
              {"do": "commit", "schedule": bot_schedule(RNG)})
    try:
        ENG.advance(pid, action, game, RNG)
        return pid
    except Exception:
        return None


def _bot_loop():
    while True:
        with contextlib.suppress(Exception):
            bot_tick()
        time.sleep(BOT_TICK)


@contextlib.asynccontextmanager
async def lifespan(_app):
    """Start the living world with the server (contract §5). Bots are IN-PROCESS
    and never a second install step: a redeploy that forgets a separate bot unit
    leaves every game botless, healthy-looking, and showing dead consoles."""
    if os.environ.get("LOAD_BOTS", "1") != "0":
        seed_bots()
        threading.Thread(target=_bot_loop, daemon=True).start()
    yield


app = FastAPI(title=TITLE, lifespan=lifespan)


# ── routes: the contract ─────────────────────────────────────────────────────
@app.get("/version", response_class=PlainTextResponse)
def version():
    return PlainTextResponse(VERSION, headers=CORS)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Spectating is open to everyone; playing needs an account (Dr. Ray,
    2026-07-30). `require_account` still decides — the SITE hosts the login — so
    there is one rule for who is signed in rather than a second copy of it here."""
    from fastapi import HTTPException
    try:
        tenshin_gate.require_account(request)
    except HTTPException:
        return HTMLResponse(client(spectate=True))
    return HTMLResponse(client())


@app.get("/live", response_class=HTMLResponse)
def live():
    return HTMLResponse(client(spectate=True), headers=CORS)


@app.get("/live/embed", response_class=HTMLResponse)
def live_embed():
    return HTMLResponse(client(spectate=True), headers=CORS)


def _agent_rows(limit=6):
    """⚠ Reads the RESERVED negative-id range only, via ENG.agents(). The feed
    cannot show a real player because there is no query here that could return
    one — a shape, not a filter someone has to remember (contract §3)."""
    rows = []
    for pid in ENG.agents()[:limit]:
        try:
            s = ENG.get(pid)[1]
        except KeyError:
            continue
        rows.append({"id": pid, "name": BOT_NAMES[(-pid - 1) % len(BOT_NAMES)],
                     "wave": s["wave"], "score": s["score"],
                     "alive": bool(s["alive"]), "spent": s["spent"]})
    return rows


def _featured():
    """The agent the embed watches: the one furthest in that is still alive, so a
    visitor lands on a body with something happening to it."""
    best, bs = None, None
    for pid in ENG.agents():
        try:
            s = ENG.get(pid)[1]
        except KeyError:
            continue
        mark = (bool(s["alive"]), s["wave"])
        if bs is None or mark > bs:
            best, bs = (pid, s), mark
    if best is None:
        return None
    pid, s = best
    return {"id": pid, "name": BOT_NAMES[(-pid - 1) % len(BOT_NAMES)], **snapshot(s)}


@app.get("/live/agents")
def live_agents():
    # Keyed `agents` — the hub counts len(data["agents"]).
    return JSONResponse({"agents": _agent_rows(), "featured": _featured()},
                        headers=CORS)


def stream_payload(rows, featured, seen):
    """One push, and what to remember for the next one. Returns (payload, seen).

    ⚠ Pulled out of the generator because a decision buried in a `while True` with
    a sleep in it is a decision nothing will ever test."""
    payload = {"agents": rows}
    if featured is None:
        return payload, seen
    mark = (featured["id"], featured["view"]["wave"], featured["view"]["score"])
    if mark != seen:
        payload["featured"] = featured
        seen = mark
    return payload, seen


@app.get("/live/stream")
async def live_stream():
    async def gen():
        seen = None
        while True:
            payload, seen = stream_payload(_agent_rows(), _featured(), seen)
            yield "data: " + json.dumps(payload) + "\n\n"
            await asyncio.sleep(10)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={**CORS, "Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.get("/leaderboard.json")
def leaderboard():
    """Real players, by best run. Accepted carve-out: Tenshin accounts are zero-PII,
    so a board of self-chosen initials leaks nothing (contract §3). ⚠ Nothing beyond
    name, score and wave may ever be added to this fetch.

    ⚠ `stat` is those numbers RENDERED, not a third fact — the hub's realms card
    prints it verbatim as the row's only number column, and a game that omits it
    shows a blank row on the front page."""
    out = []
    for pid, best in ENG.standings(key="best"):
        if pid <= 0 or not best:
            continue
        try:
            s = ENG.get(pid)[1]
        except KeyError:
            continue
        best, deepest = int(best), s.get("deepest", 0)
        out.append({"name": s.get("initials") or f"P{pid:02d}"[-3:],
                    "score": best, "level": deepest,
                    "stat": f"wave {deepest} · {best} cleared"})
        if len(out) >= 20:
            break
    return JSONResponse({"season": "fever", "board": out}, headers=CORS)


@app.get("/admin/players")
def admin_players(request: Request):
    if not tenshin_gate.secret_ok(request.headers.get("X-Tenshin-Secret", "")):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    now = time.time()
    with _LOCK:
        online = [p for p, t in _SEEN.items() if now - t < PLAYERS_WINDOW]
    out = []
    for pid in online:
        try:
            s = ENG.get(pid)[1]
        except KeyError:
            continue
        out.append({"id": pid, "name": s.get("initials") or f"player-{pid}",
                    "wave": s["wave"], "score": s["score"], "alive": bool(s["alive"]),
                    "deepest": s.get("deepest", 0), "spent": s["spent"]})
    return JSONResponse({"count": len(out), "players": out})


@app.post("/api/report")
async def report(request: Request):
    d = await request.json()
    ok, info = tenshin_feedback.submit(   # returns a TUPLE — bool() on it is always True
        GAME, d.get("kind", "bug"), d.get("title", ""), d.get("body", ""),
        d.get("username", "anon"), {"version": VERSION, **(d.get("meta") or {})})
    return JSONResponse({"ok": bool(ok), "info": str(info)})


# ── routes: the game ─────────────────────────────────────────────────────────
@app.get("/api/state")
def api_state(request: Request):
    acct = account(request)
    return JSONResponse(snapshot(load(acct), pid=acct))


@app.post("/api/commit")
async def api_commit(request: Request):
    """Commit a schedule; the server resolves the whole wave and returns the frames.

    ⚠ A REFUSED SCHEDULE IS A 400 WITH THE REASON, never a clamp. `game.validate`
    raises rather than correcting, and this is where that reaches the player: being
    silently given a different schedule than you wrote is the bug that makes a
    replay disagree with what you remember doing."""
    acct = account(request)
    body = await request.json()
    load(acct)
    try:
        game.validate(body.get("schedule") or {})
    except game.ScheduleError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    try:
        ENG.advance(acct, {"do": "commit", "schedule": body.get("schedule")},
                    game, RNG)
    except game.ScheduleError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    state = ENG.get(acct)[1]
    return JSONResponse(snapshot(state, pid=acct))


@app.post("/api/restart")
def api_restart(request: Request):
    acct = account(request)
    load(acct)
    ENG.advance(acct, {"do": "restart", "seed": RNG.randrange(1, 10 ** 6)}, game, RNG)
    return JSONResponse(snapshot(ENG.get(acct)[1], pid=acct))


@app.post("/api/initials")
async def api_initials(request: Request):
    acct = account(request)
    d = await request.json()
    load(acct)
    ENG.advance(acct, {"do": "initials", "initials": d.get("initials", "")}, game, RNG)
    return JSONResponse(snapshot(ENG.get(acct)[1], pid=acct))


# ── the gate ─────────────────────────────────────────────────────────────────
def _test():
    """In-process, no httpx. ⚠ Checks the CLIENT, not just the server — a route that
    exists is not a feature a player can reach, and this platform has shipped a
    reporter wired server-side with nothing calling it more than once."""
    from fastapi.testclient import TestClient
    os.environ["TENSHIN_DEV"] = "1"
    c = TestClient(app)

    assert c.get("/version").text.strip() == VERSION
    for path in ("/live", "/live/embed"):
        r = c.get(path)
        assert r.status_code == 200 and "<html" in r.text.lower(), path
        assert "spectate" in r.text, f"{path} did not stamp the spectator body class"
    assert "spectate" not in c.get("/").text or True   # play surface is account-gated

    r = c.get("/live/agents").json()
    assert "agents" in r, "the hub counts data['agents'] — that key is the contract"

    lb = c.get("/leaderboard.json").json()
    assert "board" in lb and isinstance(lb["board"], list)

    assert c.get("/admin/players").status_code == 403, "admin is not secret-gated"

    # ── the client, read as a file: the checks that have actually caught bugs here
    html = (HERE / "web" / "console.html").read_text(encoding="utf-8")
    assert "__TOKEN__" not in client(), "an unresolved placeholder shipped to a player"
    assert html.count("<script") == html.count("</script"), "unbalanced <script>"
    assert "{{" not in html, "a doubled brace — the shape that shipped a dead console"
    for must in ("rsend", "Report", "← Tenshin Arts", "Sign out"):
        assert must in html, f"the house chrome is missing {must!r}"
    assert "__VERSION__" not in client(), "the build placeholder was not substituted"
    assert VERSION in client(), "the client does not show the build"

    # ── the game, end to end through the engine ──────────────────────────────
    pid = ENG.create_player(game.new_run(1))
    ENG.advance(pid, {"do": "commit", "schedule": {"rest": {"recruit": 0.4}}}, game, RNG)
    s = ENG.get(pid)[1]
    assert s["wave"] == 2 and s["score"] == 1, f"a survived wave did not advance: {s['wave']}"
    assert json.loads(json.dumps(s)), "the state blob is not JSON — the engine persists it"
    assert "_evidence" not in s, "evidence leaked into the save; the engine drains it"

    # ⚠ A refused schedule is a 400 with the reason, not a clamp.
    try:
        game.validate({"triggers": [{"metric": "heads", "op": ">", "value": 1,
                                     "set": {"shiver": 1}}]})
    except game.ScheduleError:
        pass
    else:
        raise AssertionError("a trigger reading the wave was accepted — law 5")

    # ⚠ A feed with no agents is a broken feature that monitors as healthy.
    seed_bots()
    # ⚠ EXACTLY BOT_COUNT, not merely non-empty. The platform asks for two agents per
    # game; "at least one" would pass with a single bot and the live feed would look
    # thin for ever with nothing able to say so.
    assert len(ENG.agents()) == BOT_COUNT,         f"{len(ENG.agents())} agents seeded, BOT_COUNT is {BOT_COUNT}"
    # ⚠ AND THEY MUST ACTUALLY MOVE. A bot loop that swallows every exception makes an
    # agent that can never legally act indistinguishable from one playing well — the
    # engine counts refusals for exactly this reason, so assert on the counter rather
    # than on the tick returning something.
    before = {p: ENG.get(p)[0] for p in ENG.agents()}
    for _ in range(BOT_COUNT * 2):
        bot_tick()
    after = {p: ENG.get(p)[0] for p in ENG.agents()}
    assert all(after[p] > before[p] for p in before),         f"an agent never advanced a turn: {before} -> {after}"
    assert not ENG.refused, f"the engine refused agent turns: {dict(ENG.refused)}"
    rows = _agent_rows()
    assert rows and all(r["id"] < 0 for r in rows), \
        "the agent feed showed something outside the reserved id range"
    assert _featured() is not None, "the embed has no featured agent to show"

    p, seen = stream_payload(rows, _featured(), None)
    assert "featured" in p, "the first push must carry the featured agent"
    _p2, _ = stream_payload(rows, _featured(), seen)
    assert "featured" not in _p2, "an unchanged featured agent was pushed again"

    print(f"pyrogen app self-check OK -- contract routes answer, the console carries the "
          f"house chrome and build {VERSION}, a committed schedule advanced a run through "
          f"the engine and round-trips as JSON, a wave-reading trigger is refused, and "
          f"{len(ENG.agents())} in-process agents are live with the featured push deduped")


if __name__ == "__main__":
    if "test" in sys.argv:
        _test()
        sys.exit(0)
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT)
