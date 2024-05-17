from base import ModelBase


class ModelRead(ModelBase):
    name = "ModelRead"
    fields = [
        "term",
        "AmEPhonetic",
        "BrEPhonetic",
        "label",
        "usage",
        "definition",
        "def_cn",
        "examples",
        "audio"
    ]
    isCloze = False
    cardTemplates = [
        {
            "Name": "Read",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]

    def __init__(self, model_name):
        self.name = model_name
