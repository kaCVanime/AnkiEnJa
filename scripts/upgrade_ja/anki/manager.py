import re
import json

from loguru import logger

from .anki_connect import invoke as anki_invoke
from .models.models import ModelRead, ModelWrite

def handle_tag_space(tag):
    return re.sub('\s+&\s+', '&', tag).replace(' ', '_')

def get_score(entry):
    if entry["dict_type"] != 'Common_Idioms':
        return entry["score"]

    f = entry["frequency"]

    assert isinstance(f, str)

    if f == '◎':
        return 100
    elif f == '○':
        return 75
    elif f == '△':
        return 50
    else:
        return 0

class AnkiManager:
    def __init__(self, deck_name):
        self.deck_name = deck_name
        self._create_decks(deck_name)
        self.read_model = ModelRead(deck_name)
        self.write_model = ModelWrite(deck_name)

    def _create_decks(self, deck_name):
        names = [
            deck_name,
            f"{deck_name}::Read",
            f"{deck_name}::Write",
            f"{deck_name}::Listen",
        ]
        deck_names = anki_invoke("deckNames")
        for name in names:
            if name not in deck_names:
                anki_invoke("createDeck", deck=name)

    def _get_kanji(self, entry):
        kanji = entry.get("kanji", None)
        if not kanji:
            return ''
        kanji = kanji.strip()
        if not kanji.startswith('【') :
            kanji = f'【{kanji}】'
        return kanji

    def _get_note_fields(self, entry):
        return {
            "id": entry["id"],
            "word": entry["word"] or "",
            "kanji": self._get_kanji(entry),
            "accent": entry.get("accent", "") or "",
            "definition": entry["definition"] or "",
            "def_cn": entry["def_cn"] or "",
            "examples": json.dumps(entry["examples"], ensure_ascii=False),
            "reason": entry.get("reason", "") or ""
        }

    def _get_categories(self, entry):
        return [handle_tag_space(t) for t in (entry.get("categories", None) or [])]


    def _get_frequency(self, entry):
        score = int(get_score(entry))
        if score >= 95:
            return ['K_1_required']
        elif score >= 85:
            return ['K_2_daily']
        elif score > 55:
            return ['K_3_usual']
        else:
            return ['K_4_rare']

    @logger.catch
    def handle(self, entry):
        note_fields = self._get_note_fields(entry)

        tags = [*self._get_categories(entry), *self._get_frequency(entry)]

        self.read_model.add_note(note_fields, tags)
        self.write_model.add_note(note_fields, tags)


