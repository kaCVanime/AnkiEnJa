from bs4 import BeautifulSoup
from loguru import logger
import json

from .oaldpe import OaldpeParser



class ParserManager:
    def __init__(self):
        pass

    @staticmethod
    def remove_useless_part(html):
        return html

    @staticmethod
    def is_redirect_entry(html):
        dict_type = ParserManager.get_dict_type(html)
        if dict_type == "OALDPE":
            return OaldpeParser.is_redirect_entry(html)
        return False

    @staticmethod
    def get_best_redirect_entry(html, yomi):
        parser = ParserManager.get_parser(html)
        return parser.get_best_redirect_entry(yomi)


    @staticmethod
    def get_parser(s):
        dict_type = ParserManager.get_dict_type(s)
        soup = BeautifulSoup(s, "html.parser")

        if dict_type == "OALDPE":
            return OaldpeParser(soup)

    @staticmethod
    def get_dict_type(input):
        if "oaldpe.css" in input:
            return "OALDPE"
        raise NotImplementedError

    def parse(self, s):
        dict_type = self.get_dict_type(s)

        parser = self.get_parser(s)

        word = parser.get_word()
        phonetics = parser.get_phonetics()
        defs = parser.get_defs_and_egs()
        idioms = parser.get_idioms()
        usage = parser.get_usage()
        # phrases = parser.get_phrases({"word": word, "kanji": kanji, "accent": accent})

        result = {
            "dict_type": dict_type,
            "word": word,
            "phonetics": phonetics,
            "defs": defs,
            "idioms": idioms,
            # "phrases": phrases,
            "usage": usage
        }

        with logger.contextualize(**result):
            logger.debug(json.dumps(result, ensure_ascii=False))

        return result
