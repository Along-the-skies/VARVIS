# Jarvis Configuration

import os
import base64
import ctypes
from ctypes import wintypes
import requests


JARVIS_NAME = "Jarvis"
DEBUG = True


# =========================
# VARVIS Data Directory
# =========================

APP_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "VARVIS"
)

os.makedirs(APP_DATA_DIR, exist_ok=True)


# =========================
# API Configuration
# =========================

API_KEY_FILE = os.path.join(
    APP_DATA_DIR,
    "key.dat"
)

BACKEND_SETUP_URL = (
    "https://varvis-backend-server.vercel.app/setup"
)

# Existing code for now.
# We are NOT generating or asking the user for one.
VARVIS_CODE = "VARVIS-2026"


# =========================
# Windows DPAPI
# =========================

class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


crypt32 = ctypes.windll.crypt32
kernel32 = ctypes.windll.kernel32


def _make_blob(data):
    buffer = ctypes.create_string_buffer(data)

    blob = DATA_BLOB()
    blob.cbData = len(data)
    blob.pbData = ctypes.cast(
        buffer,
        ctypes.POINTER(ctypes.c_byte)
    )

    return blob, buffer


def _protect(data):
    input_blob, _ = _make_blob(data)
    output_blob = DATA_BLOB()

    result = crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob)
    )

    if not result:
        raise ctypes.WinError()

    try:
        return ctypes.string_at(
            output_blob.pbData,
            output_blob.cbData
        )
    finally:
        kernel32.LocalFree(output_blob.pbData)


def _unprotect(data):
    input_blob, _ = _make_blob(data)
    output_blob = DATA_BLOB()

    result = crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob)
    )

    if not result:
        raise ctypes.WinError()

    try:
        return ctypes.string_at(
            output_blob.pbData,
            output_blob.cbData
        )
    finally:
        kernel32.LocalFree(output_blob.pbData)


# =========================
# API Key Storage
# =========================

def has_api_key():

    if not os.path.exists(API_KEY_FILE):
        return False

    try:
        return bool(load_api_key())
    except Exception:
        return False


def save_api_key(api_key):

    if not api_key:
        return False

    try:
        encrypted = _protect(
            api_key.strip().encode("utf-8")
        )

        encoded = base64.b64encode(encrypted)

        with open(API_KEY_FILE, "wb") as file:
            file.write(encoded)

        return True

    except Exception as e:
        print("API KEY SAVE ERROR:", e)
        return False


def load_api_key():

    if not os.path.exists(API_KEY_FILE):
        return None

    try:
        with open(API_KEY_FILE, "rb") as file:
            encoded = file.read()

        encrypted = base64.b64decode(encoded)

        decrypted = _unprotect(encrypted)

        return decrypted.decode("utf-8").strip()

    except Exception as e:
        print("API KEY LOAD ERROR:", e)
        return None


# =========================
# First Setup
# =========================

def setup_api_key():

    try:

        response = requests.post(
            BACKEND_SETUP_URL,
            json={
                "code": VARVIS_CODE
            },
            timeout=15
        )

        data = response.json()

        if not response.ok:

            print(
                "SETUP ERROR:",
                data.get("error", "Unknown error")
            )

            return False

        if not data.get("success"):

            print(
                "SETUP ERROR:",
                data.get("error", "Setup failed.")
            )

            return False

        api_key = data.get("key")

        if not api_key:

            print("SETUP ERROR: No API key received.")
            return False

        return save_api_key(api_key)

    except requests.RequestException as e:

        print("SETUP CONNECTION ERROR:", e)
        return False

    except Exception as e:

        print("SETUP ERROR:", e)
        return False