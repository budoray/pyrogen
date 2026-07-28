"""Vested's game-agnostic async-turn engine.

Knows about players, turns, cohorts, and persistence — NOTHING about money.
A game (e.g. ``vested.money``) supplies what a turn *means*; the engine owns
storing state and advancing the month. This package is what Starmarch,
Nullroute and Overfit reuse later. See SPEC.md §5.
"""
