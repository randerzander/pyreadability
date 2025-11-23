import unittest
import os
from subprocess import Popen, PIPE
from bs4 import BeautifulSoup
from readability.readability import Readability, is_probably_readerable

class TestReadability(unittest.TestCase):
    def test_is_probably_readerable(self):
        html_short = "<html><body><p>This is a short article.</p></body></html>"
        long_text = "This is a long article with enough content to be considered readable. " * 10
        html_long = f"<html><body><p>{long_text}</p></body></html>"
        
        doc_short = BeautifulSoup(html_short, 'lxml')
        doc_long = BeautifulSoup(html_long, 'lxml')

        self.assertFalse(is_probably_readerable(doc_short))
        self.assertTrue(is_probably_readerable(doc_long))

    def test_dom_transformations(self):
        html = "<html><body><div><font>text</font><br><br>more text</div></body></html>"
        doc = BeautifulSoup(html, 'lxml')
        readability = Readability(doc)
        readability._prep_document()
        # a simplified check
        self.assertIsNone(doc.find('font'))
        self.assertIsNotNone(doc.find('span'))

    def test_metadata_extraction(self):
        html = """
        <html>
            <head>
                <title>Test Title</title>
                <meta name="author" content="Test Author">
                <meta property="og:site_name" content="Test Site">
                <meta name="description" content="Test Excerpt">
            </head>
            <body></body>
        </html>
        """
        doc = BeautifulSoup(html, 'lxml')
        readability = Readability(doc)
        metadata = readability._get_article_metadata()

        self.assertEqual(metadata.get('title'), 'Test Title')
        self.assertEqual(metadata.get('byline'), 'Test Author')
        self.assertEqual(metadata.get('siteName'), 'Test Site')
        self.assertEqual(metadata.get('excerpt'), 'Test Excerpt')


class TestCLI(unittest.TestCase):
    def test_cli_invocation_produces_markdown(self):
        dummy_html_path = "test.html"
        with open(dummy_html_path, "w") as f:
            f.write("<html><body><h1>Test</h1><p>This is a <strong>test</strong>.</p></body></html>")

        process = Popen(["python", "main.py", dummy_html_path], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        self.assertEqual(process.returncode, 0, f"CLI exited with error:\n{stderr.decode()}")
        
        output = stdout.decode()
        self.assertIn("Title:", output)
        self.assertIn("**test**", output)

        os.remove(dummy_html_path)

if __name__ == "__main__":
    unittest.main()
