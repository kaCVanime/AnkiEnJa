from abc import ABC, abstractmethod
from scripts.upgrade.anki_connect import invoke as anki_invoke
import logging

logger = logging.getLogger(__name__)


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
    def isCloze(self):
        pass

    @property
    @abstractmethod
    def cardTemplates(self):
        pass

    def create(self):
        logger.info(f"creating anki model {self.name}")
        return anki_invoke(
            "createModel",
            modelName=self.name,
            inOrderFields=self.fields,
            css="",
            isCloze=self.isCloze,
            cardTemplates=self.cardTemplates,
        )
