# FPL Bill Extractor

Extract data from a folder of FPL commercial electric bills — PDF or image,
digital or scanned — into one spreadsheet, with **load factor** and the
**GS-1 ↔ GSD-1 rate-fit flag** computed for every account.

Fully offline: digital PDFs are read from their text layer, and true scans
fall back to on-device OCR (tesseract). No API keys, no external services.

Built against the FPL business tariff **effective January 2026**.

---

## Install

```bash
git clone https://github.com/<you>/fpl-bill-extractor.git
cd fpl-bill-extractor
pip install -r requirements.txt
```

System OCR dependencies (needed for scanned bills):

```bash
# Ubuntu / Debian
sudo apt-get install tesseract-ocr poppler-utils
# macOS
brew install tesseract poppler
```

## Usage

```bash
python extract_bills.py ./bills -o portfolio.xlsx
python extract_bills.py ./bills --force-ocr      # force OCR on every PDF
```

Drop all your bills into one folder and point the tool at it. Digital and
scanned bills can be mixed freely — the tool detects, per file, whether a PDF
has a text layer and OCRs only the ones that don't. Output is an `.xlsx` with
one row per bill.

Try it on the included samples:

```bash
python extract_bills.py samples -o out.xlsx
```

## What it extracts

Account #, meter, service address, rate schedule, statement date, service
period (start / end / days), total kWh, on-/off-peak kWh (TOU), billed &
measured demand kW, on-peak demand (TOU), amount due.

Then it derives, per bill:

| Column | Meaning |
|---|---|
| `Min kW` | minimum possible demand = kWh ÷ period hours |
| `Load Factor` | kWh ÷ (billed kW × period hours) |
| `Breakeven kW` | peak at which GS-1 and GSD-1 cost the same |
| `Est GS-1` / `Est GSD-1` | modeled monthly cost under each rate |
| `Rec. Rate` | the cheaper rate for that account |
| `Flag` | plain-language result; **misclassified GS-1 rows are highlighted red** |

The `Extract Method` column records whether each bill was read from its
`text-layer` or via `ocr` — a quick quality signal for which rows to
spot-check.

## The rate logic in one paragraph

GS-1 has no demand charge but a high energy rate (~12.66 ¢/kWh). GSD-1 has a
low energy rate (~6.31 ¢/kWh) plus a ~$15.03/kW demand charge. Which is cheaper
depends on **load factor**; the two cross over near **32%**. Separately, the
mandatory class boundary is **GS-1 = 0–20 kW, GSD-1 = 21–499 kW**, so a GS-1
account whose demand exceeds the 20 kW ceiling can't legitimately be on GS-1 at
all — those are flagged as misclassified regardless of load factor.

## Files

```
extract_bills.py   CLI orchestrator + spreadsheet writer
gui.py             Desktop GUI (drag-and-drop)
build_app.py       Packages gui.py as a macOS .app
fpl_parser.py      text/OCR extraction and the FPL field-regex map
rates.py           Jan-2026 tariff constants + screening logic
tests/             pytest suite for the rate logic
samples/           demo bills + make_samples.py to regenerate them
```

## Desktop GUI

For non-terminal users, `gui.py` provides a drag-and-drop interface. Run it
directly or build a macOS `.app` you can double-click from Finder.

**Run directly:**

```bash
source .venv/bin/activate
python gui.py
```

**Build a standalone .app:**

```bash
pip install pyinstaller
python build_app.py
```

This creates `dist/FPL Bill Extractor.app`. Zip it to share with colleagues.
Recipients still need `brew install tesseract poppler` for scanned-bill OCR;
digital PDFs work without them.

## Tuning to your bills

`fpl_parser.REGEX_MAP` targets the field *labels* on FPL business bills.
Layouts vary by rate class and change over time, so if a column comes back
blank on your real bills:

1. Run once and open the spreadsheet to see which fields are empty.
2. In `fpl_parser.py`, find that field in `REGEX_MAP` and add a pattern that
   matches the label your bills use (patterns are an ordered list; first match
   wins, so just append an alternative).

Rate constants live in `rates.py` — update them there when the tariff changes
and every derived number recomputes.

## Caveats

- **Verify against the effective PSC-approved tariff before acting.** The
  tariff prevails over the rate insert. Rate components are confirmed against
  the Jan-2026 insert, and the GS-1/GSD-1 boundary (0–20 / 21–499 kW) against
  Tariff Section 8 (Sheets 8.101 / 8.105); re-check both when rates change.
- Extraction is only as good as the scan. Tesseract can misread a digit or
  drop a comma, and a wrong kWh silently yields a wrong load factor and flag.
  Spot-check `ocr` rows; treat a red flag as a prompt to pull the actual bill,
  not a filing.
- Load factor and rate fit swing across the year (seasonal demand, the SDTR
  split) — run a full 12 months of bills, not a single month, before deciding.
- Rate eligibility depends on service characteristics, not cost alone; FPL must
  agree an account qualifies for a class.

## License

MIT — see [LICENSE](LICENSE).
