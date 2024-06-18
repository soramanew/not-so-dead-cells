from abc import ABC

from .modifier import Modifier


class Item(ABC):
    dps: float

    @property
    def modifiers_str(self) -> str:
        return "\n".join(map(lambda m: f"  - {m.to_friendly_str()}", self.modifiers))

    def __init__(self, name: str, modifiers: list[Modifier], **kwargs):
        super().__init__(**kwargs)
        self.name: str = name
        self.modifiers: list[Modifier] = modifiers
