from abc import ABC

from .modifier import Modifier


class Item(ABC):
    AVAILABLE_MODS: list[Modifier]

    damage: int
    dps: float

    @property
    def modifiers_str(self) -> str:
        return "\n".join(map(lambda m: f"  - {m.to_friendly_str()}", self.modifiers))

    def __init__(self, name: str, desc: str, modifiers: list[Modifier], **kwargs):
        super().__init__(**kwargs)
        self.name: str = name
        self.desc: str = desc
        self.modifiers: list[Modifier] = modifiers
        for modifier in modifiers:
            modifier.apply(self)

    def to_friendly_str(self) -> str:
        return f"{self.name} - {self.dps} DPS\n{self.desc}\n{self.modifiers_str}"
