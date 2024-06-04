# 《日语常用惯用句分类学习辞典》
import re
from pathlib import Path
from bs4 import BeautifulSoup
from bs4.element import NavigableString, CData, RubyTextString
from copy import copy

kanji_correct_table = str.maketrans({
    "颏": "顔",
    "耧": "乗",
    "撙": "揃",
    "砬": "砕",
    "阊": "闇",
    "挹": "払",
    "蓠": "薬",
    "烀": "焼",
    "搿": "挙",
    "阌": "関",
    "焓": "煙",
    "仨": "仮",
    "菹": "蘊",
    "鹈": "鵜",
    "拚": "抜",
    "庥": "応",
    "陴": "隠",
    "涞": "満",
    "綦": "線",
    "帻": "帯",
    "囵": "団",
    "耵": "恥",
    "擤": "擡",
    "迤": "込",
    "阃": "闘",
    "湄": "涙",
    "囝": "図"
})
# "异": "異" 专->専 驮->駄 戏->戯 突->衝 囵->団 寄->奇 梦->夢

class CommonIdiomsIterator:
    def __init__(self, html_dir):
        self.html_dir = html_dir
    def __iter__(self):
        self.pages = list(Path(self.html_dir).glob('*.html'))
        self.idioms = None
        return self

    def __next__(self):
        try:
            return next(self.idioms)
        except (StopIteration, TypeError):
            self._get_idioms_from_page()
            return next(self.idioms)

    def _get_idioms_from_page(self):
        if not self.pages:
            raise StopIteration

        page = self.pages.pop(0)
        with open(page, mode='r', encoding='utf-8') as f:
            html = ''.join([s.strip() for s in f.readlines()])
            html = html.translate(kanji_correct_table)

        soup = BeautifulSoup(html, 'html.parser')

        # with open(self.html_dir / 'rare_cn_character.txt', mode='r', encoding='utf-8') as f:
        #     rare_string = [s.strip() for s in f.readlines()]
        # with open(self.html_dir / 'common_ja_character.txt', mode='r', encoding='utf-8') as f:
        #     common_string = [s.strip()[-1] for s in f.readlines()]
        # soup.smooth()
        # abc = []
        # for c in str(soup):
        #     if c in rare_string and c not in common_string:
        #         abc.append(c)
        # print(abc)

        entries = soup.find_all('p', class_='kindle-cn-para-no-indent')
        result = []
        for entry in entries:
            header = entry.find('span', class_='kindle-cn-bold')

            def_cn = str(header.next_sibling).strip()

            if def_cn.startswith('参见'):
                continue

            body = entry.next_sibling
            if not body or 'kindle-cn-para-no-indent' in body.get('class', ''):
                continue

            word = self._get_word(copy(header))
            kanji = self._get_kanji(copy(header))

            body_text = body.get_text().strip()
            if "◇" in body_text:
                definition = self._get_definition_from_mix(body_text)
                examples = self._get_examples_from_mix(body_text, kanji)
            else:
                definition = self._get_definition(body_text)
                eg = body.next_sibling
                if eg and 'kindle-cn-para-no-indent' not in body.get('class', ''):
                    examples = self._get_examples(eg.get_text().strip(), kanji)


            result.append({
                "word": word,
                "kanji": kanji,
                "definition": definition,
                "def_cn": def_cn,
                "examples": examples
            })
        self.idioms = iter(result)


    def _get_word(self, header):
        rubys = header.find_all('ruby')
        for ruby in rubys:
            ruby.next_element.string.replace_with('')
        return header.get_text(types=(NavigableString, CData, RubyTextString))
    def _get_kanji(self, header):
        return header.get_text()

    def _get_definition(self, text):
        return text.lstrip()[1:].strip()

    def _get_examples(self, text, prefix):
        egs = re.split('[\u2460-\u24FF]', text)[1:]
        result = []
        for i, s in enumerate(egs):
            idx = s.index('（')
            result.append({
                "ja": s[:idx].strip(),
                "cn": s[idx:].strip()[1:-1],
                "name": f'{prefix}_{i}'
            })
        return result

    def _get_definition_from_mix(self, text):
        return text.split('◇')[0].lstrip()[1:].strip()

    def _get_examples_from_mix(self, text, prefix):
        s = text.split('◇')[1]
        idx = s.index('（')
        return [{
            "ja": s[:idx].strip(),
            "cn": s[idx:].strip()[1:-1],
            "name": f'{prefix}_0'
        }]