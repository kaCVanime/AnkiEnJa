import re
import json

from tqdm import tqdm
from loguru import logger

from .anki_connect import invoke as anki_invoke
from .models.models import ModelRead, ModelWrite, ModelSynonyms
from ..utils import Recorder

results_recorder = Recorder()

def handle_tag(tag):
    tag = re.sub(r'\band\b', '&', tag)
    tag = re.sub(r'\s+&\s+', '&', tag)
    tag = re.sub(r',\s?', '&', tag)
    return re.sub(r'[\s:]', '_', tag)

class AnkiManager:
    def __init__(self, deck_name):
        self.deck_name = deck_name
        self._create_decks(deck_name)
        self.read_model = ModelRead(deck_name)
        self.write_model = ModelWrite(deck_name)
        self.synonyms_model = ModelSynonyms(deck_name)

    def _create_decks(self, deck_name):
        names = [
            deck_name,
            f"{deck_name}::Read",
            f"{deck_name}::Write",
            f"{deck_name}::Listen",
            f"{deck_name}::Synonyms"
        ]
        deck_names = anki_invoke("deckNames")
        for name in names:
            if name not in deck_names:
                anki_invoke("createDeck", deck=name)

    def _get_variant(self, entry):
        variant = entry.get("variants", None) or None
        return variant if variant and "also" not in variant and "formal" not in variant and "English" not in variant else None

    def _handle_labels(self, entry):
        entry_labels = entry.get("e_labels", "")
        def_labels = entry.get("labels", "")
        if entry_labels and def_labels:
            e_label = re.findall(r'\((.+?)\)', entry_labels)[0]
            d_label = re.findall(r'\((.+?)\)', def_labels)[0]
            if e_label in d_label:
                return f'({e_label})'
            elif d_label in e_label:
                return f'({d_label})'
            else:
                return entry_labels + def_labels

        return entry_labels or def_labels



    def _get_note_fields(self, entry):
        phonetics = entry.get("phonetics", "=_=").split("=_=")
        return {
            "id": entry["id"],
            "word": self._get_variant(entry) or entry.get("word", "") if (is_normal_word := "word" in entry) else entry.get("usage", "") or "",
            "cefr": entry.get("cefr", ""),
            "BrEPhonetic": phonetics[0],
            "AmEPhonetic": phonetics[1],
            "pos": entry.get("pos", ""),
            "usage": entry.get("usage", "") if is_normal_word else "" or "",
            "labels": self._handle_labels(entry),
            "definition": entry["definition"] or "",
            "def_cn": entry["def_cn"] or "",
            "examples": json.dumps(entry["examples"], ensure_ascii=False),
            "brief": entry.get("reason", "") or "",
        }

    def _get_categories(self, entry):
        categories = entry.get("topic", "")
        categories = categories.split("=_=") if "=_=" in categories else [categories]
        return [handle_tag(t) for t in categories]

    def _get_tags_from_labels(self, entry):
        labels = entry.get("labels", "") + entry.get("e_labels", "")
        if not labels:
            return []
        replacements = [
            ("North American English", "NAmE"),
            ("Northern British English", "NEngE"),
            ("South African English", "SAfrE"),
            ("East African English", "EAfrE"),
            ("West African English", "WAfrE"),
            ("North African English", "NAfrE"),
            ("South-East Asian English", "SEAsiaE"),
            ("Canadian English", "CanadE"),
            ("Irish English", "IrishE"),
            ("Welsh English", "WelshE"),
            ("Indian English", "IndE"),
            ("Scottish English", "ScotE"),
            ("British English", "BrE"),
            ("US English", "USE"),
            ("African English", "AfrE"),
            ("Australian English", "AustralE"),
            ("New Zealand English", "NZeaE"),
            ("especially", "esp.")
        ]
        for k, v in replacements:
            labels = labels.replace(k, v)

        groups = re.findall(r'\((.+?)\)', labels)

        def process_group(g):
            ls = g.split(", ")
            return [
                f"E_{l.replace(' ', '_')}"
                for l in ls
            ]

        results = [
            item
            for g in groups
            for item in process_group(g)
        ]

        return list(set(results))



    def _get_frequency(self, entry):
        score = int(entry.get("score", 60))
        if score >= 95:
            return ['K_1_required']
        elif score >= 85:
            return ['K_2_daily']
        elif score > 50:
            return ['K_3_usual']
        else:
            return ['K_4_rare']

    def _get_cefr_tag(self, entry):
        cefr = entry.get("cefr", "")
        if not cefr:
            return []
        return ['CEFR_' + cefr]


    @logger.catch
    def handle(self, entry):
        note_fields = self._get_note_fields(entry)

        tags = [
            *self._get_categories(entry),
            *self._get_frequency(entry),
            *self._get_tags_from_labels(entry),
            *self._get_cefr_tag(entry)
        ]

        self.read_model.add_note(note_fields, tags)
        self.write_model.add_note(note_fields, tags)

    # def _get_synonyms_note_fields(self, entry):
    #     return {
    #         "id": entry["id"],
    #         "words"
    #     }


    def handle_synonyms(self, entry):
        tags = ['K_1_required', 'Synonyms']

        self.synonyms_model.add_note(entry, tags)

    def process(self, todos, handle):
        for t in tqdm(todos):
            try:
                handle(t)
            except Exception as e:
                if 'duplicate' not in str(e):
                    raise e

    @logger.catch
    def run(self):
        print('adding words to anki...')
        todos = results_recorder.get_all()
        self.process(todos, self.handle)


        print('adding synonyms to anki...')
        synonyms = results_recorder.get_synonyms()
        whichwords = results_recorder.get_whichwords()
        def split_syn_entry(entry, typ):
            comm = {
                "words": entry["words"],
                    "overview": entry["overview"] if typ == "Synonyms" else "",
                "overview_cn": entry["overview_cn"] if typ == "Synonyms" else "",
                "type": typ
            }
            return [
                {
                    **comm,
                    "id": d["id"],
                    "definition": d["definition"],
                    "word": d.get("word", ""),
                    "def_cn": d["def_cn"],
                    "note": d.get("note", ""),
                    "examples": d["examples"]
                } for d in entry["defs"]
            ]
        ss = [
            item
            for e in synonyms
            for item in split_syn_entry(e, "Synonyms")
        ]
        ws = [
            item
            for e in whichwords
            for item in split_syn_entry(e, "Whichwords")
        ]
        self.process([*ss, *ws], self.handle_synonyms)



