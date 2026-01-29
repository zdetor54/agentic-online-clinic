#!/bin/bash
# uv Dependency Relock Script
# ========================
# Updates dependencies to their latest compatible versions by re-adding them with uv.
#
# What it does:
# 1. Extracts main and dev dependencies from pyproject.toml
# 2. Strips version constraints (>=, ==, <, etc.) from package names
# 3. Clears the existing dependency lists in pyproject.toml
# 4. Re-adds each package using 'uv add' to get fresh version pins
#
# Usage:
#   ./scripts/uv_dependency_relock.sh

set -euo pipefail

echo "🔍 Extracting dependencies from pyproject.toml..."

# Extract and strip versions for main deps
main_deps=($(sed -n '/dependencies = \[/,/]/p' pyproject.toml | grep -Eo '"[^"]+"' | tr -d '"' | sed 's/[<>=!].*//'))

# Extract and strip versions for dev deps
dev_deps=($(sed -n '/\[dependency-groups\]/,/^]/p' pyproject.toml | grep -Eo '"[^"]+"' | tr -d '"' | sed 's/[<>=!].*//'))

# Print clean list
main_list=$(IFS=", "; echo "${main_deps[*]}")
dev_list=$(IFS=", "; echo "${dev_deps[*]}")
echo "📦 Main dependencies: $main_list"
echo "🧪 Dev dependencies:  $dev_list"

echo "🧹 Clearing old dependencies (keeping block headers)..."

# Clear dependencies = [ ... ]
sed -i.bak '/dependencies = \[/,/]/ {
  /dependencies = \[/!{
    /]/!d
  }
}' pyproject.toml

# Clear [dependency-groups] dev = [ ... ]
sed -i.bak '/\[dependency-groups\]/,/^]/ {
  /dev = \[/,/]/ {
    /dev = \[/!{
      /]/!d
    }
  }
}' pyproject.toml

echo "🔁 Re-adding with uv..."

for pkg in "${main_deps[@]}"; do
    echo "→ uv add $pkg"
    uv add "$pkg"
done

for pkg in "${dev_deps[@]}"; do
    echo "→ uv add --dev $pkg"
    uv add --dev "$pkg"
done

echo "🧹 Cleaning up backup file..."
rm -f pyproject.toml.bak

echo "✅ Done. pyproject.toml now has fresh version-pinned dependencies."
