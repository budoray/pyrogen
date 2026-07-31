"""Selection — the pathogen's brain, ported from Titer UNCHANGED IN PRINCIPLE.

⚠ NOTHING IN HERE KNOWS WHAT THE PLAYER DID. Not the drives, not the body, not
the recruitment. A wave is not designed to counter you; it is *sampled from the
individuals that lived through the last one*. If wave nine shrugs off fever, that
is because your body could not cook the heat-shock carriers in wave eight and
they were the ones who got to breed.

That distinction is the whole game, and here it is load-bearing twice over: it is
also the only thing that makes fever a superweapon that disarms itself. A
scripted "fever gets weaker after wave 6" would look identical on a graph and
teach nothing at all.
"""
import sys

from febrile import catalog

# ⚠ Titer's ratio is 4.0 : 0.5, and the design record says that 8:1 is the number
# to START from here, not to copy blindly — this environment is richer, so the
# pressure may already be stronger. `bench.py` measures what it actually produces.
SURVIVOR_WEIGHT = 4.0
CASUALTY_WEIGHT = 0.5
P_ADD = 0.15
P_DROP = 0.07
P_IMMIGRANT = 0.08
MAX_TRAITS = 3


def seed_pool():
    """Wave one: nothing has met you yet."""
    return [{"traits": [], "weight": 8.0},
            {"traits": ["fast_split"], "weight": 1.0}]


def _pick(pool, rng):
    total = sum(g["weight"] for g in pool)
    roll = rng.uniform(0, total)
    acc = 0.0
    for g in pool:
        acc += g["weight"]
        if roll < acc:
            return list(g["traits"])
    return list(pool[-1]["traits"])


def _mutate(traits, n, rng):
    """⚠ `n` gates only what may be INVENTED this wave, never what may be
    inherited — a genome that already carries a trait keeps it and can take the
    pool at any wave number."""
    if traits and rng.random() < P_DROP:
        traits.remove(rng.choice(traits))
    if len(traits) < MAX_TRAITS and rng.random() < P_ADD:
        options = [t for t in catalog.HERITABLE
                   if t not in traits and catalog.TRAITS[t].get("earliest", 1) <= n]
        if options:
            traits.append(rng.choice(options))
    return sorted(set(traits))


def wave_size(n):
    return 5 + int(n * 1.7)


def wave_hp(n):
    """Gentle: the difficulty comes from the population's SHAPE, not a number
    going up. If this curve is what makes late waves hard, the game is a
    difficulty ramp wearing selection as a hat."""
    return 12.0 * (1.115 ** (n - 1))


def spawn_wave(pool, n, rng):
    base = wave_hp(n)
    out = []
    for i in range(wave_size(n)):
        traits = [] if rng.random() < P_IMMIGRANT else _mutate(_pick(pool, rng), n, rng)
        hp = base * catalog.stat(traits, "hp")
        out.append({"i": i, "traits": traits, "kind": catalog.dominant(traits),
                    "hp": round(hp, 2), "max_hp": round(hp, 2), "survived": False})
    return out


def next_pool(individuals):
    """The gene pool after a wave. That weight ratio IS the selection pressure,
    and it is the one number to turn if the pathogen adapts too fast or too slow."""
    pool = {}
    for p in individuals:
        key = tuple(p["traits"])
        pool[key] = pool.get(key, 0.0) + (SURVIVOR_WEIGHT if p["survived"] else CASUALTY_WEIGHT)
    return [{"traits": list(k), "weight": round(v, 3)} for k, v in sorted(pool.items())]


def frequencies(individuals_or_pool):
    """trait id -> share of the population carrying it, 0..1."""
    if not individuals_or_pool:
        return {}
    weights = [g.get("weight", 1.0) for g in individuals_or_pool]
    total = sum(weights) or 1.0
    out = {}
    for g, w in zip(individuals_or_pool, weights):
        for t in g["traits"]:
            out[t] = out.get(t, 0.0) + w
    return {t: round(v / total, 4) for t, v in sorted(out.items())}


def _self_check():
    import inspect
    import random

    # ⚠ THE ASSERTION THE DESIGN RECORD ASKS FOR BY NAME: this module cannot see
    # the drives. Checked against the PARSED module, never a substring scan — a
    # blocklist over raw source fails on the docstring that explains the rule,
    # and the fix for that is not to whittle exceptions into the blocklist. What
    # matters is whether any IDENTIFIER here can reach the player's side, so ask
    # the AST, which cannot see prose at all.
    import ast
    tree = ast.parse(inspect.getsource(sys.modules[__name__]))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    names |= {a.arg for n in ast.walk(tree) if isinstance(n, ast.arguments)
              for a in n.args}
    names |= {a.name for n in ast.walk(tree)
              if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    for forbidden in ("drives", "physiology", "body", "temp", "glycogen", "fever"):
        assert forbidden not in names, \
            f"selection.py has an identifier {forbidden!r} — it must not know what the player did"

    # 1 · resistance EMERGES under a pressure that only kills the susceptible.
    rng = random.Random(7)
    pool = seed_pool()
    for n in range(1, 13):
        wave = spawn_wave(pool, n, rng)
        for p in wave:                        # a "fever" that only spares heat_shock
            p["survived"] = catalog.stat(p["traits"], "heat") < 1.0
        pool = next_pool(wave)
    got = frequencies(pool).get("heat_shock", 0.0)
    assert got > 0.5, f"heat_shock never took the pool under heat pressure ({got})"

    # 2 · ...and it REVERSES when the trait stops paying. Without this, what looks
    # like selection is a difficulty curve wearing a hat: a number that only ever
    # goes up is indistinguishable from a scripted ramp.
    for n in range(13, 30):
        wave = spawn_wave(pool, n, rng)
        for p in wave:                        # pressure inverts: carrying it now kills
            p["survived"] = catalog.stat(p["traits"], "heat") >= 1.0
        pool = next_pool(wave)
    back = frequencies(pool).get("heat_shock", 0.0)
    assert back < 0.15, f"heat_shock never faded when it stopped paying ({back})"

    print(f"febrile.selection self-check OK -- blind to the drives by source; "
          f"heat_shock rose to {got:.0%} of the pool over 12 waves of heat pressure "
          f"and fell back to {back:.0%} over 17 waves once carrying it stopped paying")


if __name__ == "__main__":
    _self_check()
