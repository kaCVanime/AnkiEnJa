from bs4 import BeautifulSoup
from bs4.element import NavigableString
from loguru import logger
import re

from .base import Base
from copy import copy

logger.add('JLPT.log')

# '〜いかんにかかわらず / いかんによらず / いかんをとわず_0_3'
# -> 〜いかんにかかわらず / いかんによらず / いかんをとわず_0_3
def normalize(s):
    return re.sub('[\>\<\"\/\|\?\*\:\+：？！“”]', '', s).replace(' ', '_')

def remove_example_in_definition(tag):
    tag = copy(tag)
    c = tag.next_element
    to_remove = []
    while c:
        if c.get_text() == '例文':
            while c:
                to_remove.append(c)
                c = c.next_sibling
        c = c.next_sibling if c else None

    for t in to_remove:
        t.extract()
    return tag

def replace_strong(tag):
    tag = copy(tag)
    ts = tag.find_all('strong')
    if ts:
        for t in ts:
            text = NavigableString(t.get_text())
            t.replace_with(text)
    return tag

def join_br(tag):
    brs = tag.find_all('br')
    if not brs:
        return tag.get_text()

    us = []
    for br in brs:
        ps = []
        prev_e = br.previous_sibling
        while isinstance(prev_e, NavigableString):
            ps.append(prev_e.get_text())
            prev_e = prev_e.previous_sibling
        us.append(''.join(list(reversed(ps))))


    last_e = brs[-1].next_sibling
    s = ''
    while isinstance(last_e, NavigableString):
        s += last_e.get_text()
        last_e = last_e.next_sibling
    if s:
        us.append(s)
    return '; '.join(us)

class JLPTParser(Base):

    def get_word(self):
        s = self.html.find("span", class_="header").get_text()
        return re.sub(r"文型\d：", "", s)

    def get_kanji(self):
        pass


    def get_accent(self):
        pass

    def _get_definition(self):
        imi = self.html.find('span', class_='imi')
        return join_br(replace_strong(remove_example_in_definition(imi)))

    def _get_examples(self, prefix):
        reibun = self.html.find('span', class_='reibun')
        if not reibun:
            return []
        lis = reibun.find_all('li')
        results = []
        for idx, li in enumerate(lis):
            results.append({
                "ja": li.get_text(),
                "cn": "",
                "name": f'{prefix}_{idx}'
            })

        return results


    def _get_next_none_br_sibling(self, tag):
        n = tag.next_sibling
        if n and n.name == 'br':
            n = n.next_sibling
        return n

    def get_usage(self):
        subs = self.html.find_all("span", class_="sub-header")
        subs = list(filter(lambda s: s.get_text() != '例文' and s.get_text() != '意味' and s.get_text() != '備考', subs))
        if not subs:
            return None
        if len(subs) > 1:
            logger.warning('{}: found multiple usage', self.get_word())
        sub = subs[0]
        content = self._get_next_none_br_sibling(sub)
        return join_br(content)

    def get_defs_and_egs(self):
        prefix = self.get_entry_prefix(word=self.html.find("span", class_="header").get_text())
        id = normalize(prefix)
        definition = self._get_definition()
        examples = self._get_examples(id)

        return [{
            "id": id,
            "definition": definition,
            "def_cn": "",
            "examples": examples
        }]


    def get_idioms(self):
        pass

    def get_phrases(self, parent=None):
        pass

