# Viz-QWIM — Team Dashboard

This folder is the single shared dashboard app for the team's QWIM project.
Every team member's individual model plugs into this same tree as its own
subfolder — there is one dashboard, with one tab per model.

**Status:** the full framework from the advisor (`main_App.py`, the
pre-built models like `portfolio_optimization/`, `discounting/`, etc.,
`clients_QWIM/`, `inputs/`, etc.) has been unpacked and merged into `main`.
This folder is now the complete, working dashboard app — pull the latest
`main` and you have everything you need to get started.

**Known gap:** two file types were intentionally left out of that merge and
still need to be added separately:
- `src/dashboard/reporting/*.typ` — Typst templates the **Reporting** subtab
  needs to generate PDFs
- `tests/regression_data/**/*.parquet` and `tests/_baselines/` — fixture
  data some regression tests compare against

If the Reporting subtab or `pytest tests -n auto -q` fails for you, this is
the likely reason — it's not something broken in your own setup. Flag it in
the next advisor meeting rather than debugging around it.

## Getting set up locally

```bash
mkdir -p ~/Desktop/Git_Repos && cd ~/Desktop/Git_Repos
git clone https://github.com/cl8550-crypto/qwim_team5.git
cd qwim_team5/Viz-QWIM
pip install -U pip uv ruff
uv add polars          # bootstraps .venv/ from pyproject.toml
source .venv/bin/activate
pytest tests -n auto -q
shiny run --launch-browser src/dashboard/main_App.py
```

## Where your files go

Add your own model as a new subfolder, named after your model, in **three**
places — mirroring the pattern already used by `goal_parity`:

```
src/models/<your_model_name>/              # your model's logic
src/dashboard/shiny_tab_<your_model_name>/ # your model's dashboard tab
tests/tests_unit/models/<your_model_name>/ # your model's unit tests
```

Optionally, if your model needs tunable constants:

```
configs/<your_model_name>_config.yaml
```

Do **not** add files directly under `src/models/`, `src/dashboard/`, or
`tests/tests_unit/models/` — always nest them inside your own
`<your_model_name>/` subfolder, so your work never collides with a
teammate's.

## Naming conventions (see `src/models/goal_parity/` as a worked example)

**`src/models/<name>/`**
- `__init__.py` — module docstring, `from __future__ import annotations`
- `utils_<name>.py` — shared constants for your model
- `_<name>_<step>.py` — one private module per pipeline step/component
  (e.g. `_goalparity_cashflow.py`, `_goalparity_optimization.py`)

**`src/dashboard/shiny_tab_<name>/`**
- `__init__.py`
- `tab_<name>.py` — the tab's `@module.ui` / `@module.server` entry points,
  aggregating subtabs via `ui.navset_tab`
- `subtab_<name>_<subtab>.py` — one file per subtab, public UI/server facade
- `_subtab_<name>_<subtab>_data.py` / `_rendering.py` — optional private
  helpers once a subtab's logic grows past a few lines

**`tests/tests_unit/models/<name>/`**
- `__init__.py`
- `test_<name>_<thing>.py` — one test file per module in `src/models/<name>/`

## Workflow

Follow the advisor's guideline: work on your own feature branch (named after
your model, e.g. `<your-model-name>-model`), created off the latest `main`
(not an older commit — `main` now has the full framework). Open a pull
request when your tab runs and `pytest tests -n auto -q` passes, and merge
via squash-and-merge to keep `main`'s history to one entry per model.

Regularly rebase your branch on the latest `main` and rerun the tests after,
so you catch conflicts early rather than at the end.
