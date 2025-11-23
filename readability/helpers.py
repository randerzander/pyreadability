import requests
from bs4 import BeautifulSoup

def fetch_html(url):
    """
    Fetches HTML content from a URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

def read_html_file(filepath):
    """
    Reads HTML content from a local file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        print(f"Error reading file: {e}")
        return None

def parse_html(html):
    """
    Parses HTML content using BeautifulSoup.
    """
    if html:
        return BeautifulSoup(html, 'lxml')
    return None
