import re
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup, NavigableString

unlikelyCandidates = re.compile(
    r"-ad-|ai2html|banner|breadcrumbs|combx|comment|community|cover-wrap|disqus|"
    r"extra|footer|gdpr|header|legends|menu|related|remark|replies|rss|shoutbox|sidebar|"
    r"skyscraper|social|sponsor|supplemental|ad-break|agegate|pagination|pager|popup|yom-remote",
    re.IGNORECASE,
)
okMaybeItsACandidate = re.compile(
    r"and|article|body|column|content|main|mathjax|shadow", re.IGNORECASE
)


def is_node_visible(node):
    if not node:
        return False
    if hasattr(node, "has_attr"):
        if node.has_attr("hidden"):
            return False
        if node.has_attr("aria-hidden") and node["aria-hidden"] == "true":
            if (
                node.has_attr("class")
                and "fallback-image" in node.get("class", [])
            ):
                return True
            return False
    return True


def is_probably_readerable(doc, min_content_length=140, min_score=20):
    nodes = doc.select("p, pre, article")
    br_nodes = doc.select("div > br")
    if br_nodes:
        div_parents = set(br.parent for br in br_nodes)
        nodes.extend(list(div_parents))

    score = 0
    for node in nodes:
        if not is_node_visible(node):
            continue
        match_string = " ".join(node.get("class", [])) + " " + node.get("id", "")
        if unlikelyCandidates.search(match_string) and not okMaybeItsACandidate.search(
            match_string
        ):
            continue
        if node.name == "p" and node.parent and node.parent.name == "li":
            continue
        text_content_length = len(node.get_text(strip=True))
        if text_content_length < min_content_length:
            continue
        score += (text_content_length - min_content_length) ** 0.5
        if score > min_score:
            return True
    return False


class Readability:
    FLAG_STRIP_UNLIKELYS = 0x1
    FLAG_WEIGHT_CLASSES = 0x2
    FLAG_CLEAN_CONDITIONALLY = 0x4

    REGEXPS = {
        'unlikelyCandidates': re.compile(r'-ad-|ai2html|banner|breadcrumbs|combx|comment|community|cover-wrap|disqus|extra|footer|gdpr|header|legends|menu|related|remark|replies|rss|shoutbox|sidebar|skyscraper|social|sponsor|supplemental|ad-break|agegate|pagination|pager|popup|yom-remote', re.IGNORECASE),
        'okMaybeItsACandidate': re.compile(r'and|article|body|column|content|main|mathjax|shadow', re.IGNORECASE),
        'positive': re.compile(r'article|body|content|entry|hentry|h-entry|main|page|pagination|post|text|blog|story', re.IGNORECASE),
        'negative': re.compile(r'-ad-|hidden|^hid$| hid$| hid |^hid |banner|combx|comment|com-|contact|footer|gdpr|masthead|media|meta|outbrain|promo|related|scroll|share|shoutbox|sidebar|skyscraper|sponsor|shopping|tags|widget', re.IGNORECASE),
        'extraneous': re.compile(r'print|archive|comment|discuss|e[\-]?mail|share|reply|all|login|sign|single|utility', re.IGNORECASE),
        'byline': re.compile(r'byline|author|dateline|writtenby|p-author', re.IGNORECASE),
        'replaceFonts': re.compile(r'<\/?font[^>]*>', re.IGNORECASE),
        'normalize': re.compile(r'\s{2,}'),
        'videos': re.compile(r'\/\/(www\.)?((dailymotion|youtube|youtube-nocookie|player\.vimeo|v\.qq|bilibili|live.bilibili)\.com|(archive|upload\.wikimedia)\.org|player\.twitch\.tv)', re.IGNORECASE),
        'shareElements': re.compile(r'(\b|_)(share|sharedaddy)(\b|_)'),
        'nextLink': re.compile(r'(next|weiter|continue|>([^\|]|$)|»([^\|]|$))', re.IGNORECASE),
        'prevLink': re.compile(r'(prev|earl|old|new|<|«)', re.IGNORECASE),
        'tokenize': re.compile(r'\W+'),
        'whitespace': re.compile(r'^\s*$'),
        'hasContent': re.compile(r'\S$'),
    }

    PRESENTATIONAL_ATTRIBUTES = [ "align", "background", "bgcolor", "border", "cellpadding", "cellspacing", "frame", "hspace", "rules", "style", "valign", "vspace" ]
    DEPRECATED_SIZE_ATTRIBUTE_ELEMS = ["table", "th", "td", "hr", "pre"]
    DIV_TO_P_ELEMS = {"blockquote", "dl", "div", "img", "ol", "p", "pre", "table", "ul"}

    def __init__(self, doc, **options):
        self.doc = doc
        self.url = options.get('url')
        self._article_title = None
        self._article_byline = None
        self._article_dir = None
        self._article_site_name = None
        self._attempts = []
        self._metadata = {}

        self._debug = options.get('debug', False)
        self._max_elems_to_parse = options.get('max_elems_to_parse', 0)
        self._nb_top_candidates = options.get('nb_top_candidates', 5)
        self._char_threshold = options.get('char_threshold', 500)
        self.classes_to_preserve = options.get('classes_to_preserve', [])
        
        self._flags = self.FLAG_STRIP_UNLIKELYS | self.FLAG_WEIGHT_CLASSES | self.FLAG_CLEAN_CONDITIONALLY

    def parse(self):
        self._unwrap_noscript_images()
        self._prep_document()
        self._metadata = self._get_article_metadata()
        self._article_title = self._metadata.get('title')
        
        self._mark_data_tables()
        article_content = self._grab_article()
        if not article_content:
            return None
        self._post_process_content(article_content)
        
        return {
            "title": self._article_title,
            "byline": self._metadata.get('byline'),
            "siteName": self._metadata.get('siteName'),
            "excerpt": self._metadata.get('excerpt'),
            "content": str(article_content),
            "textContent": article_content.get_text(strip=True),
        }

    def _get_article_metadata(self):
        metadata = {}
        values = {}

        for meta in self.doc.find_all('meta'):
            element_name = meta.get('name')
            element_property = meta.get('property')
            content = meta.get('content')

            if not content:
                continue

            key = None
            if element_property:
                if 'og:' in element_property:
                    key = element_property.replace('og:', '')
                elif 'twitter:' in element_property:
                    key = element_property.replace('twitter:', '')
            elif element_name:
                key = element_name
            
            if key:
                values[key] = content.strip()
        
        metadata['title'] = values.get('title') or self._get_article_title()
        metadata['byline'] = values.get('author')
        metadata['siteName'] = values.get('site_name')
        metadata['excerpt'] = values.get('description')

        for script in self.doc.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'NewsArticle':
                    metadata['title'] = data.get('headline') or metadata['title']
                    metadata['byline'] = data.get('author', {}).get('name') or metadata['byline']
                    metadata['excerpt'] = data.get('description') or metadata['excerpt']
            except json.JSONDecodeError:
                continue

        return metadata

    def _unwrap_noscript_images(self):
        for noscript in self.doc.find_all('noscript'):
            # parse the content of the noscript tag
            noscript_doc = BeautifulSoup(noscript.get_text(), 'html.parser')
            img = noscript_doc.find('img')
            if img:
                noscript.replace_with(img)

    def _get_article_title(self):
        try:
            cur_title = orig_title = self.doc.title.string.strip()
        except AttributeError:
            cur_title = orig_title = ""

        title_separators = ['|', '-', '–', '—', '\\', '/', '»']
        title_had_hierarchical_separators = False
        
        def word_count(s):
            return len(s.split())

        for sep in title_separators:
            if f' {sep} ' in cur_title:
                if sep in ['\\', '/', '»']:
                    title_had_hierarchical_separators = True
                
                parts = cur_title.split(f' {sep} ')
                cur_title = parts[0]
                
                if word_count(cur_title) < 3:
                    cur_title = " ".join(parts[1:])
                break

        if ': ' in cur_title:
            headings = self.doc.find_all(['h1', 'h2'])
            trimmed_title = cur_title.strip()
            match = any(h.get_text(strip=True) == trimmed_title for h in headings)
            
            if not match:
                cur_title = cur_title.split(':')[-1]
                if word_count(cur_title) < 3:
                    cur_title = ":".join(cur_title.split(':')[:-1])

        cur_title = self.REGEXPS['normalize'].sub(' ', cur_title).strip()
        
        cur_title_word_count = word_count(cur_title)
        if cur_title_word_count <= 4 and (not title_had_hierarchical_separators or cur_title_word_count != word_count(orig_title.replace(f' {sep} ', '')) - 1):
             cur_title = orig_title
             
        return cur_title

    def _prep_document(self):
        for el in self.doc.find_all(['script', 'style']):
            el.decompose()

        for font_tag in self.doc.find_all('font'):
            font_tag.name = 'span'

    def _mark_data_tables(self):
        for table in self.doc.find_all('table'):
            role = table.get('role')
            if role == 'presentation':
                table._readability_data_table = False
                continue
            
            datatable = table.get('datatable')
            if datatable == '0':
                table._readability_data_table = False
                continue

            if table.find('caption'):
                table._readability_data_table = True
                continue
            
            if table.find(['col', 'colgroup', 'tfoot', 'thead', 'th']):
                table._readability_data_table = True
                continue
            
            rows = table.find_all('tr')
            if rows and len(rows) * len(rows[0].find_all('td')) > 10:
                table._readability_data_table = True

    def _get_link_density(self, element):
        text_length = len(element.get_text(strip=True))
        if text_length == 0:
            return 0
        
        link_length = 0
        for a in element.find_all('a'):
            link_length += len(a.get_text(strip=True))
            
        return link_length / text_length

    def _has_child_block_element(self, element):
        for child in element.children:
            if hasattr(child, 'name') and child.name in self.DIV_TO_P_ELEMS:
                return True
        return False
        
    def _grab_article(self, page=None):
        if not page:
            page = self.doc.body
        if not page:
            return None

        for node in list(page.find_all(True)):
            if node.parent is None:
                continue
            if not is_node_visible(node):
                node.decompose()
                continue
            
            match_string = " ".join(node.get("class", [])) + " " + node.get("id", "")
            if self.REGEXPS['unlikelyCandidates'].search(match_string) and \
               not self.REGEXPS['okMaybeItsACandidate'].search(match_string) and \
               node.name != 'body':
                node.decompose()
                continue

            if node.name == "div" and not self._has_child_block_element(node):
                node.name = "p"

        elements_to_score = page.find_all(['p', 'td', 'pre'])
        candidates = {}

        for el in elements_to_score:
            inner_text = el.get_text()
            if len(inner_text) < 25:
                continue

            ancestors = []
            parent = el.parent
            if parent is not None and hasattr(parent, 'name') and parent.name != '[document]':
                ancestors.append(parent)
                if parent.parent is not None and hasattr(parent.parent, 'name') and parent.parent.name != '[document]':
                    ancestors.append(parent.parent)

            for i, ancestor in enumerate(ancestors):
                if not hasattr(ancestor, 'readability'):
                    self._initialize_node(ancestor)
                    candidates[ancestor] = ancestor.readability

                score_divider = 1 if i == 0 else 2
                content_score = 1 + inner_text.count(',') + min(len(inner_text) // 100, 3)
                if hasattr(ancestor, 'readability') and ancestor.readability:
                    ancestor.readability['content_score'] += content_score / score_divider
        
        for candidate in candidates:
            if hasattr(candidate, 'readability') and candidate.readability:
                candidate.readability['content_score'] *= (1 - self._get_link_density(candidate))

        top_candidates = sorted(candidates.items(), key=lambda item: item[1]['content_score'], reverse=True)
        
        if not top_candidates:
            if self.doc.body:
                new_body = self.doc.new_tag('div')
                for child in list(self.doc.body.children):
                    new_body.append(child.extract())
                return new_body
            return None

        top_candidate_node = top_candidates[0][0]
        article_content = self.doc.new_tag("div")
        sibling_score_threshold = max(10, top_candidate_node.readability['content_score'] * 0.2)
        
        if top_candidate_node.parent:
            siblings = top_candidate_node.parent.children
            for sibling in list(siblings):
                append = False
                if sibling == top_candidate_node:
                    append = True
                
                content_bonus = 0
                if hasattr(sibling, 'readability') and sibling.readability and sibling.readability.get('content_score', 0) + content_bonus >= sibling_score_threshold:
                    append = True

                if append and hasattr(sibling, 'name'):
                    article_content.append(sibling.extract())
        else:
             article_content.append(top_candidate_node)

        return article_content

    def _initialize_node(self, node):
        if not hasattr(node, 'readability'):
            node.readability = {'content_score': 0}
            if node.name == 'div':
                node.readability['content_score'] += 5
            elif node.name in ['pre', 'td', 'blockquote']:
                node.readability['content_score'] += 3
            elif node.name in ['address', 'ol', 'ul', 'dl', 'dd', 'dt', 'li', 'form']:
                node.readability['content_score'] -= 3
            elif node.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'th']:
                node.readability['content_score'] -= 5
            node.readability['content_score'] += self._get_class_weight(node)
    
    def _get_class_weight(self, node):
        weight = 0
        if self._flags & self.FLAG_WEIGHT_CLASSES:
            class_name = " ".join(node.get("class", []))
            if self.REGEXPS['negative'].search(class_name):
                weight -= 25
            if self.REGEXPS['positive'].search(class_name):
                weight += 25
            _id = node.get("id", "")
            if self.REGEXPS['negative'].search(_id):
                weight -= 25
            if self.REGEXPS['positive'].search(_id):
                weight += 25
        return weight
    
    def _post_process_content(self, article_content):
        self._fix_lazy_images(article_content)
        self._fix_relative_uris(article_content)
        self._clean_attributes(article_content)
        self._clean_styles(article_content)
        self._clean_headers(article_content)
        self._clean_conditionally(article_content, "form")
        self._simplify_nested_elements(article_content)

    def _fix_lazy_images(self, article_content):
        for img in article_content.find_all('img'):
            if img.has_attr('data-src'):
                img['src'] = img['data-src']
                del img['data-src']
            if img.has_attr('data-srcset'):
                img['srcset'] = img['data-srcset']
                del img['data-srcset']

    def _fix_relative_uris(self, article_content):
        if not self.url:
            return
        
        for link in article_content.find_all('a'):
            if link.has_attr('href'):
                href = link['href']
                if href.startswith('javascript:'):
                    text_node = self.doc.new_string(link.get_text())
                    link.replace_with(text_node)
                else:
                    link['href'] = urljoin(self.url, href)
        
        for media in article_content.find_all(['img', 'picture', 'figure', 'video', 'audio', 'source']):
            for attr in ['src', 'poster', 'srcset']:
                if media.has_attr(attr):
                    media[attr] = urljoin(self.url, media[attr])

    def _clean_attributes(self, article_content):
        for el in article_content.find_all(True):
            preserved_classes = []
            if el.has_attr('class'):
                for cls in el['class']:
                    if cls in self.classes_to_preserve:
                        preserved_classes.append(cls)
            
            el.attrs = {} # remove all attributes
            if preserved_classes:
                el['class'] = preserved_classes

    def _clean_styles(self, article_content):
        for e in article_content.find_all(True):
            if e.name == 'svg':
                continue
            
            for attr in self.PRESENTATIONAL_ATTRIBUTES:
                if e.has_attr(attr):
                    del e[attr]
            
            if e.name in self.DEPRECATED_SIZE_ATTRIBUTE_ELEMS:
                if e.has_attr('width'):
                    del e['width']
                if e.has_attr('height'):
                    del e['height']
    
    def _clean_headers(self, article_content):
        for header in article_content.find_all(['h1', 'h2']):
            if self._get_class_weight(header) < 0:
                header.decompose()
    
    def _simplify_nested_elements(self, article_content):
        for el in article_content.find_all(['div', 'section']):
            if el.parent and len(el.find_all(recursive=False)) == 1 and el.find(recursive=False).name in ['div', 'section']:
                child = el.find(recursive=False)
                child.extract()
                el.replace_with(child)

    def _clean_conditionally(self, e, tag):
        if not (self._flags & self.FLAG_CLEAN_CONDITIONALLY):
            return

        for node in list(e.find_all(tag)):
            is_data_table = getattr(node, '_readability_data_table', False)

            if tag == 'table' and is_data_table:
                continue

            # Simplified conditional cleaning logic
            if self._get_class_weight(node) < 0:
                node.decompose()
