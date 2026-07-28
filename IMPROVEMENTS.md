# Febrile — design record + queue

Slug `febrile` · port 9400 · **founded 2026-07-27, not yet playable**.
Global standards live in the SSoT; this file is everything specific to this game.
⚠ **`Febrile` is a throwaway name** — a placeholder for the mechanic (a fever is a defence that
damages the defender). Renaming it is a slug change; see the SSoT's deploy runbook before doing it,
because slug == subdomain == unit == data directory == repo and a drift there deploys a game with no
saves.

## Where it stands
Nothing is built. The four founding questions below are **open**, and the rule this platform keeps
relearning applies to all of them: an answer here is not an answer until an assertion stands behind
it. `python app.py test` does not exist yet and is the first milestone.

## The pitch
Something is crossing your tissue and it learns. You have two ways to stop it: send cells to the
place it is, or change what the whole body is like — hotter, wetter, hungrier, more inflamed. The
first is slow and precise. The second is instant, works everywhere, and is indistinguishable from
being ill, because it *is* being ill. **Everything you survive you keep, and everything you did to
survive it, the next wave has already met.**

## Why the merge, and why it is not the merge that was rejected
[[Titer]] is an adapting attacker with no body to damage. [[Corpus]] is a body under insult with no
adapting insult. Each one carries the other's missing half, and two of the seams were already
written down as *unfinished* in the parents:

| in the parent | what it was | what the merge does with it |
|---|---|---|
| Titer's `autoimmunity` row | listed in its own mapping table, implemented as `inflammation - tolerance` against an abstract integrity bar | the damage lands on an actual physiology, on the actual scanner, in the units the rest of the game already uses |
| Corpus's insult list | includes *infection*, as one insult among cold and haemorrhage — a scalar that ramps | infection stops being a scalar and becomes the other game |
| Titer's placement currency | its own resource, invented to have something to spend | **deleted.** Cells are paid for in substrate, out of glycogen, under Corpus's conservation law |
| Corpus's stressors | never adapt, by construction | the pathogen adapts to the *drives*, and the drives are the environment it is selected in |

⚠ **The clock objection that killed Corpus + Progeny does not apply, and the reason must survive in
this file.** Corpus's record rejected that merge because Progeny is *no time pressure / no decay /
never punish absence* and a stressor wave ending in a flatline is the opposite — "the two cannot
share one clock." **Titer and Corpus have no clock between them.** Corpus advances when the player
lets a beat pass; Titer advances when the player commits a wave. Beats nest inside a wave with
nothing to reconcile, which is the structural fact that makes this merge cheap and that one
expensive. ⚠ It also means the first person to propose "just add a timer, it's an arcade title"
is proposing to break the only thing holding the two games together.

⚠ **Titer's `CLAUDE.md` says "Not Corpus."** That boundary was written to stop scope creep and it
did its job; it is **superseded for this repo only**, by Dr. Ray, 2026-07-27, and the parents keep
their own boundaries until this ships. Do not go and edit Titer's law on the strength of this file.

## The mapping — the genre and the subject are the same object

| mechanic | immunology / physiology |
|---|---|
| generic responders already present at a site | innate immunity |
| defences that persist between waves, filed per type | immunological memory |
| a set-point held board-wide | fever, inflammation, the acute-phase response |
| the same store paying for both | metabolic cost of the immune response |
| enemies adapting to what stopped them | antigenic and antibiotic resistance |
| your own response damaging the body | autoimmunity, sepsis, cytokine storm |
| a threat answerable locally *or* systemically | local vs systemic response, the actual clinical distinction |

---

## The four founding questions — OPEN

### 1 · What is the substrate, exactly, and does one pool really work?
Corpus conserves oxygen, glucose, heat and pH against a budget per beat. Titer spent a placement
currency. **The merge claims one pool, and the claim is unproven.** The failure mode is legible in
advance: if recruiting a cell is priced in the same units as shivering, one of the two will
dominate at every price, and the game becomes single-axis — which is the merge failing at its only
job. ⚠ **Answer this with a table, not a paragraph:** the price of a local answer and a systemic
answer to the *same* wave, and evidence that the better one changes with the wave.

### 2 · Fever is the signature mechanic and also the most likely trap
Raising core temperature slows every pathogen at once, costs glucose every beat, damages the body
above a threshold, and — because selection samples survivors — **breeds heat tolerance, so it stops
working.** That is a superweapon that disarms itself, taught mechanically rather than stated, and it
is the single best argument this game exists.
⚠ It is also exactly the shape of a mechanic that measures wonderfully and plays as one button.
**The assertion to write first:** fever-every-wave must beat a no-fever policy for the early waves
and **lose to it by wave N**, with N measured and recorded, and the crossover must come from
`selection.py` alone — nothing anywhere counting fevers.

### 3 · Where do beats live, and how much can the player pre-schedule?
The player edits a draft and commits it; the server resolves the wave beat by beat and returns a
frame log. The open question is **how much of the drive schedule the player writes in advance.** One
setting for the whole wave is too coarse to be physiology; per-beat is a spreadsheet. Candidates,
none chosen: a small number of scheduled changes at beat thresholds; a set-point plus a trigger
("raise on breach"); a budget of interventions spent anywhere in the wave.
⚠ Whichever it is, it must not become reaction speed. The platform guard is not negotiable.

### 4 · Three losses or one?
Breach, autoimmunity and metabolic failure are three deaths in the parents. **The design intent is
ONE:** the body fails, and the replay names which of the three routes got there — a breach becomes
an insult, inflammation becomes damage, and both land on the same viability. It is cleaner, it is
better physiology, and it risks making the breach feel weightless. ⚠ **Every death names which
system failed and which set-point ran away** — AMPU's rule, Corpus's flatline replay. A death that
does not teach is a bug.

---

## The saturation trap — verify before shipping, and record the table
★ The SSoT's generalised rule: **the pressure a game claims to teach must actually bind.** This
game can fail it in three separate places, and all three look playable:
1. **The two axes never trade off** — one answer is always right (question 1).
2. **Selection never bites** — the pathogen adapts too slowly to punish a repeated set-point, so
   fever is simply the best button (question 2). Titer's ratio is `SURVIVOR_WEIGHT` 4.0 :
   `CASUALTY_WEIGHT` 0.5, and that 8:1 is the number to start from, not to copy blindly — the
   environment here is richer, so the pressure may already be stronger.
3. **The body is never actually threatened** — Corpus's baselines net to zero at rest, so a wave
   that costs less than the baseline slack teaches nothing. Corpus's own number: a body at full
   drive takes **39 damage** over thirty beats where a resting one takes **0**. The merged version
   of that arithmetic is the first thing `bench.py` must reproduce.

⚠ **Budget for the benchmark being wrong.** Ember Down caught *three rounds where the benchmark was
measuring itself* rather than the game. The harness needs the same scepticism as the thing it
measures.

## Reference set
Inherited and still correct: **FTL** (allocate limited power across systems under escalating
attack; damage cascades; you lose by running out of what everything shares), **Oxygen Not Included**
(conservation is what makes failure legible), **RimWorld** (narrated consequence — "left lung
destroyed → breathing 40%" is the flatline replay), **Missile Command** (you cannot save everything;
you choose what to lose), **Defender** (the scanner: peripheral awareness of what you are not
looking at), **Plants vs Zombies** (parallel lanes read at a glance).

New, and specific to what the merge adds: **Plague Inc. inverted** — that game is the pathogen
selecting against a world's responses, which is exactly this game's `selection.py` seen from the
other side, and it is worth playing once to see how legible evolved resistance can be made without
a single number on screen.

## PixelLab — the ask
★ **ART DIRECTION (Dr. Ray, 2026-07-26): TOP-DOWN, in the artwork style of Factorio.**
★ **Anything that spreads, fills or grows is drawn PROCEDURALLY, never tiled from sprites** — the
tissue field, the inflammation bloom and the pathogen front are canvas. Sprites are for the things
the player points at and chooses.

**The honest answer today is: nothing yet, and this note has a known expiry.** Corpus's identical
note went stale within the hour because the game shipped the same evening — the *reasoning* held
(art before the loop is decoration you then design around) and only the timing failed. So: no
generation until the loop is proven, and then, in this order —

1. **The set-point acts** — the systemic verbs, ~64px, top-down, flat. Each must read as an **act**,
   not an organ, and they may not duplicate Corpus's six; the merged control set is question 3's
   output, not a copy.
2. **The cell types** — the local answers, the nouns the player points at. Distinct silhouettes at
   16px before any detail at 64px, because they are read on a 320×180 backing store.
3. **Nothing else.** The board, the traces, the front and the bloom are code.

⚠ **`credits: $0.00` is normal and misleading** — read `generations_remaining`. ⚠⚠ **Eight in-flight
jobs, ACCOUNT-WIDE**; stagger, fire two and poll. ⚠ A rate-limited job was never queued — re-issue
it unchanged.

## Queue
1. **Answer question 1 with a bench, before writing a client.** One pool, two axes, a table showing
   the better answer changes by wave. If it does not, this game is Titer with a HUD and should be
   stopped here — that is a cheap failure now and an expensive one after a client exists.
2. `febrile/physiology.py` — ported from Corpus, conservation intact, extended so a recruitment
   draws on the same store. Its self-check must fail if anything creates.
3. `febrile/selection.py` — ported from Titer **unchanged in principle**, with the extra assertion
   that it cannot see the drives, and the reversal assertion kept (a trait that stops paying must
   fade, or what looked like selection was a difficulty curve wearing a hat).
4. `febrile/catalog.py`, then the data files. No game logic until the data has a loader.
5. `app.py` + the contract: `/version`, `/live`, `/live/embed`, `/live/stream`, `/live/agents`,
   `/admin/players`, `/leaderboard.json`, in-process bots in a reserved id range, `python app.py
   test`. ⚠ **A feed with no agents is a broken feature** and it monitors as healthy.
6. The client, one file, both surfaces.
