# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-06-01

### Fixed
- **CSV import of the bundled sample file** ([dahuawin/services/csv_loader.py](dahuawin/services/csv_loader.py)) — the "Vzor CSV" toolbar action writes the file with a UTF-8 BOM (`utf-8-sig`), but `CSVLoader` opened it as plain `utf-8`. The BOM ended up glued to the first column header (`﻿Web Site`), so `row.get("Web Site")` returned empty, the IP was never extracted and every row was silently skipped. Loader now reads with `utf-8-sig`, which transparently strips the BOM when present and is a no-op when it isn't.

## [0.1.1] - 2026-05-26

### Added
- **UI Settings dialog** ([dahuawin/settings_dialog.py](dahuawin/settings_dialog.py)) — modal dialog accessible from the toolbar that lets the user edit the reference values used by the NTP / DST / clock-drift checks without touching `config.py`:
  - Allowed NTP server addresses (whitelist), NTP port, NTP enabled flag
  - Full DST schedule (start / end — month, week, day, hour) and DST enabled flag
  - Max. time drift tolerance (seconds)
  - **Restore defaults** button (clears the override → falls back to `config.py` values)
- **Settings store** ([dahuawin/settings_store.py](dahuawin/settings_store.py)) — runtime override layer backed by `QSettings` (Windows registry under `HKCU\Software\OFZ\Camera Checker`). All reference values are read through this module with `config.EXPECTED_*` constants as the fallback when nothing is persisted yet.
- **Slovak + English translations** for all new settings UI strings (`settings_*` keys in [dahuawin/translations.py](dahuawin/translations.py)).

### Changed
- Vendor modules ([dahua_camera.py](dahuawin/camera_modules/dahua_camera.py), [hikvision_camera.py](dahuawin/camera_modules/hikvision_camera.py), [base_camera.py](dahuawin/camera_modules/base_camera.py)) and [services/camera_checker.py](dahuawin/services/camera_checker.py) now read reference values through `settings_store` instead of importing `config.EXPECTED_*` directly. This means the user's UI overrides are picked up automatically — no app restart required.
- Hikvision `set_dst_settings` previously wrote a hardcoded XML payload; it now uses the values from `settings_store.expected_dst()` so auto-fix produces output consistent with the configured reference values.
- `BaseCamera.check_all` clock-drift threshold is now driven by `settings_store.max_time_diff_seconds()` instead of the hardcoded `60`.

### Notes
- `config.py` remains the single source of **defaults** — the values there still apply when the UI dialog has not been used yet.
- To fully reset the override on a machine, delete `HKCU\Software\OFZ\Camera Checker` from the registry (or click **Restore defaults** + **Save** in the dialog).

## [0.1.0] - 2026-05-25

### Added
- Initial release of Camera Checker.
- Parallel NTP / DST / clock-drift audit for Dahua and Hikvision IP cameras driven from a CSV file.
- Qt UI (PySide6) with filterable stat cards, results table, CSV / Excel export, single-camera recheck, "open in browser" fix shortcut.
- SK / EN translations and dark / light theme toggle.
- Built-in demo mode (`--demo`) with synthetic data on `192.0.2.0/24` (RFC 5737) — no network calls.

[0.1.2]: https://github.com/Orimslav/camera_checker/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Orimslav/camera_checker/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Orimslav/camera_checker/releases/tag/v0.1.0
