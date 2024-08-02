from bs4 import BeautifulSoup
import re

from .base import Base
from copy import copy

class KJEParser(Base):
    def _get_head(self):
        return copy(self.html.find("div", class_="midashi"))
    def get_word(self):
        header = self._get_head()
        sub = header.find('sub')
        if sub:
            return sub.get_text()

    def get_kanji(self):
        header = self._get_head()
        sub = header.find('sub')
        if sub:
            sub.decompose()
        result = header.get_text().strip()
        if result.startswith("○"):
            result = result[1:]
        if "【" in result:
            result = re.search("【(.+)】", result).group(1)
        return result


    def get_accent(self):
        pass

    def get_defs_and_egs(self):
        pass


    def get_idioms(self):
        pass

    def get_phrases(self, parent=None):
        pass

    def get_usage(self):
        pass
