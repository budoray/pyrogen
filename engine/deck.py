"""Generic weighted event deck — game-agnostic.

Loads card records (plain dicts) from YAML and draws one, with optional
focus-boost (the adaptive lean) and tier gating (content that phases in as a
player advances). The engine draws DATA and never interprets a card's `effect`
— the game does that. So a new game ships new YAML, not new engine code.

    deck = Deck.from_dir("vested/events")
    card = deck.draw(rng, focus="emergency_fund", max_tier=2)
"""
from pathlib import Path

import yaml


class Deck:
    def __init__(self, cards):
        self.cards = list(cards)
        for c in self.cards:
            c.setdefault("weight", 1.0)
            c.setdefault("tier", 1)

    @classmethod
    def from_dir(cls, path):
        cards = []
        for f in sorted(Path(path).glob("*.yaml")):
            cards.extend(yaml.safe_load(f.read_text(encoding="utf-8")) or [])
        if not cards:
            raise ValueError(f"no cards found in {path}")
        return cls(cards)

    def draw(self, rng, focus=None, boost=3.0, max_tier=None, focus_key="competency"):
        """Weighted draw. Cards whose `focus_key` == `focus` get `boost`x weight
        (lean the game at a gap); cards above `max_tier` are held back."""
        pool = [c for c in self.cards if max_tier is None or c["tier"] <= max_tier]
        if not pool:
            pool = self.cards
        weights = [c["weight"] * (boost if focus and c.get(focus_key) == focus else 1.0)
                   for c in pool]
        roll = rng.uniform(0, sum(weights))
        acc = 0.0
        for c, w in zip(pool, weights):
            acc += w
            if roll < acc:
                return c
        return pool[-1]


def _self_check():
    import random

    cards = [
        {"id": "quiet", "weight": 10, "tier": 1},
        {"id": "shock", "weight": 10, "tier": 2, "competency": "emergency_fund"},
    ]
    deck = Deck(cards)
    rng = random.Random(0)

    # max_tier gates out the tier-2 card entirely.
    assert all(deck.draw(rng, max_tier=1)["id"] == "quiet" for _ in range(20))

    # focus-boost makes the emergency_fund card much more likely.
    rng = random.Random(1)
    focused = sum(deck.draw(rng, focus="emergency_fund")["id"] == "shock" for _ in range(400))
    rng = random.Random(1)
    plain = sum(deck.draw(rng)["id"] == "shock" for _ in range(400))
    assert focused > plain, (focused, plain)
    print(f"engine.deck self-check OK — max_tier=1 drew the tier-1 card 20 of 20 times, and "
          f"naming a focus competency pulled its card {focused} times in 400 against {plain} "
          f"unfocused, so the deck steers at the gap without ever locking a card out")


if __name__ == "__main__":
    _self_check()
