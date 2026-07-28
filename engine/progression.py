"""Progression — turns raw mastery into a curriculum and a difficulty curve.

Game-agnostic. Sits on a CompetencyTracker (the evidence store) and a
CompetencyMap (what the game teaches, with tiers and prerequisites) and answers
the questions a game-that-teaches actually needs:

  * What band is the player in on each competency?  (unproven → mastered)
  * What has the player UNLOCKED? — a competency opens only once its
    prerequisites are demonstrated (proficient+). You aren't assessed on
    investing before you've shown you can budget. This is curriculum order,
    enforced by evidence, not by a menu.
  * What should the game do NEXT? — `focus()` names the weakest *active*
    competency so the deck can lean toward it (adaptive difficulty).
  * How far has the player come? — `level()` / `rank()` give a player-facing
    sense of progress without ever showing a grade.

Mastery bands need CONFIDENCE, not just a point estimate: one lucky month can't
promote you. A competency stays "unproven" until there's enough evidence to
claim anything.
"""

_BANDS = ("unproven", "novice", "developing", "proficient", "mastered")
_RANK = {b: i for i, b in enumerate(_BANDS)}
_MIN_CONFIDENCE = 0.25            # below this, the estimate is "unproven"
_PROFICIENT = _RANK["proficient"]


def band(m):
    """Map a mastery estimate (from CompetencyTracker.mastery) to a band."""
    if m["confidence"] < _MIN_CONFIDENCE:
        return "unproven"
    if m["mastery"] >= 0.85:
        return "mastered"
    if m["mastery"] >= 0.65:
        return "proficient"
    if m["mastery"] >= 0.45:
        return "developing"
    return "novice"


class Progression:
    def __init__(self, tracker, comp_map):
        self.t = tracker
        self.m = comp_map

    def status(self, player_id, now_month=None):
        """Full picture: per competency, the (decay-adjusted) mastery estimate +
        band + whether its prerequisites are met (unlocked) + its tier. Pass
        `now_month` so stale skills fade — that's what makes mastery revert and
        drives spaced repetition below."""
        bands = {c.id: band(self.t.mastery(player_id, c.id, now_month)) for c in self.m}
        out = {}
        for c in self.m:
            est = self.t.mastery(player_id, c.id, now_month)
            # THE GATE IS ONE-WAY. Prerequisites decide when a competency is
            # INTRODUCED; they do not get to un-introduce it. Once there is
            # evidence against a competency it stays unlocked forever, even if a
            # prereq later decays out of proficient.
            #
            # Why (from what the player lives, not what is cheapest): a two-way
            # gate re-locks a tier-3 skill the moment a tier-2 prereq fades, and
            # the game then (1) stops recording evidence for it — because the
            # game only emits for unlocked competencies — while (2) decay keeps
            # running. So a player who invests every single month watches
            # "compound growth" FALL. Measured before this fix on a synthetic
            # 240-month run: 0.988 -> 0.746 while the behaviour never changed.
            # That teaches "practising a skill makes you worse at it", which is
            # a lie, and it is the same class of defect as the debt_payoff rule
            # Dr. Ray killed. Merely stopping decay (option a) freezes the number
            # instead — still wrong, and focus() still refuses to steer there.
            # Dropping the gate entirely (option b) throws away curriculum order,
            # which is the point of the tier map. One-way is the only option that
            # keeps the order AND keeps the readout honest.
            unlocked = (est["opportunities"] > 0
                        or all(_RANK[bands[p]] >= _PROFICIENT for p in c.prereqs))
            out[c.id] = {**est, "band": bands[c.id], "unlocked": unlocked, "tier": c.tier}
        return out

    def unlocked(self, player_id, now_month=None):
        return [cid for cid, v in self.status(player_id, now_month).items() if v["unlocked"]]

    def active(self, player_id, now_month=None):
        """Unlocked but not yet mastered — what the game should keep testing. A
        skill that decays out of 'mastered' re-enters here: spaced repetition."""
        return [cid for cid, v in self.status(player_id, now_month).items()
                if v["unlocked"] and v["band"] != "mastered"]

    def mastered(self, player_id, now_month=None):
        return [cid for cid, v in self.status(player_id, now_month).items()
                if v["band"] == "mastered"]

    def focus(self, player_id, now_month=None):
        """The competency to steer the next turn toward: the weakest active one,
        computed on DECAYED mastery — so an overdue-for-review skill (its mastery
        faded) outranks a freshly-practiced one. Spaced repetition falls out of
        this for free. None if everything unlocked is mastered."""
        st = self.status(player_id, now_month)
        active = [(cid, v) for cid, v in st.items()
                  if v["unlocked"] and v["band"] != "mastered"]
        if not active:
            return None
        return min(active, key=lambda kv: (kv[1]["mastery"], kv[1]["confidence"]))[0]

    def level(self, player_id, now_month=None):
        """Player-facing level = how many competencies are currently mastered."""
        return len(self.mastered(player_id, now_month))

    def rank(self, player_id, titles, now_month=None):
        """A title for the current level (clamped to the titles list)."""
        return titles[min(self.level(player_id, now_month), len(titles) - 1)]


def _self_check():
    import sqlite3
    from engine.competency import Competency, CompetencyMap, CompetencyTracker

    cmap = CompetencyMap([
        Competency("budget", "Budget", "", tier=1),
        Competency("save", "Save", "", tier=2, prereqs=("budget",)),
        Competency("invest", "Invest", "", tier=3, prereqs=("save",)),
    ])
    db = sqlite3.connect(":memory:")
    prog = Progression(CompetencyTracker(db), cmap)

    # Nothing shown yet: only the prereq-free competency is unlocked.
    assert prog.unlocked(1) == ["budget"]
    assert prog.focus(1) == "budget"
    assert prog.level(1) == 0

    # Master budgeting -> saving unlocks; investing stays gated behind saving.
    for _ in range(12):
        prog.t.record(1, "budget", 1.0)
    st = prog.status(1)
    assert st["budget"]["band"] == "mastered", st["budget"]
    assert st["save"]["unlocked"] and not st["invest"]["unlocked"]
    assert prog.level(1) == 1
    assert prog.focus(1) == "save"           # the new frontier, not the mastered one

    # One good month can't promote (confidence gate).
    prog.t.record(2, "budget", 1.0)
    assert prog.status(2)["budget"]["band"] == "unproven"

    # Spaced repetition: a mastered skill left unpracticed decays out of
    # 'mastered' and re-enters the active set to be re-drilled.
    for _ in range(15):
        prog.t.record(9, "budget", 1.0, month=1)
    assert prog.status(9, now_month=1)["budget"]["band"] == "mastered"
    assert prog.status(9, now_month=80)["budget"]["band"] != "mastered"
    assert "budget" in prog.active(9, now_month=80)

    # THE GATE IS ONE-WAY (2026-07-26). A player who mastered budget -> save ->
    # invest and then let budget go stale must NOT have invest re-locked: the
    # game emits evidence only for unlocked competencies, so re-locking silences
    # a skill the player is still practising and leaves decay to eat it. Drive it
    # exactly as vested.money does — only record what is unlocked.
    for m in range(1, 13):
        for c in ("budget", "save", "invest"):
            prog.t.record(11, c, 1.0, month=m)
    for m in range(13, 200):                       # keeps investing, stops budgeting
        if "invest" in prog.unlocked(11, now_month=m):
            prog.t.record(11, "invest", 1.0, month=m)
    late = prog.status(11, now_month=199)
    assert late["budget"]["band"] == "unproven", late["budget"]   # the prereq really did fade
    assert late["invest"]["unlocked"], "a practised skill must not re-lock behind a faded prereq"
    assert late["invest"]["mastery"] > 0.9, late["invest"]        # and so it must not decay
    # ...but a competency with NO evidence is still gated by its prereqs.
    assert not prog.status(12)["save"]["unlocked"], "the gate still holds for un-introduced skills"

    print(f"engine.progression self-check OK — a 3-tier ladder opens one rung at a time "
          f"(budget, then save, never invest), one good month cannot promote, a mastered skill "
          f"left 79 months goes {prog.status(9, now_month=1)['budget']['band']}->"
          f"{prog.status(9, now_month=80)['budget']['band']} and re-enters the active set — and "
          f"THE GATE IS ONE-WAY: after 199 months the faded prereq reads "
          f"{late['budget']['band']} while the practised skill it unlocked still reads "
          f"{late['invest']['mastery']:.2f} and stays unlocked")


if __name__ == "__main__":
    _self_check()
