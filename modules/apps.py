# Application Control

import json
import os
import shutil
import subprocess


def GetAppDataDir():
    """
    Stable, writable location for VARVIS's own data, independent of the
    current working directory the process happens to be launched from.
    %LOCALAPPDATA%\\VARVIS is the standard place for per-user app data
    on Windows - unlike a path relative to cwd, this resolves the same
    way whether you run `python main.py` from the project root or launch
    the packaged exe from anywhere on disk.
    """
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    appDir = os.path.join(base, "VARVIS")
    os.makedirs(appDir, exist_ok=True)
    return appDir


DatabaseFile = os.path.join(GetAppDataDir(), "apps.json")

# One-time migration: if you already have a scanned apps.json sitting in
# the old project-relative "database/" folder, copy it into the new
# stable location so you don't lose that scan the first time this runs.
_OldDatabaseFile = "database/apps.json"
if not os.path.exists(DatabaseFile) and os.path.exists(_OldDatabaseFile):
    shutil.copy(_OldDatabaseFile, DatabaseFile)

SearchFolders = [
    os.environ.get("ProgramFiles", ""),
    os.environ.get("ProgramFiles(x86)", ""),
    os.environ.get("LOCALAPPDATA", "")
]
ProtectedApps = [
    "windowsterminal",
    "python",
    "code"
]

def LoadApps():
    if not os.path.exists(DatabaseFile):
        return {}

    with open(DatabaseFile, "r") as File:
        return json.load(File)


def SaveApps(Apps):
    with open(DatabaseFile, "w") as File:
        json.dump(Apps, File, indent=4)


def ScanForApps():
    FoundApps = {}

    for Folder in SearchFolders:
        if not Folder:
            continue

        for Root, _, Files in os.walk(Folder):
            for File in Files:
                if File.lower().endswith(".exe"):
                    AppName = os.path.splitext(File)[0].lower()
                    FoundApps[AppName] = os.path.join(Root, File)

    SaveApps(FoundApps)
    return FoundApps


def FindExecutable(AppName):
    Apps = LoadApps()

    Executable = Apps.get(AppName.lower())

    if Executable:
        return Executable

    print("Application not in cache. Scanning...")
    Apps = ScanForApps()

    return Apps.get(AppName.lower())


def open_app(AppName):
    Executable = FindExecutable(AppName)
    print(Executable)

    if Executable:
        subprocess.Popen(Executable)
        return f"Opening {AppName}..."
    else:
        return f"Application '{AppName}' not found."


def close_app(AppName):
    Executable = FindExecutable(AppName)

    if Executable:
        if os.path.basename(Executable).lower() in ProtectedApps:
            return f"Cannot close protected application '{AppName}'."

        subprocess.call([
            "taskkill",
            "/f",
            "/im",
            os.path.basename(Executable)
        ])

        return f"Closing {AppName}..."

    else:
        return f"Application '{AppName}' not found."