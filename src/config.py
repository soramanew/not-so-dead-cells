from __future__ import annotations

import json
import sys

from platformdirs import user_config_path
from util.func import get_project_root


# For dot access
class DotDict(dict):
    def __getattr__(self, k):
        return self.__getitem__(k)

    def __setattr__(self, k, v):
        self.__setitem__(k, v)

    def __delattr__(self, v):
        self.__delitem__(v)


class NestedConfig(DotDict):
    def __init__(self, parent: Config, **kwargs):
        object.__setattr__(self, "parent", parent)  # object setattr cause overridden in DotDict for dot access
        super().__init__(**kwargs)

    # Save when changes
    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        object.__getattr__(self, "parent").save()


class Config(DotDict):
    DEFAULT = {}

    FILE = user_config_path(get_project_root().stem, "Soramane") / "config.json"

    def __init__(self):
        super().__init__(
            json.loads(
                Config.FILE.read_text() if Config.FILE.is_file() else Config.DEFAULT,
                object_hook=lambda o: NestedConfig(self, **o),
            )
        )

    # Save when changes
    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        self.save()

    def load(self) -> None:
        pass

    def save(self) -> None:
        Config.FILE.parent.mkdir(parents=True, exist_ok=True)
        Config.FILE.write_text(json.dumps(self, indent=4))


# Replace module with class instance so I don't have to do `config.config.YYY` or `from config import config`
sys.modules[__name__] = Config()
