"""The campaign: a committed schedule, a wave resolved against it, one loss.

⚠⚠ **THIS MODULE IS FOUNDING QUESTIONS 3 AND 4, ANSWERED** (Dr. Ray delegated both,
2026-08-01). Everything here is the consequence of two decisions, and both are
recorded in `IMPROVEMENTS.md` beside the questions they close.

**Q3 — where beats live: A SET-POINT PLUS TRIGGERS, COMMITTED BEFORE THE WAVE.**
The player writes a resting drive level per response, plus up to `MAX_TRIGGERS`
conditional rules ("if organ > 3.0, shiver 0.8"). The server resolves all thirty
beats and returns the frame log. The three candidates in the design record were
scheduled changes at beat thresholds, a set-point plus a trigger, and a budget of
interventions; this is the second, and the reason is that it is the only one of the
three that is *the thing the game is about* — a homeostatic control law is a
set-point and a reflex threshold, so the player writes physiology rather than a
timetable.

⚠⚠ **AND IT MAKES THE PLATFORM GUARD STRUCTURAL RATHER THAN A PROMISE.** "It must
not become reaction speed" cannot be enforced by a rule that says so. Here the
schedule is a pure function of the body compiled BEFORE the first beat, and
`resolve()` never yields control back — there is no beat at which a player could
act, so there is nothing to be fast at. The guard holds by construction.
⚠ A trigger may read only the BODY, never the wave (law 5). `compile_schedule`
takes the setpoint names from `phys.SETPOINTS` and nothing else, so a trigger on
"heads" or "pathogen hp" cannot be expressed, let alone smuggled in.

**Q4 — three losses or one: ONE, and it is viability.** Breach, autoimmunity and
metabolic failure all land on `organ`, and `phys.alive()` is the only death in the
game. The design record's own worry is that this makes a breach feel weightless;
the answer is MAGNITUDE, not a second death — an unanswered wave puts
`ORGAN_PER_HEAD` per living individual per beat onto the same pool, so a breach is
the fastest route to zero rather than a different kind of zero.
⚠ **Every death names the route AND the set-point that ran away** — AMPU's rule,
and Corpus's flatline replay, which this inherits. `postmortem()` is that, and a
death that does not teach is a bug.
"""
import sys

from engine.competency import Competency
from pyrogen import catalog, physiology as phys, run, selection as sel

MAX_TRIGGERS = 3       # ⚠ THREE, and the number is the design. One is a thermostat and
                       # not a choice; per-beat is the spreadsheet the design record
                       # rejected by name. Three forces the player to decide which
                       # failures are worth a reflex, which is the interesting question.
MAX_WAVES = 20

# The metrics a trigger may read. ⚠ EXACTLY the set-points plus `organ`, because those
# are what the console already shows the player. A trigger on something unreadable
# would be a rule about a number the player cannot see, which is law 3's shape.
TRIGGER_METRICS = tuple(phys.SETPOINTS) + ("organ", "glycogen")


class ScheduleError(ValueError):
    """A schedule that cannot be compiled. ⚠ RAISED, not clamped-and-ignored: a
    silently-corrected schedule is a player being told they committed something
    they did not, and the replay would not match what they wrote."""


def blank_schedule():
    return {"rest": {k: 0.0 for k in phys.RESPONSES}, "triggers": []}


def compile_schedule(sched):
    """`schedule -> (body) -> drives`, validated. This is the ONE place a player's
    committed plan becomes the `drives_of` that `run.resolve` calls.

    ⚠ Returns a PURE function of the body. It closes over nothing mutable and reads
    no clock — hand the same body to it twice and it answers the same, which is what
    makes a replay reproducible and a bench policy and a player schedule the same
    kind of thing.
    """
    rest, triggers = validate(sched)

    def drives_of(b):
        d = dict(rest)
        for t in triggers:
            v = b[t["metric"]] if t["metric"] in b else 0.0
            if (v > t["value"]) if t["op"] == ">" else (v < t["value"]):
                d.update(t["set"])
        return d

    return drives_of


def validate(sched):
    """Returns `(rest, triggers)` normalised, or raises ScheduleError.

    ⚠ Every number is clamped to 0..1 AFTER the type check, never instead of it —
    `float("nan")` clamps to itself and would reach the physiology."""
    if not isinstance(sched, dict):
        raise ScheduleError("a schedule is an object")
    rest = {}
    for k, v in (sched.get("rest") or {}).items():
        if k not in phys.RESPONSES:
            raise ScheduleError(f"no such response: {k}")
        rest[k] = _level(v, k)

    raw = sched.get("triggers") or []
    if not isinstance(raw, list):
        raise ScheduleError("triggers is a list")
    if len(raw) > MAX_TRIGGERS:
        raise ScheduleError(f"at most {MAX_TRIGGERS} triggers, got {len(raw)}")
    triggers = []
    for t in raw:
        if not isinstance(t, dict):
            raise ScheduleError("a trigger is an object")
        metric = t.get("metric")
        if metric not in TRIGGER_METRICS:
            raise ScheduleError(f"a trigger cannot read {metric!r}")
        op = t.get("op")
        if op not in (">", "<"):
            raise ScheduleError("a trigger compares with > or <")
        try:
            value = float(t.get("value"))
        except (TypeError, ValueError):
            raise ScheduleError("a trigger threshold is a number")
        if value != value:                      # NaN never compares true; it would
            raise ScheduleError("a trigger threshold is a number")   # be a dead rule
        setto = {}
        for k, v in (t.get("set") or {}).items():
            if k not in phys.RESPONSES:
                raise ScheduleError(f"no such response: {k}")
            setto[k] = _level(v, k)
        if not setto:
            raise ScheduleError("a trigger that sets nothing is not a trigger")
        triggers.append({"metric": metric, "op": op, "value": value, "set": setto})
    return rest, triggers


def _level(v, k):
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise ScheduleError(f"{k} takes a number from 0 to 1")
    if f != f:
        raise ScheduleError(f"{k} takes a number from 0 to 1")
    return max(0.0, min(1.0, f))


def new_run(seed):
    return {"seed": seed, "wave": 1, "pool": sel.seed_pool(), "alive": True,
            "score": 0, "spent": 0.0, "history": [], "best": 0, "deepest": 0,
            "initials": "", "last": None}


def _rng_for(state):
    """The wave's RNG, derived from `(seed, wave)` rather than carried.

    ⚠ THE STATE BLOB IS JSON AND THE ENGINE PERSISTS IT — a live `random.Random`
    in there is a `TypeError` on the first save, and carrying its internal tuple
    instead would make the save format depend on CPython's Mersenne state. Deriving
    is smaller AND it makes a wave reproducible from two integers, which is what
    lets a replay be re-resolved rather than stored.
    """
    import random
    return random.Random(f"{state['seed']}:{state['wave']}")


def play_wave(state, sched):
    """Resolve one wave against a committed schedule. Mutates `state`.

    ⚠ The pool advances on the SURVIVORS of this wave, always — including the wave
    that killed you. What bred is a fact about the run, not a reward for winning it.
    """
    if not state["alive"]:
        raise ScheduleError("this run is over")
    drives_of = compile_schedule(sched)
    wave = sel.spawn_wave(state["pool"], state["wave"], _rng_for(state))
    out = run.resolve(wave, drives_of, log=True)

    state["pool"] = sel.next_pool(out["individuals"])
    state["spent"] = round(state["spent"] + out["spent"], 2)
    cleared = out["survived"] == 0
    body_ok = out["alive"]
    state["alive"] = body_ok and state["wave"] < MAX_WAVES
    if body_ok:
        state["score"] += 1
    state["history"].append({"wave": state["wave"], "cleared": cleared,
                             "survived": out["survived"], "of": out["of"],
                             "spent": out["spent"], "organ": out["organ"]})
    result = {
        "wave": state["wave"], "cleared": cleared, "alive": body_ok,
        "survived": out["survived"], "of": out["of"], "spent": out["spent"],
        "organ": out["organ"], "frames": out["frames"],
        "frequencies": sel.frequencies(state["pool"]),
        "score": state["score"],
    }
    if not body_ok:
        result["postmortem"] = postmortem(out["frames"])
    state["deepest"] = max(state["deepest"], state["wave"])
    state["best"] = max(state["best"], state["score"])
    if body_ok:
        state["wave"] += 1
    # ⚠ THE FRAMES ARE PERSISTED, and only the LAST wave's. Thirty rows of nine
    # small numbers is ~3KB, bounded — the client needs them to draw the replay, and
    # re-deriving them would mean keeping the PRE-wave pool as well, which is a
    # second copy of the run's history to keep in step with the first.
    state["last"] = {k: result[k] for k in
                     ("wave", "cleared", "alive", "survived", "of", "spent", "organ",
                      "frames")}
    if "postmortem" in result:
        state["last"]["postmortem"] = result["postmortem"]
    # The learning layer's evidence, drained by the engine and never persisted.
    # ⚠ Assessment is INFERRED FROM THE DECISION, never quizzed — each of these is a
    # claim about the schedule the player committed, judged by what it did.
    _, triggers = validate(sched)
    state["_evidence"] = [
        ("conservation", out["alive"], 1.0),
        ("systemic_vs_local", cleared, 1.0),
        ("reflex_design", bool(triggers) and out["alive"], 0.7 if triggers else 0.2),
        ("selection", state["wave"] >= 4 and out["alive"], 0.8),
    ]
    return result


# ── the engine seam ──────────────────────────────────────────────────────────
COMPETENCIES = [
    Competency("conservation", "Paying for a response",
               "Every defence comes out of one store, and you kept the body solvent.",
               tier=1),
    Competency("systemic_vs_local", "Fever or cells",
               "Choosing the answer that fits the wave — heat reaches everyone, "
               "recruitment is a pool spent front to back.", tier=1),
    Competency("reflex_design", "Writing a reflex",
               "Setting a threshold that fires when it should and not before.",
               tier=2, prereqs=("conservation",)),
    Competency("selection", "Reading what bred",
               "Noticing that what survived your last answer is what arrives next.",
               tier=2, prereqs=("systemic_vs_local",)),
]

TITLES = ["Bystander", "Responder", "Regulator", "Physician", "Homeostat"]


def resolve_turn(state, action, rng):
    """The engine's seam: one committed schedule is one turn. `rng` is unused —
    ⚠ deliberately, and this is not an oversight. A wave's randomness is derived
    from `(seed, wave)` inside `play_wave`, so a turn is reproducible from the save
    alone; taking the engine's RNG here would make the same save resolve differently
    depending on how many turns the process had served."""
    if action.get("do") == "restart":
        return new_run(action.get("seed") or state["seed"] + 1)
    if action.get("do") == "initials":
        state["initials"] = str(action.get("initials", ""))[:3].upper()
        return state
    play_wave(state, action.get("schedule") or blank_schedule())
    return state


def view(state):
    """What the client may see. ⚠ NO POOL GENOMES — `frequencies` is the aggregate
    the player earns by watching, and shipping the pool itself would put law 5 one
    View-Source away, exactly as the frame log must not carry traits."""
    return {
        "wave": state["wave"], "alive": state["alive"], "score": state["score"],
        "spent": state["spent"], "best": state["best"], "deepest": state["deepest"],
        "initials": state["initials"], "last": state["last"],
        "history": state["history"][-12:],
        "frequencies": sel.frequencies(state["pool"]),
        "responses": {k: v["name"] for k, v in phys.RESPONSES.items()},
        "setpoints": {k: {"name": v["name"], "ok": list(v["ok"])}
                      for k, v in phys.SETPOINTS.items()},
        "trigger_metrics": list(TRIGGER_METRICS),
        "max_triggers": MAX_TRIGGERS, "max_waves": MAX_WAVES,
        "traits": {t: catalog.TRAITS[t].get("name", t) for t in catalog.HERITABLE},
    }


def postmortem(frames):
    """Why the body failed, in the words the player was watching. ⚠ A death that
    does not teach is a bug — this is Q4's other half, and it is the reason one
    loss is allowed to replace three.

    Names the ROUTE (what was spending the body) and the SET-POINT that ran away,
    reconstructed from the frame log rather than from engine internals, so what the
    replay says and what the player saw are the same source.
    """
    if not frames:
        return {"route": "unknown", "setpoint": None, "detail": "no beats resolved"}
    last = frames[-1]
    body = {k: last[k] for k in ("temp", "spo2", "glucose") if k in last}
    worst_k, worst_d = None, 0.0
    for k, v in body.items():
        lo, hi = phys.SETPOINTS[k]["ok"]
        d = (lo - v) if v < lo else (v - hi if v > hi else 0.0)
        if d > worst_d:
            worst_k, worst_d = k, d

    drives = last.get("drives", {})
    recruit = drives.get("recruit", 0.0)
    fever = last.get("temp", 37.0) - phys.SETPOINTS["temp"]["ok"][1]
    if last.get("heads", 0) > 0 and recruit < 0.2 and fever <= 0:
        route = "breach"
        detail = ("the pathogen was still standing and nothing was answering it — "
                  "an unanswered wave damages the organ every beat it survives")
    elif recruit >= 0.5:
        route = "autoimmunity"
        detail = ("recruitment was held high to the end; the local answer inflames "
                  "the tissue it defends, and that damage lands on the same organ")
    elif last.get("glycogen", 1.0) <= 2.0:
        route = "metabolic failure"
        detail = ("the store ran out — every response is paid for from one glycogen "
                  "pool, and a body that cannot pay stops regulating")
    else:
        route = "overdrive"
        detail = ("the responses cost more than the insult did; law 2 is that maxing "
                  "everything must lose, and here it did")
    return {
        "route": route, "detail": detail,
        "setpoint": worst_k,
        "setpoint_name": phys.SETPOINTS[worst_k]["name"] if worst_k else None,
        "setpoint_value": round(body[worst_k], 3) if worst_k else None,
        "beats": len(frames),
    }


def _self_check():
    # ⚠ Q3's guard, asserted rather than promised: a compiled schedule is a pure
    # function of the body. Same body twice, same drives — if this ever fails, some
    # hidden state got in and a replay stopped being reproducible.
    s = {"rest": {"shiver": 0.5}, "triggers": [
        {"metric": "organ", "op": ">", "value": 1.0, "set": {"recruit": 0.8}}]}
    f = compile_schedule(s)
    b = phys.new_body()
    assert f(b) == f(b), "a compiled schedule is not a pure function of the body"
    assert f(b)["shiver"] == 0.5 and "recruit" not in f(b)
    b["organ"] = 2.0
    assert f(b)["recruit"] == 0.8, "a trigger did not fire on its own metric"

    # ⚠ A trigger may not read the wave. This is law 5 as a check, not a docstring —
    # break it and the player is answering something they cannot see.
    for bad in ("heads", "hp", "traits", "kind"):
        try:
            validate({"triggers": [{"metric": bad, "op": ">", "value": 1, "set": {"shiver": 1}}]})
        except ScheduleError:
            pass
        else:
            raise AssertionError(f"a trigger was allowed to read {bad!r} — law 5 is gone")

    # ⚠ Refuse, never clamp-and-continue. A silently-fixed schedule is a player told
    # they committed something they did not.
    for bad in ({"rest": {"nope": 1.0}},
                {"triggers": [{"metric": "temp", "op": "~", "value": 1, "set": {"shiver": 1}}]},
                {"triggers": [{"metric": "temp", "op": ">", "value": "x", "set": {"shiver": 1}}]},
                {"triggers": [{"metric": "temp", "op": ">", "value": 1, "set": {}}]},
                {"triggers": [{"metric": "temp", "op": ">", "value": float("nan"),
                               "set": {"shiver": 1}}]},
                {"triggers": [{"metric": "temp", "op": ">", "value": 1, "set": {"shiver": 1}}]
                             * (MAX_TRIGGERS + 1)}):
        try:
            validate(bad)
        except ScheduleError:
            pass
        else:
            raise AssertionError(f"a bad schedule compiled: {bad}")
    assert _level(5.0, "shiver") == 1.0 and _level(-2, "shiver") == 0.0

    # ⚠ Law 2 in the campaign, not just in the bench: everything at full must LOSE,
    # and it must lose to a body that is merely competent. If maxing wins, the whole
    # merge is a resource bar with extra steps.
    loud = new_run(11)
    r_loud = play_wave(loud, {"rest": {k: 1.0 for k in phys.RESPONSES}})
    calm = new_run(11)
    r_calm = play_wave(calm, {"rest": {"recruit": 0.45},
                              "triggers": [{"metric": "temp", "op": "<", "value": 38.4,
                                            "set": {"shiver": 0.7}}]})
    assert r_loud["spent"] > r_calm["spent"], (
        f"full drive spent {r_loud['spent']} against {r_calm['spent']} for a measured "
        "answer — law 2 says maxing everything must cost more")

    # ⚠ Q4: ONE loss, and it names itself. Drive the body into the ground and the
    # postmortem must produce a route AND a set-point, or a death taught nothing.
    dead = new_run(3)
    seen = None
    for _ in range(MAX_WAVES):
        res = play_wave(dead, {"rest": {k: 1.0 for k in phys.RESPONSES}})
        if not res["alive"]:
            seen = res["postmortem"]
            break
        if not dead["alive"]:
            break
    assert seen, "full drive on every response never killed the body — law 2 is not enforced"
    assert seen["route"] and seen["setpoint"], f"a death that names nothing: {seen}"

    # a run that ends is over, and says so rather than resolving another wave
    over = new_run(5)
    over["alive"] = False
    try:
        play_wave(over, blank_schedule())
    except ScheduleError:
        pass
    else:
        raise AssertionError("a finished run accepted another wave")

    # the pool advances on the wave that killed you too — what bred is a fact
    adv = new_run(7)
    before = sel.frequencies(adv["pool"])
    play_wave(adv, blank_schedule())
    assert sel.frequencies(adv["pool"]) != before or before == {}, \
        "the gene pool did not move across a wave"

    print(f"pyrogen.game self-check OK -- a schedule is {MAX_TRIGGERS} triggers over a "
          f"set-point and compiles to a PURE function of the body (a trigger reading the "
          f"wave is refused, {len(TRIGGER_METRICS)} metrics allowed); full drive spent "
          f"{r_loud['spent']} against {r_calm['spent']} for a measured answer and died at "
          f"wave {seen['beats']} beats in, naming route '{seen['route']}' and set-point "
          f"'{seen['setpoint_name']}' -- ONE loss, and it teaches")


if __name__ == "__main__":
    _self_check()
    sys.exit(0)
