#!/usr/bin/env python3
"""Test script to verify pyreadability library functionality."""

import sys
from bs4 import BeautifulSoup
from readability import Readability, fetch_html, parse_html
import html2text

def test_basic_import():
    """Test that the library can be imported."""
    print("✓ Import test passed")
    return True

def test_simple_html():
    """Test parsing simple HTML."""
    html = """
    <html>
        <head><title>Test Article</title></head>
        <body>
            <div>
                <h1>Main Article Title</h1>
                <p>This is a paragraph with some content.</p>
                <p>This is another paragraph with more content.</p>
                <p>And yet another paragraph to make it substantial.</p>
            </div>
        </body>
    </html>
    """
    
    doc = BeautifulSoup(html, 'lxml')
    readability = Readability(doc)
    article = readability.parse()
    
    if article and article.get('title'):
        print(f"✓ Simple HTML test passed - Title: {article['title']}")
        return True
    else:
        print("✗ Simple HTML test failed")
        return False

def test_with_url():
    """Test parsing HTML from a URL (using example.com as simple test)."""
    try:
        # Use a simple, reliable URL for testing
        url = 'https://example.com'
        html = fetch_html(url)
        
        if not html:
            print("✗ URL fetch test failed - could not fetch HTML")
            return False
        
        doc = parse_html(html)
        readability = Readability(doc, url=url)
        article = readability.parse()
        
        if article:
            print(f"✓ URL test passed - Fetched and parsed: {url}")
            return True
        else:
            print("✗ URL test failed - could not parse article")
            return False
    except Exception as e:
        print(f"✗ URL test failed with exception: {e}")
        return False

def test_markdown_conversion():
    """Test converting extracted content to Markdown."""
    html = """
    <html>
        <head><title>Markdown Test</title></head>
        <body>
            <article>
                <h1>Article Title</h1>
                <p>First paragraph with <strong>bold text</strong>.</p>
                <p>Second paragraph with <em>italic text</em>.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
            </article>
        </body>
    </html>
    """
    
    doc = BeautifulSoup(html, 'lxml')
    readability = Readability(doc)
    article = readability.parse()
    
    if article:
        h = html2text.HTML2Text()
        markdown = h.handle(article['content'])
        
        if markdown and len(markdown) > 0:
            print("✓ Markdown conversion test passed")
            return True
        else:
            print("✗ Markdown conversion test failed")
            return False
    else:
        print("✗ Markdown conversion test failed - could not parse article")
        return False

def main():
    """Run all tests."""
    print("Testing pyreadability library installation...\n")
    
    tests = [
        test_basic_import,
        test_simple_html,
        test_markdown_conversion,
        test_with_url,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
