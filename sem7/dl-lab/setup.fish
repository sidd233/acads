#!/usr/bin/env fish

set_color cyan
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "             Deep Learning Lab Project Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
set_color normal
echo

# -------------------------------------------------------
# Lab Number
# -------------------------------------------------------

read -P "Lab Number: " LAB

if test -z "$LAB"
    echo "Invalid lab number."
    exit 1
end

set LAB_DIR "lab$LAB"

mkdir -p "$LAB_DIR"
cd "$LAB_DIR"

set_color green
echo "✓ Created $LAB_DIR"
set_color normal

# -------------------------------------------------------
# Virtual Environment
# -------------------------------------------------------

echo "Creating virtual environment..."

python3 -m venv env

source env/bin/activate.fish

set_color green
echo "✓ Virtual environment activated"
set_color normal

# -------------------------------------------------------
# Install packages
# -------------------------------------------------------

echo "Installing packages..."

pip install --upgrade pip -q > /dev/null 2>&1
pip install -q numpy pandas matplotlib > /dev/null 2>&1

read -P "Additional packages (space separated, leave empty to skip): " EXTRA

if test -n "$EXTRA"
    echo "Installing additional packages..."
    pip install -q $EXTRA > /dev/null 2>&1
end

set_color green
echo "✓ Dependencies installed"
set_color normal

# -------------------------------------------------------
# Gitignore
# -------------------------------------------------------

printf "%s\n" \
"env/" \
"build/" \
"__pycache__/" \
"*.pyc" \
"*.aux" \
"*.log" \
"*.out" \
"*.toc" \
"*.synctex.gz" > .gitignore

set_color green
echo "✓ .gitignore created"
set_color normal

# -------------------------------------------------------
# Experiments
# -------------------------------------------------------

read -P "Number of experiments: " NUM

for i in (seq $NUM)
    touch "exp$i.py"
end

set_color green
echo "✓ Created $NUM experiment file(s)"
set_color normal

# -------------------------------------------------------
# Report
# -------------------------------------------------------

cp ../sample_report.tex report.tex

set_color green
echo "✓ report.tex created"
set_color normal

set_color cyan
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
set_color normal

echo
echo "Project Structure:"

tree -a -C -I 'env|build|__pycache__'

echo
echo "Happy coding :)"