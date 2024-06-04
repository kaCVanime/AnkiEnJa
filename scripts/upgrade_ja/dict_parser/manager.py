from bs4 import BeautifulSoup

from .xsj import XSJParser
from .djs import DJSParser
from .moji import MojiParser


class ParserManager:
    def __init__(self):
        pass

    @staticmethod
    def remove_useless_part(html):
        dict_type = ParserManager.get_dict_type(html)
        if dict_type == "DJS" and "<HeaderTitle>大辞泉プラス</HeaderTitle>" in html:
            parser = DJSParser(BeautifulSoup(html, "html.parser"))
            defs = parser.get_defs_and_egs()
            if defs:
                return str(parser.html)
            return None

        return html

    @staticmethod
    def is_redirect_entry(html):
        dict_type = ParserManager.get_dict_type(html)
        if dict_type == "Moji":
            return MojiParser.is_redirect_entry(html)
        if dict_type == "XSJ":
            return XSJParser.is_redirect_entry(html)
        if dict_type == "DJS":
            return DJSParser.is_redirect_entry(html)
        return False

    @staticmethod
    def get_best_redirect_entry(html, yomi):
        parser = ParserManager.get_parser(html)
        return parser.get_best_redirect_entry(yomi)

    @staticmethod
    def get_redirect_entries(html):
        parser = ParserManager.get_parser(html)
        return parser.get_redirect_entries()

    @staticmethod
    def get_parser(s):
        dict_type = ParserManager.get_dict_type(s)
        soup = BeautifulSoup(s, "html.parser")

        if dict_type == "XSJ":
            return XSJParser(soup)
        elif dict_type == "DJS":
            return DJSParser(soup)
        elif dict_type == "Moji":
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
            return None

    def parse(self, s, mode=None):
        dict_type = self.get_dict_type(s)

        parser = self.get_parser(s)

        if mode == "accent":
            return {
                "accent": parser.get_accent(),
            }
        word = parser.get_word()
        kanji = parser.get_kanji()
        accent = parser.get_accent()
        defs = parser.get_defs_and_egs()
        idioms = parser.get_idioms()
        phrases = parser.get_phrases({"word": word, "kanji": kanji, "accent": accent})

        return {
            "dict_type": dict_type,
            "word": word,
            "kanji": kanji,
            "accent": accent,
            "defs": defs,
            "idioms": idioms,
            "phrases": phrases,
        }
