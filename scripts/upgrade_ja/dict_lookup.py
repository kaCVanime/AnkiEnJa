import re
import jaconv
import pykakasi
import logging

from dict_helper import DictHelper
from utils import is_katakana

logger = logging.getLogger(__name__)
kks = pykakasi.kakasi()
mdx_helper = DictHelper()

def is_string_katakana(text):
    return all(is_katakana(c) for c in text)

def convert_to_hiragana(word):
    # 絵付け　-> えつけ
    results = kks.convert(word)
    return ''.join([block.get('hira', '') for block in results])

def redirect_if_link(result, word, yomi):
    result = result.strip()
    LINK_KEYWORD = "@@@LINK="
    if result.upper().startswith(LINK_KEYWORD):
        redirect_word = result[len(LINK_KEYWORD):]
        if LINK_KEYWORD in redirect_word:
            logger.warning(f"{word}: Multiple LINK detected: {result}. Choosing 1st")
            redirect_word = redirect_word.split(LINK_KEYWORD)[0]
        # logger.warning(f'{word}: redirecting')
        results = mdx_helper.query_all(word)
        return pick(redirect_word, yomi, results)
    return result

def replace_repeater(s):
    result = []
    for i, char in enumerate(s):
        if char == '々':
            if i > 0:
                result.append(s[i-1])
            else:
                logger.error("The character '々' cannot be the first character in the string.")
                return s
        else:
            result.append(char)
    return ''.join(result)

def check_entry(entry, word, yomi):
    # word = 赤々
    if '々'in word:
        return check_entry(entry, replace_repeater(word), yomi)

    yomi = jaconv.kata2hira(yomi)
    if f'{word}【{yomi}】' in entry or f'{yomi}【{word}】' in entry:
        return True

    # word = おびやかす【脅かす】
    if '【' in word:
        return word in entry



    return bool(re.search(f'{yomi}【{word}.+】', entry))

def pick(word, yomi, results):
    if not len(results):
        logger.error(f'{word}-{yomi}. no entries')
        return None

    if not results[0].startswith('@@@LINK='):
        return results[0].strip()

    if is_string_katakana(word) or len(results) == 1:
        result = redirect_if_link(results[0], word, yomi)
    else:
        targets = list(filter(lambda res: check_entry(res, word, yomi), results))
        if not len(targets):
            targets = mdx_helper.query_best(word, -2)
            if not len(targets):
                logger.error(f'{word}-{yomi}. no valid entries')
                logger.debug(str(results))
                return None
        if len(targets) > 1:
            logger.warning(f'{word} has multiple entries. choose the first one')
        result = redirect_if_link(targets[0], word, yomi)

    if not result:
        logger.error(f'{word}-{yomi}. no entries found')

    return result

def lookup(word, yomi):
    logging.basicConfig(
        filename="lookup.log",
        level=logging.ERROR,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
        encoding='utf-8'
    )

    # 全角英文转半角
    word = jaconv.z2h(word, kana=False, ascii=True, digit=True)

    results = mdx_helper.query_all(word)
    if '々' in word and not len(results):
        logger.warning(f'{word}: try replacing onaji')
        logger.debug(replace_repeater(word))
        word = replace_repeater(word)
        results = mdx_helper.query_all(word)
    if not len(results):
        logger.warning(f'{word}: try mode full hiragana')
        word = convert_to_hiragana(word)
        results = mdx_helper.query_all(word)

    result = pick(word, yomi, results)

    return result
