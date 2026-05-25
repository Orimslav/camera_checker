# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Camera Checker (package: `dahuawin`, repo dir: `DahuaWin`) is a PySide6 desktop app (Windows) that audits Dahua and Hikvision IP cameras from a CSV file, checking NTP, DST, and clock drift in parallel and surfacing problems for fix-up. Source language for UI strings, comments, and user-facing text is Slovak (with an English translation layer); keep new strings consistent and route them through `dahuawin/translations.py`.

## Common commands

PowerShell, run from the repo root:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

There is no test suite, linter, or build step configured — `python main.py` is the only run target. `main.py` re-execs itself under `./venv` or `./.venv` if one exists (see `_relaunch_in_project_venv`), so you can launch it from any interpreter and it will land on the project venv. The `DAHUAWIN_VENV_BOOTSTRAPPED=1` env var short-circuits that re-exec.

## Architecture

Three layers, top-down:

1. **`dahuawin/app.py`** — the entire Qt UI lives in one `MainWindow` class plus a `CheckWorker(QThread)` that runs `CameraChecker` off the UI thread and emits `progress_changed` / `finished_with_results` / `failed` signals. All theming (light/dark) and i18n (sk/en) is handled by re-applying stylesheets and re-reading from `TRANSLATIONS` on toggle — there is no Qt translator infrastructure. The 7-column results table is filterable by clicking the stat cards (`_set_filter` → `_filtered_results` → `_refresh_table`).

2. **`dahuawin/services/`** — pure-Python orchestration, no Qt:
   - `CSVLoader` parses CSV files with columns `Web Site`, `Login Name`/`Username`, `Password`, `Account`, `Comments`. Extracts the IP via regex from the URL and a model code via prefix patterns from the comments column. Rows missing IP/username/password are silently skipped.
   - `CameraChecker` is the orchestrator: `run_check` fans cameras out across a `ThreadPoolExecutor(max_workers=config.MAX_WORKERS)` and reports completion via `progress_callback(done, total, result)`. `summarize` bucketizes results into ok / problems / auth_failed / skipped — the same keys used by the UI filter and stat cards.
   - `ResultExporter` writes CSV/Excel using its own internal `TRANSLATIONS` table (separate from `dahuawin/translations.py` — column headers live here).

3. **`dahuawin/camera_modules/`** — vendor abstraction:
   - `BaseCamera` (ABC) defines the contract: `authenticate`, `get_current_time`, `get_ntp_settings`, `get_dst_settings`, `set_*`, `sync_time_now`. `check_all` is the template method that calls auth → time → ntp → dst, concatenates `ntp_issues + dst_issues`, and prepends a time-drift issue when `|time_diff| > 60s`. The hardcoded 60 here intentionally mirrors `config.MAX_TIME_DIFF_SECONDS`.
   - `DahuaCamera` talks to the Dahua CGI API (`/cgi-bin/magicBox.cgi`, `/cgi-bin/global.cgi`, etc.) and tries HTTP Digest then HTTP Basic auth.
   - `HikvisionCamera` talks to the Hikvision ISAPI XML endpoints.
   - `DeviceDetector.detect_vendor` resolves model + name to one of `Hikvision` / `Switch` / `Server` / `Dahua` / `Unknown` using keyword/prefix lists from `config.py`. Switches and servers get a `DahuaCamera` instance with `skipped=True` set so `check_all` short-circuits — this is intentional to keep them visible in the table as "skipped" rather than dropped.

`config.py` centralizes everything site-specific: expected NTP servers (`192.168.10.5`, `cams.ofz.sk`), DST schedule (EU rules), the `SLOW_IPS` list that bumps timeout from 10s to 20s, `SKIP_IPS` for manual skips, `MAX_WORKERS`, and the vendor-detection keyword lists. Change site policy here, not in the camera modules.

## Conventions worth knowing

- Result dicts (the rows passed around between checker, UI, exporter) are loosely typed `Dict` with stable keys defined by `BaseCamera.to_dict`. When adding a field, update `to_dict`, the table population in `app.py._populate_table`, and the exporter headers.
- The four status buckets (`ok`, `problem`, `auth_failed`, `skipped`) are derived by `MainWindow._camera_status_key` from `skipped` / `auth_ok` / `issues` — there's no explicit status field on the dict. Don't add one; derive consistently.
- Translation keys are required for any user-facing string; add to both `sk` and `en` blocks in `dahuawin/translations.py`. Exporter headers are a separate table inside `ResultExporter`.
