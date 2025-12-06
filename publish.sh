#!/bin/bash
# Publish script for pyreadability
# This script publishes the package to PyPI or TestPyPI

set -e  # Exit on error

# Default to TestPyPI for safety
REPOSITORY="testpypi"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            REPOSITORY="pypi"
            shift
            ;;
        --test)
            REPOSITORY="testpypi"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--production|--test]"
            echo "  --production: Publish to PyPI (production)"
            echo "  --test: Publish to TestPyPI (default)"
            exit 1
            ;;
    esac
done

echo "🚀 Publishing pyreadability package..."
echo ""

# Check if dist/ directory exists and has files
if [ ! -d "dist" ] || [ -z "$(ls -A dist/)" ]; then
    echo "❌ Error: dist/ directory is empty. Run ./build.sh first."
    exit 1
fi

# Install twine if needed
echo "🔨 Ensuring twine is installed..."
python -m pip install --upgrade twine

# Show what will be uploaded
echo ""
echo "📦 Files to be uploaded:"
ls -lh dist/

echo ""
if [ "$REPOSITORY" = "pypi" ]; then
    echo "⚠️  WARNING: Publishing to PRODUCTION PyPI!"
    echo "   This action cannot be undone."
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Upload cancelled."
        exit 0
    fi
    echo ""
    echo "📤 Uploading to PyPI..."
    python -m twine upload dist/*
else
    echo "📤 Uploading to TestPyPI..."
    python -m twine upload --repository testpypi dist/*
fi

echo ""
echo "✨ Upload complete!"

if [ "$REPOSITORY" = "testpypi" ]; then
    echo ""
    echo "📝 To install from TestPyPI:"
    echo "   pip install --index-url https://test.pypi.org/simple/ pyreadability"
else
    echo ""
    echo "📝 To install from PyPI:"
    echo "   pip install pyreadability"
fi
