"""The async-turn engine core — game-agnostic.

The engine owns: a per-player state store (SQLite), the month counter, cohorts,
and turn resolution *mechanics*. It does NOT know what a turn means — a `game`
object supplies that via `resolve_turn(state, action, rng) -> new_state`.

    engine = TurnEngine(":memory:")
    pid = engine.create_player(vested.money.new_life(goal=25_000))
    engine.advance(pid, action, game=vested.money, rng=random.Random(1))

Player state is an opaque JSON blob (game-specific), so a new game is a new
`resolve_turn` — the engine changes not at all. See SPEC.md §5.
"""
import json
import sqlite3
import threading
from collections import Counter

from engine.competency import CompetencyTracker
from engine.progression import Progression


class TurnEngine:
    def __init__(self, db_path=":memory:", comp_map=None):
        # check_same_thread=False + one shared re-entrant lock: a web server runs
        # sync endpoints in a threadpool AND an in-process bot ticker in another
        # thread, so the single connection is used from many threads. The lock
        # serializes every DB touch (engine + competency tracker).
        # ponytail: one global lock, fine at this scale; per-thread connections
        # if write throughput ever matters.
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.RLock()
        # pid -> turns this process asked for and the game refused. See advance().
        self.refused: Counter[int] = Counter()
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS players(
                   id     INTEGER PRIMARY KEY AUTOINCREMENT,
                   cohort TEXT    NOT NULL DEFAULT 'default',
                   month  INTEGER NOT NULL DEFAULT 0,
                   is_bot INTEGER NOT NULL DEFAULT 0,
                   state  TEXT    NOT NULL)"""
        )
        self.db.commit()
        # The learning layer rides along on the same connection + lock. A game
        # that declares a competency map also gets progression for free.
        self.comp = CompetencyTracker(self.db, self.lock)
        self.progression = Progression(self.comp, comp_map) if comp_map else None

    def create_player(self, initial_state, cohort="default", is_bot=False):
        with self.lock:
            cur = self.db.execute(
                "INSERT INTO players(cohort, is_bot, state) VALUES(?,?,?)",
                (cohort, int(is_bot), json.dumps(initial_state)),
            )
            self.db.commit()
            pid = cur.lastrowid
            assert pid is not None, "INSERT did not yield a rowid"
            return pid

    def ensure_player(self, pid, initial_state, cohort="default"):
        """Get-or-create a player at an EXPLICIT positive id (e.g. a Tenshin
        account id), so a web client can key saves by account without a mapping
        table. No-op if the row already exists."""
        with self.lock:
            if self.db.execute("SELECT 1 FROM players WHERE id=?", (pid,)).fetchone() is None:
                self.db.execute("INSERT INTO players(id, cohort, is_bot, state) VALUES(?,?,0,?)",
                                (pid, cohort, json.dumps(initial_state)))
                self.db.commit()
            return pid

    def create_bot(self, initial_state, cohort="default"):
        """Create a bot in the RESERVED negative-id range. Human players get
        positive autoincrement ids, so a `/live` feed that reads only id < 0
        (see `agents`) can structurally never show a real player — the safety
        rule is a shape, not a filter someone has to remember (contract §3)."""
        with self.lock:
            row = self.db.execute("SELECT MIN(id) FROM players WHERE id < 0").fetchone()
            next_id = (row[0] - 1) if row and row[0] is not None else -1
            self.db.execute(
                "INSERT INTO players(id, cohort, is_bot, state) VALUES(?,?,1,?)",
                (next_id, cohort, json.dumps(initial_state)),
            )
            self.db.commit()
            return next_id

    def agents(self, cohort="default"):
        """The `/live`-safe set: bot ids only (the reserved negative range)."""
        with self.lock:
            rows = self.db.execute(
                "SELECT id FROM players WHERE id < 0 AND cohort=? ORDER BY id DESC", (cohort,)
            ).fetchall()
        return [r[0] for r in rows]

    def retire_bot(self, pid, cohort="default"):
        """Remove one bot and hand back its FINAL STATE, or None if it was not a bot.

        The state comes back rather than being dropped because an agent's run is the only
        thing it was ever for: it is retired when its TTL expires, and what it did — how far
        it got, what it scored, how long it lived — is the data the retirement exists to
        collect. Returning it here means the caller cannot forget to read it first, which a
        `delete_bot()` would invite every single time.

        ⚠ THE `id < 0` GUARD IS THE POINT, not a filter that can be forgotten: bots live in
        the reserved negative range (see `create_bot`), so this can never delete a real
        player's save even if handed their id by a bug or a crafted request. Same shape as
        `agents()`, for the same reason (contract §3)."""
        with self.lock:
            row = self.db.execute(
                "SELECT state FROM players WHERE id=? AND id < 0 AND cohort=?", (pid, cohort)
            ).fetchone()
            if row is None:
                return None
            self.db.execute("DELETE FROM players WHERE id=? AND id < 0", (pid,))
            self.db.commit()
        return json.loads(row[0])

    def roster(self, cohort="default"):
        """Everyone in a cohort (humans + bots) — the admin/instructor view."""
        with self.lock:
            rows = self.db.execute(
                "SELECT id, state FROM players WHERE cohort=?", (cohort,)
            ).fetchall()
        return [(pid, json.loads(s)) for pid, s in rows]

    def get(self, pid):
        """Return (month, state) for a player. Raises KeyError if unknown."""
        with self.lock:
            row = self.db.execute(
                "SELECT month, state FROM players WHERE id=?", (pid,)
            ).fetchone()
        if row is None:
            raise KeyError(pid)
        return row[0], json.loads(row[1])

    def advance(self, pid, action, game, rng):
        """Resolve ONE turn. The engine persists and ticks the month; `game`
        decides what the turn does to the state — and may emit stealth-assessment
        evidence via the reserved `_evidence` key, which the engine drains into
        the competency tracker and does not persist into the state blob."""
        with self.lock:
            month, state = self.get(pid)
            # ⚠ COUNT WHAT THE GAME REFUSED, then re-raise unchanged.
            #
            # Every caller of this method swallows the refusal, in three spellings:
            # `contextlib.suppress(ValueError)` in five seed_bots, a bare
            # `except Exception: pass`, and `except Exception as e: print(...)`
            # around a whole bot tick. Each is defensible on its own — a bot
            # stumble must not kill the world — and together they mean a bot that
            # can NEVER legally act is indistinguishable from one playing well.
            # Two repos worked that out separately, from the symptom.
            #
            # The fix is not to stop the callers swallowing; it is for the
            # PRIMITIVE to self-report, so no caller has to remember. `refused` is
            # in-memory on purpose: it answers "is this agent stuck right now",
            # which is a question about the running process, not about the save.
            try:
                state = game.resolve_turn(state, action, rng)
            except Exception:
                self.refused[pid] += 1
                raise
            month += 1
            for comp, success, weight in state.pop("_evidence", []):
                self.comp.record(pid, comp, success, weight, month)
            self.db.execute(
                "UPDATE players SET month=?, state=? WHERE id=?",
                (month, json.dumps(state), pid),
            )
            self.db.commit()
            return month, state

    # --- progression wrappers: pass the player's CURRENT month as "now" so the
    #     decay/spaced-repetition read is automatic wherever the game asks. -----
    @property
    def _prog(self) -> Progression:
        if self.progression is None:
            raise RuntimeError("this engine has no competency map — no learning layer")
        return self.progression

    def status(self, pid):
        return self._prog.status(pid, now_month=self.get(pid)[0])

    def unlocked(self, pid):
        return self._prog.unlocked(pid, now_month=self.get(pid)[0])

    def focus(self, pid):
        return self._prog.focus(pid, now_month=self.get(pid)[0])

    def level(self, pid):
        return self._prog.level(pid, now_month=self.get(pid)[0])

    def rank(self, pid, titles):
        return self._prog.rank(pid, titles, now_month=self.get(pid)[0])

    def standings(self, cohort="default", key="net_worth"):
        """Cohort leaderboard: [(pid, value)] high→low, reading `key` from state.
        Generic — the engine sorts on a state field it doesn't interpret.

        ⚠ RESTORED 2026-07-25. This was removed when Vested cut its multiplayer
        modes, which is a Vested product decision — but this file is the SHARED
        engine, and Nullroute's public leaderboard runs on it
        (`ENG.standings(key="credits")`). The vendored copies had not been synced,
        so nothing broke; the next `dropins.sh sync` would have taken Nullroute's
        /leaderboard.json down with an AttributeError.

        The rule the near-miss earns: **`engine/` is game-agnostic, so one game no
        longer calling a method is not a reason to delete it.** Check the other
        carriers first — `grep -rn "ENG\\.<method>" ../*/ --include=*.py`."""
        with self.lock:
            rows = self.db.execute(
                "SELECT id, state FROM players WHERE cohort=?", (cohort,)
            ).fetchall()
        scored = [(pid, json.loads(s).get(key, 0)) for pid, s in rows]
        return sorted(scored, key=lambda r: r[1], reverse=True)


def _self_check():
    """A trivial game proves the engine is game-agnostic: it just counts."""
    import random

    class CountGame:
        @staticmethod
        def resolve_turn(state, action, rng):
            state["n"] = state.get("n", 0) + action
            return state

    eng = TurnEngine(":memory:")
    pid = eng.create_player({"n": 0})
    rng = random.Random(0)
    for _ in range(5):
        eng.advance(pid, 2, CountGame, rng)
    month, state = eng.get(pid)
    assert month == 5, month
    assert state["n"] == 10, state
    assert eng.roster() == [(pid, {"n": 10})], eng.roster()
    # standings is carried for the other packs, so it needs a test HERE — an
    # untested shared method is the one that gets deleted again
    assert eng.standings(key="n")[0] == (pid, 10), eng.standings(key="n")

    # reserved-range safety: bots are negative, humans positive; the live feed
    # (agents) can only ever return bots.
    human = eng.create_player({"n": 0})
    bot = eng.create_bot({"n": 0})
    assert human > 0 and bot < 0, (human, bot)
    assert eng.agents() == [bot], eng.agents()

    # ── retiring a bot returns its run, and CANNOT touch a human ──────────────
    # An agent is retired when its TTL expires and its final state is the data
    # the retirement exists to collect, so the two are one call. Both directions
    # are asserted: a human id must be refused even when passed deliberately,
    # because the negative-range guard is the only thing standing between a
    # crafted admin request and somebody's save.
    doomed = eng.create_bot({"n": 7})
    assert eng.retire_bot(doomed) == {"n": 7}, "retiring must hand back the run"
    assert doomed not in eng.agents(), "a retired bot is still on the live feed"
    assert eng.retire_bot(doomed) is None, "retiring twice must be a no-op, not a crash"
    assert eng.retire_bot(human) is None, "a HUMAN id was accepted by retire_bot"
    assert eng.get(human) == (0, {"n": 0}), "retire_bot deleted a human player's save"

    # ── refusals are COUNTED even when the caller swallows them ───────────────
    # This is the whole point of the counter, so it is tested the way the callers
    # actually behave — inside a `suppress`, which is one of the three spellings
    # in the fleet — and NOT by watching the exception, which no caller sees.
    class RefusingGame:
        @staticmethod
        def resolve_turn(state, action, rng):
            raise ValueError("that move is not legal")

    import contextlib
    stuck = eng.create_bot({"n": 0})
    before_month, before_state = eng.get(stuck)
    for _ in range(3):
        with contextlib.suppress(ValueError):
            eng.advance(stuck, 1, RefusingGame, rng)
    assert eng.refused[stuck] == 3, eng.refused
    # ...and a refused turn changed NOTHING: not the month, not the state, and
    # not some other player's counter.
    assert eng.get(stuck) == (before_month, before_state), eng.get(stuck)
    assert eng.refused[pid] == 0, "a refusal was charged to the wrong player"
    # the exception still reaches a caller that wants it — the counter is an
    # addition, not a swallow, and a primitive that ate the error would be worse
    # than the callers that do
    raised = False
    try:
        eng.advance(stuck, 1, RefusingGame, rng)
    except ValueError:
        raised = True
    assert raised, "advance() swallowed the refusal instead of re-raising"
    assert eng.refused[stuck] == 4, eng.refused
    # a turn the game ACCEPTS must not be counted
    eng.advance(stuck, 2, CountGame, rng)
    assert eng.refused[stuck] == 4 and eng.get(stuck)[0] == before_month + 1

    print(f"engine.turns self-check OK — {month} turns advanced one month each, standings "
          f"sorts on a field it never interprets, bots sit below zero and humans above, and "
          f"{eng.refused[stuck]} refusals were counted through a caller that swallowed them")


if __name__ == "__main__":
    _self_check()
