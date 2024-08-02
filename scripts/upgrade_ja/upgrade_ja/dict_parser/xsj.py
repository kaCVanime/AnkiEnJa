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

class XSJParser(Base):
    # TODO special case 気に入る
    def get_word(self):
        tag = self.html.find("span", class_="xsjrh-word1")
        return tag.get_text() if tag else None

    def get_kanji(self):
        tag = self.html.find("span", class_="xsjrh-word2")
        return tag.get_text() if tag else None

    def get_accent(self):
        return None

    def _get_def_egs(self, definition, prefix):
        eg_box = definition.find("div", class_="xsjrh-exbox")
        if not eg_box:
            return None
        egs = eg_box.find_all("span", recursive=False)
        result = []
        for eg_idx, eg in enumerate(egs):
            ja = get_soup_text(eg.find("span", class_="xsjrh-j"))
            cn = get_soup_text(eg.find("span", class_="xsjrh-c"))
            result.append({"ja": ja, "cn": cn, "name": f"{prefix}_{eg_idx}"})
        return result

    def _get_defs_and_egs(self, body, sense_class, sense_li_class):
        prefix = self.get_entry_prefix()
        senses = body.find_all("div", class_=sense_class)
        result = []
        for def_box_idx, sense in enumerate(senses):
            sense_li = sense.find_all("span", class_=sense_li_class)
            for def_idx, definition in enumerate(sense_li):
                def_ja = get_soup_text(definition.find("span", class_="xsjrh-j"))
                def_cn = get_soup_text(definition.find("span", class_="xsjrh-c"))
                id = f"{prefix}_{def_box_idx}_{def_idx}"
                result.append(
                    {
                        "id": id,
                        "definition": def_ja,
                        "def_cn": def_cn,
                        "examples": self._get_def_egs(definition, id),
                    }
                )
        return result

    def get_defs_and_egs(self):
        body = self.html.find("div", class_="xsjrh-body")
        return self._get_defs_and_egs(body, "xsjrh-sense", "xsjrh-sense-li")

    def get_redirect_word_from_a(self, soup):
        href = soup.get("href")
        return re.sub("entry://", "", href)

    def get_idioms(self):
        lookup = import_from("upgrade_ja.dict_lookup", "lookup")

        container = self.html.find("div", class_="xsjrh-pbox")
        if not container:
            return None
        boxs = container.find_all("span", class_="xsjrh-p")
        results = []
        for idx, box in enumerate(boxs):
            a = box.a
            if not a:
                logger.error(f"no link found. {str(box)}")
                continue
            result = lookup(self.get_redirect_word_from_a(a), None, mode="XSJ")
            if not result:
                logger.error(f"{a.get_text()} no idiom entry.")
                continue

            idiom_parser = XSJIdiomParser(BeautifulSoup(result, "html.parser"))
            result = {
                "dict_type": "XSJ",
                "word": idiom_parser.get_word(),
                "kanji": idiom_parser.get_kanji(),
                "accent": idiom_parser.get_accent(),
                "defs": idiom_parser.get_defs_and_egs(),
            }
            if not result["word"] and not result["kanji"]:
                logger.error(f"{a.get_text()} entry is empty.")
                continue
            results.append(result)
        return results

    def get_phrases(self, parent=None):
        startpoint = self.html.find("div", class_="phrase-item")
        if not startpoint:
            return None

        parent = parent or {}
        prefix = self.get_entry_prefix(
            parent.get("word", None), parent.get("kanji", None)
        )

        result = []
        phrases = [
            e for e in startpoint.next_siblings if "xsjrh-word-block" in e.get("class")
        ]
        for idx, phrase in enumerate(phrases):
            usage = phrase.find("span", class_="xsjrh-pword").get_text()

            defs = []
            current = phrase.next_sibling
            while current and "xsjrh-psense" in current.get("class"):
                defs.append(current)
                current = current.next_sibling

            for def_idx, definition in enumerate(defs):
                id = f"{prefix}_{idx}_{def_idx}"
                result.append(
                    {
                        **parent,
                        "id": id,
                        "usage": usage,
                        "definition": get_soup_text(
                            definition.find("span", class_="xsjrh-j")
                        ),
                        "def_cn": get_soup_text(
                            definition.find("span", class_="xsjrh-c")
                        ),
                        "examples": self._get_def_egs(definition, id),
                    }
                )

        return result

    @staticmethod
    def is_redirect_entry(s):
        parser = XSJParser(BeautifulSoup(s, "html.parser"))
        defs = parser.get_defs_and_egs()
        return len(defs) >= 1 and defs[0]["definition"].startswith("➪")

    def get_redirect_entries(self):
        defs = self.get_defs_and_egs()
        return [
            normalize_redirect_word(d["definition"][1:])
            for d in defs
            if d["definition"].startswith("➪")
        ]

    def get_best_redirect_entry(self, yomi):
        entries = self.get_redirect_entries()
        return [entries[0]]


class XSJIdiomParser(XSJParser):
    def _get_head(self):
        head = self.html.find("div", class_="xsjrh-head")
        return copy.copy(head.find("span", class_="xsjrh-pword"))

    def get_word(self):
        head = self._get_head()
        ks = head.find_all("span", class_="xsjrh-k")
        for k in ks:
            prev = k.previous_element
            prev.string.replace_with(remove_last_word(str(prev.string)))
        return head.get_text()

    def get_kanji(self):
        head = self._get_head()
        ks = head.find_all("span", class_="xsjrh-k")
        for k in ks:
            k.extract()
        return head.get_text()

    def get_defs_and_egs(self):
        body = self.html.find("div", class_="xsjrh-body")
        return self._get_defs_and_egs(body, "xsjrh-psense", "xsjrh-psense-li")

    def get_accent(self):
        pass

    def get_idioms(self):
        pass

    def get_usage(self):
        pass