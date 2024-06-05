import importlib
import pykakasi

import jaconv
import re

kks = None


def import_from(package, method):
    module = importlib.import_module(package)
    return getattr(module, method)


def is_katakana(letter):
    return "\u30a0" <= letter <= "\u30ff"


def is_hiragana(letter):
    return "\u3041" <= letter <= "\u3094" or "\u3099" <= letter <= "\u309e"

def is_onaji(letter):
    return letter == '々'

def is_cjk(letter):
    return "\u4e00" <= letter <= "\u9FFF"


def is_string_katakana(text):
    return all(is_katakana(c) for c in text)


def z2h(*args, **kwargs):
    return jaconv.z2h(*args, **kwargs)


def kata2hira(*args, **kwargs):
    return jaconv.kata2hira(*args, **kwargs)


def remove_any_in_parenthesis(text):
    return re.sub(r"[(（].+[)）]", "", text)


def remove_punctuations(text):
    return re.sub(r"[。.、,，]", "", text)


def remove_ord(text):
    return re.sub(r"[123456789⓪①②③④⑤⑥⑦⑧⑨⑴⑵⑶⑷⑸⑹⑺⑻⑼]", "", text)


# '煽る【あおる】' -> あおる【煽る】
def swap_bracket_content(s):
    match = re.match(r"(.*)【(.*)】", s)
    if match:
        outside, inside = match.groups()
        # Swap and reconstruct the string
        return f"{inside}【{outside}】"
    else:
        return s  # Return the original string if no match is found


def normalize_redirect_word(text):
    methods = [remove_any_in_parenthesis, remove_punctuations, remove_ord]
    for method in methods:
        text = method(text)

    return text.strip()


def get_soup_text(soup):
    return soup.get_text().strip() if soup else ""


def check_kakasi():
    global kks
    if not kks:
        kks = pykakasi.kakasi()
    return kks


def remove_last_word(text):
    kks = check_kakasi()
    results = kks.convert(text)
    if results:
        return "".join([r["orig"] for r in results[:-1]])
    return ""


# 絵付け　-> えつけ
def convert_to_hiragana(word):
    kks = check_kakasi()
    results = kks.convert(word)
    return "".join([block.get("hira", "") for block in results])
