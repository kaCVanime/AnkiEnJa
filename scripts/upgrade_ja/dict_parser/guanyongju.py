# 《日语常用惯用句分类学习辞典》
import re
from pathlib import Path
from bs4 import BeautifulSoup
from bs4.element import NavigableString, CData, RubyTextString
from copy import copy


class CommonIdiomsIterator:
    def __init__(self, html_dir):
        self.html_dir = html_dir
        self.parser = Parser()
    def __iter__(self):
        self.pages = list(Path(self.html_dir).glob('*.html'))
        self.idioms = None
        return self

    def __next__(self):
        try:
            return next(self.idioms)
        except (StopIteration, TypeError):
            self._get_idioms_from_page()
            return next(self.idioms)

    def _get_idioms_from_page(self):
        if not self.pages:
            raise StopIteration

        page = self.pages.pop(0)
        with open(page, mode='r', encoding='utf-8') as f:
            html = ''.join([s.strip() for s in f.readlines()])
            # html = html.translate(kanji_correct_table)

        result = self.parser.parse(html)

        self.idioms = iter(result)

class PageIterator:
    def __init__(self, html_dir):
        self.parser = Parser()
        self.htmls = list(Path(html_dir).glob('*.html'))

    def __iter__(self):
        self.pages = self.htmls
        return self

    def __next__(self):
        if not self.pages:
            raise StopIteration
        page = self.pages.pop(0)
        with open(page, mode='r', encoding='utf-8') as f:
            html = ''.join([s.strip() for s in f.readlines()])
        return html, page.stem


class Parser:
    def get_page_head(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find('h1', class_='kindle-cn-heading-1').get_text()

    def parse(self, html):
        soup = BeautifulSoup(html, 'html.parser')

        entries = soup.find_all('p', class_='kindle-cn-para-no-indent')
        result = []
        for entry in entries:
            header = entry.find('span', class_='kindle-cn-bold')

            frequency = None
            if header.previous_sibling:
                frequency = str(header.previous_sibling)

            def_cn = str(header.next_sibling).strip()

            word = self._get_word(copy(header))
            kanji = self._get_kanji(copy(header))

            if def_cn.startswith('参见'):
                result.append({
                    "frequency": frequency,
                    "word": word,
                    "kanji": kanji,
                    "def_cn": def_cn,
                    "is_redirect": True
                })
                continue
            body = entry.next_sibling
            if not body or 'kindle-cn-para-no-indent' in body.get('class', ''):
                continue

            body_text = body.get_text().strip()
            if "◇" in body_text:
                definition = self._get_definition_from_mix(body_text)
                examples = self._get_examples_from_mix(body_text, kanji)
            else:
                definition = self._get_definition(body_text)
                eg = body.next_sibling
                if eg and 'kindle-cn-para-no-indent' not in eg.get('class', ''):
                    examples = self._get_examples(eg.get_text().strip(), kanji)
                else:
                    examples = []

            # 同一条目下有两条释义时，第二条释义可能会把中文释义带上。
            # TODO 适配两条以上释义
            if definition.endswith("）"):
                definition = re.sub('（.+）$', '', definition)

            result.append({
                "frequency": frequency,
                "word": word,
                "kanji": kanji,
                "definition": definition,
                "def_cn": def_cn,
                "examples": examples,
                "is_redirect": False
            })

        return result

    def _get_word(self, header):
        rubys = header.find_all('ruby')
        for ruby in rubys:
            ruby.next_element.string.replace_with('')
        return header.get_text(types=(NavigableString, CData, RubyTextString))
    def _get_kanji(self, header):
        return header.get_text()

    def _normalize_definition(self, text):
        if text.startswith('► '):
            text = text[1:]
        return text.strip()

    def _get_definition(self, text):
        return self._normalize_definition(text.lstrip())

    def _get_examples(self, text, prefix):
        egs = re.split('[\u2460-\u24FF]', text)
        if egs[0].strip().startswith('◇') or not egs[0].strip():
            egs = egs[1:]
        result = []
        for i, s in enumerate(egs):
            idx = s.index('（')
            result.append({
                "ja": s[:idx].strip(),
                "cn": s[idx:].strip()[1:-1],
                "name": f'{prefix}_{i}'
            })
        return result
    def _get_definition_from_mix(self, text):
        text = text.split('◇')[0].lstrip()
        return self._normalize_definition(text)

    def _get_examples_from_mix(self, text, prefix):
        s = text.split('◇')[1]
        return self._get_examples(s, prefix)


INITIAL_HTML = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
    <title></title>
    <link href="flow0001.css" rel="stylesheet" type="text/css" />
</head>

<body>
</body>

</html>'''

class Writer:
    def __init__(self, html_dir):
        self.pages = PageIterator(html_dir)

    def run(self, output_dir, mapping_html, mapping_entry, mapping_defs):
        for page, page_name in self.pages:
            PageWriter(page.translate(str.maketrans(mapping_html)), page_name, output_dir, mapping_entry, mapping_defs).start()


class PageWriter:
    def __init__(self, html, filename, output_dir, mapping_entry, mapping_defs):
        self.parser = Parser()
        self.name = self.parser.get_page_head(html)
        self.origin = BeautifulSoup(html, 'html.parser')
        self.page = BeautifulSoup(INITIAL_HTML, 'html.parser')
        self.filename = filename
        self.output_dir = output_dir

        self.entry_correct_table = str.maketrans(mapping_entry)
        self.defs_correct_table = str.maketrans(mapping_defs)

        self._init_entries(html)

    def _init_entries(self, html):
        self.entries = self.parser.parse(html)
        self.origin_entries = self.origin.find_all('p', class_='kindle-cn-para-no-indent')
        assert len(self.entries) == len(self.origin_entries)

    def _append_page_header(self):
        h1 = self.page.new_tag("h1", class_="kindle-cn-heading-1")
        h1.string = self.name
        self.page.body.append(h1)

    def _get_orgin_entry_word(self, index):
        origin = self.origin_entries[index]
        return copy(origin.find('span', class_='kindle-cn-bold'))

    def _make_frequency_tag(self, content):
        tag = self.page.new_tag("span", class_='gyj-frequency')
        tag.string = content
        return tag

    def _make_def_cn_tag(self, content):
        tag = self.page.new_tag("span", class_='gyj-def_cn')
        tag.string = content
        return tag

    def _get_def_cn_redirect_tag(self, idx):
        origin = copy(self.origin_entries[idx])
        # rubys = origin.find_all('ruby', recursive=False)
        container = self.page.new_tag('span', class_='gyj-def_cn gyj-redirect')
        anchor = origin.find('span', class_='kindle-cn-bold')
        p = list(anchor.next_siblings)
        container.extend(p)

        return container

    def _translate_tag(self, tag):
        return BeautifulSoup(str(tag).translate(self.entry_correct_table), 'html.parser')


    def _append_entry_head(self, idx, entry):
        origin_entry_word = self._get_orgin_entry_word(idx)

        container = self.page.new_tag('p', class_='kindle-cn-para-no-indent', attrs={"xml:lang": "ja", "lang": "ja"})

        contents = [self._make_frequency_tag(entry['frequency']), self._translate_tag(origin_entry_word), " 　"]
        if not entry["is_redirect"]:
            contents.append(self._make_def_cn_tag(entry['def_cn']))
        else:
            contents.append(self._get_def_cn_redirect_tag(idx))

        container.extend(contents)

        self.page.body.append(container)

    def _append_definition(self, content):
        tag = self.page.new_tag("p", class_='gyj-definition', attrs={"xml:lang": "ja", "lang": "ja"})
        tag.string = f'► {content}'.translate(self.defs_correct_table)
        self.page.body.append(tag)

    def _make_example_tag(self, ja, cn):
        container = self.page.new_tag("p", class_='gyj-example', attrs={"xml:lang": "ja", "lang": "ja"})
        ja_tag = self.page.new_tag("span", class_='gyj-example-ja')
        ja_tag.string = ja.translate(self.defs_correct_table)
        contents = ["◇ ", ja_tag, " 　"]
        if cn:
            cn_tag = self.page.new_tag("span", class_='gyj-example-cn')
            cn_tag.string = f'（{cn}）'
            contents.append(cn_tag)
        container.extend(contents)
        return container

    def _append_examples(self, examples):
        self.page.body.extend([self._make_example_tag(eg["ja"], eg["cn"]) for eg in examples])

    def _append_entry_body(self, entry):
        if not entry["is_redirect"]:
            self._append_definition(entry['definition'])
            self._append_examples(entry['examples'])

    def start(self):
        self._append_page_header()

        for idx, entry in enumerate(self.entries):
            self._append_entry_head(idx, entry)
            self._append_entry_body(entry)

        self._write_to_file()

    def _write_to_file(self):
        with open(Path(self.output_dir) / f'{self.filename}.html', mode='w+', encoding='utf-8') as f:
            f.write(str(self.page))




