from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import logging

from utils import is_hiragana, is_katakana

logger = logging.getLogger(__name__)

logging.basicConfig(
        filename="parser.log",
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
        encoding='utf-8'
    )

class ParserManager:
    def __init__(self):
        pass
    def get_dict_type(self, input):
        soup = BeautifulSoup(input, parser="html.parser")
        dict_type = None
        if "xsjrh.css" in str(soup):
            dict_type = "XSJ"
        elif "DJS.css" in str(soup):
            dict_type = "DJS"
        elif "mojicishu.css" in str(soup):
            dict_type = "Moji"
        else:
            logger.error("Unknown dict type")
            logger.debug(input)

        return dict_type, soup

    def parse(self, s):
        dict_type, soup = self.get_dict_type(s)

        if dict_type == 'XSJ':
            parser = XSJParser(soup)
        elif dict_type == 'DJS':
            parser = DJSParser(soup)
        elif dict_type == 'Moji':
            parser = MojiParser(soup)
        else:
            return None

        return {
            "word": parser.get_word(),
            "kanji": parser.get_kanji()
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
    # @abstractmethod
    # def get_accent(self):
    #     pass
    #
    # @abstractmethod
    # def get_definition_and_examples(self):
    #     pass

class XSJParser(Base):
    def get_word(self):
        tag = self.html.find('span', class_='xsjrh-word1')
        return tag.get_text() if tag else None

    def get_kanji(self):
        tag = self.html.find('span', class_='xsjrh-word2')
        return tag.get_text() if tag else None


class DJSParser(Base):
    def get_word(self):
        tag = self.html.find('headword', class_='見出')
        return tag.get_text() if tag else None

    def get_kanji(self):
        tag = self.html.find('headword', class_='表記')
        return tag.get_text() if tag else None


def kata_only(s):
    return ''.join([c for c in s if is_katakana(c) or is_hiragana(c)])

class MojiParser(Base):

    def _get_entry_str(self):
        entry = self.html.find('h3', class_="entry_name")
        entry = entry.get_text() if entry else None
        if entry and "【" not in entry:
            logger.error("get_word error")
            logger.debug(self.html)
            return None
        return entry
    def get_word(self):
        entry = self._get_entry_str()
        if entry:
            index = entry.index("【")
            return kata_only(entry[index:])
        return None

    def get_kanji(self):
        entry = self._get_entry_str()
        if entry:
            index = entry.index("【")
            return f"【{entry[:index]}】"
        return None


