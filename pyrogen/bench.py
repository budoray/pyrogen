"""The bench — and it exists to try to KILL this game before a client does.

Queue item 1: *answer question 1 with a bench, before writing a client. One pool,
two axes, a table showing the better answer changes by wave. If it does not, this
game is Titer with a HUD and should be stopped here — that is a cheap failure now
and an expensive one after a client exists.*

⚠ BUDGET FOR THE BENCHMARK BEING WRONG. Ember Down caught three rounds where the
benchmark was measuring itself rather than the game. Every measurement below is
therefore made against a CONTROL that must come out a known way, and the controls
are asserted before any result is believed:
  · a wave nobody answers must not be cleared  (or "clearing" is free)
  · the two answers must face the IDENTICAL wave (or the table compares dice)
  · spending everything must lose to spending nothing (law 2, on both axes)

    python -m pyrogen.bench            # the tables
    python -m pyrogen.bench --check    # the gate: assert, print one line
"""
import random
import sys

from pyrogen import catalog, physiology as phys, selection as sel
from pyrogen import run

# ⚠⚠ THE BEAT LOOP AND ITS CONSTANTS MOVED TO `pyrogen/run.py` (2026-07-31) AND ARE
# RE-EXPORTED HERE UNCHANGED. They were defined in this file when the bench was the
# only thing that resolved a wave; the server resolves one too, and two copies of the
# two-channel asymmetry is exactly the shape where a balance change moves one and not
# the other — with both still printing confident numbers. The bench now measures the
# same forty lines the player plays. ★ Re-exported rather than rewritten at each use
# site so this file reads as it did and the tables it certifies are byte-identical;
# `metrics/founding-questions.txt` is the regression test for that claim.
BEATS = run.BEATS
FEVER_KILL = run.FEVER_KILL

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
LOAD_O2 = run.LOAD_O2        # oxygen the fight costs, per living individual per beat
LOAD_GLU = run.LOAD_GLU      # glucose the fight costs, per living individual per beat
ORGAN_PER_HEAD = run.ORGAN_PER_HEAD  # damage per living individual per beat, unanswered

# The policies. A policy is a function (body) -> drives: it may react to the body,
# never to the wave — the player cannot see genomes either.
#
# ⚠⚠ THE TWO ANSWERS BEING COMPARED MUST BE COMPETENT PLAY, NOT MAXED PLAY, and
# the first version of this file got that wrong in a way worth keeping written
# down. Both were pinned at 1.0 for all 30 beats, so both flatlined in every wave
# (organ > ORGAN_LIMIT before the wave ended) and both left the same survivors —
# which made selection DRIFT rather than pressure, and the no-fever run finished
# with MORE heat tolerance than the fever run. The bench was measuring law 2,
# which it also measures on purpose two functions below, instead of the question.
#
# So these close the loop: push until it is dangerous, then back off. That is what
# a player who has read the body does, and it is the only comparison that means
# anything. `everything` stays pinned at 1.0 because it is the CONTROL that must
# die — its job is to lose.
# ⚠⚠ REWRITTEN 2026-08-01, AND THIS IS THE THIRD ROUND OF THE SAME MISTAKE.
# Round one: both policies pinned at full drive, so both flatlined and selection
# became drift. Round two: the oxygen stressor scaled with total hp, so everything
# died at wave 1. Round three: these two backed off their DRIVE but still sat above
# the response's oxygen cliff and still carried `glycogenolysis: 0.45`, so BOTH DIED
# in every run — and nothing here asserted otherwise, because the only viability
# assertions were on the two CONTROLS. Two answers that both die look identical, and
# a comparison between them measures the harness.
# ★ The rule this keeps re-teaching: the policies being COMPARED must be competent
# play, and "competent" has to be checked, not asserted in a comment. `_self_check`
# now requires every compared policy to finish alive.
# ⚠ Levels are under the oxygen cliff: demand is 3.4 + 2.6*shiver against delivery
# 4.90, so shiver breaks even at 0.507 and anything above it drowns the body.
# ⚠ Both now FUND THEMSELVES from the store when blood sugar falls, rather than
# carrying a flat `glycogenolysis: 0.45`. That flat draw was doing all the paying in
# the old Q1 result — the two axes looked like they traded off, and what actually
# traded off was a sugar release they happened to share.
POLICIES = {
    "nothing":    lambda b: {},
    # hold a fever below the oxygen cliff, and pay for it when the sugar runs down
    "systemic":   lambda b: {"shiver": 0.35 if b["temp"] < 38.6 else 0.0,
                             "glycogenolysis": 0.4 if b["glucose"] < 4.6 else 0.0},
    # recruit until inflammation has eaten half the viability, then stop
    "local":      lambda b: {"recruit": 0.45 if b["organ"] < 3.0 else 0.0,
                             "glycogenolysis": 0.4 if b["glucose"] < 4.6 else 0.0},
    "everything": lambda b: {k: 1.0 for k in phys.RESPONSES},
}


def resolve(wave, policy, seed=0):
    """One wave, one policy — `pyrogen.run.resolve`, which the SERVER also calls.

    ⚠ The pathogen is damaged by two SEPARATE channels with different reach:
    fever touches every individual at once and is blunted per-genome by `heat`;
    recruitment is a fixed clearance pool spent on whoever is in front and is
    blunted per-genome by `clear`. That asymmetry IS the merge — collapse them
    into one number and there is nothing to choose between.

    ⚠ `seed` is accepted and unused, as it always was: the resolution is
    deterministic given the wave and the policy. It stays in the signature because
    callers pass it positionally and removing it would be a silent argument shift.
    """
    return run.resolve(wave, policy)


def q1_table(waves=8, seed=11):
    """QUESTION 1 — the price of a local and a systemic answer to the SAME wave.

    ⚠ Both policies face a wave spawned from the SAME pool with the SAME rng
    draw. Without that this table compares two different waves and says nothing.
    The pool advances on the SYSTEMIC history, because that is the history in
    which the question is interesting: it is the one that breeds heat tolerance.
    """
    rng_pool = random.Random(seed)
    pool = sel.seed_pool()
    rows = []
    for n in range(1, waves + 1):
        wave = sel.spawn_wave(pool, n, random.Random(seed * 100 + n))
        syst = resolve(wave, POLICIES["systemic"])
        loc = resolve(wave, POLICIES["local"])
        rows.append({
            "wave": n,
            "heat_shock": sel.frequencies(pool).get("heat_shock", 0.0),
            "capsule": sel.frequencies(pool).get("capsule", 0.0),
            "sys_left": syst["survived"], "sys_spent": syst["spent"],
            "loc_left": loc["survived"], "loc_spent": loc["spent"],
            # The better answer: fewer survivors wins; substrate breaks a tie.
            "better": ("systemic" if syst["survived"] < loc["survived"] else
                       "local" if loc["survived"] < syst["survived"] else
                       "systemic" if syst["spent"] <= loc["spent"] else "local"),
        })
        pool = sel.next_pool(syst["individuals"])
        rng_pool.random()
    return rows


def q2_crossover(waves=14, seed=5):
    """QUESTION 2 — fever-every-wave must BEAT no-fever early and LOSE to it by
    wave N, and the crossover must come from selection alone.

    Two independent histories: each policy breeds its own pool, which is the
    whole point — the fever run selects for heat tolerance and the other does not.
    """
    out = []
    runs = {}
    for name in ("systemic", "local"):
        pool, rows = sel.seed_pool(), []
        for n in range(1, waves + 1):
            wave = sel.spawn_wave(pool, n, random.Random(seed * 1000 + n))
            r = resolve(wave, POLICIES[name])
            rows.append(r)
            pool = sel.next_pool(r["individuals"])
        runs[name] = (rows, sel.frequencies(pool))
    for n in range(waves):
        s, l = runs["systemic"][0][n], runs["local"][0][n]
        out.append({"wave": n + 1, "sys_left": s["survived"], "loc_left": l["survived"],
                    "sys_organ": s["organ"], "loc_organ": l["organ"]})
    return out, runs["systemic"][1], runs["local"][1]


def law2():
    """LAW 2 — spending everything must lose to spending nothing, on both axes.
    Corpus's arithmetic, carried across the merge."""
    wave = sel.spawn_wave(sel.seed_pool(), 3, random.Random(3))
    return {k: resolve(wave, POLICIES[k]) for k in ("nothing", "everything")}


def _check():
    # ── controls first. A result is not believed until these come out right. ──
    wave = sel.spawn_wave(sel.seed_pool(), 4, random.Random(4))
    idle = resolve(wave, POLICIES["nothing"])
    assert idle["survived"] == idle["of"], \
        f"a wave nobody answered lost {idle['of'] - idle['survived']} — clearing is free somewhere"
    assert idle["spent"] <= 0.01, f"doing nothing spent {idle['spent']} substrate"
    # ⚠ THE CONTROL THAT WAS MISSING, and whose absence made every number above
    # it meaningless: an unanswered wave must HURT the body without killing it.
    # If doing nothing already flatlines, every policy flatlines, both answers
    # look equally bad, and selection degenerates into drift.
    assert idle["alive"], \
        (f"an unanswered wave 4 killed the body outright ({idle['organ']} damage) — "
         "there is no room for an answer to be better than another")
    assert idle["organ"] > 0.5, \
        f"an unanswered wave cost the body only {idle['organ']} — it is not a threat"

    # ⚠⚠ THE ASSERTION THIS BENCH NEVER HAD, and whose absence let three separate
    # rounds of broken comparison certify an answer. `nothing` and `everything` are
    # CONTROLS and their viability is asserted above; the two policies actually being
    # COMPARED were never checked at all, and in round three both died in every run.
    # Two answers that both flatline look identical, so the comparison measures the
    # harness rather than the game. This is the check that catches the whole class.
    for _name in ("systemic", "local"):
        _r = resolve(wave, POLICIES[_name])
        assert _r["alive"], (
            f"the '{_name}' policy KILLED THE BODY ({_r['organ']} damage). A policy that "
            "dies is not competent play, and comparing two of them measures nothing. "
            "Fix the policy or the balance before reading any answer below.")

    a = resolve(wave, POLICIES["systemic"])
    b = resolve(wave, POLICIES["systemic"])
    assert a["survived"] == b["survived"] and a["spent"] == b["spent"], \
        "the same policy on the same wave gave two answers — the bench is not deterministic"

    l2 = law2()
    assert l2["everything"]["organ"] > l2["nothing"]["organ"], \
        "spending everything cost less than spending nothing (law 2)"
    assert not l2["everything"]["alive"], "a body at full drive on every response survived"

    # ── question 1: does the better answer CHANGE with the wave? ──
    rows = q1_table()
    winners = {r["better"] for r in rows}
    # ⚠⚠ THIS FIRES AS OF 2026-08-01 AND IT IS TELLING THE TRUTH. It was green only
    # while both compared policies died (see the viability assertion above) and while
    # both carried a flat `glycogenolysis: 0.45` that was doing all the paying — the
    # two axes looked like they traded off, and what traded off was a shared sugar
    # release. Make the policies competent and the systemic answer wins EVERY wave.
    # ⚠ Verified across a sweep of both families before accepting it, because a weak
    # `local` policy would be the same mistake again: recruit at 0.35/0.45/0.60/0.75
    # with cutoffs 2.5–4.0 all leak survivors from wave 2 (3, 6, 7, 10, 13 …) at ~130
    # substrate, against a fever that clears to zero for eight waves at ~20.
    # ★ QUESTION 2 STILL HOLDS — fever collapses at wave 9–10 once heat resistance is
    # bred, which is the crossover Q2 asks for. It is Q1 that fails: the LOCAL answer
    # is dominated everywhere, not merely late. Recruitment's throughput is a pool
    # spent front-to-back while a fever reaches every individual at once, so the two
    # are not priced against each other at all.
    # ⚠ DO NOT MAKE THIS GREEN BY WEAKENING IT. A kill switch that gets softened when
    # it fires is the failure mode this whole file exists to prevent. The choice —
    # reprice the local answer, or accept that the merge's premise needs restating —
    # is Dr. Ray's, and it is written up in IMPROVEMENTS.md.
    assert winners == {"systemic", "local"}, (
        "THE MERGE FAILS QUESTION 1: the better answer was always "
        f"{winners.pop()} across {len(rows)} waves. One pool, two axes, and no "
        "tradeoff between them — this is Titer with a HUD. Stop here.")
    flip = next(i for i in range(1, len(rows)) if rows[i]["better"] != rows[i - 1]["better"])

    # ── question 2: fever wins early and loses late, from selection alone ──
    q2, sys_freq, loc_freq = q2_crossover()
    early = q2[0]
    late = [r for r in q2 if r["sys_left"] > r["loc_left"]]
    assert early["sys_left"] <= early["loc_left"], \
        f"fever did not beat the local answer on wave 1 ({early})"
    assert late, ("THE MERGE FAILS QUESTION 2: fever-every-wave never lost to "
                  "no-fever. It is simply the best button and selection never bit.")
    n_cross = late[0]["wave"]
    assert sys_freq.get("heat_shock", 0.0) > loc_freq.get("heat_shock", 0.0), \
        ("heat tolerance did not come from holding fevers — if the fever run and "
         "the no-fever run breed the same pool, the crossover is a difficulty ramp")

    print(f"pyrogen.bench self-check OK -- controls held (an unanswered wave lost "
          f"0 of {idle['of']}, and full drive took {l2['everything']['organ']:.0f} "
          f"damage against {l2['nothing']['organ']:.0f} for doing nothing, and died); "
          f"question 1 ANSWERED: the better answer flips at wave {flip + 1} and both "
          f"win somewhere across {len(rows)} waves; question 2 ANSWERED: fever wins "
          f"wave 1 and loses from wave {n_cross}, with heat-shock at "
          f"{sys_freq.get('heat_shock', 0):.0%} of the fever run's pool against "
          f"{loc_freq.get('heat_shock', 0):.0%} of the no-fever run's -- so the "
          f"crossover was bred, not scripted")


def _report():
    print("QUESTION 1 -- the same wave, answered two ways")
    print(f"{'wave':>4} {'heat%':>6} {'caps%':>6} | {'sys left':>8} {'spent':>6} |"
          f" {'loc left':>8} {'spent':>6} | better")
    for r in q1_table():
        print(f"{r['wave']:>4} {r['heat_shock']:>6.0%} {r['capsule']:>6.0%} |"
              f" {r['sys_left']:>8} {r['sys_spent']:>6.1f} |"
              f" {r['loc_left']:>8} {r['loc_spent']:>6.1f} | {r['better']}")
    print("\nQUESTION 2 -- fever every wave vs never, independent histories")
    q2, sf, lf = q2_crossover()
    print(f"{'wave':>4} | {'fever left':>10} {'organ':>6} | {'local left':>10} {'organ':>6}")
    for r in q2:
        print(f"{r['wave']:>4} | {r['sys_left']:>10} {r['sys_organ']:>6.1f} |"
              f" {r['loc_left']:>10} {r['loc_organ']:>6.1f}")
    print(f"\nfinal pools -- fever run: {sf}\n              local run: {lf}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        _check()
    else:
        _report()
        print()
        _check()
