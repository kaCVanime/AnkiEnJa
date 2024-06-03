from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import logging
import re

from utils import is_hiragana, is_katakana, kata2hira

logger = logging.getLogger(__name__)

class ParserManager:
    def __init__(self):
        pass

    @staticmethod
    def is_redirect_entry(html):
        dict_type = ParserManager.get_dict_type(html)
        if dict_type == 'Moji':
            return MojiParser.is_redirect_entry(html)
        if dict_type == 'XSJ':
            return XSJParser.is_redirect_entry(html)
        return False

    @staticmethod
    def get_best_redirect_entry(html, yomi):
        parser = ParserManager.get_parser(html)
        if isinstance(parser, MojiParser):
            return parser.get_best_redirect_entry(yomi)
        if isinstance(parser, XSJParser):
            return parser.get_best_redirect_entry(yomi)
        return []

    @staticmethod
    def get_redirect_entries(html):
        parser = ParserManager.get_parser(html)
        if isinstance(parser, MojiParser):
            return parser.get_redirect_entries()
        return []

    @staticmethod
    def get_parser(s):
        dict_type = ParserManager.get_dict_type(s)
        soup = BeautifulSoup(s, "html.parser")

        if dict_type == 'XSJ':
            return XSJParser(soup)
        elif dict_type == 'DJS':
            return DJSParser(soup)
        elif dict_type == 'Moji':
            return MojiParser(soup)
        else:
            return None


    @staticmethod
    def get_dict_type(input):
        if "xsjrh.css" in input:
            return "XSJ"
        elif "DJS.css" in input:
            return "DJS"
        elif "mojicishu.css" in input:
            return "Moji"
        else:
            logger.error("Unknown dict type")
            logger.error(input)
            return None

    def parse(self, s):
        dict_type = self.get_dict_type(s)

        parser = self.get_parser(s)

        word = parser.get_word()
        kanji = parser.get_kanji()
        accent = parser.get_accent()
        defs = parser.get_defs_and_egs()
        if not word and not kanji:
            logger.error("get word and kanji failed")
            logger.error(str(parser.html))
        return {
            "dict_type": dict_type,
            "word": word,
            "kanji": kanji,
            "accent": accent,
            "defs": defs
        }




class Base(ABC):
    def __init__(self, html):
        self.html = html
    @abstractmethod
    def get_word(self):
        pass

    @abstractmethod
    def get_kanji(self):
        pass

    # @abstractmethod
    # def get_yomi(self):
    #     pass
    #
    @abstractmethod
    def get_accent(self):
        pass

    def get_entry_prefix(self):
        word = self.get_word()
        kanji = self.get_kanji()
        return "_".join(filter(None, [word, kanji]))


    @abstractmethod
    def get_defs_and_egs(self):
        pass

def get_soup_text(soup):
    return soup.get_text() if soup else ''

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
        return [d["definition"][1:] for d in defs if d["definition"].startswith("➪")]

    def get_best_redirect_entry(self, yomi):
        entries = self.get_redirect_entries()
        return [entries[0]]


class DJSParser(Base):
    def get_word(self):
        tag = self.html.find('headword', class_='見出')
        return tag.get_text() if tag else None

    def get_kanji(self):
        tag = self.html.find('headword', class_='表記')
        return tag.get_text() if tag else None

    def get_accent(self):
        tag = self.html.find('maccentaudiog')
        return tag.get_text() if tag else None

    def get_defs_and_egs(self):
        prefix = self.get_entry_prefix()
        contents = self.html.find('contents')
        defs = contents.find('span', class_='解説G').find_all("mg", id=bool)
        result = []
        for def_idx, definition_box in enumerate(defs):
            definition = definition_box.meaning
            if definition.rect:
                definition.rect.decompose()
            eg_boxs = definition.find_all('exg')
            egs = []
            for eg_idx, eg in enumerate(eg_boxs):
                eg.extract()
                egs.append({
                    "name": f'{prefix}_{def_idx}_{eg_idx}',
                    "ja": eg.get_text(),
                    "cn": ''
                })
            result.append({
                "id": f'{prefix}_{def_idx}',
                "definition": definition.get_text(),
                "def_cn": "",
                "examples": egs
            })
        return result






def kata_only(s):
    return ''.join([c for c in s if is_katakana(c) or is_hiragana(c)])

class MojiParser(Base):
    def _get_entry_str(self):
        entry = self.html.find('h3', class_="entry_name")
        entry = entry.get_text() if entry else None
        if entry and "【" not in entry:
            see_also = self.html.find('div', class_="seealso")
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
            return entry[index+1:-1]
        return None

    def _get_def_egs(self, definition, prefix):
        result = []
        current = definition
        count = 0
        while current.next_sibling and 'sentence' in current.next_sibling['class']:
            current = current.next_sibling
            result.append({
                'name': f'{prefix}_{count}',
                'ja': get_soup_text(current.find('div', class_='sentence_o')),
                'cn': get_soup_text(current.find('div', class_='sentence_t'))
            })
            count += 1
        return result

    def _get_def_cn(self, explanation):
        pattern = "（"
        if len(re.findall(pattern, explanation)) > 1:
            logger.error(f"Multiple ( found")
            logger.error(explanation)
        if pattern in explanation:
            return explanation[:explanation.index(pattern)]
        return None


    def _get_def_ja(self, explanation):
        pattern = "（"
        if pattern in explanation:
            return explanation[(explanation.index(pattern) + 1):-1]
        return None

    def get_defs_and_egs(self):
        prefix = self.get_entry_prefix()
        body = self.html.find('div', class_='cixing')
        if not body:
            return None
        result = []
        defs = body.find_all('div', class_='explanation')
        for def_idx, definition in enumerate(defs):
            id = f'{prefix}_{def_idx}'
            egs = self._get_def_egs(definition, id)
            explanation = get_soup_text(definition)
            result.append({
                "id": id,
                "definition": self._get_def_ja(explanation),
                "def_cn": self._get_def_ja(explanation),
                "examples": egs
            })
        return result

    @staticmethod
    def is_redirect_entry(html):
        return '<div class="cixing">' not in html and '<div class="seealso">' in html

    def get_redirect_entries(self):
        see_alsos = self.html.find_all('div', class_="seealso")
        return [also.a.get_text() for also in see_alsos]

    def get_best_redirect_entry(self, yomi):
        entries = self.get_redirect_entries()
        for entry in entries:
            word = self.get_word(entry)
            if word == kata2hira(yomi):
                return [entry]
        return entries




if __name__ == '__main__':
    print(ParserManager.is_redirect_entry('<link rel="stylesheet" href="xsjrh.css" type="text/css"><div class="xsjrh-entry"><div class="xsjrh-head"><span class="xsjrh-word-block"><span class="xsjrh-word1">IQ</span><span class="xsjrh-word2"></span></span></div><div class="xsjrh-body"><span class="xsjrh-cat">〔intelligence quotient〕</span><div class="xsjrh-sense"><span class="xsjrh-sense-wrap"><span class="xsjrh-sense-li"><span class="xsjrh-j">➪知能指数</span></span></span></div></div></div>'))
