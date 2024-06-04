from .base import Base
from ..utils import (
    is_katakana,
    is_hiragana,
    get_soup_text,
    remove_punctuations,
    remove_any_in_parenthesis,
    kata2hira,
)


def kata_only(s):
    return "".join([c for c in s if is_katakana(c) or is_hiragana(c)])


class MojiParser(Base):
    def _get_entry_str(self):
        entry = self.html.find("h3", class_="entry_name")
        entry = entry.get_text() if entry else None
        if entry and "【" not in entry:
            see_also = self.html.find("div", class_="seealso")
            if see_also:
                return see_also.find("a").get_text()
            return None
        return entry

    def get_word(self, text=None):
        entry = text or self._get_entry_str()
        if entry:
            index = entry.index("【")
            return kata_only(entry[index:])
        return None

    def get_kanji(self, text=None):
        entry = text or self._get_entry_str()
        if entry:
            index = entry.index("【")
            return f"【{entry[:index]}】"
        return None

    def get_accent(self):
        entry = self._get_entry_str()
        if entry:
            index = entry.index("【")
            return entry[index + 1 : -1]
        return None

    def _get_def_egs(self, definition, prefix):
        result = []
        current = definition
        count = 0
        while current.next_sibling and "sentence" in current.next_sibling["class"]:
            current = current.next_sibling
            result.append(
                {
                    "name": f"{prefix}_{count}",
                    "ja": get_soup_text(current.find("div", class_="sentence_o")),
                    "cn": get_soup_text(current.find("div", class_="sentence_t")),
                }
            )
            count += 1
        return result

    def _get_def_cn(self, explanation):
        pattern = "（"
        if pattern in explanation:
            return explanation[: explanation.index(pattern)]
        return None

    def _get_def_ja(self, explanation):
        pattern = "（"
        if pattern in explanation:
            return explanation[(explanation.index(pattern) + 1) : -1]
        return None

    def get_defs_and_egs(self):
        prefix = self.get_entry_prefix()
        body = self.html.find("div", class_="cixing")
        if not body:
            return None
        result = []
        defs = body.find_all("div", class_="explanation")
        for def_idx, definition in enumerate(defs):
            id = f"{prefix}_{def_idx}"
            egs = self._get_def_egs(definition, id)
            explanation = get_soup_text(definition)
            result.append(
                {
                    "id": id,
                    "definition": self._get_def_ja(explanation),
                    "def_cn": self._get_def_ja(explanation),
                    "examples": egs,
                }
            )
        return result

    @staticmethod
    def is_redirect_entry(html):
        return '<div class="cixing">' not in html and '<div class="seealso">' in html

    def get_redirect_entries(self):
        see_alsos = self.html.find_all("div", class_="seealso")
        return [
            remove_punctuations(remove_any_in_parenthesis(also.a.get_text())).strip()
            for also in see_alsos
        ]

    def get_best_redirect_entry(self, yomi):
        entries = self.get_redirect_entries()
        for entry in entries:
            word = self.get_word(entry)
            if word == kata2hira(yomi):
                return [entry]
        return entries

    def get_idioms(self):
        pass

    def get_phrases(self, parent=None):
        pass
