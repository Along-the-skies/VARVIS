"""
VARVIS :: Voice I/O
====================
speak(text)  -> synthesizes with edge-tts and plays it back.
listen()     -> captures mic audio and returns recognized text.

Playback strategy
------------------
edge-tts streams audio back in small chunks over the network. The original
approach waited for every chunk to arrive (i.e. the whole clip, fully
downloaded) before playing anything -- that's what caused the multi-second
delay between a reply appearing and the voice starting.

Here, chunks are piped straight into an external player's stdin (`mpv`,
falling back to `ffplay`) as they arrive, so playback starts as soon as the
first sliver of audio shows up instead of waiting for the whole thing.

If neither `mpv` nor `ffplay` is found on PATH, this falls back to the
original "download full clip, then play with pygame" behavior, so the app
still works -- it'll just have the old delay until one of those is
installed (e.g. `brew install mpv`, `winget install mpv`, `apt install mpv`).
"""

import asyncio
import os
import re
import shutil
import subprocess
import tempfile

import edge_tts
import speech_recognition as sr

VOICE = "en-GB-RyanNeural"

_MPV_PATH = shutil.which("mpv")
_FFPLAY_PATH = shutil.which("ffplay")

# Only pull in pygame's mixer if we actually need the fallback path.
if _MPV_PATH is None and _FFPLAY_PATH is None:
    import pygame

    pygame.mixer.init()


def clean_for_speech(text: str) -> str:
    text = re.sub(r"[.,!?;:]+", "", text)
    return text.strip()


def speak(text: str) -> None:
    text = clean_for_speech(text)
    if not text:
        return

    if _MPV_PATH or _FFPLAY_PATH:
        _SpeakStreaming(text)
    else:
        _SpeakBuffered(text)


def _SpeakStreaming(text: str) -> None:
    """Pipe edge-tts audio chunks into mpv/ffplay's stdin as they arrive."""
    playerCmd = (
        [_MPV_PATH, "--no-video", "--really-quiet", "-"]
        if _MPV_PATH
        else [_FFPLAY_PATH, "-nodisp", "-autoexit", "-loglevel", "quiet", "-"]
    )

    async def StreamToPlayer():
        process = subprocess.Popen(playerCmd, stdin=subprocess.PIPE)
        communicate = edge_tts.Communicate(text, VOICE)
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    process.stdin.write(chunk["data"])
                    process.stdin.flush()
        finally:
            if process.stdin:
                try:
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
            process.wait()

    asyncio.run(StreamToPlayer())


def _SpeakBuffered(text: str) -> None:
    """Original behavior: wait for the full clip, then play with pygame."""
    import pygame  # local import: only reached when the module-level pygame wasn't set up

    async def Generate():
        communicate = edge_tts.Communicate(text, VOICE)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as file:
            audioFile = file.name
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
        return audioFile

    audioFile = asyncio.run(Generate())

    try:
        pygame.mixer.music.load(audioFile)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(30)
    finally:
        pygame.mixer.music.unload()
        try:
            os.remove(audioFile)
        except PermissionError:
            pass


def listen() -> str:
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Calibrating...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        print("Listening...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

    try:
        text = recognizer.recognize_google(audio)
        print("Recognized:", text)
        return text

    except sr.UnknownValueError:
        print("Could not understand audio")
        return "I couldn't understand you."

    except sr.RequestError as e:
        print("Google API error:", e)
        return "Speech service unavailable."