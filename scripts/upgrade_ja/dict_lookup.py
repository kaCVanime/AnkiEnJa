import re
import jaconv
import pykakasi
import logging

from dict_helper import DictHelper
from dict_parser import ParserManager
from utils import is_string_katakana, kata2hira, z2h

logger = logging.getLogger(__name__)
kks = pykakasi.kakasi()
mdx_helper = DictHelper()

def convert_to_hiragana(word):
    # 絵付け　-> えつけ
    results = kks.convert(word)
    return ''.join([block.get('hira', '') for block in results])

def redirect_if_link(result, word, yomi, mode='all'):
    result = result.strip()
    LINK_KEYWORD = "@@@LINK="
    query = get_query_method(mode)
    if result.upper().startswith(LINK_KEYWORD):
        redirect_word = result[len(LINK_KEYWORD):]
        if LINK_KEYWORD in redirect_word:
            logger.warning(f"{word}: Multiple LINK detected: {result}. Choosing 1st")
            redirect_word = redirect_word.split(LINK_KEYWORD)[0]
        # logger.warning(f'{word}: redirecting')
        results = query(redirect_word)
        return pick(redirect_word, yomi, results, mode=mode)
    else:
        redirect_entries = ParserManager.get_best_redirect_entry(result, yomi)
        if redirect_entries:
            if len(redirect_entries) > 1:
                logger.warning(f"{word}: Multiple LINK detected: {redirect_entries}. Choosing 1st")
            redirect_word = redirect_entries[0]
            results = query(redirect_word)
            return pick(redirect_word, yomi, results, mode=mode)

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
    if "<link rel=" in entry:
        return True
    # word = 赤々
    if '々'in word:
        return check_entry(entry, replace_repeater(word), yomi)

    yomi = kata2hira(yomi)
    if f'{word}【{yomi}】' in entry or f'{yomi}【{word}】' in entry:
        return True

    # word = おびやかす【脅かす】
    if '【' in word:
        return word in entry

    return bool(re.search(f'{yomi}【.*{word}.*】', entry))

def filter_dict_entries(results):
    blacklist = ["<HeaderTitle>大辞泉プラス</HeaderTitle>"]
    return list(
        filter(
            lambda result: all([keyword not in result for keyword in blacklist]),
            results
        )
    )

def is_redirect_entry(html):
    if html.startswith('@@@LINK='):
        return True
    return ParserManager.is_redirect_entry(html)


def pick(word, yomi, results, mode):
    results = filter_dict_entries(results)

    if not len(results):
        logger.error(f'{word}-{yomi}. no entries')
        return None

    if not is_redirect_entry(results[0]):
        if len(results) > 1:
            logger.error(f'{word}-{yomi}. Multiple entries found, choose 1st valid')
        return results[0].strip()

    if is_string_katakana(word) or len(results) == 1:
        result = redirect_if_link(results[0], word, yomi, mode=mode)
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
        result = redirect_if_link(targets[0], word, yomi, mode=mode)

    if not result:
        logger.error(f'{word}-{yomi}. no entries found')

    return result

def get_query_method(mode='all'):
    if mode == 'all':
        return mdx_helper.query_all
    elif mode == 'XSJ':
        return mdx_helper.query_xsj
    elif mode == 'DJS':
        return mdx_helper.query_djs
    elif mode == 'MOJI':
        return mdx_helper.query_moji

def lookup(word, yomi, mode='all'):
    # 全角英文转半角
    word = z2h(word, kana=False, ascii=True, digit=True)
    query = get_query_method(mode=mode)

    results = query(word)
    if '々' in word and not len(results):
        logger.warning(f'{word}: try replacing onaji')
        logger.debug(replace_repeater(word))
        word = replace_repeater(word)
        results = query(word)
    if not len(results):
        logger.warning(f'{word}: try mode full hiragana')
        word = convert_to_hiragana(word)
        results = query(word)

    result = pick(word, yomi, results, mode=mode)

    return result


if __name__ == '__main__':
    result = lookup('ＩＱ', 'アイキュー')
    pass