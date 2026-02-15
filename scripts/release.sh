#!/bin/bash
set -e

# OpenMemX Release Helper Script
# Usage: ./scripts/release.sh [version]

VERSION=$1

echo "🚀 Starting Pre-release Checks..."

# 1. Run Tests
echo "🧪 Running tests..."
pytest

# 2. Run Linter
echo "🧹 Running linter (ruff)..."
ruff check src/

# 3. Clean and Build
echo "📦 Building package..."
rm -rf dist/ build/ *.egg-info
python3 -m build

# 4. Check Package
echo "📋 Checking distribution..."
twine check dist/*

if [ -n "$VERSION" ]; then
    echo "⚠️  Updating version in pyproject.toml to $VERSION..."
    # Universal sed for macOS/Linux
    sed -i.bak "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml && rm pyproject.toml.bak
fi

echo "✅ Pre-release checks passed!"
echo ""
echo "Next steps:"
echo "1. Update CHANGELOG.md"
echo "2. Commit changes: git add . && git commit -m \"chore: prep release \$(grep version pyproject.toml | cut -d'\"' -f2)\""
echo "3. Tag release: git tag v\$(grep version pyproject.toml | cut -d'\"' -f2)"
echo "4. Push: git push origin main --tags"
echo ""
echo "GitHub Actions will handle the PyPI upload automatically on release publication."
