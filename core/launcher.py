# core/launcher.py
# Splash/launcher screen shown before the main VARVIS GUI.
# Left  -> logo
# Right -> live log console (init messages get printed here instead of stdout)

import os
import sys

from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer, QElapsedTimer
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTextEdit, QProgressBar,
)

from core.logger import Logger
from core.config import has_api_key, setup_api_key



def ResourcePath(*parts):
    """
    Resolves a path to a bundled resource (like assets/) so it works both:
    - when running as a normal .py script (dev), and
    - when running as a PyInstaller-built .exe (frozen).

    PyInstaller sets sys.frozen=True and sys._MEIPASS to the folder that
    holds the bundled files — that's true for both --onedir and --onefile
    builds, so this one helper covers both.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


LOGO_PATH = ResourcePath("assets", "varvis_logo.png")


class LoadWorker(QObject):
    """
    Runs the actual startup work (LoadApps / ScanForApps) on a background
    thread so the launcher window doesn't freeze while it scans.

    Signals are how a worker thread safely talks back to the GUI thread —
    you never touch a QWidget directly from another thread.
    """
    logMessage = Signal(str)
    finished = Signal()

    def run(self):
        from modules.apps import LoadApps, ScanForApps

        self.logMessage.emit("Initialising....")
        Logger.info("VARVIS starting")

        # =========================
        # API Setup
        # =========================

        if not has_api_key():

            self.logMessage.emit(
                "Connecting to VARVIS services..."
            )

            if setup_api_key():

                self.logMessage.emit(
                    "AI configuration ready."
                )

            else:

                self.logMessage.emit(
                    "AI configuration failed."
                )

                self.finished.emit()
                return

        else:

            self.logMessage.emit(
                "AI configuration loaded."
            )

        # =========================
        # Application Loading
        # =========================

        Apps = LoadApps()

        if not Apps:

            self.logMessage.emit(
                "Scanning for installed applications..."
            )

            ScanForApps()

        else:

            self.logMessage.emit(
                "Loaded applications from database."
            )

        self.logMessage.emit("Hello, Vasudev!")

        Logger.info("Startup sequence complete")

        self.finished.emit()


class LauncherWindow(QWidget):
    """
    Splash window: logo on the left, log console on the right.
    Auto-closes and hands off to `onFinished` once loading completes.
    """

    # Launcher stays visible at least this long, even if loading finishes
    # faster (e.g. app list already cached). Stops the splash from just
    # flashing on screen and disappearing before it's readable.
    MIN_DISPLAY_MS = 4000

    def __init__(self, onFinished, parent=None):
        super().__init__(parent)
        self.onFinished = onFinished
        self._thread = None
        self._worker = None
        self._elapsed = QElapsedTimer()

        self.setWindowTitle("VARVIS — Cognitive Interface")
        self.setFixedSize(720, 420)
        self.setStyleSheet("""
            QWidget {
                background-color: #05070a;
                color: #d6e4ef;
            }
            QTextEdit {
                background-color: #0b0f14;
                color: #7fe7ff;
                border: 1px solid #14202b;
                border-radius: 6px;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
            }
            QProgressBar {
                background-color: #0b0f14;
                border: 1px solid #14202b;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: #22d3ee;
                border-radius: 4px;
            }
        """)

        self._buildUi()

    def _buildUi(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # ---- Left: logo ----
        logoLabel = QLabel()
        pixmap = QPixmap(LOGO_PATH)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                260, 260,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logoLabel.setPixmap(pixmap)
        else:
            logoLabel.setText("VARVIS")
            logoLabel.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        logoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logoLabel.setFixedWidth(280)
        root.addWidget(logoLabel)

        # ---- Right: title + log console + progress ----
        rightCol = QVBoxLayout()
        rightCol.setSpacing(10)

        title = QLabel("VARVIS")
        title.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #e6f7ff;")

        subtitle = QLabel("COGNITIVE INTERFACE")
        subtitle.setFont(QFont("Consolas", 9))
        subtitle.setStyleSheet("color: #22d3ee; letter-spacing: 2px;")

        self.logConsole = QTextEdit()
        self.logConsole.setReadOnly(True)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 0)  # indeterminate — we don't know step count in advance

        rightCol.addWidget(title)
        rightCol.addWidget(subtitle)
        rightCol.addWidget(self.logConsole, stretch=1)
        rightCol.addWidget(self.progressBar)

        root.addLayout(rightCol, stretch=1)

    def Log(self, message: str):
        self.logConsole.append(message)

    def StartLoading(self):
        """Kick off the background worker and wire up its signals."""
        self._elapsed.start()

        self._thread = QThread(self)
        self._worker = LoadWorker()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.logMessage.connect(self.Log)
        self._worker.finished.connect(self._onWorkerFinished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _onWorkerFinished(self):
        """
        Worker's done - but if that happened faster than MIN_DISPLAY_MS,
        wait out the remainder before actually closing, so the launcher
        doesn't just flash and vanish on a fast (cached) load.
        """
        remaining = self.MIN_DISPLAY_MS - self._elapsed.elapsed()
        if remaining > 0:
            QTimer.singleShot(remaining, self._onLoadFinished)
        else:
            self._onLoadFinished()

    def _onLoadFinished(self):
        self.progressBar.setRange(0, 1)
        self.progressBar.setValue(1)
        self.close()

        # Keep a reference to whatever LaunchApp() returns (the main window).
        # Without this, the window object falls out of scope and gets
        # garbage-collected the instant this method returns - which is why
        # the app appeared to "close immediately."
        self.mainWindow = self.onFinished()