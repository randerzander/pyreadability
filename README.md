# pyreadability

A pure Python implementation of Mozilla's Readability.js. This library extracts the main readable content from a web page and can return it as cleaned HTML or Markdown.

## Installation

### Option 1: Install directly from GitHub (Recommended)

```bash
pip install git+https://github.com/randerzander/pyreadability.git
```

### Option 2: Install from local clone

1.  Clone the repository:
    ```bash
    git clone https://github.com/randerzander/pyreadability.git
    cd pyreadability
    ```

2.  Install with pip:
    ```bash
    pip install .
    ```

    Or for development (editable install):
    ```bash
    pip install -e .

## Usage

### Command-Line Interface

You can use `pyreadability` from the command line to extract content from a URL or a local HTML file.

**From a URL:**

```bash
pyreadability https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/
```

**From a local file:**

```bash
pyreadability /path/to/your/file.html
```

**Saving the output to a file:**

Use the `-o` or `--output` flag to save the extracted content as a Markdown file.

```bash
pyreadability https://some-url.com/article -o my-article.md
```

**Debugging:**

Use the `--debug` flag to enable debug logging, which provides extra information about the parsing process, such as image inclusion decisions.

```bash
pyreadability https://some-url.com/article --debug
```

### As a Library

You can also use `pyreadability` as a library in your own Python projects.

```python
import requests
from pyreadability import Readability
import html2text

url = 'https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/'
response = requests.get(url)

# Pass HTML directly - Readability handles parsing
# Accepts: HTML string, bytes, or BeautifulSoup object
readability = Readability(response.text, url=url)
article = readability.parse()

# The article content is in HTML
html_content = article['content']

# You can convert it to Markdown
h = html2text.HTML2Text()
markdown_content = h.handle(html_content)

print(f"Title: {article['title']}")
print(markdown_content)
```
