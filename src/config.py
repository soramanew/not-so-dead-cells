import json
import logging
import os
import platform
import subprocess
import sys

from constants import APP_AUTHOR, APP_NAME
from platformdirs import user_config_path
from util.func import clamp

logger = logging.getLogger(__name__)


def set_volume(vol: float):
    if platform.system() == "Windows":  # FIXME untested
        from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.pid == os.getpid():
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                volume.SetMasterVolume(vol, None)
    elif platform.system() == "Linux":
        from shutil import which

        if which("wpctl"):
            subprocess.run(["wpctl", "set-volume", "-p", str(os.getpid()), str(vol)])
        else:
            logger.warn("Volume control on Linux requires PipeWire with the WirePlumber session controller.")
    else:
        logger.warn("Volume control is only supported on Linux and Windows.")


class Config:
    FILE = user_config_path(APP_NAME, APP_AUTHOR) / "config.json"

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = clamp(value, 1, 0)
        set_volume(self._volume)
        self.save()

    @property
    def muted(self) -> bool:
        return self._muted

    @muted.setter
    def muted(self, value: bool) -> None:
        self._muted = value
        set_volume(0 if value else self.volume)  # 0 if muted otherwise set back to prev vol
        self.save()

    def __init__(self):
        data = json.loads(Config.FILE.read_text()) if Config.FILE.is_file() else dict()
        self.volume = data.get("volume", 1)
        self.muted = data.get("muted", False)

    def save(self) -> None:
        Config.FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            Config.FILE.write_text(json.dumps({"volume": self.volume, "muted": self.muted}, indent=4))
        except AttributeError:
            pass  # Ignore when not fully initialised


# Replace module with class instance so I don't have to do `config.config.YYY` or `from config import config`
sys.modules[__name__] = Config()
