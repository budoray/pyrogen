"""The learning layer — game-agnostic stealth assessment.

Vested is a game that promotes learning, NOT a teaching app: there are no
quizzes. Mastery is *inferred from the decisions a player makes in play* and the
consequences they live with. This module is how every Tenshin game does that.

The contract:
  * A game declares WHAT it teaches as a competency map (id -> description) —
    data, not code. This module never knows what "emergency_fund" means.
  * During a turn the game emits EVIDENCE: (competency_id, success 0..1, weight)
    — "the player was in a situation that tests this, and here's how well they
    did." A car repair that wiped them out is weak evidence for `emergency_fund`;
    absorbing it from savings is strong evidence.
  * This module tracks mastery per (player, competency) with a Beta-Bernoulli
    model (a uniform prior, updated by weighted successes/failures). That gives
    both a point estimate AND a confidence that grows with evidence.

Two things read the result, both game-serving — not a gradebook:
  * `mastery()` -> the instructor dashboard (a decision-informed picture of each
                   student, per SPEC.md §5; aggregated per-cohort in vested/bots).
  * `weakest()` -> ADAPTIVITY: the game biases what happens next toward what the
                   player hasn't shown yet. The knowledge check IS a mechanic.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Competency:
    """One thing a game teaches. Declared by the game as DATA; the engine never
    interprets `id` — it only tracks evidence against it and orders by tier."""
    id: str
    name: str
    description: str = ""
    tier: int = 1                       # curriculum layer (1 = foundations)
    prereqs: tuple = ()                 # competency ids that must be proficient first


DECAY = 0.97   # monthly retention: unpracticed mastery fades back toward the prior


class CompetencyMap:
    """An ordered set of competencies — the game's curriculum. Iteration order
    is declaration order (kept stable for reports)."""

    def __init__(self, competencies):
        self._by_id = {c.id: c for c in competencies}
        self.ids = tuple(self._by_id)

    def __iter__(self):
        return iter(self._by_id.values())

    def __getitem__(self, cid):
        return self._by_id[cid]

    def __len__(self):
        return len(self._by_id)


class CompetencyTracker:
    """Beta-Bernoulli mastery per (player, competency). Shares a game's SQLite
    connection so evidence lives alongside player state."""

    def __init__(self, db, lock=None):
        import threading
        self.db = db
        self.lock = lock or threading.RLock()   # shared with TurnEngine when web-served
        db.execute(
            """CREATE TABLE IF NOT EXISTS competency(
                   player_id     INTEGER NOT NULL,
                   comp          TEXT    NOT NULL,
                   alpha         REAL    NOT NULL DEFAULT 1.0,
                   beta          REAL    NOT NULL DEFAULT 1.0,
                   opportunities INTEGER NOT NULL DEFAULT 0,
                   last_month    INTEGER,
                   PRIMARY KEY (player_id, comp))"""
        )
        db.commit()

    def record(self, player_id, comp, success, weight=1.0, month=None):
        """Log one piece of evidence. success in [0,1]; weight scales how much
        this moment counts (a real emergency counts more than a quiet month)."""
        success = max(0.0, min(1.0, float(success)))
        with self.lock:
            row = self.db.execute(
                "SELECT alpha, beta, opportunities FROM competency WHERE player_id=? AND comp=?",
                (player_id, comp),
            ).fetchone()
            a, b, opp = row if row else (1.0, 1.0, 0)
            a += weight * success
            b += weight * (1.0 - success)
            opp += 1
            self.db.execute(
                """INSERT INTO competency(player_id, comp, alpha, beta, opportunities, last_month)
                       VALUES(?,?,?,?,?,?)
                   ON CONFLICT(player_id, comp) DO UPDATE SET
                       alpha=excluded.alpha, beta=excluded.beta,
                       opportunities=excluded.opportunities, last_month=excluded.last_month""",
                (player_id, comp, a, b, opp, month),
            )
            self.db.commit()

    def mastery(self, player_id, comp, now_month=None):
        """Estimate for one competency: mastery (posterior mean), confidence
        (grows with evidence), how many chances the player has had, and how stale
        it is. Pass `now_month` to apply DECAY — a skill unpracticed for `stale`
        months has its evidence shrunk back toward the uniform prior, so both
        mastery and confidence fade until it's refreshed."""
        with self.lock:
            row = self.db.execute(
                "SELECT alpha, beta, opportunities, last_month FROM competency WHERE player_id=? AND comp=?",
                (player_id, comp),
            ).fetchone()
        if row is None:
            return {"mastery": 0.5, "confidence": 0.0, "opportunities": 0, "stale": 0}
        a, b, opp, last = row
        stale = 0
        if now_month is not None and last is not None and now_month > last:
            stale = now_month - last
            f = DECAY ** stale                          # forgetting curve
            a = 1.0 + (a - 1.0) * f
            b = 1.0 + (b - 1.0) * f
        evidence = (a + b) - 2.0                         # weighted evidence seen
        return {
            "mastery": a / (a + b),
            "confidence": evidence / (evidence + 4.0),   # shrinkage toward 0
            "opportunities": opp,
            "stale": stale,
        }

    def weakest(self, player_id, comps):
        """The competency to steer the game toward: lowest mastery, breaking
        ties toward the one with the least evidence (least confidence)."""
        best = None
        for c in comps:
            m = self.mastery(player_id, c)
            key = (m["mastery"], m["confidence"])    # low mastery, then low conf
            if best is None or key < best[1]:
                best = (c, key)
        return best[0] if best else None


def _self_check():
    import sqlite3

    db = sqlite3.connect(":memory:")
    t = CompetencyTracker(db)
    COMPS = ["budgeting", "emergency_fund", "fraud_avoidance"]

    # No evidence -> prior, and weakest falls back deterministically.
    assert t.mastery(1, "budgeting") == {"mastery": 0.5, "confidence": 0.0,
                                         "opportunities": 0, "stale": 0}

    # Demonstrate budgeting repeatedly; fail emergency_fund a couple of times.
    for _ in range(8):
        t.record(1, "budgeting", 1.0)
    t.record(1, "emergency_fund", 0.0, weight=2.0)
    t.record(1, "emergency_fund", 0.0, weight=2.0)

    assert t.mastery(1, "budgeting")["mastery"] > 0.8, "shown mastery should be high"
    assert t.mastery(1, "emergency_fund")["mastery"] < 0.3, "repeated failure shows a gap"
    # The game should steer toward the demonstrated gap...
    assert t.weakest(1, COMPS) == "emergency_fund"
    # ...over budgeting, which they've shown, and fraud, which has no evidence.
    assert t.mastery(1, "budgeting")["confidence"] > t.mastery(1, "fraud_avoidance")["confidence"]

    # Decay: a skill shown only early fades if it's never refreshed.
    for _ in range(10):
        t.record(3, "budgeting", 1.0, month=1)
    fresh = t.mastery(3, "budgeting", now_month=1)
    faded = t.mastery(3, "budgeting", now_month=60)
    assert faded["mastery"] < fresh["mastery"], (faded, fresh)
    assert faded["confidence"] < fresh["confidence"]
    assert faded["stale"] == 59
    print(f"engine.competency self-check OK — 8 successes read mastery "
          f"{t.mastery(1, 'budgeting')['mastery']:.2f} and 2 weighted failures read "
          f"{t.mastery(1, 'emergency_fund')['mastery']:.2f}, so the game steers at the gap; "
          f"a skill shown once at month 1 and never again decays "
          f"{fresh['mastery']:.2f}->{faded['mastery']:.2f} over {faded['stale']} stale months")


if __name__ == "__main__":
    _self_check()
