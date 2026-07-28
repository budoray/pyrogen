# Febrile — for Claude

⚠ **`Febrile` is a THROWAWAY PROJECT NAME.** It is the merge of [[Titer]] and [[Corpus]] into one
game, and the name is a placeholder for the mechanic it is built on (a fever is a defence that
damages the defender). Dr. Ray renames it before it deploys; nothing below depends on the word.
Slug `febrile`, port 9400.

**Not playable yet.** This repo is a founding: the two documents, the vendored drop-ins and
`engine/`. The design record and the four founding questions are in
[`IMPROVEMENTS.md`](IMPROVEMENTS.md) — read it before writing `app.py`.

<!-- tenshin:platform:start -->
**Two documents.** Global standards + future work: the SSoT
([`../Website/SSOT.md`](../Website/SSOT.md)) — read its **Platform conventions** first, it
lists the standards every game meets. **Everything specific to this game lives here in
[`IMPROVEMENTS.md`](IMPROVEMENTS.md)** — architecture, gotchas, design record, and this game's queue.
Strike an item there in the same commit that ships it.
⚠ **This replaces the old "do not start a new `.md` here" rule** (Dr. Ray, 2026-07-25): project
specifics were split out of the SSoT per game, so a new `.md` here is now correct, not forbidden.

**Every commit bumps the build** — the patch of `vX.Y.Z-beta` in `VERSION`, staged in that commit.
Dr. Ray alone moves major/minor, and the build restarts at `0` when either does. **No CI/CD** — gates
run locally and through the Command Center; do not add a `.github/` directory.

**The house chrome, in every client:** build · report · back · sign out, same set, same order. `back`
is `← Tenshin Arts` → the site ROOT (not `/games`) and leaves you signed in; `sign out` ends the
session. They are different doors — one account opens every game, so leaving one is navigation. The
unauthenticated `/live/embed` carries the first three and drops sign out.

**Show the BUILD, never a hand-kept number.** Whatever `/version` serves is what every screen shows
and every bug report carries, or the hub's card and the game disagree.

⚠ **Check the CLIENT, not the server.** A route that exists is not a feature a player can reach: a
reporter wired server-side with nothing calling it, a version in the state payload that nothing
renders, and a tutorial with no replay have all shipped here while `app.py` grepped clean. If the
client is a static file or a bundle, the gate must read it.

⚠ **`tenshin_feedback.submit()` returns `(ok, info)` — a tuple.** `bool()` on a 2-tuple is always
True, so `if submit(...)` tells the player "sent" while the report goes nowhere. Unpack it.

⚠ **An assertion that cannot fail is not a test.** Break it three ways before trusting it — the value, the absence, the selector scope.

⚠ **A broken measurement still returns a number.** Make the primitive self-report; guard on OUTPUT not inventory; refuse rather than compute across a mismatched commit/ticks/seed; one draw is not a ranking.

⚠ **Derive, don't migrate.** Display data is derived at READ time; what must persist migrates at the ONE door every load passes — never at a call site, never inside a seed guarded by `if already_seeded: return`.

⚠ **Test the deployed shape, not the convenient one.** Mutate a live row to the old shape, re-run the fix, assert it landed — a fresh-DB test passes for the wrong reason.

⚠ **A self-check prints what it proved, in a sentence, with the numbers** — interpolated from what it computed, never typed in. The gate output IS this platform's behaviour documentation; a literal in a status line is the stale second copy.

⚠ **Results a document quotes go in `metrics/` and are COMMITTED; scratch and sqlite do not.** A claim in a design record you cannot re-check is a claim nobody can revisit.
<!-- tenshin:platform:end -->

## What this game is, in one sentence

**A pathogen is crossing tissue toward an organ, and every way you have of stopping it is a way of
hurting yourself.** You are not a commander placing turrets and you are not a nurse reading gauges;
you are the regulation, and the regulation is the weapon.

## THE FIVE LAWS

**1 · CONSERVATION, and it now spans both halves.** Corpus's first rule, extended, and it is the
entire reason this merge exists: **a defence is paid for out of the same finite store a set-point
draws on.** Recruiting cells to a site and holding a fever both spend substrate; substrate is
released from a finite glycogen store; releasing it costs what release costs. **Nothing in
`physiology.py` or `recruit.py` may create anything.** Two economies would make this Titer with a
health bar; one economy is what makes the choice a choice.

**2 · EVERY RESPONSE COSTS, SO MAXING EVERYTHING MUST LOSE.** Inherited from Corpus and now
doubly load-bearing, because the player has two ways to overspend and both must kill: hold every
drive at full and the body fails; recruit at every site and inflammation exceeds tolerance and the
body fails. ⚠ The benchmark's spend-everything policy must die **faster than the policy that does
nothing at all**, on both axes, and the numbers go in `metrics/`.

**3 · NEVER RECOMMEND A RESPONSE.** No gauge is flagged urgent, no threat carries its answer,
nothing is sorted by severity, and no site is highlighted as "undefended". Reading the body is the
skill. The gate greps the client for `recommend` / `suggest` / `best` / `urgent`.

**4 · NOTHING IS NAMED BEFORE IT IS USED.** Titer's law and AMPU's. A defence that persists between
waves is not labelled *memory* the first time it persists — it persists, the player notices they
kept it, and the reveal names it afterwards. The word *homeostasis* must not reach the browser
before the player has been one; same for *pyrexia*, *clonal selection*, *autoimmunity*.

**5 · SELECTION IS EARNED, AND IT MUST NOT LEARN THE PLAYER.** ⚠ `febrile/selection.py` may not
read the board, the placements, the drives, or a difficulty tier. It samples the next wave from the
genomes that lived through the last one and nothing else. **This is stricter than Titer's version,
not looser**: the drives are now part of the environment a pathogen survives, so the temptation to
pass them in is real and must be refused. Hold a fever every wave and heat-tolerant genomes take
the pool over — because they *lived*, not because anything counted your fevers.

## The one new mechanic, and the test for whether it is working

**Every threat has a LOCAL answer and a SYSTEMIC answer, and they cost different things.**

| | local — recruit at a site | systemic — hold a set-point |
|---|---|---|
| reach | one site | the whole body |
| speed | arrives over several beats | this beat |
| paid in | substrate, and inflammation at that site | substrate per beat, and damage everywhere |
| taught by | Titer | Corpus |

Neither parent game has both axes, and that is the merge's whole justification. ⚠ **The design test:
a wave that is answerable *only* locally or *only* systemically is a badly designed wave.** If the
best play never changes between the two, this is Titer with a HUD and the merge failed.

## Boundaries (do not cross)
- **Not [[Progeny]].** Genetics of the organism. Selection here is a pathogen population's, over
  waves, and it never touches a player's genome.
- **Not [[Nullroute]].** A pathogen is selection pressure, not an attacker with intent.
- **No routing, no throughput, no conveyors.** Tissue is a field, not a network. (This boundary
  pointed at Clearance until that game was killed 2026-07-27; the boundary is the useful half.)
- **Titer and Corpus are the PARENTS and this replaces them.** ⚠ Neither is deleted or redeployed
  until this ships and Dr. Ray says so; until then all three exist and the two parents stay live.

## The arcade rules — read the SSoT's *★ The arcade titles* before designing anything here
- **2D ONLY. No isometric, ever.** ⚠ Not vector-glow either. Top-down, Factorio-style art direction.
- Canvas backing store **320×180**, scaled, `image-rendering: pixelated`. Text stays in the DOM.
- ⚠ **Fixed-rate `setInterval`, never `requestAnimationFrame`** — rAF is throttled to zero when the
  page is not composited, and a replay that silently stops is worse than a late frame.
- ★ **The scanner is the signature, inherited from Corpus and now shared with the board.** Five
  traces with their safe bands shaded behind them, sitting above the tissue field. A set-point
  sliding out reads as a **shape leaving a zone** while something crosses toward an organ.
- ⚠ **Anything that spreads, fills or grows is drawn PROCEDURALLY** — tissue, inflammation, the
  pathogen front. Sprites are for the things the player points at and chooses.

## No clock, and this is what makes the merge legal
Corpus was kept out of a merge with Progeny because *"the two cannot share one clock"*. **That
objection does not apply here and the reason must not be lost:** Corpus advances only when the
player lets a beat pass, Titer advances only when the player commits a wave — **neither has a
clock**, so there is nothing to reconcile. ⚠ **Do not add one.**

⚠ **One turn is one WAVE.** The player edits a draft — placements *and* a set-point schedule — and
commits the whole thing; the server resolves every beat with a seeded RNG and returns a frame log,
and the client is a projector. Beats are not turns. Placing is not a turn. Setting a drive is not a
turn. Otherwise the shared engine's month counter would tick on every mouse press and decay
mastery for moving the mouse.

★ **The calm is where the game is decided, and here the calm is the whole of the input.** The
player cannot touch the wave while it plays. That is the structural answer to the platform guard —
**can a fast player who does not know the immunology beat a slow player who does?** Here the fast
player has nothing to be fast at.

## The gate — all must pass before a commit
```bash
python app.py test
```

## Run
```bash
TENSHIN_DEV=1 python app.py     # http://127.0.0.1:9400/?_acct=1  (no login in dev)
```

## Conventions
- ⚠ **`TENSHIN_DEV` must be set BEFORE `import tenshin_gate`** — read into a module constant at import.
- Tenshin drop-ins are copied **verbatim** — never fork them here. So is `engine/` (from Vested).
- A pathogen, trait, defence, insult, set-point or reveal is **data**, never code
  (`febrile/data/*.yaml`). Adding one must cost a data file.
- ⚠ **`febrile/catalog.py` is the ONE loader**, and the only place assertions about what is IN the
  data live. Every assertion there must be breakable by editing a real data file — `assert
  len(TRAITS) > 0` is worse than nothing, because it makes the gate look like it checks content
  while it checks that a file parsed.
- ⚠ **Reveals ship earned-only**, in `view.codex`, and the gate asserts the vocabulary is absent
  from a fresh session's payload.
- ⚠ **The client is ONE file for both surfaces** (`web/console.html`), switched by the body class
  the server stamps. The spectator rule is declarative CSS. Never strip chrome with a runtime regex.
- ⚠ **The bench is part of the gate**, as in Corpus. Law 2 is arithmetic here, not balance, and an
  unmeasured claim about it is the failure mode this platform keeps rediscovering.
