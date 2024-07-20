from .base import ModelBase

class ModelListen(ModelBase):
    name = "Listen"
    fields = [
        "id",
        "word",
        "label",
        "usage",
        "definition",
        "def_cn",
        "examples",
        "audio",
    ]
    is_cloze = False
    card_templates = [
        {
            "Name": "Listen",
            "Front": "Front {{id}}",
            "Back": "Back {{id}}",
        }
    ]


class ModelRead(ModelBase):
    name = "Read"
    fields = [
        "id",
        "word",
        "cefr",
        "AmEPhonetic",
        "BrEPhonetic",
        "pos",
        "usage",
        "labels,"
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
            "Front": "Front {{id}}",
            "Back": "Back {{id}}",
        }
    ]


class ModelWrite(ModelBase):
    name = "Write"
    fields = [
        "id",
        "word",
        "cefr",
        "AmEPhonetic",
        "BrEPhonetic",
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
            "Name": "Write",
            "Front": "Front {{id}}",
            "Back": "Back {{id}}",
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