# Pyrogen — for Claude

**`Pyrogen` is the REAL NAME** (Dr. Ray, 2026-08-01), replacing the throwaway `Febrile` this repo
was founded under. A pyrogen is the substance that *causes* a fever — literally "fire-maker" — and
the **endogenous** ones are IL-1, IL-6 and TNF, which is what this engine actually models. So the
name is the mechanic in the house way: *the thing that burns you is one you made.*
Slug `pyrogen`, port **9100**.

⚠ **The rename was safe only because it landed BEFORE the first deploy.** slug == subdomain == unit
== data directory == repo, so past a deploy this is a saves migration, not a string change. This was
a `registered` row with no vhost, no unit and nothing bound — the cheapest possible moment.
**Both halves outside this repo are DONE (Dr. Ray, 2026-08-01) and were verified, not assumed** —
`github.com/budoray/pyrogen` exists, and a lookup against 8.8.8.8 reads `febrile.tenshinarts.com`
→ NXDOMAIN with `pyrogen.tenshinarts.com` → 104.131.165.79. The old name was **removed**, not merely
supplemented, which is the half that matters: a name resolving to the box with no vhost gets
whatever Caddy's default host serves rather than failing clean, and that is exactly how Asymptote
published a cabinet reading *sent an invalid response*.
⚠⚠ **So this game is now in G8's shape: the name resolves and NOTHING is behind it.** Correct and
necessary — the record must exist before a deploy can work — but **nothing about this game may be
published or lit on the strength of it.** The OPS row stays `registered`, there is no Caddy vhost
and no unit, and the cabinet on the site is unlit by construction. Deploying is what changes that.

**PORT 9100 IS CLEAR.** It is Corpus's port, freed when Corpus and Titer — the two games this one
is the merge of — were retired 2026-08-01. The condition on reissuing a port is that no name still
resolves in front of it, and that was **checked rather than assumed**: `corpus.tenshinarts.com` and
`titer.tenshinarts.com` both read NXDOMAIN against 8.8.8.8 the same day. Removing the A record is
what frees a port; the undeploy is not. This repo said 9400 at founding (Continuous Yield's) and
9200 after that (Doctrine of Signatures took it) — so check `../Website/app.py`'s `OPS`
table for the live map before believing any number in a game document, including this one.

⚠ **[[Titer]] and [[Corpus]] are GONE as of 2026-08-01** — absorbed into this game. Rows, cabinets,
plates, vhosts, units and deploy-registry entries removed from the platform, and Dr. Ray deleted
both A records and both GitHub repos. ⚠⚠ **THE LOCAL WORKING COPIES ARE GONE TOO. CONFIRMED BY DR. RAY 2026-08-01: "gone gone, 100%
deleted."** Repos deleted, A records removed, checkouts destroyed — **that code no longer exists in
any form.** The physiology and selection Pyrogen was built from survive ONLY as they were rewritten
into `pyrogen/physiology.py` and `pyrogen/selection.py`. **Those two files are now originals, not
ports.** Treat them accordingly: there is nothing left to diff against, nothing to re-read when a
constant looks wrong, and no way to recover an intention that did not make it into the rewrite.
★ The warning here was correct, specific, written twice — and it still failed, because it recorded
a *fact about the world* ("nothing remote backs them up") rather than an *action*. Nothing could
catch the drift either: `app.py check` walks the repos in the **registry**, and a retired game is by
definition out of every registry, so pulling the OPS rows also switched off the one process that
might have noticed. **A document that says "this is the only copy" is a to-do item, not a note.**

**Playable and deployed, `v0.1.1-beta`.** Engine core — `pyrogen/catalog.py`, `selection.py`,
`physiology.py`, `run.py`, `bench.py` — plus the server (`app.py`, the full contract) and the
one-file client (`web/console.html`). All six founding milestones are done and the queue is empty.
What the repo still carries from the founding is `engine/`. The design record and the four founding questions are in
[`IMPROVEMENTS.md`](IMPROVEMENTS.md) — read it before writing a line of code.

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

⚠⚠ **A LINK IS NOT A FEATURE — ITS TARGET IS.** The house chrome rendered
`<a href="/api/report">report</a>` for this game's whole life, and `/api/report` is **POST
only**: the link answered **405**, in production, on both surfaces, on the one control a
player uses to say something is broken. Everything the gate asked was true — the POST route
existed, the word "report" was in the page, the contract checker POSTed and passed. Nothing
asked where the link pointed. The house pattern is `<a id="report" href="#">` plus a handler
that POSTs; three sibling games already did it and this one was the lone deviation, which is
why no shared check caught it. **When you add a control, follow it to what it hits.**

★ **A game that teaches a subject is designed in the PRAXAGOGICAL mode** — the fourth rung after
pedagogy, andragogy and heutagogy. Locus of control is the learner *inside a complex system*; the
goal is **process resilience and adaptive confidence**, not subject mastery; failure is **tolerated
as cognitive friction**, never penalised. The instructor is a **validating mentor / co-conspirator**:
it tells a learner their process was sound *separately from whether it worked*, and it is inside the
problem rather than holding the answer key — an oracle that is never wrong is an authority figure,
which is the pedagogy column. ⚠ Never in player-facing copy: a game that announces its mode has
become an exercise. ⚠ **This framework was called PCRT until 2026-08-03** — same content, retired
name; do not write PCRT in new work. Full section, the three scales and what each demands of a game:
[`SSOT.md`](../Website/SSOT.md) → *Praxagogy — why these games exist*.

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
released from a finite glycogen store; releasing it costs what release costs. **Nothing in the
physiology or recruitment code may create anything.** Two economies would make this Titer with a
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

**5 · SELECTION IS EARNED, AND IT MUST NOT LEARN THE PLAYER.** ⚠ The selection code may not
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
- **Titer and Corpus were the PARENTS and this replaced them.** ⚠ ~~Neither is deleted or redeployed
  until this ships and Dr. Ray says so; until then all three exist and the two parents stay live.~~
  **The condition was met and executed 2026-08-01** — both retired, both repos and A records deleted.
  ⚠⚠ The stale half is the dangerous one: this line still read *"the two parents stay live"* in the
  same file that records their deletion twelve lines above. **Their local working copies are the only
  copies left, with nothing remote behind them.**

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

## The gate — the house one-liner, plus the engine chain it did not replace
```bash
python -m pyrogen.catalog && python -m pyrogen.selection && python -m pyrogen.physiology && python -m pyrogen.run && python -m pyrogen.bench --check
```
⚠ **`python app.py test` is now the house gate** — milestone 5 shipped and the OPS row says so.
⚠⚠ **It JOINED the chain above, it did not replace it:** the engine modules still self-check, and
the bench is still part of the gate. Run both.

⚠ **This paragraph said "there is still no `app.py`" for a day after `app.py` shipped** — eight
lines under a code fence that names it. ★ **A doc sentence about what does not exist yet has no
check behind it and no expiry**; the only defence is to pin the claim to something verifiable (a
version, a route, the OPS row) so the contradiction is visible rather than plausible.

⚠ **The bench is part of the gate**, as in Corpus — and it earns that here. It caught three separate
errors that each printed a confident number, including a pathogen that was healing faster than it
hurt. See the design record.

## Conventions
- ⚠ **`TENSHIN_DEV` must be set BEFORE `import tenshin_gate`** — read into a module constant at import.
- Tenshin drop-ins are copied **verbatim** — never fork them here. So is `engine/` (from Vested).
- A pathogen, trait, defence, insult, set-point or reveal is **data**, never code
  (`pyrogen/data/*.yaml`). Adding one must cost a data file.
- ⚠ **ONE loader owns the data**, and it is the only place assertions about what is IN the data
  live. Every assertion there must be breakable by editing a real data file — an
  `assert len(TRAITS) > 0` is worse than nothing, because it makes the gate look like it checks
  content while it checks that a file parsed.
- ⚠ **Reveals ship earned-only**, in `view.codex`, and the gate asserts the vocabulary is absent
  from a fresh session's payload.
- ⚠ **The client is ONE file for both surfaces** (`web/console.html`), switched by the body class
  the server stamps. The spectator rule is declarative CSS. Never strip chrome with a runtime regex.
- ⚠ **The bench is part of the gate**, as in Corpus. Law 2 is arithmetic here, not balance, and an
  unmeasured claim about it is the failure mode this platform keeps rediscovering.
