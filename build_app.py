#!/usr/bin/env python3
"""
Build script: packages FPL Bill Extractor as a macOS .app

Usage (from inside the repo with venv active):
    python build_app.py

Produces:
    dist/FPL Bill Extractor.app

Requirements:
    pip install pyinstaller

Notes:
    - tesseract and poppler must be installed on the Mac (brew install tesseract poppler)
    - The .app bundles the Python code but NOT tesseract/poppler system binaries.
      The user's Mac needs those installed via Homebrew for OCR to work on scanned bills.
      Digital PDFs (text-layer) work without them.
"""
import subprocess
import sys
import os

def build():
    # Find tesseract and poppler paths to include in the app bundle
    # (optional — falls back to system PATH at runtime)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=FPL Bill Extractor",
        "--windowed",                    # .app bundle, no terminal window
        "--onedir",                      # faster startup than --onefile
        "--noconfirm",                   # overwrite previous build
        "--clean",

        # Include our modules
        "--add-data=rates.py:.",
        "--add-data=fpl_parser.py:.",

        # Hidden imports that PyInstaller might miss
        "--hidden-import=fitz",
        "--hidden-import=pytesseract",
        "--hidden-import=pdf2image",
        "--hidden-import=PIL",
        "--hidden-import=openpyxl",

        # Entry point
        "gui.py",
    ]

    print("Building .app ...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    if result.returncode == 0:
        print("\n✅  Built successfully!")
        print("    dist/FPL Bill Extractor.app")
        print("\nTo distribute: zip the .app and share it.")
        print("Recipients need: brew install tesseract poppler (for scanned bill OCR)")
    else:
        print("\n❌  Build failed. Check the output above.")
    return result.returncode

if __name__ == "__main__":
    sys.exit(build())
