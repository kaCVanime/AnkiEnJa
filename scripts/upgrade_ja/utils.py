import jaconv

def is_katakana(letter):
    return "\u30A0" <= letter <= "\u30FF"

def is_hiragana(letter):
    return "\u3041" <= letter <= "\u3094" or "\u3099" <= letter <= "\u309E"

def is_string_katakana(text):
    return all(is_katakana(c) for c in text)


def z2h(*args, **kwargs):
    return jaconv.z2h(*args, **kwargs)

def kata2hira(*args, **kwargs):
    return jaconv.kata2hira(*args, **kwargs)

