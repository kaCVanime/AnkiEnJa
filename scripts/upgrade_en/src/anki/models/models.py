from .base import ModelBase

class ModelSkills(ModelBase):
    name = "KEXP3_Skills"
    fields = [
        "id",
        "word",
        "AmEPhonetic",
        "BrEPhonetic",
        "usage",
        "definition",
        "def_cn",
        "examples",
        "AmEPronounciation",
        "BrEPronounciation",
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
        }
    ]

class ModelSynonyms(ModelBase):
    name = "KEXP3_Synonyms"
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