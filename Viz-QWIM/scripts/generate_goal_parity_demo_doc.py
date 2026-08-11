"""Generate the QWIM Dashboard demo guide (.docx) with live screenshots.

Captures every main tab and Goal Parity subtab from a RUNNING dashboard via
headless Playwright (including one completed Historical Backtest run), then
assembles a client-facing walkthrough document. The output is committed as a
static asset served by the Overview & Guide subtab's download button.

Usage (dashboard must already be running):
    .venv/bin/shiny run src/dashboard/main_App.py &
    .venv/bin/python scripts/generate_goal_parity_demo_doc.py \
        [--url http://127.0.0.1:8000] [--out <path.docx>]
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from PIL import Image
from playwright.sync_api import sync_playwright


DEFAULT_OUT = (
    Path(__file__).resolve().parents[1]
    / "src" / "dashboard" / "shiny_tab_goal_parity" / "assets"
    / "QWIM_Dashboard_Demo_Guide.docx"
)

MAIN_TABS = ["Overview", "Setup", "Clients", "Portfolios", "Products", "Results"]
GP_SUBTABS = [
    "Overview & Guide",
    "Investor Profile",
    "4×4 Asset Map",
    "Strategic Optimization",
    "Tactical Rebalancing",
    "Historical Backtest",
]

IMAGE_WIDTH_IN = 6.3
#: Split full-page captures taller than this many px so no image overflows a page.
MAX_IMAGE_HEIGHT_PX = 1200


def _slug(name: str) -> str:
    return name.lower().replace(" & ", "_").replace(" ", "_").replace("×", "x")


def capture_screenshots(url: str, shots_dir: Path) -> None:
    """Screenshot every tab/subtab of the running dashboard."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(4000)

        for tab in MAIN_TABS:
            page.click(f"nav >> text={tab}")
            page.wait_for_timeout(2500)
            page.screenshot(path=shots_dir / f"tab_{_slug(tab)}.png")

        page.click("nav >> text=Goal Parity")
        page.wait_for_timeout(1500)
        for subtab in GP_SUBTABS:
            page.click(f"a:has-text('{subtab}')")
            page.wait_for_timeout(2500)
            page.screenshot(
                path=shots_dir / f"gp_{_slug(subtab)}.png",
                full_page=(subtab == "Overview & Guide"),
            )

        page.click("button:has-text('Run backtest')")
        page.wait_for_timeout(12000)
        page.screenshot(path=shots_dir / "gp_historical_backtest_results.png")
        browser.close()


def _add_picture(document: Document, path: Path, caption: str) -> None:
    """Insert an image (splitting page-overflowing captures) plus a caption."""
    image = Image.open(path)
    width, height = image.size
    if height > MAX_IMAGE_HEIGHT_PX:
        pieces = []
        for top in range(0, height, MAX_IMAGE_HEIGHT_PX):
            piece = image.crop((0, top, width, min(top + MAX_IMAGE_HEIGHT_PX, height)))
            piece_path = path.with_name(f"{path.stem}_part{top}.png")
            piece.save(piece_path)
            pieces.append(piece_path)
    else:
        pieces = [path]
    for piece_path in pieces:
        document.add_picture(str(piece_path), width=Inches(IMAGE_WIDTH_IN))
    paragraph = document.add_paragraph()
    run = paragraph.add_run(caption)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x6C, 0x75, 0x7D)


def build_document(shots_dir: Path, out_path: Path) -> None:
    document = Document()

    title = document.add_heading("QWIM Dashboard — Demo & User Guide", level=0)
    for run in title.runs:  # default Title style (28pt) wraps to two lines
        run.font.size = Pt(22)
    document.add_paragraph(
        "This guide walks through the QWIM dashboard the way we present it to "
        "business partners: what each tab shows, the order to demo it in, and "
        "the talking points for the Goal Parity investment model. Screenshots "
        "are taken from the live dashboard."
    )

    document.add_heading("Suggested demo flow", level=1)
    for line in [
        "Open on the Overview tab and state the value proposition in one line.",
        "Show Clients: the advisor-entered profile that personalizes everything downstream.",
        "Walk the Goal Parity tab left to right — it is a story in six steps.",
        "Close with the Historical Backtest: out-of-sample evidence, then the Results tab.",
    ]:
        document.add_paragraph(line, style="List Number")

    document.add_heading("The main tabs", level=1)
    tab_notes = {
        "Overview": (
            "The executive summary — the one-slide version of the QWIM "
            "approach. Start the demo here and keep it short."
        ),
        "Setup": (
            "Data sources, computation settings, and per-subtab console "
            "verbosity. In a partner demo you normally skip this tab; mention "
            "it exists so partners know configuration is centralized."
        ),
        "Clients": (
            "The advisor enters the client's personal information, assets, "
            "income, and goals here. Emphasize that models downstream — "
            "including Goal Parity — read this profile automatically: enter "
            "the client once, and every analysis is personalized."
        ),
        "Portfolios": (
            "Classical portfolio construction and comparison tooling "
            "(analysis, optimizers, benchmarks). Useful to frame Goal Parity "
            "against: this is the conventional toolkit."
        ),
        "Products": (
            "The investable product shelf backing the portfolios."
        ),
        "Results": (
            "Simulations and consolidated outputs, and where the client PDF "
            "report is produced. End the demo here: everything shown on "
            "screen can be handed to the client as a document."
        ),
    }
    for tab in MAIN_TABS:
        document.add_heading(tab, level=2)
        document.add_paragraph(tab_notes[tab])
        _add_picture(document, shots_dir / f"tab_{_slug(tab)}.png", f"The {tab} tab.")

    document.add_heading("The Goal Parity tab — step by step", level=1)
    document.add_paragraph(
        "Goal Parity builds the portfolio around four client goals — "
        "Liquidity, Income, Preservation, and Growth — instead of a single "
        "market benchmark. Demo the subtabs left to right; each step feeds "
        "the next."
    )
    # Per subtab: (intro paragraph, list of instruction bullets). A bullet is
    # either a string, or a (text, [sub-bullets]) pair for nested detail.
    gp_notes: dict[str, tuple[str, list]] = {
        "Overview & Guide": (
            "The landing page: why goal-based investing holds up across "
            "market regimes, and the step-by-step usage guide. This document "
            "can be downloaded from the button here.",
            [
                "Read the five advantage cards first — they are the 'why' "
                "behind everything that follows.",
                "The numbered stepper below them mirrors the subtabs to the "
                "right; use it as your checklist while working through them.",
                "Skim the amber 'Common mistakes' box before starting — it "
                "covers the errors that most often lead to misleading results.",
            ],
        ),
        "Investor Profile": (
            "Step 1 — tell the model who you are. The client's risk comfort "
            "and time horizon become the model's risk-aversion parameter and "
            "personal loss barrier.",
            [
                (
                    "If your advisor has filled in the Clients tab, leave "
                    "'Use Clients tab inputs' checked — your horizon and risk "
                    "profile flow in automatically; nothing else to do.",
                    [],
                ),
                (
                    "Otherwise, uncheck the box and set three sidebar inputs:",
                    [
                        "Risk profile — from Conservative to Aggressive; when "
                        "unsure, start with Moderate.",
                        "Strategic horizon T — years until the money is "
                        "needed (e.g. years to retirement). Use the real "
                        "timeline: a too-short horizon makes the portfolio "
                        "overly cautious.",
                        "Rebalancing frequency τ — how often the portfolio is "
                        "reviewed. Semi-annual is the recommended default.",
                    ],
                ),
                (
                    "Before moving on, check two things on the right:",
                    [
                        "The table's 'loss tolerance' row — the decline you "
                        "could accept before changing course. If it feels "
                        "wrong, adjust the risk profile.",
                        "The 'Source:' line — it says whether inputs came "
                        "from the Clients tab or the sidebar. If it says "
                        "Clients tab but that tab is empty or stale, uncheck "
                        "the box and enter values manually.",
                    ],
                ),
            ],
        ),
        "4×4 Asset Map": (
            "Steps 2–4 — choose what the model can invest in. Every asset is "
            "scored on how it actually behaves toward each goal (option-style "
            "triggers, not static labels), and the scatter places each asset "
            "between the four goal corners.",
            [
                "Tick the checkboxes for the investments to consider; keeping "
                "the full default list selected is a good starting point.",
                "One asset can serve several goals at once (e.g. part Income, "
                "part Preservation) — hover the scatter points to see each "
                "asset's split.",
                "Keep the universe broad: every goal needs at least a few "
                "supporting assets. If a later step flags a goal as "
                "'structurally scarce', return here and re-add tickers rather "
                "than fighting the optimizer.",
            ],
        ),
        "Strategic Optimization": (
            "Step 5 — build the target portfolio. The optimizer balances the "
            "four goal powers (default: 25% each) or applies a deliberate "
            "tilt toward one goal.",
            [
                "Start with Goal Parity Balanced (the default) — for most "
                "clients this is the recommended portfolio.",
                (
                    "Choose Goal Tilted only to deliberately favor one goal "
                    "(more Growth for a young saver, more Income near "
                    "retirement):",
                    [
                        "Pick the goal, then set the tilt-strength slider — "
                        "small tilts (10–30%) are usually enough.",
                        "A tilt shifts priorities between goals; it is NOT a "
                        "'more return' dial. Maximum tilt concentrates the "
                        "portfolio and gives up diversification.",
                    ],
                ),
                (
                    "Read any warning banners before trusting the numbers:",
                    [
                        "'Solver failure' — the shown weights are a best "
                        "effort; confirm with your advisor before acting.",
                        "'Structurally scarce goal' — the chosen investments "
                        "cannot support that goal much further; fix it in "
                        "Step 2, not here.",
                    ],
                ),
            ],
        ),
        "Tactical Rebalancing": (
            "Step 6 — see how the portfolio stays on track. This page is a "
            "simulation: markets drift the portfolio away from its targets, "
            "and the model shows the cost-aware trades that restore the goal "
            "balance.",
            [
                "Two controls: the σ slider sets how large the simulated "
                "market move is; the seed picks which random scenario is "
                "shown.",
                (
                    "Read the results top to bottom:",
                    [
                        "The summary line — number of trades and portfolio "
                        "turnover (capped by design: the model will not churn "
                        "everything).",
                        "The bar chart — goal support drifted → after "
                        "rebalance → target; bars should move back toward the "
                        "target.",
                        "The trade table — each row is one sell/buy pair, "
                        "ranked so the most goal-restoring, lowest-cost "
                        "trades come first.",
                    ],
                ),
                "Different seeds give different trades — that is expected: "
                "each seed is a different market scenario, not a different "
                "answer to the same question.",
            ],
        ),
        "Historical Backtest": (
            "The evidence — a walk-forward replay with no look-ahead: the "
            "model is re-trained on past data only at every step, its "
            "portfolio is held for one step, and realized results accumulate "
            "next to a classic 60/40 benchmark.",
            [
                (
                    "Four sidebar settings (the defaults are sensible — start "
                    "there):",
                    [
                        "Backtest date range — which slice of history to "
                        "replay.",
                        "Training window — years of past data the model "
                        "learns from at each step; keep it at 2.5 years or "
                        "more, shorter windows trigger a noise warning.",
                        "Test window — the horizon each fold's performance is "
                        "measured over in the fold table.",
                        "Step size — how often the model re-trains and "
                        "rebalances; leave it equal to the review frequency τ "
                        "unless there is a reason not to.",
                    ],
                ),
                (
                    "Click 'Run backtest' and read the results top to bottom:",
                    [
                        "The chart — growth of $1 for the model vs. the "
                        "benchmark; dotted vertical lines mark re-training "
                        "dates.",
                        "The metrics table — return, volatility, Sharpe "
                        "ratio, and max drawdown side by side.",
                        "The fold table — per-period results, showing when "
                        "the model helped (stress periods) and when it lagged "
                        "(strong bull runs).",
                    ],
                ),
                "A red message means the configuration is impossible (e.g. "
                "the date range is too short for the training window) — "
                "shrink the training window or widen the dates.",
            ],
        ),
    }
    for subtab in GP_SUBTABS:
        intro, bullets = gp_notes[subtab]
        document.add_heading(subtab, level=2)
        document.add_paragraph(intro)
        _add_picture(
            document,
            shots_dir / f"gp_{_slug(subtab)}.png",
            f"Goal Parity — {subtab}.",
        )
        document.add_paragraph("How to use this page:").runs[0].bold = True
        for bullet in bullets:
            if isinstance(bullet, tuple):
                text, children = bullet
                document.add_paragraph(text, style="List Bullet")
                for child in children:
                    document.add_paragraph(child, style="List Bullet 2")
            else:
                document.add_paragraph(bullet, style="List Bullet")

    document.add_heading("Common mistakes to avoid", level=2)
    for mistake in [
        "Jumping straight to Optimization or Rebalancing — the results then "
        "reflect the default Moderate profile, not the client's.",
        "Leaving 'Use Clients tab inputs' checked when the Clients tab is "
        "empty or stale — always check the 'Source:' line in Step 1.",
        "Setting a horizon shorter than the client's actual timeline, which "
        "understates how much Growth the plan can safely carry.",
        "Ignoring the solver-failure or scarce-goal warnings in Step 3 — "
        "they qualify every number shown downstream.",
        "Comparing rebalancing trades across different drift seeds and "
        "concluding the model is unstable — each seed is a different "
        "scenario.",
    ]:
        document.add_paragraph(mistake, style="List Bullet")

    document.add_heading("Backtest results (live run)", level=2)
    document.add_paragraph(
        "A completed run with the default settings (3-year training window, "
        "6-month step). The talking point: Goal Parity targets smaller "
        "drawdowns and lower volatility than the 60/40 benchmark — it gives "
        "up some upside in strong bull markets in exchange for a smoother "
        "ride through stress periods. It is not trying to beat the "
        "benchmark's raw return."
    )
    _add_picture(
        document,
        shots_dir / "gp_historical_backtest_results.png",
        "Historical Backtest after a completed run: out-of-sample equity "
        "curves and side-by-side performance metrics.",
    )

    document.add_heading("Practical notes for presenters", level=1)
    for note in [
        "Warning banners are features, not bugs: solver-failure and "
        "scarce-goal notes tell the advisor when judgement is needed — "
        "demo one deliberately if asked about model limits.",
        "Backtest guardrails reject impossible window configurations and "
        "warn on training windows under ~2.5 years.",
        "All figures are illustrative and do not constitute investment "
        "advice.",
    ]:
        document.add_paragraph(note, style="List Bullet")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(out_path))
    print(f"Wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        shots_dir = Path(tmp)
        capture_screenshots(args.url, shots_dir)
        build_document(shots_dir, args.out)


if __name__ == "__main__":
    main()
