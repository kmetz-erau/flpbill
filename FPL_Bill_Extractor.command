#!/bin/bash
# ============================================================================
# FPL Bill Extractor — One-Click Launcher for macOS
# ============================================================================
# Double-click this file in Finder. It will:
#   1. Install Homebrew (if missing)
#   2. Install Python, tesseract, poppler (if missing)
#   3. Create a Python virtual environment (first run only)
#   4. Install Python libraries (first run only)
#   5. Launch the GUI
#
# After the first run, steps 1-4 are skipped and the GUI opens in seconds.
# ============================================================================

set -e

# Move to the script's own directory (where the repo lives)
cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       FPL Bill Extractor — Setup         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Homebrew ──────────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
    echo "📦 Installing Homebrew (one-time, may ask for your password)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add Homebrew to PATH for Apple Silicon Macs
    if [ -f /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    echo "✅ Homebrew installed"
else
    echo "✅ Homebrew found"
fi

# ── 2. System dependencies ──────────────────────────────────────────────────
NEED_BREW=""
command -v python3 &>/dev/null || NEED_BREW="$NEED_BREW python"
command -v tesseract &>/dev/null || NEED_BREW="$NEED_BREW tesseract"
command -v pdftoppm &>/dev/null || NEED_BREW="$NEED_BREW poppler"

# Check for tkinter support
if ! python3 -c "import tkinter" &>/dev/null 2>&1; then
    PY_VER=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    NEED_BREW="$NEED_BREW python-tk@${PY_VER}"
fi

if [ -n "$NEED_BREW" ]; then
    echo "📦 Installing system tools:$NEED_BREW ..."
    brew install $NEED_BREW
    echo "✅ System tools installed"
else
    echo "✅ System tools found (python3, tesseract, poppler, tkinter)"
fi

# ── 3. Python virtual environment ───────────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python environment (one-time)..."
    python3 -m venv .venv
    echo "✅ Environment created"
fi

source .venv/bin/activate

# ── 4. Python libraries ─────────────────────────────────────────────────────
if [ ! -f ".venv/.deps_installed" ]; then
    echo "📦 Installing Python libraries (one-time)..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    touch .venv/.deps_installed
    echo "✅ Libraries installed"
else
    echo "✅ Libraries ready"
fi

# ── 5. Launch ────────────────────────────────────────────────────────────────
echo ""
echo "🚀 Launching FPL Bill Extractor..."
echo ""
python gui.py
