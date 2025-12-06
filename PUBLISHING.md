# Publishing pyreadability to PyPI

This guide explains how to build and publish pyreadability to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/)
2. **API Tokens**: Generate API tokens for both PyPI and TestPyPI
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

3. **Configure credentials**: Create or update `~/.pypirc` with your API tokens:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

## Building the Package

### Using the build script (Recommended)

```bash
./build.sh
```

This script will:
- Clean previous builds
- Install/upgrade build tools (pip, build, twine)
- Build both wheel and source distribution
- Validate the distribution files
- Display the output files in `dist/`

### Manual build

```bash
# Clean old builds
rm -rf build/ dist/ *.egg-info

# Install build tools
python -m pip install --upgrade pip build twine

# Build the package
python -m build

# Check the distribution
python -m twine check dist/*
```

## Testing the Package Locally

Before publishing, test the package locally:

```bash
# Install from the wheel
pip install dist/pyreadability-0.1.0-py3-none-any.whl

# Test the CLI
pyreadability --help
pyreadability https://example.com

# Test as a library
python -c "from pyreadability import Readability; print('Import successful')"
```

## Publishing to TestPyPI (Testing)

**Always test on TestPyPI first!**

### Using the publish script

```bash
./publish.sh --test
```

### Manual upload

```bash
python -m twine upload --repository testpypi dist/*
```

### Testing the TestPyPI installation

```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    pyreadability

# Test it works
pyreadability --help
```

Note: The `--extra-index-url` is needed because dependencies (requests, beautifulsoup4, etc.) 
are not on TestPyPI and need to be fetched from the main PyPI.

## Publishing to PyPI (Production)

**WARNING: This action cannot be undone! Once uploaded, a version cannot be deleted or replaced.**

### Using the publish script

```bash
./publish.sh --production
```

This will:
- Show what will be uploaded
- Ask for confirmation
- Upload to PyPI

### Manual upload

```bash
python -m twine upload dist/*
```

### Verify the publication

After publishing, verify the package:

```bash
# Wait a minute for PyPI to process
sleep 60

# Install from PyPI
pip install pyreadability

# Test it works
pyreadability --help
```

Visit https://pypi.org/project/pyreadability/ to see your package page.

## Version Management

Before releasing a new version:

1. Update the version in `pyproject.toml`
2. Update the version in `pyreadability/__init__.py`
3. Create a git tag: `git tag v0.1.0`
4. Push the tag: `git push --tags`
5. Build and publish following the steps above

## Troubleshooting

### "File already exists" error

If you get this error when uploading:
- You cannot overwrite an existing version on PyPI
- Increment the version number in `pyproject.toml`
- Rebuild and try again

### Authentication errors

If you get authentication errors:
- Check your `~/.pypirc` file is correctly configured
- Verify your API token is valid and hasn't expired
- Ensure you're using `__token__` as the username (not your PyPI username)

### "Invalid distribution metadata" warning

If you see warnings about 'Dynamic: license-file' field:
- This is a known issue with twine 6.2.0 and modern setuptools
- The packages are valid and PyPI will accept them
- See: https://github.com/pypa/twine/issues/1096

### Import errors after installation

If the package installs but can't be imported:
- Verify all dependencies are installed
- Check that the package structure is correct
- Try installing in a clean virtual environment

## Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [Setuptools Documentation](https://setuptools.pypa.io/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [PyPI Help](https://pypi.org/help/)
