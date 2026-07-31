"""One wave, resolved beat by beat — the ONE place the two channels are spent.

⚠⚠ **THIS EXISTS SO THE ASYMMETRY HAS EXACTLY ONE IMPLEMENTATION.** The merge's
whole justification is that a threat has a local answer and a systemic answer that
cost different things (CLAUDE.md, *the one new mechanic*): fever reaches every
individual at once and is blunted per-genome by `heat`; recruitment is a finite
clearance pool spent front-to-back and is blunted per-genome by `clear`. Collapse
them into one number and there is nothing to choose between.

`bench.py` proved that asymmetry and the founding questions rest on its numbers.
A server that re-implemented the same loop would be a SECOND copy of the thing the
bench certified — and the first balance change would move one and not the other,
silently, with both still printing confident numbers. So the bench calls this too:
what the gate measured and what a player plays are the same forty lines.

★ The reason this is a separate module rather than a function in `bench.py`: the
bench is a *harness*, and a server importing its harness would make the harness a
runtime dependency — which is how a `--check` flag ends up shipping. The game core
belongs under the game.

⚠ **NOTHING HERE MAY CREATE ANYTHING** (law 1, conservation). Substrate is spent,
never minted; this module reads the body through `physiology` and never writes a
store directly.

⚠ **`drives_of` MAY NOT SEE THE WAVE** (law 5). It takes the body and nothing else,
which is the same blindness the player has — they cannot read genomes either. A
schedule the player committed and a bench policy are both just `(body) -> drives`,
which is why one resolver serves both.

    python -m febrile.run          # self-check
"""
import sys

from febrile import catalog, physiology as phys

BEATS = 30            # beats in one wave. Corpus's number, so the 39-damage
                      # arithmetic in the design record stays comparable.
FEVER_KILL = 5.2      # pathogen hp cleared per degree of fever per beat

# ⚠ WHAT AN UNANSWERED PATHOGEN DOES TO THE BODY, and these three numbers are
# HARNESS, not game. The first version coupled the oxygen stressor to total hp
# (`o2: 0.02 * load`), which at wave 1 already put demand above delivery on its
# own: saturation hit its floor in two beats, the organ clock ran for the other
# twenty-eight, and EVERY policy flatlined. Two answers that both die look
# identical, so selection became drift and the no-fever run bred MORE heat
# tolerance than the fever run — a result about my arithmetic, not about the game.
#
# Scaled per individual rather than per hp, and sized against a control that is
# now asserted: an unanswered wave 1 must hurt the body WITHOUT killing it. If
# doing nothing is already fatal there is no room for an answer to be better.
LOAD_O2 = 0.03        # oxygen the fight costs, per living individual per beat
LOAD_GLU = 0.004      # glucose the fight costs, per living individual per beat
ORGAN_PER_HEAD = 0.012  # damage per living individual per beat, unanswered


def resolve(wave, drives_of, log=False):
    """One wave, one way of answering it. Returns what it cost and what it bought.

    `drives_of` is `(body) -> drives` — a bench policy or a player's committed
    schedule, and it may react to the body but never to the wave.

    `log=True` additionally returns `frames`: one row per beat, which is what the
    client projects. ⚠ The log is a RECORD of the resolution, never an input to it —
    if computing it could change a number, the spectator feed and the player's own
    replay would disagree with the score.
    """
    b = phys.new_body()
    living = [dict(p) for p in wave]
    start_glycogen = b["glycogen"]
    frames = []
    for _beat in range(BEATS):
        heads = sum(1 for p in living if p["hp"] > 0)
        drives = drives_of(b)
        _ev, clearance = phys.step(b, drives,
                                   {"o2": LOAD_O2 * heads, "glu": LOAD_GLU * heads,
                                    "load": ORGAN_PER_HEAD * heads})
        if not phys.alive(b):
            if log:
                frames.append(_frame(b, living, drives, dead=True))
            break

        # systemic: reaches everyone, blunted per genome
        deg = phys.fever_over(b)
        if deg > 0:
            for p in living:
                if p["hp"] > 0:
                    p["hp"] -= FEVER_KILL * deg * catalog.stat(p["traits"], "heat")

        # local: a finite pool spent front-to-back, blunted per genome
        pool = clearance
        for p in living:
            if pool <= 0:
                break
            if p["hp"] <= 0:
                continue
            eff = catalog.stat(p["traits"], "clear")
            if eff <= 0:
                continue
            spend = min(pool, p["hp"] / eff)
            p["hp"] -= spend * eff
            pool -= spend

        if log:
            frames.append(_frame(b, living, drives))

    for p in living:
        p["survived"] = p["hp"] > 0
    out = {
        "survived": sum(1 for p in living if p["survived"]),
        "of": len(living),
        "spent": round(start_glycogen - b["glycogen"], 2),
        "organ": round(b["organ"], 2),
        "alive": phys.alive(b),
        "individuals": living,
    }
    if log:
        out["frames"] = frames
    return out


def _frame(b, living, drives, dead=False):
    """One beat as the client sees it.

    ⚠ **NO GENOMES.** The client is a projector and the player cannot read genomes —
    shipping traits in the frame log would put law 5's blindness one View-Source away.
    Heads and total hp are the front; what is IN it is not the player's to see.
    """
    return {
        "temp": round(b["temp"], 2),
        "spo2": round(b["spo2"], 3),
        "glucose": round(b["glucose"], 3),
        "glycogen": round(b["glycogen"], 2),
        "organ": round(b["organ"], 2),
        "drives": {k: round(v, 2) for k, v in drives.items() if v},
        "heads": sum(1 for p in living if p["hp"] > 0),
        "hp": round(sum(p["hp"] for p in living if p["hp"] > 0), 1),
        "dead": dead,
    }


def _self_check():
    from febrile import selection as sel
    import random

    rng = random.Random(4)
    wave = sel.spawn_wave(sel.seed_pool(), 1, rng)

    nothing = resolve(wave, lambda b: {})
    assert nothing["survived"] == nothing["of"], (
        f"an unanswered wave lost {nothing['of'] - nothing['survived']} of {nothing['of']} "
        "— if clearing is free there is nothing to pay for")

    # ⚠ The log must be a RECORD, never an input. Same wave, same answer, logged and
    # unlogged: every number the score is made of has to match, or the replay a
    # spectator watches is not the run that scored.
    def _sched(b):
        return {"shiver": 1.0 if b["temp"] < 39.6 else 0.0, "glycogenolysis": 0.45}

    quiet = resolve(wave, _sched)
    loud = resolve(wave, _sched, log=True)
    for k in ("survived", "of", "spent", "organ", "alive"):
        assert quiet[k] == loud[k], f"logging changed {k}: {quiet[k]} vs {loud[k]}"
    assert loud["frames"], "log=True produced no frames"
    assert len(loud["frames"]) <= BEATS

    # ⚠ The frame log may not carry genomes — law 5 is not a docstring.
    for f in loud["frames"]:
        assert "traits" not in f and "individuals" not in f, (
            "a frame carried the genomes the player is not allowed to read")

    fevered = sum(1 for f in loud["frames"] if f["temp"] >= 38.0)
    print(f"febrile.run self-check OK -- an unanswered wave of {nothing['of']} lost none, "
          f"and a systemic answer to the same wave ran {len(loud['frames'])} beats "
          f"({fevered} of them febrile) for {loud['spent']} substrate, leaving "
          f"{loud['survived']} of {loud['of']} -- logged and unlogged agree on every "
          "number the score is made of")


if __name__ == "__main__":
    _self_check()
    sys.exit(0)
