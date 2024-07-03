from bs4 import BeautifulSoup
from loguru import logger
import json

from .oaldpe import OaldpeParser

from ..utils import remove_non_ascii



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
    def get_best_redirect_word(html):
        dict_type = ParserManager.get_dict_type(html)
        if dict_type == "OALDPE":
            return OaldpeParser.get_best_redirect_word(html)
        raise NotImplementedError


    @staticmethod
    def get_parser(s, word, match=False):
        dict_type = ParserManager.get_dict_type(s)
        soup = BeautifulSoup(s, "html.parser")
        if dict_type == "OALDPE":
            entries = OaldpeParser.get_entries(soup)
            parsers = [OaldpeParser(soup, e) for e in entries]
            if match:
                results = [p for p in parsers if remove_non_ascii(p.get_word()) == word]
                if not results:
                    for p in parsers:
                        defs = p.get_defs_and_egs()
                        if defs:
                            for d in defs:
                                if d["variants"] == word:
                                    p.specify_def(d["id"])
                                    return [p]
            else:
                return [p for p in parsers]

            return results

    @staticmethod
    def get_dict_type(input):
        if "oaldpe.css" in input:
            return "OALDPE"
        raise NotImplementedError

    def _parse(self, parser, dict_type, mode=None):
        defs = parser.get_defs_and_egs()
        word = parser.get_word()
        usage = parser.get_usage()
        idioms = parser.get_idioms()
        phonetics = parser.get_phonetics()
        phrases = parser.get_phrases()
        pos = parser.get_pos()

        if not defs and not idioms and not phrases:
            return None

        if hasattr(parser, 'x_def_id'):
            defs = [d for d in defs if d["id"] == parser.x_def_id]
            usage = None
            word = defs[0]["variants"]
            phrases = None

        result = {
            "dict_type": dict_type,
            "word": word,
            "phonetics": phonetics,
            "defs": defs,
            "idioms": idioms,
            "phrases": phrases,
            "usage": usage,
            "pos": pos
        }

        with logger.contextualize(**result):
            logger.debug(json.dumps(result, ensure_ascii=False))

        return result

    def parse(self, s, word, mode=None):
        dict_type = self.get_dict_type(s)

        parsers = self.get_parser(s, word, match=mode!='phrv')

        return list(filter(None, [self._parse(p, dict_type, mode) for p in parsers]))
