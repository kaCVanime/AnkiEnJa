from base import ModelBase


class ModelWrite(ModelBase):
    name = "ModelWrite"
    fields = [
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
    isCloze = True
    cardTemplates = [
        {
            "Name": "Write",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]

    def __init__(self, model_name):
        self.name = model_name
