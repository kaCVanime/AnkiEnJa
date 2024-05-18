from .base import ModelBase


class ModelListen(ModelBase):
    name = "Listen"
    fields = ["id", "term", "label", "usage", "definition", "def_cn", "examples", "audio"]
    is_cloze = False
    card_templates = [
        {
            "Name": "Listen",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]


class ModelRead(ModelBase):
    name = "Read"
    fields = [
        "id",
        "term",
        "AmEPhonetic",
        "BrEPhonetic",
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
            "Name": "Read",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]


class ModelWrite(ModelBase):
    name = "Write"
    fields = [
        "id",
        "term",
        "AmEPhonetic",
        "BrEPhonetic",
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
            "Name": "Write",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]


class ModelListenJA(ModelBase):
    name = "Listen"
    fields = ["id", "term", "kana", "label", "usage", "definition", "def_cn", "examples", "audio"]
    is_cloze = False
    card_templates = [
        {
            "Name": "Listen",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]


class ModelReadJA(ModelBase):
    name = "Read"
    fields = [
        "id",
        "term",
        "kana",
        "phonetic",
        "hyouki",
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
            "Name": "Read",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]


class ModelWriteJA(ModelBase):
    name = "Write"
    fields = [
        "id",
        "term",
        "AmEPhonetic",
        "BrEPhonetic",
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
            "Name": "Write",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]
