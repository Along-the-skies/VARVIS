# VARVIS Logger

import logging
import os


def GetAppDataDir():
    """
    Stable, writable location for VARVIS's own data, independent of the
    current working directory. Matters especially for an installed exe:
    a relative "logs" folder resolves against whatever directory the
    process happened to be launched from, and under Program Files a
    standard user has no write permission there at all.
    """
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    appDir = os.path.join(base, "VARVIS")
    os.makedirs(appDir, exist_ok=True)
    return appDir


LogFolder = os.path.join(GetAppDataDir(), "logs")
LogFile = os.path.join(LogFolder, "jarvis.log")


os.makedirs(LogFolder, exist_ok=True)


logging.basicConfig(
    filename=LogFile,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


Logger = logging.getLogger("VARVIS")