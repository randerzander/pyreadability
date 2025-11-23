import argparse
import html2text
from bs4 import BeautifulSoup
from readability.readability import Readability
from readability.helpers import fetch_html, read_html_file, parse_html

def main():
    parser = argparse.ArgumentParser(description="A pure Python implementation of Mozilla's Readability.")
    parser.add_argument("source", help="URL or path to an HTML file")
    parser.add_argument("-o", "--output", help="Output file path for Markdown")
    args = parser.parse_args()

    if args.source.startswith("http://") or args.source.startswith("https://"):
        html = fetch_html(args.source)
    else:
        html = read_html_file(args.source)

    if not html:
        print("Failed to get HTML content.")
        return

    doc = parse_html(html)
    if not doc:
        print("Failed to parse HTML.")
        return

    readability = Readability(doc, url=args.source if args.source.startswith("http") else None)
    article = readability.parse()

    if article:
        h = html2text.HTML2Text()
        h.ignore_links = True # for cleaner output
        markdown = h.handle(article.get('content'))
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(f"# {article.get('title')}\n\n")
                f.write(markdown)
            print(f"Article saved to {args.output}")
        else:
            print("Title:", article.get("title"))
            print("\nContent:\n")
            print(markdown)
    else:
        print("Could not extract article.")

if __name__ == "__main__":
    main()
