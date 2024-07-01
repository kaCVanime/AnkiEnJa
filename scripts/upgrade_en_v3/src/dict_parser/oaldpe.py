import re
import copy
from bs4 import BeautifulSoup
from loguru import logger
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

    def __init__(self, soup):
        super().__init__(soup)
        self.entry = self._parse_entry()

    @staticmethod
    def is_redirect_entry(html):
        return False

    @staticmethod
    def get_best_redirect_entry(html):
        return False


    def _parse_entry(self):
        entries = self.soup.find_all('div', class_='entry')
        if len(entries) > 1:
            word = self.soup.find('h1', class_='headword')
            logger.warning('{} has multiple entries', word)
        return entries[0]

    def get_word(self):
        return self.entry.find('h1', class_='headword').get_text()

    def get_phonetics(self):
        return (
            get_soup_text(self.entry.find('div', class_='phons_br')),
            get_soup_text(self.entry.find('div', class_='phons_n_am'))
        )

    def _parse_example(self, li, prefix):
        cf = li.find('span', class_='cf')
        x = li.find('span', {'class': ['x', 'unx']})

        p = x
        xt = x.find(['xt', 'unxt'])
        if xt:
            xt.extract()
            p = xt
        s_chn = p.find('chn', class_='simple')
        t_chn = p.find('chn', class_='traditional')
        s_chn.extract()
        t_chn.extract()
        return {
            "usage": abbrev(cf.get_text()) if cf else "",
            "en": x.get_text(),
            "cn": s_chn.get_text(),
            "ai": bool(s_chn.find('ai')),
            "name": prefix
        }

    def _parse_def(self, li):
        cefr = li.get('cefr', '')
        cf = li.find('span', class_='cf')
        id = li.get('id')
        labels = li.find_all('span', class_='labels')
        for label in labels:
            labelx = label.find('labelx')
            if labelx:
                labelx.extract()

        eg_box = li.find('ul', class_='examples')
        examples = [self._parse_example(li, f'{id}_{idx}') for idx, li in enumerate(eg_box.find_all('li', recursive=False))] if eg_box else []
        if len(examples) < 25:
            extra = li.find('span', class_='unbox', unbox='extra_examples')
            if extra:
                extra_eg_box = extra.find('ul', class_='examples')
                start = len(examples)
                examples.extend([self._parse_example(li, f'{id}_{idx+start}') for idx, li in enumerate(extra_eg_box.find_all('li', recursive=False))])
        return {
            "id": id,
            "cefr": cefr.upper(),
            "usage": abbrev(cf.get_text()) if cf else "",
            "labels": "".join([a.get_text() for a in labels]) if labels else "",
            "definition": li.find('span', class_='def').get_text(),
            "def_cn": normalize_chn(li.find('deft').find('chn', class_='simple').get_text()),
            "examples": examples
        }

    def get_defs_and_egs(self, root=None):
        if not root:
            root = self.entry
        defs = root.find('ol', class_='senses_multiple')
        if not defs:
            defs = root.find('ol', class_='sense_single')

        return [self._parse_def(box.find('li')) for box in defs.find_all('div', class_='li_sense')]

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

    def get_phrases(self, parent=None):
        pass

    def get_entry_prefix(self, word=None, kanji=None):
        pass