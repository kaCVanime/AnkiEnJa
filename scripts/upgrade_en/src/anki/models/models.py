from .base import ModelBase

class ModelSkills(ModelBase):
    name = "Skills"
    fields = [
        "id",
        "word",
        "cefr",
        "AmEPhonetic",
        "BrEPhonetic",
        "pronunciation",
        "pos",
        "usage",
        "labels",
        "definition",
        "def_cn",
        "examples",
        "brief",
        "audio",
    ]
    is_cloze = False
    card_templates = [
        {
            "Name": "Read",
            "Front": "Read front {{id}}",
            "Back": "Read front {{id}}",
        },
        {
            "Name": "Write",
            "Front": "Write front {{id}}",
            "Back": "Write front {{id}}",
        },
        {
            "Name": "Listen",
            "Front": "Listen Front {{id}}",
            "Back": "Listen Back {{id}}",
        }
    ]

class ModelSynonyms(ModelBase):
    name = "Synonyms"
    fields = [
        "id",
        "word",
        "words",
        "overview",
        "overview_cn",
        "definition",
        "def_cn",
        "examples",
        "note",
        "type"
    ]
    is_cloze = False
    card_templates = [
        {
            "Name": "SynonymsRead",
            "Front": "Front {{id}}",
            "Back": "Back {{id}}",
        }
    ]
    pass