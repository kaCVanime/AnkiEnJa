import jaconv
import re


def is_katakana(letter):
    return "\u30a0" <= letter <= "\u30ff"


def is_hiragana(letter):
    return "\u3041" <= letter <= "\u3094" or "\u3099" <= letter <= "\u309e"


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
    return soup.get_text() if soup else ""