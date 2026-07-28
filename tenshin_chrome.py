"""Drop-in CHECKER for the house chrome. Copy this ONE file into a game repo.

Asymptote, Clearance, Corpus, Ember Down and Titer share a footer, a report box
and a reporter route BYTE-IDENTICALLY. ⚠ **This file does NOT extract that code.**
That code is already correct in five places, and the near-miss on
`TurnEngine.standings()` — a shared method one game stopped calling and somebody
nearly deleted out from under the others — is the argument against hoisting
working runtime into a shared module for tidiness.

What IS worth extracting is the ASSERTIONS. The five-repo `page()` defect was
caught by adding conformance rows, and the fix was five identical assertions
written five times; thirteen of them are already common to all five, verbatim.
So this is a CHECKER: it has no runtime coupling, nothing imports it at serve
time, and it can never become load-bearing the way `standings()` nearly did. It
is also pure — `assert_chrome(html, ...)` takes a string — so it works unchanged
in Fading Wilds' non-FastAPI client, or against a file, or against a live fetch.

    import tenshin_chrome
    tenshin_chrome.assert_chrome(client(), name="console",
                                 site_url=SITE_URL, version=VERSION, signed_in=True)
    tenshin_chrome.assert_chrome(client(spectate=True), name="spectator",
                                 site_url=SITE_URL, version=VERSION, signed_in=False)

⚠ Do NOT extend this to Legend of the Ashen Dragon or Epoch & Entropy. Both
mutate their chrome at runtime, so a string checker is the wrong instrument, and
E&E's existing check is strictly better than this one for what it covers.

⚠ THE HOUSE CHROME IS build · report · back · sign out, IN THAT ORDER, and until
this file nothing on the platform checked the ORDER — five gates asserted that
all four controls existed and none of them asserted where. The SSoT records a
session "fixing" a chrome order that was already correct, because reading markup
does not tell you the visual order; reading the ORDER OF APPEARANCE in the footer
does, for a footer that is a single flow row, which all five of these are.
"""
import re

# ⚠ `back` goes to the site ROOT, and `sign out` ends the session. They are
# DIFFERENT DOORS — one account opens every game, so leaving one is navigation.
# The unauthenticated /live/embed carries the first three and drops sign out.
ORDER = ("build", "report", "back", "sign out")


def _find(html, *needles):
    """Index of the first needle present, or -1. Games spell a control two ways."""
    hits = [html.index(n) for n in needles if n in html]
    return min(hits) if hits else -1


def assert_chrome(html, *, name, site_url, version, signed_in):
    """Raise AssertionError unless `html` carries the whole house chrome.

    `name` names the surface in every message ("console", "spectator"), because a
    failure that does not say WHICH surface sends you reading both.
    `signed_in` is the surface's contract, not a hint: a player surface MUST
    carry sign out, and a public one MUST NOT.
    """
    def bad(msg):
        raise AssertionError(f"{name}: {msg}")

    # ── the page rendered at all ──────────────────────────────────────────────
    # ⚠ A template token that never got substituted is 200 OK and a blank page.
    # A sibling game shipped one whose every brace was doubled: valid HTTP,
    # invalid CSS, a script that never parsed, and every check green.
    for tok in ("{{", "__VERSION__", "__SITE__", "__BODYCLASS__"):
        if tok in html:
            bad(f"unresolved template token {tok!r} shipped — 200 OK and a blank page")
    if html.count("<script") != html.count("</script>"):
        bad(f"unbalanced script tags: {html.count('<script')} open, "
            f"{html.count('</script>')} close")

    # ── build ─────────────────────────────────────────────────────────────────
    # Whatever /version serves is what every screen shows, or the hub's card and
    # the game disagree.
    if version not in html:
        bad(f"does not SHOW the build {version!r} — a hand-kept number drifts")

    # ── report ────────────────────────────────────────────────────────────────
    # ⚠ Reporting is CENTRAL. A game must never store its own reports, and a
    # Report button with no report box is a ReferenceError on click.
    if "/api/report" not in html:
        bad("no /api/report — the reporter is unreachable from this surface")
    if 'id="rbox"' not in html or 'id="rt"' not in html:
        bad('a Report control with no id="rbox"/id="rt" is a ReferenceError on click')

    # ── back ──────────────────────────────────────────────────────────────────
    if f'href="{site_url}"' not in html:
        bad(f"no way back to {site_url} — a public page owes its visitor a way back")
    if f"{site_url}/games" in html:
        bad("back goes to the site ROOT, not /games")

    # ── sign out: on a player surface, and GOVERNED on a public one ───────────
    # ⚠⚠ THE FIRST VERSION OF THIS RULE WAS WRONG, AND ALL FIVE REAL CLIENTS SAID
    # SO. It asserted `/logout` must be ABSENT from a public surface. Every one of
    # them failed, because the client is ONE FILE for both surfaces and the
    # spectator rule is DECLARATIVE CSS — `body.spectate .sess{display:none}` —
    # which each repo's own CLAUDE.md states as law: *never strip chrome with a
    # runtime regex*. A checker written from the contract rather than from the
    # architecture would have failed five healthy games and been "fixed" by
    # loosening it. So the rule is the mechanism, not the markup.
    if signed_in and "/logout" not in html:
        bad("a player surface with no sign out — back and sign out are different doors")
    if not signed_in:
        if 'body class="spectate"' not in html.replace("'", '"'):
            bad("a public surface that never entered spectator mode")
        if "body.spectate .sess" not in html:
            bad("no `body.spectate .sess` rule — sign out must be hidden DECLARATIVELY, "
                "never by stripping the DOM at runtime")
        if "/logout" in html:
            i = html.index("/logout")
            # the control has to be inside the element the rule governs, and the
            # opening tag carrying `sess` is the nearest one before it
            if 'class="sess"' not in html[max(0, i - 400):i]:
                bad("sign out is on the public surface and NOT inside a .sess element, "
                    "so the rule that hides it does not reach it")

    # ── the order, which nothing on the platform checked before ───────────────
    # ⚠⚠ SCOPE IT TO THE FOOTER. Measured over the whole page this reads
    # `report · build · back · sign out` on a perfectly correct client, because
    # `/api/report` appears in the <script> long before the footer's version span
    # — a false positive, which is worse here than a miss: a checker that is red
    # on healthy pages teaches five repos to skim their gate output.
    foot = re.search(r"<footer\b.*?</footer>", html, re.S)
    if foot:
        f = foot.group(0)
        at = {"build": f.rindex(version) if version in f else -1,
              "report": _find(f, 'id="rbox"', "/api/report", ">Report"),
              "back": f.index(f'href="{site_url}"') if f'href="{site_url}"' in f else -1,
              "sign out": _find(f, "/logout") if signed_in else -1}
        seen = [(k, at[k]) for k in ORDER if at[k] >= 0]
        got = [k for k, _ in sorted(seen, key=lambda kv: kv[1])]
        if got != [k for k, _ in seen]:
            bad("chrome is out of order — the house order is "
                + " · ".join(ORDER) + f", the footer reads {' · '.join(got)}")

    # ── G4: the brief is replayable, not fire-once ────────────────────────────
    # A player who hit `skip` — the button right next to the one that starts the
    # game — never saw the rules again. Fire-once means replayable, not gone.
    if 'id="btnBrief"' not in html or "function brief" not in html:
        bad("G4 — the brief must be replayable, so it needs a control and a function")

    # ── the board is served AND reached ───────────────────────────────────────
    # The house's most repeated defect: a route that exists is not a feature.
    # /leaderboard.json was served and fetched by nothing at all for a whole
    # release in one of these games.
    if "/leaderboard.json" not in html:
        bad("the leaderboard is served and no client here reaches it")
    if 'id="lb"' not in html or "renderBoard" not in html:
        bad("the leaderboard markup or its renderer is missing")

    # ── a feed that fails silently looks healthy and shows nothing ────────────
    if "EventSource" in html and "onerror" not in html:
        bad("an EventSource with no onerror fails silently and looks healthy")

    # ── tap targets: WCAG 2.5.8 wants 24x24 ──────────────────────────────────
    # ⚠ READ THE VALUE, not the presence of a word. `back` rendered 80x15 on both
    # surfaces in two of these games, because an anchor with no vertical padding
    # has a hit box exactly the size of its glyphs. Every check above proves the
    # controls EXIST; not one of them proved a thumb could hit one.
    t = re.search(r"--tap:\s*(\d+)px", html)
    if not t or int(t.group(1)) < 24:
        bad(f"tap floor is {t.group(1) + 'px' if t else 'undeclared'} — WCAG 2.5.8 wants 24")
    rule = re.search(r"footer a,\s*footer button,\s*\.rbox summary\s*\{([^}]*)\}", html)
    if not rule or "min-height:var(--tap)" not in rule.group(1).replace(" ", ""):
        bad("back/report/sign out lost the 24px floor on the shared rule")
    back = re.search(r"footer a\[href\]\s*\{([^}]*)\}", html)
    if not back or not re.search(r"padding:\s*[1-9]", back.group(1)):
        bad("`back` is padding:0 again — the hit box is the glyph box")


# ── the negative cases, which are the point ──────────────────────────────────
_OK = """<!doctype html><html><head><style>
:root{--tap:24px}
footer a,footer button,.rbox summary{min-height:var(--tap)}
footer a[href]{padding:4px 6px}
body.spectate .sess{display:none}
body.spectate .po{display:none}
</style></head><body class="play">
<button id="btnBrief">Brief</button>
<script>function brief(){}
var es=new EventSource('/live/stream'); es.onerror=function(){};
function renderBoard(b){} function rsend(){fetch('/api/report')}
fetch('/leaderboard.json')</script>
<footer>
  <span>v0.1.0-beta</span>
  <details class="rbox" id="rbox"><summary>Report</summary><textarea id="rt"></textarea></details>
  <a href="https://tenshinarts.com">&larr; Tenshin Arts</a>
  <form class="sess" action="/logout"><button>Sign out</button></form>
</footer>
<div id="lb"></div>
</body></html>"""

_SPECTATE = _OK.replace('body class="play"', 'body class="spectate"')

_ARGS = dict(name="fixture", site_url="https://tenshinarts.com",
             version="v0.1.0-beta", signed_in=True)


def _rejects(html, because, **over):
    """Assert assert_chrome REFUSES this page, and that the message says why.

    ⚠ A checker whose negative cases are untested is the gate that encoded the
    defect and went green. Every rule above is broken here on purpose."""
    try:
        assert_chrome(html, **{**_ARGS, **over})
    except AssertionError as e:
        assert because in str(e), f"rejected for the wrong reason: {e}"
        return str(e)
    raise AssertionError(f"ACCEPTED a page it must reject ({because})")


def _self_check():
    # The healthy page passes, both ways round — without this the whole suite
    # below could be satisfied by a function that rejects everything.
    assert_chrome(_OK, **_ARGS)
    assert_chrome(_SPECTATE, **{**_ARGS, "signed_in": False})

    n = [
        # ⚠ CHROME OUT OF ORDER — the case nothing on the platform checked. The
        # controls are all present and all reachable; only the order is wrong.
        _rejects(_OK.replace('<a href="https://tenshinarts.com">&larr; Tenshin Arts</a>\n  '
                             '<form class="sess" action="/logout"><button>Sign out</button></form>',
                             '<form class="sess" action="/logout"><button>Sign out</button></form>\n  '
                             '<a href="https://tenshinarts.com">&larr; Tenshin Arts</a>'),
                 "out of order"),
        # MISSING REPORTER — the control renders and nothing is behind it
        _rejects(_OK.replace('id="rbox"', 'id="reportbox"'), "ReferenceError"),
        _rejects(_OK.replace("/api/report", "/api/nothing"), "unreachable"),
        # THE EMBED DROPPING `back` INSTEAD OF `sign out`. Both are one anchor
        # gone, both leave three controls, and only one of them is correct.
        _rejects(_OK.replace('<a href="https://tenshinarts.com">&larr; Tenshin Arts</a>', ""),
                 "way back", signed_in=False),
        _rejects(_OK.replace('<form class="sess" action="/logout"><button>Sign out</button></form>', ""),
                 "different doors"),
        # ...and the public surface's sign out must be GOVERNED, not gone: hidden
        # by the declarative rule, inside the element that rule names.
        _rejects(_SPECTATE.replace('<form class="sess" action="/logout">', '<form action="/logout">'),
                 "NOT inside a .sess element", signed_in=False),
        _rejects(_SPECTATE.replace("body.spectate .sess{display:none}", ""),
                 "DECLARATIVELY", signed_in=False),
        _rejects(_SPECTATE.replace('body class="spectate"', 'body class="play"'),
                 "never entered spectator mode", signed_in=False),
        # AN UNRESOLVED TOKEN — 200 OK and a blank page
        _rejects(_OK.replace("v0.1.0-beta", "__VERSION__"), "unresolved"),
        _rejects(_OK.replace("--tap:24px", "--tap:{{tap}}px"), "unresolved"),
        # ...and the version simply absent, which is the hand-kept-number bug
        _rejects(_OK.replace("v0.1.0-beta", "v9.9.9"), "does not SHOW the build"),
        # BACK POINTING AT /games instead of the root
        # ⚠ Keep the root anchor and ADD a /games one. Replacing it outright
        # trips "no way back" first, which is a different rule passing.
        _rejects(_OK.replace('<a href="https://tenshinarts.com">',
                             '<a href="https://tenshinarts.com/games">Games</a>'
                             '<a href="https://tenshinarts.com">'), "site ROOT"),
        # THE TAP FLOOR, three ways — the value, the shared rule, the override
        _rejects(_OK.replace("--tap:24px", "--tap:18px"), "WCAG 2.5.8"),
        _rejects(_OK.replace("--tap:24px", "--taps:24px"), "WCAG 2.5.8"),
        _rejects(_OK.replace("footer a,footer button,.rbox summary{min-height:var(--tap)}",
                             "footer a,footer button,.rbox summary{color:red}"), "24px floor"),
        _rejects(_OK.replace("footer a[href]{padding:4px 6px}", "footer a[href]{padding:0}"),
                 "glyph box"),
        # G4, the board, and a feed that fails silently
        _rejects(_OK.replace('id="btnBrief"', 'id="btnHelp"'), "replayable"),
        _rejects(_OK.replace("function brief(){}", ""), "replayable"),
        _rejects(_OK.replace("/leaderboard.json", "/board.json"), "no client here reaches it"),
        _rejects(_OK.replace("renderBoard", "drawBoard"), "renderer is missing"),
        _rejects(_OK.replace("es.onerror=function(){};", ""), "fails silently"),
        # A BROKEN PAGE that still returns 200
        _rejects(_OK.replace("</script>", ""), "unbalanced script"),
    ]
    print(f"tenshin_chrome self-check OK — the house order is {' · '.join(ORDER)}, and "
          f"{len(n)} broken pages were REJECTED (chrome out of order, a reporter with no box, "
          f"an embed dropping `back` instead of `sign out`, an unresolved __VERSION__, a "
          f"padding:0 hit box) while the healthy page passed signed-in and signed-out")


if __name__ == "__main__":
    _self_check()
