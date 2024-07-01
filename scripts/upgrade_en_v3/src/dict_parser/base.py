from abc import ABC, abstractmethod


class Base(ABC):
    def __init__(self, soup):
        self.soup = soup

    @abstractmethod
    def _parse_entry(self):
        pass

    @abstractmethod
    def get_word(self):
        pass


    @abstractmethod
    def get_phonetics(self):
        pass

    def get_entry_prefix(self, word=None, kanji=None):
        word = word or self.get_word()
        return "_".join(filter(None, [word, kanji]))

    @abstractmethod
    def get_defs_and_egs(self):
        pass

    @abstractmethod
    def get_idioms(self):
        pass

    @abstractmethod
    def get_phrases(self, parent=None):
        pass

    @abstractmethod
    def get_usage(self):
        pass
