from bs4 import BeautifulSoup
from copy import copy

from .base import Base
from ..utils import normalize_redirect_word


class DJSParser(Base):
    def __init__(self, soup):
        super().__init__(soup)
        self.remove_djs_plus()

    def remove_djs_plus(self):
        header = self.html.find("header", class_="DJSP")
        if header:
            if header.next_sibling:
                header.next_sibling.decompose()
            header.decompose()

    def get_word(self):
        tag = self.html.find("headword", class_="見出")
        return tag.get_text() if tag else None

    def get_kanji(self):
        tag = self.html.find("headword", class_="表記")
        return tag.get_text() if tag else None

    def get_accent(self):
        tag = copy(self.html.find("maccentaudiog"))
        if not tag:
            return None
        prefix = tag.find('span', class_='補足ロゴG')
        link = tag.find('a')
        for t in (prefix, link):
            if t:
                t.decompose()

        return tag.get_text().strip()

    def get_defs_and_egs(self):
        prefix = self.get_entry_prefix()
        contents = copy(self.html.find("contents"))
        if not contents:
            return None
        kaisetsu = contents.find("span", class_="解説G")
        defs = kaisetsu.find_all("mg", id=bool)
        if not defs:
            defs = kaisetsu.find_all("mg", id=True)
            # remove 類語
            defs = [defs[0]]
        result = []
        for def_idx, definition_box in enumerate(defs):
            definition = definition_box.meaning
            if not definition:
                continue

            # skip definition that has children. eg. 1. balabala(ア. balabala イ.balabala)
            if definition.next_sibling and definition.next_sibling.name == 'mg':
                continue

            if definition.rect:
                definition.rect.decompose()

            # remove ㋐
            if definition.l4:
                definition.l4.decompose()

            # 〘名〙
            if definition.hinshi:
                definition.hinshi.decompose()

            # スル
            if definition.hinshisahen:
                definition.hinshisahen.decompose()

            # 1一0〇代から2二0〇代の読者 -> 10代から20代の読者
            kh = definition.find_all('k-h', recursive=False)
            kv = definition.find_all('k-v', recursive=False)
            if kh and kv:
                for k in kv:
                    k.decompose()

            # eg_boxs = definition.find_all("exg")
            # egs = []
            # for eg_idx, eg in enumerate(eg_boxs):
            #     eg.extract()
            #     egs.append(
            #         {
            #             "name": f"{prefix}_{def_idx}_{eg_idx}",
            #             "ja": eg.get_text().strip(),
            #             "cn": "",
            #         }
            #     )
            result.append(
                {
                    "id": f"{prefix}_{def_idx}",
                    "definition": definition.get_text().strip(),
                    "def_cn": "",
                    "examples": None,
                }
            )
        return result

    @staticmethod
    def is_redirect_entry(s):
        parser = DJSParser(BeautifulSoup(s, "html.parser"))
        defs = parser.get_defs_and_egs()
        if not defs:
            return False
        return len(defs) >= 1 and defs[0]["definition"].startswith("⇒")

    def get_redirect_entries(self):
        defs = self.get_defs_and_egs()
        if defs:
            return [
                normalize_redirect_word(d["definition"][1:])
                for d in defs
                if d["definition"].startswith("⇒")
            ]

    def get_best_redirect_entry(self, yomi):
        entries = self.get_redirect_entries()
        if not entries:
            return None
        return [entries[0]]

    def get_idioms(self):
        pass

    def get_phrases(self, parent=None):
        pass

    def get_usage(self):
        pass