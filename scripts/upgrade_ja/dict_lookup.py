import re
from loguru import logger
from pathlib import Path

from .dict_helper import DictHelper
from .utils import import_from, is_string_katakana, kata2hira, z2h, swap_bracket_content, is_string_hiragana, hira2kata

cur_dir = Path(__file__).parent

mdx_helper = DictHelper()


def redirect_if_link(result, word, yomi, mode="all"):
    ParserManager = import_from("upgrade_ja.dict_parser.manager", "ParserManager")

    result = result.strip()
    LINK_KEYWORD = "@@@LINK="
    query = get_query_method(mode)
    if result.upper().startswith(LINK_KEYWORD):
        redirect_word = result[len(LINK_KEYWORD) :]
        if LINK_KEYWORD in redirect_word:
            logger.warning(f"{word}: Multiple LINK detected: {result}. Choosing 1st")
            redirect_word = redirect_word.split(LINK_KEYWORD)[0]
        # logger.warning(f'{word}: redirecting')
        results = query(redirect_word)
        return pick(redirect_word, yomi, results, mode=mode)
    elif is_redirect_entry(result):
        redirect_entries = ParserManager.get_best_redirect_entry(result, yomi)
        if redirect_entries:
            if len(redirect_entries) > 1:
                logger.warning(
                    f"{word}: Multiple LINK detected: {redirect_entries}. Choosing 1st"
                )
            redirect_word = redirect_entries[0]
            results = query(redirect_word)
            if not results:
                redirect_word = swap_bracket_content(redirect_word)
                results = query(redirect_word)
            return pick(redirect_word, yomi, results, mode=mode)

    return result


def replace_repeater(s):
    result = []
    for i, char in enumerate(s):
        if char == "々":
            if i > 0:
                result.append(s[i - 1])
            else:
                logger.error(
                    "The character '々' cannot be the first character in the string."
                )
                return s
        else:
            result.append(char)
    return "".join(result)


def check_entry(entry, word, yomi):
    if "<link rel=" in entry:
        return True
    # word = 赤々
    if "々" in word:
        return check_entry(entry, replace_repeater(word), yomi)

    if yomi:
        yomi = kata2hira(yomi)
    if f"{word}【{yomi}】" in entry or f"{yomi}【{word}】" in entry:
        return True

    # word = おびやかす【脅かす】
    if "【" in word:
        return word in entry

    return bool(re.search(f"{yomi}【.*{word}.*】", entry))


def is_redirect_entry(html):
    ParserManager = import_from("upgrade_ja.dict_parser.manager", "ParserManager")

    if html.startswith("@@@LINK="):
        return True
    return ParserManager.is_redirect_entry(html)


def pick(word, yomi, results, mode):
    if not len(results):
        if mode == "all" and not is_string_katakana(word):
            logger.error(f"{word}-{yomi}. no entries")
        return None

    if not is_redirect_entry(results[0]):
        if len(results) > 1:
            logger.warning(f"{word}-{yomi}. Multiple entries found, choose 1st valid")
        return results[0].strip()

    if is_string_katakana(word) or len(results) == 1:
        result = redirect_if_link(results[0], word, yomi, mode=mode)
    else:
        targets = list(filter(lambda res: check_entry(res, word, yomi), results))
        if not targets:
            targets = mdx_helper.query_djs(word)
            if not targets:
                targets = mdx_helper.query_moji(word)
                if not targets:
                    if mode == "all":
                        logger.error(f"{word}-{yomi}. no valid entries")
                    logger.debug(str(results))
                return None
        if len(targets) > 1:
            logger.warning(f"{word} has multiple entries. choose the first one")
        result = redirect_if_link(targets[0], word, yomi, mode=mode)

    if not result and mode == "all" and not is_string_katakana(word):
        logger.error(f"{word}-{yomi}. no entries found")

    return result


def get_query_method(mode="all"):
    if mode == "all":
        return mdx_helper.query_all
    elif mode == "XSJ":
        return mdx_helper.query_xsj
    elif mode == "DJS":
        return mdx_helper.query_djs
    elif mode == "MOJI":
        return mdx_helper.query_moji
    elif mode == 'KJE':
        return mdx_helper.query_kje


def lookup(word, yomi, mode="all"):
    # 全角英文转半角
    word = z2h(word, kana=False, ascii=True, digit=True)
    query = get_query_method(mode=mode)

    if yomi and is_string_hiragana(yomi):
        yomi = hira2kata(yomi)

    results = query(word)
    if "々" in word and not len(results):
        logger.warning(f"{word}: try replacing onaji")
        logger.debug(replace_repeater(word))
        word = replace_repeater(word)
        results = query(word)
    if not len(results) and yomi:
        logger.debug(f"{word}: try mode full hiragana")
        # word = convert_to_hiragana(word)
        word = kata2hira(yomi)
        results = query(word)
    if not len(results) and word.endswith("と") and len(word) >= 4:
        # ずらりと  -えっと
        word = word[:-1]
        results = query(word)

    result = pick(word, yomi, results, mode=mode)

    return result


if __name__ == "__main__":
    result = lookup("けっきにはやる", None, mode="KJE")
    pass
