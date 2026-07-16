"""Generate synthetic FPL-style bills (digital PDFs + one scanned image)."""
import os
import fitz  # PyMuPDF

os.makedirs(".", exist_ok=True)

BILLS = [
    dict(fn="bill_610_studentunion.pdf", acct="38217-04591", meter="KN73384",
         addr="600 S Clyde Morris Blvd - Student Union", rate="GS-1",
         stmt="06/03/2026", start="05/01/2026", end="05/31/2026", days=30,
         lines=["kWh Used                       132,612",
                "Total Amount You Owe        $16,806.42"]),
    dict(fn="bill_259_boeing.pdf", acct="44120-88210", meter="KNL2686",
         addr="Boeing Building - Mixed Use", rate="GSD-1",
         stmt="06/03/2026", start="05/01/2026", end="05/31/2026", days=30,
         lines=["kWh Used                        39,007",
                "Billing Demand (kW)                118.4",
                "Measured Demand (kW)               121.0",
                "Total Amount You Owe         $3,942.15"]),
    dict(fn="bill_915_facilities.pdf", acct="51002-33170", meter="KJ70457",
         addr="Facilities Outdoor - Mixed Use", rate="GSD-1",
         stmt="06/03/2026", start="05/01/2026", end="05/31/2026", days=30,
         lines=["kWh Used                         2,360",
                "Billing Demand (kW)                 6.5",
                "Total Amount You Owe           $268.90"]),
    dict(fn="bill_311_simcenter.pdf", acct="29984-11005", meter="MV32681",
         addr="311 Sim Center - Mixed Use", rate="GSDT-1",
         stmt="06/03/2026", start="05/01/2026", end="05/31/2026", days=30,
         lines=["On-Peak kWh                     18,120",
                "Off-Peak kWh                    45,440",
                "kWh Used                        63,560",
                "On-Peak Demand (kW)                142.0",
                "Total Amount You Owe         $6,410.77"]),
]

def make_pdf(b, path):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    y = 60
    def line(txt, size=11, dy=20, bold=False):
        nonlocal y
        page.insert_text((60, y), txt, fontsize=size,
                         fontname="helvetica-bold" if bold else "helvetica")
        y += dy
    line("FPL - Florida Power & Light Company", 15, 28, bold=True)
    line("Energy Bill", 12, 26)
    line(f"Account Number: {b['acct']}")
    line(f"Meter Number: {b['meter']}")
    line(f"Service Address: {b['addr']}")
    line(f"Rate Schedule: {b['rate']}")
    line(f"Statement Date: {b['stmt']}")
    line(f"Service from {b['start']} to {b['end']} ({b['days']} days)")
    y += 10
    line("Details of Charges", 12, 24, bold=True)
    for ln in b["lines"]:
        line(ln, 11, 20)
    doc.save(path)
    doc.close()

for b in BILLS:
    make_pdf(b, os.path.join(".", b["fn"]))

# make one *scanned* version: rasterize a PDF to a PNG (no text layer) to
# exercise the OCR path.
src = "./bill_915_facilities.pdf"
doc = fitz.open(src)
pix = doc[0].get_pixmap(dpi=200)
pix.save("./bill_915_SCANNED.png")
doc.close()
os.remove(src)  # keep only the scanned image version for this account

print("generated:", sorted(os.listdir(".")))
