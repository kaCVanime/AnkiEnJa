from bs4 import BeautifulSoup

from .base import Base
from ..utils import get_soup_text, normalize_redirect_word

class XSJParser(Base):

    # TODO special case 気に入る
    def get_word(self):
        tag = self.html.find('span', class_='xsjrh-word1')
        return tag.get_text() if tag else None

    def get_kanji(self):
        tag = self.html.find('span', class_='xsjrh-word2')
        return tag.get_text() if tag else None

    def get_accent(self):
        return None

    def _get_def_egs(self, definition, prefix):
        eg_box = definition.find('div', class_='xsjrh-exbox')
        if not eg_box:
            return None
        egs = eg_box.find_all('span', recursive=False)
        result = []
        for eg_idx, eg in enumerate(egs):
            ja = get_soup_text(eg.find('span', class_='xsjrh-j'))
            cn = get_soup_text(eg.find('span', class_='xsjrh-c'))
            result.append({
                "ja": ja,
                "cn": cn,
                "name": f"{prefix}_{eg_idx}"
            })
        return result

    def get_defs_and_egs(self):
        prefix = self.get_entry_prefix()
        body = self.html.find('div', class_='xsjrh-body')
        senses = body.find_all('div', class_='xsjrh-sense')
        result = []
        for def_box_idx, sense in enumerate(senses):
            sense_li = sense.find_all('span', class_='xsjrh-sense-li')
            for def_idx, definition in enumerate(sense_li):
                def_ja = get_soup_text(definition.find('span', class_='xsjrh-j'))
                def_cn = get_soup_text(definition.find('span', class_='xsjrh-c'))
                id = f"{prefix}_{def_box_idx}_{def_idx}"
                result.append({
                    "id": id,
                    "definition": def_ja,
                    "def_cn": def_cn,
                    "examples": self._get_def_egs(definition, id)
                })
        return result

    @staticmethod
    def is_redirect_entry(s):
        parser = XSJParser(BeautifulSoup(s, "html.parser"))
        defs = parser.get_defs_and_egs()
        return len(defs) >= 1 and defs[0]["definition"].startswith("➪")

    def get_redirect_entries(self):
        defs = self.get_defs_and_egs()
        return [normalize_redirect_word(d["definition"][1:]) for d in defs if d["definition"].startswith("➪")]

    def get_best_redirect_entry(self, yomi):
        entries = self.get_redirect_entries()
        return [entries[0]]