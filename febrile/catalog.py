"""The ONE loader, and the only place assertions about what is IN the data live.

Same rule as Corpus's catalog: every assertion here must be breakable by editing
a real data file. `assert len(TRAITS) > 0` is worse than nothing — it makes the
gate look like it checks content while it checks that a file parsed.
"""
import pathlib

import yaml

HERE = pathlib.Path(__file__).parent
TRAITS = yaml.safe_load((HERE / "data" / "traits.yaml").read_text(encoding="utf-8"))
HERITABLE = sorted(TRAITS)


def stat(traits, key):
    """Multiplicative, so two traits that each halve something quarter it. A
    genome with nothing carries 1.0 and is the baseline the bench compares to."""
    v = 1.0
    for t in traits:
        v *= float(TRAITS[t].get(key, 1.0))
    return v


def dominant(traits):
    return traits[0] if traits else "unmarked"


def _self_check():
    # ⚠ Each of these fails on a real edit to traits.yaml, which is the point.
    assert HERITABLE, "no traits at all — selection has nothing to select on"

    # The two answers must each have something that resists them, or the merge's
    # whole claim (two axes that trade off) has nothing to trade off against.
    heat_resistant = [t for t in HERITABLE if TRAITS[t].get("heat", 1.0) < 1.0]
    clear_resistant = [t for t in HERITABLE if TRAITS[t].get("clear", 1.0) < 1.0]
    assert heat_resistant, "nothing resists fever — the systemic answer never stops working"
    assert clear_resistant, "nothing resists recruitment — the local answer never stops working"

    # ⚠ A trait that resisted BOTH would be a dead end rather than a choice: no
    # answer to it, so the wave carrying it is decided by dice.
    for t in HERITABLE:
        assert not (TRAITS[t].get("heat", 1.0) < 1.0 and TRAITS[t].get("clear", 1.0) < 1.0), \
            f"{t} resists both answers — that is unanswerable, not difficult"

    # `earliest` gates only what may be INVENTED. A trait that could mutate in on
    # wave 1 and beats an answer the player cannot afford yet decides the run.
    for t in heat_resistant + clear_resistant:
        assert TRAITS[t].get("earliest", 1) >= 2, \
            f"{t} can mutate in on wave 1, before the player has met the answer to it"

    assert stat([], "heat") == 1.0, "the unmarked baseline is not 1.0"
    assert stat(["heat_shock"], "heat") < 1.0, "heat_shock does not blunt fever"
    print(f"febrile.catalog self-check OK -- {len(HERITABLE)} heritable traits, "
          f"{len(heat_resistant)} blunting fever and {len(clear_resistant)} blunting "
          f"recruitment, none blunting both, and none of them able to appear before "
          f"wave {min(TRAITS[t].get('earliest', 1) for t in heat_resistant + clear_resistant)}")


if __name__ == "__main__":
    _self_check()
