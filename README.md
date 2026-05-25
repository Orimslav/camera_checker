# Camera Checker

---

## EN — English

Desktop application for auditing **Dahua and Hikvision IP cameras** — checks NTP servers,
DST settings and clock drift in parallel, surfaces issues per camera, and lets you fix
them straight from the UI.

![Camera Checker](img/camera_checker.gif)

### Features

- Import camera list from a CSV file
- Parallel check of NTP, DST and time drift across all cameras
- Filter results by status (OK / problem / auth failed / skipped) via clickable stat cards
- Recheck a single camera after fixing it
- Export results to CSV or Excel
- Open the camera's web UI directly from the app
- Built-in demo mode with synthetic data on `192.0.2.0/24` (RFC 5737) — no real cameras contacted
- SK / EN UI, dark / light theme

### Download

Pre-built binary is available on the [Releases](https://github.com/Orimslav/camera_checker/releases/latest) page:

| Platform | File |
|----------|------|
| Windows | `CameraChecker.exe` |

### Requirements (run from source)

- Python 3.10+
- PySide6 6.8.1
- requests 2.32.3 · openpyxl 3.1.5

### Installation (run from source)

```bash
git clone https://github.com/Orimslav/camera_checker.git
cd camera_checker

python -m venv venv
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Usage

```bash
# Run the application
python main.py

# Run the built-in demo (English UI, synthetic data, no network calls)
python main.py --demo
```

`main.py` automatically re-launches itself under the project's `venv` if one exists,
so it never silently runs against your global Python.

### CSV format

A CSV file with these columns:

| Column | Used for |
|--------|----------|
| `Web Site` | Camera URL — IP is extracted by regex |
| `Login Name` or `Username` | HTTP auth username |
| `Password` | HTTP auth password |
| `Account` | Friendly camera name |
| `Comments` | Optional — model code (`IPC-…`, `DS-…`) is parsed from here |

Rows missing IP, username or password are silently skipped.

### What gets checked

| Check | Notes |
|-------|-------|
| **Authentication** | HTTP Digest then HTTP Basic (Dahua) · ISAPI auth (Hikvision) |
| **Current time** | Reads camera clock, compares to host time |
| **Clock drift** | Flagged as problem when `|drift| > 60s` |
| **NTP settings** | Server address, port, enabled flag — compared to expected values in `config.py` |
| **DST settings** | Start/end month, week, day, hour — compared to EU schedule in `config.py` |

Switches, servers and manually skipped IPs (`config.SKIP_IPS`) appear in the table as
**skipped** so you keep visibility without burning network calls on them.

### Configuration

Site-specific policy lives in `dahuawin/config.py`:

- `EXPECTED_NTP_ADDRESSES`, `EXPECTED_NTP_PORT`
- `EXPECTED_DST` — full EU DST schedule
- `MAX_TIME_DIFF_SECONDS` — drift tolerance (default 60s)
- `SLOW_IPS` — cameras that need the longer 20s timeout
- `SKIP_IPS` — manually excluded cameras
- `MAX_WORKERS` — parallel check concurrency (default 10)
- Vendor detection keyword lists

---

## SK — Slovensky

Desktopová aplikácia na kontrolu **Dahua a Hikvision IP kamier** — paralelne overí
NTP servery, DST nastavenia a časovú odchýlku, ukáže problémy po jednotlivých kamerách
a umožní ich opraviť priamo z aplikácie.

![Camera Checker](img/camera_checker.gif)

### Funkcie

- Import zoznamu kamier z CSV súboru
- Paralelná kontrola NTP, DST a časovej odchýlky na všetkých kamerách
- Filtrovanie výsledkov podľa stavu (OK / problém / chyba prihlásenia / preskočené) cez klikateľné štatistické karty
- Opätovná kontrola jednej kamery po oprave
- Export výsledkov do CSV alebo Excelu
- Otvorenie web rozhrania kamery priamo z aplikácie
- Vstavaný demo režim so syntetickými dátami na `192.0.2.0/24` (RFC 5737) — žiadne skutočné kamery
- SK / EN rozhranie, tmavá / svetlá téma

### Stiahnutie

Pripravená binárka je dostupná na stránke [Releases](https://github.com/Orimslav/camera_checker/releases/latest):

| Platforma | Súbor |
|-----------|-------|
| Windows | `CameraChecker.exe` |

### Požiadavky (spustenie zo zdrojového kódu)

- Python 3.10+
- PySide6 6.8.1
- requests 2.32.3 · openpyxl 3.1.5

### Inštalácia (spustenie zo zdrojového kódu)

```bash
git clone https://github.com/Orimslav/camera_checker.git
cd camera_checker

python -m venv venv
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Spustenie

```bash
# Spustenie aplikácie
python main.py

# Spustenie vstavaného demo režimu (anglické UI, syntetické dáta, žiadne sieťové volania)
python main.py --demo
```

`main.py` sa pri spustení automaticky prepne na projektový `venv` ak existuje,
takže nikdy nebude potichu bežať z globálneho Pythonu.

### Formát CSV

CSV súbor s týmito stĺpcami:

| Stĺpec | Použitie |
|--------|----------|
| `Web Site` | URL kamery — IP sa vytiahne regexom |
| `Login Name` alebo `Username` | HTTP auth meno |
| `Password` | HTTP auth heslo |
| `Account` | Zobrazený názov kamery |
| `Comments` | Voliteľné — model (`IPC-…`, `DS-…`) sa parsuje odtiaľto |

Riadky bez IP, mena alebo hesla sa ticho preskočia.

### Čo sa kontroluje

| Kontrola | Poznámka |
|----------|----------|
| **Autentifikácia** | HTTP Digest potom HTTP Basic (Dahua) · ISAPI auth (Hikvision) |
| **Aktuálny čas** | Načíta hodiny kamery, porovná s časom hostu |
| **Časová odchýlka** | Označená ako problém keď `|odchýlka| > 60s` |
| **NTP nastavenia** | Adresa servera, port, enable flag — porovnané s očakávanými hodnotami v `config.py` |
| **DST nastavenia** | Začiatok/koniec — mesiac, týždeň, deň, hodina — porovnané s EU rozvrhom v `config.py` |

Switche, servery a manuálne preskočené IP (`config.SKIP_IPS`) sa zobrazia v tabuľke ako
**preskočené** — máš o nich prehľad ale neminieš na ne sieťové volanie.

### Konfigurácia

Site-špecifická konfigurácia je v `dahuawin/config.py`:

- `EXPECTED_NTP_ADDRESSES`, `EXPECTED_NTP_PORT`
- `EXPECTED_DST` — kompletný EU DST rozvrh
- `MAX_TIME_DIFF_SECONDS` — tolerancia časovej odchýlky (predvolene 60s)
- `SLOW_IPS` — kamery ktoré potrebujú dlhší 20s timeout
- `SKIP_IPS` — manuálne vylúčené kamery
- `MAX_WORKERS` — počet paralelných kontrol (predvolene 10)
- Zoznamy kľúčových slov pre detekciu výrobcu
