# pyreadability

A pure Python implementation of Mozilla's Readability.js. This library extracts the main readable content from a web page and can return it as cleaned HTML or Markdown.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/randerzander/pyreadability.git
    cd pyreadability
    ```

2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Command-Line Interface

You can use `pyreadability` from the command line to extract content from a URL or a local HTML file.

**From a URL:**

```bash
python main.py https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/
```

**From a local file:**

```bash
python main.py /path/to/your/file.html
```

**Saving the output to a file:**

Use the `-o` or `--output` flag to save the extracted content as a Markdown file.

```bash
python main.py https://some-url.com/article -o my-article.md
```

### As a Library

You can also use `pyreadability` as a library in your own Python projects.

```python
import requests
from bs4 import BeautifulSoup
from readability.readability import Readability
import html2text

url = 'https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/'
response = requests.get(url)
doc = BeautifulSoup(response.text, 'lxml')

readability = Readability(doc, url=url)
article = readability.parse()

# The article content is in HTML
html_content = article['content']

# You can convert it to Markdown
h = html2text.HTML2Text()
markdown_content = h.handle(html_content)

print(f"Title: {article['title']}")
print(markdown_content)
```
