# Installation Guide

## Install from Source

### Using pip

```bash
# Clone the repository
git clone https://github.com/randerzander/pyreadability.git
cd pyreadability

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Using uv (recommended for development)

```bash
# Clone the repository
git clone https://github.com/randerzander/pyreadability.git
cd pyreadability

# Create virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows

# Install the package
uv pip install -e .
```

## Verify Installation

### Test the Library

Run the test script:

```bash
python test_library.py
```

### Test the CLI

```bash
pyreadability --help
pyreadability https://example.com
```

## Usage

### As a Library

```python
from pyreadability import Readability, fetch_html
import html2text

# Fetch and parse a URL
html = fetch_html('https://example.com')

# Pass HTML directly - Readability handles parsing
readability = Readability(html, url='https://example.com')
article = readability.parse()

# Convert to Markdown
h = html2text.HTML2Text()
markdown = h.handle(article['content'])

print(f"Title: {article['title']}")
print(markdown)
```

### As a CLI Tool

```bash
# Extract content from URL
pyreadability https://example.com

# Save to file
pyreadability https://example.com -o article.md

# Enable debug logging
pyreadability https://example.com --debug

# Process local HTML file
pyreadability /path/to/file.html
```

## Development

### Running Tests

```bash
python test_library.py
```

### Building Distribution

```bash
python -m build
```

This will create `.whl` and `.tar.gz` files in the `dist/` directory.
