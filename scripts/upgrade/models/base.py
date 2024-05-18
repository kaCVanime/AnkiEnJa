from abc import ABC, abstractmethod
from scripts.upgrade.anki_connect import invoke as anki_invoke
import logging

logger = logging.getLogger(__name__)


class ModelBase(ABC):
    def __init__(self, root_deck):
        self.deck = f"{root_deck}::{self.name}"

    def deck(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    def model_name(self):
        return f"{self.deck}_model"

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
        logger.info(f"creating anki model {self.model_name}")
        return anki_invoke(
            "createModel",
            modelName=self.model_name,
            inOrderFields=self.fields,
            css="",
            isCloze=self.is_cloze,
            cardTemplates=self.card_templates,
        )

    def has_model(self):
        model_names = anki_invoke("modelNames")
        return self.model_name in model_names

    def add_note(self, fields):
        if not self.has_model():
            self.create_model()
        return anki_invoke(
            "addNote",
            note={
                "deckName": self.deck,
                "modelName": self.model_name,
                "fields": fields,
            },
        )
