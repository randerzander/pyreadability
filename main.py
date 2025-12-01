import argparse
import html2text
import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pyreadability import Readability, fetch_html, read_html_file, parse_html

def download_images(article_content, output_path, debug=False):
    """Download images from article content and update their paths."""
    soup = BeautifulSoup(article_content, 'html.parser')
    images = soup.find_all('img')
    
    if not images:
        return article_content
    
    # Create images directory next to output file
    output_dir = Path(output_path).parent
    images_dir = output_dir / f"{Path(output_path).stem}_images"
    images_dir.mkdir(exist_ok=True)
    
    downloaded_count = 0
    for img in images:
        src = img.get('src')
        if not src:
            continue
        
        try:
            # Download the image
            response = requests.get(src, timeout=10)
            response.raise_for_status()
            
            # Generate filename from URL
            parsed_url = urlparse(src)
            filename = Path(parsed_url.path).name
            if not filename:
                filename = f"image_{downloaded_count}.jpg"
            
            # Save image
            image_path = images_dir / filename
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            # Update src to relative path
            relative_path = f"{images_dir.name}/{filename}"
            img['src'] = relative_path
            
            downloaded_count += 1
            if debug:
                print(f"Downloaded: {src} -> {relative_path}")
                
        except Exception as e:
            if debug:
                print(f"Failed to download {src}: {e}")
    
    if debug:
        print(f"\nDownloaded {downloaded_count} of {len(images)} images")
    
    return str(soup)

def main():
    parser = argparse.ArgumentParser(description="A pure Python implementation of Mozilla's Readability.")
    parser.add_argument("source", help="URL or path to an HTML file")
    parser.add_argument("-o", "--output", help="Output file path for Markdown")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for extra logging")
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

    readability = Readability(doc, url=args.source if args.source.startswith("http") else None, debug=args.debug)
    article = readability.parse()

    if article:
        content = article.get('content')
        
        # Download images if output file is specified
        if args.output:
            content = download_images(content, args.output, debug=args.debug)
        
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        markdown = h.handle(content)
        
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
