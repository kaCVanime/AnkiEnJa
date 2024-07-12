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
    def get_parser(s, word, match=False, redirect_word=None):
        o_word = word
        if redirect_word:
            word = redirect_word
        dict_type = ParserManager.get_dict_type(s)
        soup = BeautifulSoup(s, "html.parser")
        whitelist = ["o'clock", "Olympics", "and/or", "sauté", "Jeep", "IPod", "micro", "Band-Aid", "Dumpster", "oriented", "Thermos"]
        if dict_type == "OALDPE":
            entries = OaldpeParser.get_entries(soup)
            parsers = [OaldpeParser(soup, e, o_word) for e in entries]
            if o_word not in whitelist and match:
                results = [p for p in parsers if (pword := remove_non_ascii(p.get_word())) == word or pword == word.replace('-', ' ') or any([word in v for v in p.get_word_variants()])]
                if not results:
                    for p in parsers:
                        defs = p.get_defs_and_egs()
                        if defs:
                            for d in defs:
                                if word in d["variants"]:
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
        word = parser.word_overwrite or parser.get_word()
        usage = parser.get_usage()
        idioms = parser.get_idioms()
        phonetics = parser.get_phonetics()
        phrases = parser.get_phrases()
        pos = parser.get_pos()
        labels = parser.get_labels()
        synonyms = parser.get_synonyms()
        whichwords = parser.get_which_words()

        if not defs and not idioms and not phrases:
            return None

        if hasattr(parser, 'x_def_id'):
            defs = [d for d in defs if d["id"] == parser.x_def_id]
            usage = None
            word = v if '(' not in (v := defs[0]["variants"]) else word
            phrases = None
            synonyms = None
            whichwords = None

        result = {
            "dict_type": dict_type,
            "word": word,
            "phonetics": phonetics,
            "defs": defs,
            "idioms": idioms,
            "phrases": phrases,
            "usage": usage,
            "pos": pos,
            "labels": labels,
            "synonyms": synonyms,
            "whichwords": whichwords
        }

        with logger.contextualize(**result):
            logger.debug(json.dumps(result, ensure_ascii=False))

        return result

    def parse(self, s, word, mode=None, redirect_word=None):
        dict_type = self.get_dict_type(s)

        parsers = self.get_parser(s, word, match=mode!='phrv', redirect_word=redirect_word)

        return list(filter(None, [self._parse(p, dict_type, mode) for p in parsers]))
