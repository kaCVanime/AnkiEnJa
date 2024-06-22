from .base import ModelBase

class ModelListen(ModelBase):
    name = "Listen"
    fields = [
        "id",
        "word",
        "kanji",
        "accent",
        "definition",
        "def_cn",
        "reason",
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
        "kanji",
        "accent",
        "definition",
        "def_cn",
        "reason",
        "examples",
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
        "kanji",
        "accent",
        "definition",
        "def_cn",
        "reason",
        "examples",
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