import subprocess
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc


def change_volume(value):
    try:
        value = int(value)

        if value < 0 or value > 100:
            return "Volume must be between 0 and 100."

        devices = AudioUtilities.GetSpeakers()
        volume = devices.EndpointVolume

        volume.SetMasterVolumeLevelScalar(value / 100, None)

        return f"Volume changed to {value}%"

    except Exception as e:
        return f"Volume error: {e}"

def change_brightness(value):
    try:
        value = int(value)

        if value < 0 or value > 100:
            return "Brightness must be between 0 and 100."

        sbc.set_brightness(value)

        return f"Brightness changed to {value}%"

    except Exception as e:
        return f"Brightness error: {e}"


def change_settings(item, value=None):
    item = item.lower()

    if value is None:
        subprocess.Popen("start ms-settings:", shell=True)
        return "Opening settings..."

    if item == "volume" or item == "vol":
        return change_volume(value)

    elif item == "brightness" or item == "light":
        return change_brightness(value)

    else:
        return "Unknown setting."