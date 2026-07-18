"""
Turn an FPL bill file (PDF or image, digital or scanned) into structured fields.

Two stages:
  1. get_text()   -- extract a text layer; if the PDF has none (scanned),
                     rasterize and OCR it with tesseract.
  2. parse_fields() -- pull labeled values with a configurable regex map.

The regex map targets the field *labels* that appear on FPL business bills.
Layouts vary between rate classes and over time, so treat REGEX_MAP as a
starting template: when a field comes back blank on your real bills, adjust
that one pattern (see README -> "Tuning to your bills").
"""
import re
import os

# ---------------------------------------------------------------- text layer
def get_text(path, ocr_dpi=300, force_ocr=False):
    """Return (text, method). method is 'text-layer' or 'ocr'."""
    ext = os.path.splitext(path)[1].lower()

    if ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
        return _ocr_image(path), "ocr"

    import fitz  # PyMuPDF
    doc = fitz.open(path)
    text = "\n".join(page.get_text() for page in doc)

    # A digital FPL PDF yields plenty of text; a scan yields ~nothing.
    if force_ocr or len(text.strip()) < 40:
        text = _ocr_pdf(path, dpi=ocr_dpi)
        return text, "ocr"
    return text, "text-layer"


def _ocr_pdf(path, dpi=300):
    from pdf2image import convert_from_path
    import pytesseract
    pages = convert_from_path(path, dpi=dpi)
    return "\n".join(pytesseract.image_to_string(p) for p in pages)


def _ocr_image(path):
    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(path))


# ---------------------------------------------------------------- field parse
# Each field maps to an ordered list of patterns; first match wins. Patterns
# are case-insensitive. Keep the numeric capture group named 'v'.
_NUM = r"(?P<v>[\d,]+(?:\.\d+)?)"
_DATE = r"(?P<v>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"

REGEX_MAP = {
    "account_number": [
        r"account\s*(?:number|no\.?|#)\s*[:\-]?\s*(?P<v>[\d\-]{6,})",
    ],
    "meter_number": [
        # "Meter reading - Meter MV51029" — require at least one digit
        # (excludes "SUMMARY", "reading", etc.)
        r"[Mm]eter\s+(?P<v>(?=\S*\d)[A-Z0-9]{5,})\b",
        r"meter\s*(?:number|no\.?|#)\s*[:\-]?\s*(?P<v>(?=\S*\d)[A-Z0-9]{5,})",
    ],
    "rate_schedule": [
        r"rate\s*(?:schedule)?\s*[:\-]?\s*(?P<v>GSLDT?-\d|GSDT?-\d|GST?-\d|"
        r"SDTR-\d[AB]?|CST?-\d|OL-\d|SL-\d|OS-\d|LT-\d)",
        r"\b(?P<v>GSLDT-\d|GSLD-\d|GSDT-\d|GSD-\d|GST-\d|GS-\d|SDTR-\d[AB]?|"
        r"OL-\d|SL-\d|OS-\d)\b",
    ],
    "service_period_start": [
        r"service\s+(?:from|period)\D{0,10}" + _DATE,
        r"billing\s+period\D{0,10}" + _DATE,
    ],
    "service_period_end": [
        r"(?:to|through|thru)\s+" + _DATE + r"\s*(?:\(|\d+\s*days)",
        r"service\s+(?:from|period).{0,40}?(?:to|-)\s+" + _DATE,
    ],
    "days_in_period": [
        r"(?P<v>\d{1,2})\s*(?:billing\s*)?days",
    ],
    "kwh_total": [
        # ENERGY USAGE COMPARISON section: line starts with "kWh Used  55560"
        # (not preceded by on/off-peak)
        r"^\s*kwh\s+used\s+(?P<v>\d[\d,]*)\s*$",
    ],
    "kwh_on_peak": [
        r"on[\-\s]*peak\s+kwh\s+used?\s+(?P<v>\d{3,})\s*$",
    ],
    "kwh_off_peak": [
        r"off[\-\s]*peak\s+kwh\s+used?\s+(?P<v>\d{3,})\s*$",
    ],
    "demand_kw_billed": [
        r"billing\s+demand\D{0,10}" + _NUM,
        r"billed\s+(?:kw|demand)\D{0,10}" + _NUM,
    ],
    "demand_kw_actual": [
        # "Maximum demand  114" as standalone (comparison section)
        r"max(?:imum)?\s+demand\s+(?P<v>\d[\d,]*(?:\.\d+)?)\s*$",
        r"(?:measured|actual)\s+demand\D{0,10}" + _NUM,
        r"demand\s*\(kw\)\D{0,10}" + _NUM,
    ],
    "demand_kw_on_peak": [
        r"on[\-\s]*peak\s+demand\D{0,10}" + _NUM,
    ],
    "total_amount_due": [
        # label then $amount (BILL SUMMARY section)
        r"(?:total\s+amount\s+you\s+owe|total\s+new\s+charges|amount\s+due|"
        r"total\s+current\s+charges|total\s+due)\D{0,6}\$\s*" + _NUM,
        # $amount then label (page header on OCR'd bills)
        r"\$\s*" + _NUM + r"\s{0,30}(?:total\s+amount\s+you\s+owe)",
    ],
    "statement_date": [
        r"(?:statement|bill|invoice)\s+date\D{0,10}" + _DATE,
        # "Statement Date: Jun 16, 2026" (month-name format)
        r"statement\s+date\s*[:\-]?\s*(?P<v>[A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4})",
    ],
}

_NUMERIC_FIELDS = {
    "days_in_period", "kwh_total", "kwh_on_peak", "kwh_off_peak",
    "demand_kw_billed", "demand_kw_actual", "demand_kw_on_peak",
    "total_amount_due",
}


def _clean_num(s):
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _last_number_on_line(text, label_pattern):
    """Find a line matching label_pattern and return its LAST number.

    FPL meter-summary lines look like:
        Total kWh used  43349  42886  120  55560
    where the last number (55560) is the actual usage. Standard regex
    grabs the first (43349 = current reading), which is wrong.
    """
    for line in text.split("\n"):
        if re.search(label_pattern, line, re.IGNORECASE):
            nums = re.findall(r"\d[\d,]*(?:\.\d+)?", line)
            if nums:
                return _clean_num(nums[-1])
    return None


def parse_fields(text):
    """Apply REGEX_MAP to a text blob; return a dict of field -> value."""
    flat = re.sub(r"[ \t]+", " ", text)
    out = {k: None for k in REGEX_MAP}
    for field, patterns in REGEX_MAP.items():
        for pat in patterns:
            m = re.search(pat, flat, re.IGNORECASE | re.MULTILINE)
            if m:
                val = m.group("v").strip()
                out[field] = _clean_num(val) if field in _NUMERIC_FIELDS else val
                break
    # Fallback: for kWh fields, if regex missed (common with meter-summary
    # lines), grab the LAST number on the matching line.
    if out["kwh_total"] is None:
        out["kwh_total"] = _last_number_on_line(text, r"total\s+kwh\s+used")
    if out["kwh_on_peak"] is None:
        out["kwh_on_peak"] = _last_number_on_line(text, r"on[\-\s]*peak\s+kwh\s+used")
    if out["kwh_off_peak"] is None:
        out["kwh_off_peak"] = _last_number_on_line(text, r"off[\-\s]*peak\s+kwh\s+used")
    if out["demand_kw_on_peak"] is not None and out["demand_kw_on_peak"] < 1:
        # Meter line: "On-peak demand 0.95 120.00 114" — grabbed 0.95 (multiplier)
        # instead of 114. Fall back to last number.
        val = _last_number_on_line(text, r"on[\-\s]*peak\s+demand")
        if val and val > out["demand_kw_on_peak"]:
            out["demand_kw_on_peak"] = val
    return out
