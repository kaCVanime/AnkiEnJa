import re
import copy
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from .base import Base
from ..utils import (
    import_from,
    get_soup_text,
    normalize_redirect_word,
    remove_last_word,
)

def normalize_chn(chn):
    return re.sub('[(（）)]', '', chn).strip()

def abbrev(s):
    s = s.replace('somebody', 'sb')
    s = s.replace('something', 'sth')
    return s


class OaldpeParser(Base):

    def __init__(self, soup, entry):
        super().__init__(soup)
        self.entry = entry

    def specify_def(self, def_id):
        self.x_def_id = def_id

    @staticmethod
    def is_redirect_entry(html):
        # raise NotImplementedError
        soup = BeautifulSoup(html, 'html.parser')
        entries = OaldpeParser.get_entries(soup)
        if len(entries) > 1:
            return False
        entry = entries[0]
        single = entry.find('ol', class_='sense_single', recursive=False)
        if single:
            definition = single.find('span', class_='def')
        return single and not definition

    @staticmethod
    def get_best_redirect_word(html):
        entry = BeautifulSoup(html, 'html.parser')
        single = entry.find('ol', class_='sense_single')
        href = single.find('a', class_='Ref').get('href', None)
        keyword = 'entry://'
        return href[len(keyword):]

    @staticmethod
    def get_entries(soup):
        entries = soup.find_all('div', class_='entry')
        return entries

    def get_word(self):
        headword = self.entry.find('h1', class_='headword')
        hms = headword.find_all('span', class_='hm')
        for hm in hms:
            hm.extract()
        return headword.get_text()

    def get_phonetics(self):
        return (
            get_soup_text(self.entry.find('div', class_='phons_br')),
            get_soup_text(self.entry.find('div', class_='phons_n_am'))
        )

    def _parse_example(self, li, prefix):
        cf = li.find('span', class_='cf')
        x = li.find('span', {'class': ['x', 'unx']})
        if not x:
            return None
        p = x
        xt = x.find(['xt', 'unxt'])
        if xt:
            xt.extract()
            p = xt
        s_chn = p.find('chn', class_='simple')
        t_chn = p.find('chn', class_='traditional')
        if s_chn:
            s_chn.extract()
        if t_chn:
            t_chn.extract()
        return {
            "usage": abbrev(cf.get_text()) if cf else "",
            "labels": self._parse_labels(li.find('div', class_='exText')),
            "en": x.get_text(),
            "cn": s_chn.get_text() if s_chn else "",
            "ai": bool(s_chn.find('ai')) if s_chn else False,
            "name": prefix
        }

    def _parse_labels(self, box):
        labels = box.find_all('span', class_='labels', recursive=False)
        for label in labels:
            labelx = label.find('labelx')
            if labelx:
                labelx.extract()
        s = "".join([a.get_text() for a in labels]) if labels else ""
        return s

    def _parse_def(self, li):
        definition = get_soup_text(li.find('span', class_='def'))
        if not definition:
            return None

        variants = li.find('div', { "class": "variants", "type": "alt" })

        cefr = li.get('cefr', '')
        cf = li.find('span', class_='cf')
        id = li.get('id')
        topic = li.find('span', class_='topic-g', recursive=False)
        if topic and not cefr:
            topic_cefr = topic.find('span', class_='topic_cefr')
            cefr = get_soup_text(topic_cefr)

        eg_box = li.find('ul', class_='examples')
        examples = list(filter(None, [self._parse_example(li, f'{id}_{idx}') for idx, li in enumerate(eg_box.find_all('li', recursive=False))] if eg_box else []))
        if len(examples) < 10:
            extra = li.find('span', class_='unbox', unbox='extra_examples')
            if extra:
                extra_eg_box = extra.find('ul', class_='examples')
                start = len(examples)
                examples.extend([self._parse_example(li, f'{id}_{idx+start}') for idx, li in enumerate(extra_eg_box.find_all('li', recursive=False))])
        def_t = li.find('deft')

        return {
            "id": id,
            "cefr": cefr.upper(),
            "usage": abbrev(cf.get_text()) if cf else "",
            "labels": self._parse_labels(li),
            "definition": definition,
            "def_cn": normalize_chn(def_t.find('chn', class_='simple').get_text()) if def_t else '',
            "examples": examples,
            "variants": get_soup_text(variants),
            "topic": topic.find('span', class_='topic_name').get_text() if topic else ''
        }

    def get_defs_and_egs(self, root=None):
        if not root:
            root = self.entry
        defs = root.find('ol', class_='senses_multiple', recursive=False)
        if not defs:
            defs = root.find('ol', class_='sense_single', recursive=False)
        if not defs:
            return None

        return list(filter(None, [self._parse_def(box.find('li')) for box in defs.find_all('div', class_='li_sense')]))

    def get_idioms(self):
        return [
            {
                "usage": abbrev(g.find('span', class_='idm').get_text()),
                "defs": self.get_defs_and_egs(root=g)
            }
            for g in self.entry.find_all('span', class_='idm-g')
        ]

    def get_usage(self):
        pass

    def _parse_phrase(self, li):
        a = li.find('a', class_='Ref')
        href = a.get('href', None)
        keyword = 'entry://'
        idx = href.index('#') if '#' in href else None
        redirect = href[len(keyword):idx]

        if '_' in redirect:
            redirect = redirect.split('_')[0]
        # tear-up1
        redirect = re.sub('\d+$', '', redirect)

        DictHelper = import_from('..utils', 'DictHelper', package='src.dict_parser')
        ParserManager = import_from('..dict_parser', 'ParserManager', package='src.dict_parser')

        dict_helper = DictHelper()
        parser = ParserManager()

        html = dict_helper.query_oaldpe(redirect)
        h = html[0]
        redirect_keyword = '@@@LINK='
        if h.startswith(redirect_keyword):
            h.strip()
            h=h[len(redirect_keyword):]
        return parser.parse(h, redirect, mode='phrv')
    def get_phrases(self, parent=None):
        box = self.entry.find('aside', class_='phrasal_verb_links')

        return list(filter(None, [self._parse_phrase(p) for p in box.ul.find_all('li', recursive=False)]))  if box else None

    def get_entry_prefix(self, word=None, kanji=None):
        pass

    def get_pos(self):
        pos = self.entry.find('span', class_='pos')
        return get_soup_text(pos)