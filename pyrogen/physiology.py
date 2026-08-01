"""The body — ported from Corpus, conservation intact, extended by one thing.

⚠ THE ONE EXTENSION IS THE WHOLE MERGE: recruiting immune cells draws on the
SAME finite glycogen store that every systemic response draws on. In Titer,
placement had its own invented currency; here it does not, and that deletion is
the claim the design record's question 1 asks us to prove or abandon.

⚠ CONSERVATION: nothing in this module may CREATE anything. Heat made by
shivering is paid for in glucose; released sugar comes out of glycogen; cells
recruited come out of the same store. Conservation is what lets a player reason
about a tradeoff instead of memorising which button helps.

⚠ The body already regulates itself; the player MODULATES it. Each balance below
nets to zero at rest, so a resting body does not drift — without that, every run
is a race against the model rather than against the pathogen, and no response the
player makes can be read as theirs.
"""
SETPOINTS = {
    "map_":    {"lo": 45.0,  "hi": 135.0, "ok": (70.0, 105.0), "name": "Pressure"},
    "spo2":    {"lo": 0.72,  "hi": 1.01,  "ok": (0.92, 1.0),   "name": "Saturation"},
    "temp":    {"lo": 31.0,  "hi": 41.5,  "ok": (36.2, 37.8),  "name": "Core temp"},
    "glucose": {"lo": 2.5,   "hi": 18.0,  "ok": (4.0, 8.0),    "name": "Blood sugar"},
    "ph":      {"lo": 7.05,  "hi": 7.65,  "ok": (7.34, 7.45),  "name": "Acid-base"},
}

RESPONSES = {
    "vasoconstrict":  {"name": "Vasoconstrict"},
    "tachycardia":    {"name": "Drive the heart"},
    "hyperventilate": {"name": "Breathe harder"},
    "glycogenolysis": {"name": "Release sugar"},
    "shiver":         {"name": "Shiver"},
    "vasodilate":     {"name": "Vasodilate & sweat"},
    # THE LOCAL ANSWER. Priced in the same units as everything above.
    "recruit":        {"name": "Recruit cells"},
}

O2_CAP = 1.0
BASE_DEMAND = 3.4
BASE_HEAT = 3.0
BASE_GLU = 0.16
NORMAL_VOLUME = 5.0
ORGAN_LIMIT = 6.0

# What one beat of full recruitment costs and buys. ⚠ These two numbers are the
# price of the LOCAL answer, and question 1 lives exactly here: if the systemic
# answer is better at every price, the merge has failed at its only job.
RECRUIT_GLYCOGEN = 3.0      # substrate drawn per beat at full drive
RECRUIT_CLEARANCE = 9.0     # hp of pathogen cleared per beat at full drive
RECRUIT_INFLAMMATION = 0.22  # ⚠ the local answer damages the body too (autoimmunity)


def new_body():
    return {
        "map_": 88.0, "spo2": 0.98, "temp": 37.0, "glucose": 5.4, "ph": 7.40,
        "volume": NORMAL_VOLUME,
        "glycogen": 100.0,      # conserved: the ONLY source of sugar AND of cells
        "co2": 40.0,
        "debt": 0.0,
        "organ": 0.0,
        "hr": 70.0,
        "periphery": 1.0,
        "cells": 0.0,           # cells standing at the site right now
    }


def delivery(b):
    """⚠ A PRODUCT — carried × pumped × saturated — so any one at zero is zero,
    and no response conjures delivery out of a body that has bled out."""
    return O2_CAP * b["spo2"] * (b["volume"] / NORMAL_VOLUME) * (b["hr"] / 70.0) * 5.0


def demand(b, drives, stressor):
    d = BASE_DEMAND + stressor.get("o2", 0.0)
    d += 2.6 * drives.get("shiver", 0.0)
    d += 1.5 * drives.get("tachycardia", 0.0)
    d += 0.8 * drives.get("hyperventilate", 0.0)
    d += 1.1 * drives.get("recruit", 0.0)     # cells are metabolically expensive
    return d


def _hepatic(b):
    return min(1.0, b["glycogen"] / 40.0)


def _vent(b):
    return min(1.0, max(0.0, b["map_"] / 70.0))


def step(b, drives, stressor):
    """One beat. Mutates `b`, returns (events, clearance_available).

    ⚠ The ORDER is the ruleset: the insult lands, then the responses the player
    committed, then the balances settle, then the damage clock. A response always
    answers a stressor that has ALREADY happened — triage, not prediction.
    """
    ev = []
    g = lambda k: max(0.0, min(1.0, float(drives.get(k, 0.0))))

    # 1 · the insult lands
    b["volume"] = max(0.5, b["volume"] - stressor.get("bleed", 0.0))
    b["temp"] += stressor.get("heat", 0.0)
    b["glucose"] = max(0.1, b["glucose"] + stressor.get("sugar", 0.0))

    # 2 · the responses, each paid for out of the pool it is protecting
    tone = 1.0 + 0.55 * g("vasoconstrict") - 0.45 * g("vasodilate")
    b["hr"] = 70.0 + 62.0 * g("tachycardia") - 6.0 * g("vasodilate")
    b["periphery"] = max(0.05, 1.0 - 0.75 * g("vasoconstrict"))

    want = 2.4 * g("glycogenolysis")
    got = min(want, b["glycogen"])
    b["glycogen"] -= got
    b["glucose"] += got * 0.9
    if want > got + 0.01:
        ev.append({"t": "empty", "what": "glycogen"})

    # ⚠ THE MERGE, in four lines. Recruitment is bought from the same store, and
    # it is REFUSED when the store cannot pay — there is no overdraft, because an
    # overdraft is how a conserved quantity quietly stops being conserved.
    want_c = RECRUIT_GLYCOGEN * g("recruit")
    paid_c = min(want_c, b["glycogen"])
    b["glycogen"] -= paid_c
    b["cells"] = paid_c / RECRUIT_GLYCOGEN if RECRUIT_GLYCOGEN else 0.0
    if want_c > paid_c + 0.01:
        ev.append({"t": "starved", "what": "recruitment"})

    # 3 · the balances
    dl, dm = delivery(b), demand(b, drives, stressor)
    gap = dm - dl
    if gap > 0:
        b["debt"] += gap
        b["spo2"] = max(0.35, b["spo2"] - 0.045 * gap)
    else:
        b["debt"] = max(0.0, b["debt"] + gap * 0.5)
        b["spo2"] = min(1.0, b["spo2"] + 0.05 * (-gap) + 0.06 * g("hyperventilate"))

    b["map_"] = 96.0 * tone * (b["volume"] / NORMAL_VOLUME) * (0.55 + 0.45 * b["hr"] / 70.0)

    made = BASE_HEAT + 3.4 * g("shiver") + stressor.get("work", 0.0)
    lost = (BASE_HEAT + 2.2 * g("vasodilate") + 0.9 * g("hyperventilate")) * b["periphery"] ** 0.35
    b["temp"] += (made - lost) * 0.09

    burn = (0.26 * g("shiver") + 0.14 * g("tachycardia")
            + 0.10 * g("recruit") + stressor.get("glu", 0.0))
    b["glucose"] = max(0.1, b["glucose"] - burn + BASE_GLU * _hepatic(b))
    b["glucose"] -= BASE_GLU
    b["glycogen"] = min(100.0, b["glycogen"] + 0.35)

    b["co2"] += 1.5 - 1.5 * _vent(b) - 1.6 * g("hyperventilate") + 0.5 * max(0.0, gap)
    b["co2"] = max(14.0, min(90.0, b["co2"]))
    b["ph"] = 7.40 - (b["co2"] - 40.0) * 0.0068 - min(0.30, b["debt"] * 0.012)

    # 4 · the damage clock, and the repair clock. ⚠ Damage must be RECOVERABLE or
    # a wave game is decided by its first bad beat.
    hurt = False
    for k, sp in SETPOINTS.items():
        v = b[k]
        if v < sp["lo"] or v > sp["hi"]:
            b["organ"] += 0.6
            hurt = True
            ev.append({"t": "out", "k": k, "v": round(v, 2)})
    if b["periphery"] < 0.2:
        b["organ"] += 0.3
        hurt = True
        ev.append({"t": "ischaemia"})
    # ⚠ ONE DEATH, THREE ROUTES (question 4). Inflammation from recruitment is
    # damage on the SAME viability as a set-point running away — it is not a
    # second life bar. The replay names which route got there.
    if b["cells"] > 0.0:
        b["organ"] += RECRUIT_INFLAMMATION * b["cells"]
        hurt = True
        ev.append({"t": "inflammation", "n": round(RECRUIT_INFLAMMATION * b["cells"], 2)})
    # ⚠ THE PATHOGEN IS AN INSULT IN HERE, not damage a caller adds afterwards,
    # and the difference is not cosmetic: the repair clock below only runs when
    # nothing hurt this beat, so load applied after the step was silently healed
    # at 0.25/beat against its own 0.13. An unanswered wave read as no threat at
    # all — failure mode 3 in the design record, arriving through the seam
    # between two modules rather than through a number.
    if stressor.get("load", 0.0) > 0.0:
        b["organ"] += stressor["load"]
        hurt = True
        ev.append({"t": "load", "n": round(stressor["load"], 3)})
    if not hurt:
        b["organ"] = max(0.0, b["organ"] - 0.25)

    return ev, RECRUIT_CLEARANCE * b["cells"]


def fever_over(b):
    """Degrees above the top of the comfortable band. This is the SYSTEMIC
    answer's whole output, and it is deliberately a property of the body rather
    than a drive: a fever the player produced by shivering and a fever produced
    by the insult itself do the same thing to the pathogen."""
    return max(0.0, b["temp"] - SETPOINTS["temp"]["ok"][1])


def alive(b):
    return b["organ"] < ORGAN_LIMIT


def worst(b):
    """The set-point furthest out of its band. ⚠ For the FLATLINE REPLAY only —
    every death names which system failed. Never sent during play; reading the
    body is the game."""
    out = None
    for k, sp in SETPOINTS.items():
        lo, hi = sp["ok"]
        d = (lo - b[k]) if b[k] < lo else (b[k] - hi if b[k] > hi else 0.0)
        if out is None or d > out[1]:
            out = (k, d)
    return out


def _self_check():
    # ⚠ CONSERVATION, and it must fail if anything creates. Recruit at full drive
    # with nothing else running: the store must fall by what was drawn, no more
    # and no less, and the slow refill is the only thing putting any back.
    b = new_body()
    before = b["glycogen"]
    _ev, clear = step(b, {"recruit": 1.0}, {})
    drawn = before - b["glycogen"]
    assert abs(drawn - (RECRUIT_GLYCOGEN - 0.35)) < 1e-6, \
        f"recruitment drew {drawn}, not the {RECRUIT_GLYCOGEN} it was priced at"
    assert clear == RECRUIT_CLEARANCE, "a paid recruitment cleared nothing"

    # ...and it is REFUSED, not overdrawn, when the store cannot pay.
    b = new_body()
    b["glycogen"] = 1.0
    ev, clear = step(b, {"recruit": 1.0}, {})
    assert b["glycogen"] >= 0.0, "the glycogen store went negative — that is creation"
    assert any(e["t"] == "starved" for e in ev), "an unpayable recruitment was not reported"
    assert clear < RECRUIT_CLEARANCE, "an unpaid recruitment cleared full value"

    # ⚠ RULE 2 FROM CORPUS, AND IT MUST SURVIVE THE MERGE: maxing everything
    # loses. A body at full drive must take real damage where a resting one takes
    # none — otherwise brute force is viable and the game teaches reflex.
    rest = new_body()
    for _ in range(30):
        step(rest, {}, {})
    full = new_body()
    for _ in range(30):
        step(full, {k: 1.0 for k in RESPONSES}, {})
    assert rest["organ"] == 0.0, f"a resting body damaged itself ({rest['organ']})"
    assert full["organ"] > 20.0, f"full drive cost only {full['organ']} damage over 30 beats"
    assert not alive(full), "a body at full drive on every response survived"

    # Fever is a property of the BODY, not a flag: shivering produces it, and so
    # does an insult that brings its own heat.
    b1, b2 = new_body(), new_body()
    for _ in range(12):
        step(b1, {"shiver": 1.0}, {})
        step(b2, {}, {"heat": 0.12})
    assert fever_over(b1) > 0.0 and fever_over(b2) > 0.0, \
        "fever is not readable from the body alone"

    print(f"pyrogen.physiology self-check OK -- recruitment drew exactly "
          f"{RECRUIT_GLYCOGEN} substrate from the one store and was REFUSED rather "
          f"than overdrawn at 1.0 left; a resting body took {rest['organ']:.0f} damage "
          f"over 30 beats where full drive on all {len(RESPONSES)} responses took "
          f"{full['organ']:.0f} and flatlined; and {fever_over(b1):.2f}C of shivered "
          f"fever reads the same as {fever_over(b2):.2f}C the insult brought")


if __name__ == "__main__":
    _self_check()
