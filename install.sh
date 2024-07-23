#!/bin/sh

# Check python version
if ! command -v python3 &> /dev/null || [ "$(python3 -c 'import sys; print(sys.version_info.minor >= 12)')" = 'False' ]; then
    echo 'Python >= 3.12 is required'
    exit
fi

# Change to script dir
cd "$(dirname "$0")" || exit

# Check if git is installed and update repo
if command -v git &> /dev/null; then
    git pull origin main
fi

# Create venv
python3 -m venv .venv
# Activate venv
. .venv/bin/activate
# Install deps
pip install -r requirements.txt
# Package
pip install -U pyinstaller
pyinstaller --noconfirm main.spec

# Give executable execute permission
chmod u+x dist/main/main

# Rename executable
mv dist/main/main dist/main/'Not so Dead Cells'
