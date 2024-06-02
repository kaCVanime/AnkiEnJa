def is_katakana(letter):
    return "\u30A0" <= letter <= "\u30FF"

def is_hiragana(letter):
    return "\u3041" <= letter <= "\u3094" or "\u3099" <= letter <= "\u309E"

