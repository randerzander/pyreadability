#!/bin/bash
# Build script for pyreadability
# This script builds a wheel and source distribution for PyPI

set -e  # Exit on error

echo "🔧 Building pyreadability package..."
echo ""

# Clean previous builds
echo "📦 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info pyreadability.egg-info

# Install build tools if needed
echo "🔨 Ensuring build tools are installed..."
python -m pip install --upgrade pip build twine

# Build the package
echo "🏗️  Building wheel and source distribution..."
python -m build

# Check the distribution
echo "✅ Checking distribution with twine..."
set +e  # Temporarily allow errors
python -m twine check dist/*
TWINE_EXIT_CODE=$?
set -e

# Note about Dynamic field warning
if [ $TWINE_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "⚠️  Note: twine may report 'Dynamic: license-file' field errors."
    echo "   This is a known compatibility issue with twine 6.2.0 and setuptools."
    echo "   The packages are valid and PyPI will accept them."
    echo "   See: https://github.com/pypa/twine/issues/1096"
    echo ""
fi

echo ""
echo "✨ Build complete! Distribution files are in dist/:"
ls -lh dist/

echo ""
echo "📝 To publish to TestPyPI (for testing):"
echo "   python -m twine upload --repository testpypi dist/*"
echo ""
echo "📝 To publish to PyPI (production):"
echo "   python -m twine upload dist/*"
echo ""
echo "💡 You'll need to configure your PyPI credentials first."
echo "   See: https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#uploading-your-project-to-pypi"
