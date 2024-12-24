from abc import ABC, abstractmethod
from ..anki_connect import invoke as anki_invoke


class ModelBase(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def fields(self):
        pass

    @property
    @abstractmethod
    def is_cloze(self):
        pass

    @property
    @abstractmethod
    def card_templates(self):
        pass

    def create_model(self):
        return anki_invoke(
            "createModel",
            modelName=self.name,
            inOrderFields=self.fields,
            css="",
            isCloze=self.is_cloze,
            cardTemplates=self.card_templates,
        )

    def has_model(self):
        model_names = anki_invoke("modelNames")
        return self.name in model_names

    def add_note(self, deck, fields, tags=None):
        if not self.has_model():
            self.create_model()
        note = {
                "deckName": deck,
                "modelName": self.name,
                "fields": fields,
                "options": {
                    "allowDuplicate": True,
                },
            }
        if tags:
            note["tags"] = tags

        return anki_invoke(
            "addNote",
            note=note,
        )
