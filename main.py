# Main VARVIS Controller / Launcher entry point

import sys
from PySide6.QtWidgets import QApplication

from core.launcher import LauncherWindow
from core.gui import LaunchApp


def StartJarvis():
    # One QApplication for the whole process - the launcher and the main
    # GUI both live inside this single event loop.
    app = QApplication(sys.argv)

    launcher = LauncherWindow(onFinished=LaunchApp)
    launcher.show()
    launcher.StartLoading()

    sys.exit(app.exec())


if __name__ == "__main__":
    StartJarvis()