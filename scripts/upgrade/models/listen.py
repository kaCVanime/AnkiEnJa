from base import ModelBase


class ModelListen(ModelBase):
    name = "ModelListen"
    fields = [
        "term",
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
            "Name": "Listen",
            "Front": "Front {{term}}",
            "Back": "Back {{term}}",
        }
    ]

    def __init__(self, model_name):
        self.name = model_name
