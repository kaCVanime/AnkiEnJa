from abc import ABC, abstractmethod


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

    def get_entry_prefix(self, word=None, kanji=None):
        word = word or self.get_word()
        kanji = kanji or self.get_kanji()
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
