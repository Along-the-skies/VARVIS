"""
VARVIS :: Desktop GUI
======================
A futuristic, dark-themed desktop interface for the VARVIS AI assistant,
styled as a chat-app conversation: your messages align right, VARVIS's
replies align left, system notices are centered.

This module is PRESENTATION ONLY. It contains zero assistant logic.
Every user command is forwarded to `core.brain.process_command(text)`,
which is expected to return a plain string (the assistant's reply).

Voice input/output is handled by `core.voice` (listen(), speak()) and
is wired here through the same off-thread worker pattern used for the
brain, so neither listening nor speaking ever freezes the UI.

If `core.brain` isn't importable yet, a stub is used automatically so the
window still runs and echoes commands back.

Run directly:
    python -m core.gui
"""

from __future__ import annotations

import sys
import threading
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QFont, QColor, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QScrollArea,
    QGraphicsDropShadowEffect,
)
from core.voice import speak, listen


# --------------------------------------------------------------------------- #
# Brain hookup (falls back to a stub so the GUI is previewable on its own)
# --------------------------------------------------------------------------- #
try:
    from core.brain import process_command as ProcessCommand
except Exception:  # pragma: no cover - only hit when core.brain isn't wired yet
    def ProcessCommand(text: str) -> str:
        return (
            "[stub] core.brain.process_command() not found yet — "
            f"echoing input: \u201c{text}\u201d"
        )


# --------------------------------------------------------------------------- #
# Palette / Theme constants
# --------------------------------------------------------------------------- #
class VarvisTheme:
    BgVoid = "#05070A"
    BgPanel = "#0B0E14"
    BgPanelAlt = "#0F131B"
    BgInput = "#11151D"
    BorderSoft = "#1C2330"
    BorderAccent = "#2A3B4D"

    AccentCyan = "#4CF3FF"
    AccentCyanDim = "#1E8A95"
    AccentBlue = "#3E7BFA"
    AccentPurple = "#8B5CF6"
    AccentGreen = "#39FF9E"
    AccentAmber = "#FFB454"
    AccentRed = "#FF5C6C"

    UserBubble = "#2A4FCB"
    UserBubbleText = "#EAF1FF"
    AssistantBubble = "#131826"
    AssistantBubbleText = "#E7EEF5"

    TextPrimary = "#E7EEF5"
    TextSecondary = "#8792A3"
    TextMuted = "#4C5568"

    FontFamily = "Segoe UI, Consolas, 'Roboto', 'Helvetica Neue', sans-serif"
    MonoFamily = "Consolas, 'Cascadia Code', 'Courier New', monospace"


# --------------------------------------------------------------------------- #
# Workers: run blocking calls off the UI thread so the GUI never freezes
# --------------------------------------------------------------------------- #
class BrainWorker(QObject):
    """Runs core.brain.process_command() on a background thread."""

    ResultReady = Signal(str)
    ErrorRaised = Signal(str)

    def __init__(self, commandText: str):
        super().__init__()
        self.commandText = commandText

    def Run(self):
        try:
            reply = ProcessCommand(self.commandText)
            if reply is None or str(reply).strip() == "":
                reply = "Command executed."
            self.ResultReady.emit(str(reply))
        except Exception as exc:  # noqa: BLE001
            self.ErrorRaised.emit(f"{type(exc).__name__}: {exc}")


class VoiceWorker(QObject):
    """Runs core.voice.listen() on a background thread (mic capture blocks)."""

    TextReady = Signal(str)
    ErrorRaised = Signal(str)

    def Run(self):
        try:
            text = listen()
            if text == "I couldn't understand you.":
                self.ErrorRaised.emit(text)
            else:
                self.TextReady.emit(text)
        except Exception as exc:  # noqa: BLE001
            self.ErrorRaised.emit(f"{type(exc).__name__}: {exc}")


class SpeakWorker(QObject):
    """
    Runs core.voice.speak() on a background thread.

    speak() is a blocking call (it streams TTS audio and plays it), so it
    must never run on the Qt/UI thread. Anything this worker needs to touch
    on the UI afterward goes through the Finished signal instead of being
    called directly from Run() -- Run() executes on this worker's own
    thread, and Qt widgets are not safe to touch from any thread but the
    main one.
    """

    Finished = Signal()

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def Run(self):
        try:
            speak(self.text)
        except Exception as exc:  # noqa: BLE001
            print(f"TTS error: {type(exc).__name__}: {exc}")
        finally:
            self.Finished.emit()


# --------------------------------------------------------------------------- #
# Small reusable widgets
# --------------------------------------------------------------------------- #
class StatusPill(QFrame):
    """A small status indicator: dot + label, e.g. 'ONLINE'."""

    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusPill")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 14, 6)
        layout.setSpacing(8)

        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.textLabel = QLabel(label.upper())
        self.textLabel.setStyleSheet(
            f"color: {VarvisTheme.TextSecondary}; font-size: 11px; letter-spacing: 1px;"
        )
        self.textLabel.setFont(QFont(VarvisTheme.FontFamily, 9, QFont.DemiBold))

        layout.addWidget(self.dot)
        layout.addWidget(self.textLabel)
        self.setStyleSheet(
            f"""
            #StatusPill {{
                background-color: {VarvisTheme.BgPanelAlt};
                border: 1px solid {VarvisTheme.BorderSoft};
                border-radius: 13px;
            }}
            """
        )

    def SetActive(self, active: bool, activeColor: str = None):
        color = activeColor or VarvisTheme.AccentGreen
        self.dot.setStyleSheet(
            f"color: {color if active else VarvisTheme.TextMuted}; font-size: 11px;"
        )


class MetricRow(QFrame):
    """label ........ value, used in the sidebar telemetry panel."""

    def __init__(self, label: str, value: str, valueColor: str = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        labelWidget = QLabel(label.upper())
        labelWidget.setStyleSheet(
            f"color: {VarvisTheme.TextMuted}; font-size: 10px; letter-spacing: 1px;"
        )
        labelWidget.setFont(QFont(VarvisTheme.FontFamily, 8, QFont.DemiBold))

        self.valueWidget = QLabel(value)
        self.valueWidget.setAlignment(Qt.AlignRight)
        self.valueWidget.setStyleSheet(
            f"color: {valueColor or VarvisTheme.TextPrimary}; font-size: 11px;"
        )
        self.valueWidget.setFont(QFont(VarvisTheme.MonoFamily, 10))

        layout.addWidget(labelWidget)
        layout.addStretch()
        layout.addWidget(self.valueWidget)

    def SetValue(self, value: str):
        self.valueWidget.setText(value)


# --------------------------------------------------------------------------- #
# Chat bubbles
# --------------------------------------------------------------------------- #
class MessageBubble(QFrame):
    """A single chat bubble. sender is 'user', 'assistant', 'system', or 'error'."""

    def __init__(self, text: str, sender: str = "assistant", parent=None):
        super().__init__(parent)
        self.setObjectName("MessageBubble")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 9, 14, 8)
        layout.setSpacing(3)

        messageLabel = QLabel(text)
        messageLabel.setWordWrap(True)
        messageLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        messageLabel.setFont(QFont(VarvisTheme.FontFamily, 11))
        layout.addWidget(messageLabel)

        timeLabel = QLabel(datetime.now().strftime("%H:%M:%S"))
        timeLabel.setFont(QFont(VarvisTheme.MonoFamily, 8))
        layout.addWidget(timeLabel)

        self.setMaximumWidth(460)

        if sender == "user":
            bg, radius = VarvisTheme.UserBubble, "16px 16px 4px 16px"
            textColor = VarvisTheme.UserBubbleText
            timeColor, timeAlign = "#C3D3FF", Qt.AlignRight
            border = "none"
        elif sender == "assistant":
            bg, radius = VarvisTheme.AssistantBubble, "16px 16px 16px 4px"
            textColor = VarvisTheme.AssistantBubbleText
            timeColor, timeAlign = VarvisTheme.AccentCyanDim, Qt.AlignLeft
            border = f"1px solid {VarvisTheme.BorderAccent}"
        elif sender == "error":
            bg, radius = "#22131A", "16px 16px 16px 4px"
            textColor = VarvisTheme.AccentRed
            timeColor, timeAlign = VarvisTheme.AccentRed, Qt.AlignLeft
            border = f"1px solid {VarvisTheme.AccentRed}"
        else:  # system
            bg, radius = "transparent", "10px"
            textColor = VarvisTheme.TextMuted
            timeColor, timeAlign = VarvisTheme.TextMuted, Qt.AlignCenter
            border = "none"
            messageLabel.setAlignment(Qt.AlignCenter)
            timeLabel.hide()

        timeLabel.setAlignment(timeAlign)
        messageLabel.setStyleSheet(f"color: {textColor}; background: transparent; border: none;")
        timeLabel.setStyleSheet(f"color: {timeColor}; background: transparent; border: none;")

        self.setStyleSheet(
            f"""
            #MessageBubble {{
                background-color: {bg};
                border-radius: {radius if sender != 'system' else '0px'};
                border: {border};
            }}
            """
        )


class TypingBubble(MessageBubble):
    """A transient 'VARVIS is thinking…' indicator shown while the brain runs."""

    def __init__(self, parent=None):
        super().__init__("VARVIS is thinking…", sender="assistant", parent=parent)
        self.setStyleSheet(
            self.styleSheet().replace(
                VarvisTheme.AssistantBubble, VarvisTheme.AssistantBubble
            )
        )


class MessageRow(QWidget):
    """Wraps a bubble in a row that aligns it left, right, or center."""

    def __init__(self, bubble: MessageBubble, sender: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)

        if sender == "user":
            layout.addStretch(1)
            layout.addWidget(bubble)
        elif sender == "system":
            layout.addStretch(1)
            layout.addWidget(bubble)
            layout.addStretch(1)
        else:  # assistant / error
            layout.addWidget(bubble)
            layout.addStretch(1)


# --------------------------------------------------------------------------- #
# Chat scroll area (holds all message rows, anchored to the bottom)
# --------------------------------------------------------------------------- #
class ChatLog(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatLog")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(2)
        self._layout.addStretch(1)  # keeps messages pinned to the bottom
        self.setWidget(self._container)

        self._typingRow: MessageRow | None = None

        self.setStyleSheet(
            f"""
            #ChatLog {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 4px 0px 4px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {VarvisTheme.BorderAccent};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {VarvisTheme.AccentCyanDim};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

        self.AppendSystemLine("VARVIS online. Awaiting your command.")

    def _AddRow(self, text: str, sender: str) -> MessageRow:
        bubble = MessageBubble(text, sender=sender)
        row = MessageRow(bubble, sender=sender)
        # insert just before the trailing stretch (always the last item)
        self._layout.insertWidget(self._layout.count() - 1, row)
        self._ScrollToBottom()
        return row

    def AppendUserMessage(self, text: str):
        self._AddRow(text, "user")

    def AppendAssistantMessage(self, text: str):
        self._AddRow(text, "assistant")

    def AppendErrorLine(self, text: str):
        self._AddRow(text, "error")

    def AppendSystemLine(self, text: str):
        self._AddRow(text.upper(), "system")

    def ShowTyping(self):
        if self._typingRow is not None:
            return
        bubble = TypingBubble()
        self._typingRow = MessageRow(bubble, "assistant")
        self._layout.insertWidget(self._layout.count() - 1, self._typingRow)
        self._ScrollToBottom()

    def HideTyping(self):
        if self._typingRow is None:
            return
        self._typingRow.setParent(None)
        self._typingRow.deleteLater()
        self._typingRow = None

    def _ScrollToBottom(self):
        QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        ))


# --------------------------------------------------------------------------- #
# Sidebar (identity + telemetry)
# --------------------------------------------------------------------------- #
class SidePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidePanel")
        self.setFixedWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 20)
        layout.setSpacing(18)

        brandRow = QHBoxLayout()
        brandRow.setSpacing(10)
        core = QLabel("◉")
        core.setStyleSheet(f"color: {VarvisTheme.AccentCyan}; font-size: 22px;")
        titleBlock = QVBoxLayout()
        titleBlock.setSpacing(0)
        title = QLabel("VARVIS")
        title.setFont(QFont(VarvisTheme.FontFamily, 17, QFont.Black))
        title.setStyleSheet(f"color: {VarvisTheme.TextPrimary}; letter-spacing: 3px;")
        subtitle = QLabel("COGNITIVE INTERFACE")
        subtitle.setFont(QFont(VarvisTheme.FontFamily, 8, QFont.DemiBold))
        subtitle.setStyleSheet(f"color: {VarvisTheme.TextMuted}; letter-spacing: 2px;")
        titleBlock.addWidget(title)
        titleBlock.addWidget(subtitle)
        brandRow.addWidget(core)
        brandRow.addLayout(titleBlock)
        brandRow.addStretch()
        layout.addLayout(brandRow)

        layout.addWidget(self._Divider())

        statusLabel = QLabel("SYSTEM STATUS")
        statusLabel.setFont(QFont(VarvisTheme.FontFamily, 9, QFont.DemiBold))
        statusLabel.setStyleSheet(f"color: {VarvisTheme.TextMuted}; letter-spacing: 2px;")
        layout.addWidget(statusLabel)

        self.corePill = StatusPill("Core: Online", VarvisTheme.AccentGreen)
        self.brainPill = StatusPill("Brain: Ready", VarvisTheme.AccentCyan)
        self.linkPill = StatusPill("Link: Secure", VarvisTheme.AccentPurple)
        layout.addWidget(self.corePill)
        layout.addWidget(self.brainPill)
        layout.addWidget(self.linkPill)

        layout.addWidget(self._Divider())

        telemetryLabel = QLabel("SESSION TELEMETRY")
        telemetryLabel.setFont(QFont(VarvisTheme.FontFamily, 9, QFont.DemiBold))
        telemetryLabel.setStyleSheet(f"color: {VarvisTheme.TextMuted}; letter-spacing: 2px;")
        layout.addWidget(telemetryLabel)

        self.commandsRow = MetricRow("Commands Sent", "0")
        self.uptimeRow = MetricRow("Uptime", "00:00:00")
        self.lastLatencyRow = MetricRow("Last Latency", "—", VarvisTheme.AccentCyan)
        layout.addWidget(self.commandsRow)
        layout.addWidget(self.uptimeRow)
        layout.addWidget(self.lastLatencyRow)

        layout.addStretch()

        footer = QLabel("VARVIS BUILD 1.0.0")
        footer.setStyleSheet(f"color: {VarvisTheme.TextMuted}; font-size: 9px; letter-spacing: 1px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        self.setStyleSheet(
            f"""
            #SidePanel {{
                background-color: {VarvisTheme.BgPanel};
                border-right: 1px solid {VarvisTheme.BorderSoft};
            }}
            """
        )

    def _Divider(self) -> QFrame:
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {VarvisTheme.BorderSoft}; border: none;")
        return line


# --------------------------------------------------------------------------- #
# Top bar
# --------------------------------------------------------------------------- #
class TopBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)

        heading = QLabel("MAIN CONSOLE")
        heading.setFont(QFont(VarvisTheme.FontFamily, 11, QFont.DemiBold))
        heading.setStyleSheet(f"color: {VarvisTheme.TextSecondary}; letter-spacing: 2px;")

        self.clockLabel = QLabel()
        self.clockLabel.setFont(QFont(VarvisTheme.MonoFamily, 11))
        self.clockLabel.setStyleSheet(f"color: {VarvisTheme.AccentCyan};")

        timer = QTimer(self)
        timer.timeout.connect(self._UpdateClock)
        timer.start(1000)
        self._UpdateClock()

        layout.addWidget(heading)
        layout.addStretch()
        layout.addWidget(self.clockLabel)

        self.setStyleSheet(
            f"""
            #TopBar {{
                background-color: {VarvisTheme.BgPanel};
                border-bottom: 1px solid {VarvisTheme.BorderSoft};
            }}
            """
        )

    def _UpdateClock(self):
        self.clockLabel.setText(datetime.now().strftime("%A · %d %b %Y · %H:%M:%S"))


# --------------------------------------------------------------------------- #
# Command input row
# --------------------------------------------------------------------------- #
class CommandBar(QFrame):
    CommandSubmitted = Signal(str)
    VoiceRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CommandBar")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 18)
        outer.setSpacing(8)

        self.hintLabel = QLabel("Try: \u201copen notepad\u201d  ·  \u201cclose chrome\u201d")
        self.hintLabel.setStyleSheet(f"color: {VarvisTheme.TextMuted}; font-size: 10px;")
        outer.addWidget(self.hintLabel)

        row = QHBoxLayout()
        row.setSpacing(12)

        promptGlyph = QLabel("❯")
        promptGlyph.setStyleSheet(f"color: {VarvisTheme.AccentCyan}; font-size: 16px;")

        self.inputField = QLineEdit()
        self.inputField.setPlaceholderText("Enter command for VARVIS…")
        self.inputField.setFont(QFont(VarvisTheme.FontFamily, 12))
        self.inputField.setFixedHeight(44)
        self.inputField.returnPressed.connect(self._EmitSubmit)
        self.inputField.setObjectName("CommandInput")

        self.micButton = QPushButton("🎤")
        self.micButton.setFixedSize(44, 44)
        self.micButton.setCursor(Qt.PointingHandCursor)
        self.micButton.setObjectName("MicButton")
        self.micButton.clicked.connect(lambda: self.VoiceRequested.emit())

        self.sendButton = QPushButton("SEND")
        self.sendButton.setFixedSize(96, 44)
        self.sendButton.setCursor(Qt.PointingHandCursor)
        self.sendButton.setObjectName("SendButton")
        self.sendButton.clicked.connect(self._EmitSubmit)

        row.addWidget(promptGlyph)
        row.addWidget(self.inputField)
        row.addWidget(self.micButton)
        row.addWidget(self.sendButton)
        outer.addLayout(row)

        self.setStyleSheet(
            f"""
            #CommandBar {{
                background-color: {VarvisTheme.BgPanel};
                border-top: 1px solid {VarvisTheme.BorderSoft};
            }}
            #CommandInput {{
                background-color: {VarvisTheme.BgInput};
                border: 1px solid {VarvisTheme.BorderSoft};
                border-radius: 8px;
                padding: 0px 14px;
                color: {VarvisTheme.TextPrimary};
                selection-background-color: {VarvisTheme.AccentCyanDim};
            }}
            #CommandInput:focus {{
                border: 1px solid {VarvisTheme.AccentCyan};
            }}
            #MicButton {{
                background-color: {VarvisTheme.BgInput};
                border: 1px solid {VarvisTheme.BorderSoft};
                border-radius: 8px;
                font-size: 16px;
            }}
            #MicButton:hover {{
                border: 1px solid {VarvisTheme.AccentCyan};
            }}
            #MicButton:disabled {{
                background-color: {VarvisTheme.BorderSoft};
                color: {VarvisTheme.TextMuted};
            }}
            #SendButton {{
                background-color: {VarvisTheme.AccentCyanDim};
                color: {VarvisTheme.BgVoid};
                border: none;
                border-radius: 8px;
                font-weight: 700;
                letter-spacing: 1px;
                font-size: 11px;
            }}
            #SendButton:hover {{
                background-color: {VarvisTheme.AccentCyan};
            }}
            #SendButton:pressed {{
                background-color: {VarvisTheme.AccentCyanDim};
            }}
            #SendButton:disabled {{
                background-color: {VarvisTheme.BorderSoft};
                color: {VarvisTheme.TextMuted};
            }}
            """
        )

    def _EmitSubmit(self):
        text = self.inputField.text().strip()
        if not text:
            return
        self.CommandSubmitted.emit(text)
        self.inputField.clear()

    def SetBusy(self, busy: bool):
        self.sendButton.setEnabled(not busy)
        self.inputField.setEnabled(not busy)
        self.micButton.setEnabled(not busy)
        self.sendButton.setText("…" if busy else "SEND")


# --------------------------------------------------------------------------- #
# Main window
# --------------------------------------------------------------------------- #
class VarvisMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VARVIS — Cognitive Interface")
        self.resize(1180, 740)
        self.setMinimumSize(900, 600)

        self._commandCount = 0
        self._startTime = datetime.now()
        # Tracks every background QThread currently in flight (brain calls,
        # voice listening, speech playback). A list rather than a single
        # slot because these can be started back-to-back (brain -> speak,
        # or voice -> brain -> speak) before the previous thread's
        # `finished` signal has fired and cleaned itself up -- a single
        # slot would get silently overwritten in that window, which would
        # make closeEvent's "wait for it to finish" check miss a thread
        # that's still running.
        self._activeThreads: list[QThread] = []
        self._dispatchStart = datetime.now()

        self._BuildUi()
        self._ApplyGlobalStyle()

        self._uptimeTimer = QTimer(self)
        self._uptimeTimer.timeout.connect(self._UpdateUptime)
        self._uptimeTimer.start(1000)

    def _BuildUi(self):
        central = QWidget()
        self.setCentralWidget(central)
        rootLayout = QHBoxLayout(central)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        self.sidePanel = SidePanel()
        rootLayout.addWidget(self.sidePanel)

        rightColumn = QVBoxLayout()
        rightColumn.setContentsMargins(0, 0, 0, 0)
        rightColumn.setSpacing(0)

        self.topBar = TopBar()
        rightColumn.addWidget(self.topBar)

        chatContainer = QFrame()
        chatContainer.setObjectName("ChatContainer")
        chatLayout = QVBoxLayout(chatContainer)
        chatLayout.setContentsMargins(0, 0, 0, 0)

        self.chatLog = ChatLog()
        chatLayout.addWidget(self.chatLog)
        rightColumn.addWidget(chatContainer, stretch=1)

        self.commandBar = CommandBar()
        self.commandBar.CommandSubmitted.connect(self._HandleCommandSubmitted)
        self.commandBar.VoiceRequested.connect(self._HandleVoiceRequested)
        rightColumn.addWidget(self.commandBar)

        rightWidget = QWidget()
        rightWidget.setLayout(rightColumn)
        rootLayout.addWidget(rightWidget, stretch=1)

    def _ApplyGlobalStyle(self):
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {VarvisTheme.BgVoid};
            }}
            #ChatContainer {{
                background-color: {VarvisTheme.BgVoid};
            }}
            QToolTip {{
                background-color: {VarvisTheme.BgPanelAlt};
                color: {VarvisTheme.TextPrimary};
                border: 1px solid {VarvisTheme.BorderAccent};
                padding: 4px 8px;
            }}
            """
        )

    # --- Thread bookkeeping ------------------------------------------------ #
    def _StartThread(self, thread: QThread, worker: QObject):
        """
        Starts `thread` and keeps both it and `worker` alive for as long as
        the thread is running. Attaching `worker` directly to the thread
        object (rather than only to a local variable) means it can't be
        garbage-collected out from under a signal connection mid-run.
        """
        thread._worker = worker  # keep worker alive alongside its thread
        self._activeThreads.append(thread)
        thread.finished.connect(self._CleanupThread)
        thread.start()

    def _CleanupThread(self):
        thread = self.sender()
        if thread in self._activeThreads:
            self._activeThreads.remove(thread)
        if thread:
            thread.deleteLater()

    # --- Text command path ------------------------------------------------ #
    def _HandleCommandSubmitted(self, text: str):
        self.chatLog.AppendUserMessage(text)
        self.chatLog.ShowTyping()
        self.commandBar.SetBusy(True)
        self.sidePanel.brainPill.SetActive(True, VarvisTheme.AccentAmber)

        self._dispatchStart = datetime.now()

        thread = QThread(self)
        worker = BrainWorker(text)
        worker.moveToThread(thread)

        thread.started.connect(worker.Run)
        worker.ResultReady.connect(self._HandleBrainResult)
        worker.ErrorRaised.connect(self._HandleBrainError)
        worker.ResultReady.connect(thread.quit)
        worker.ErrorRaised.connect(thread.quit)

        self._StartThread(thread, worker)

    def _HandleBrainResult(self, reply: str):
        self.chatLog.HideTyping()
        self.chatLog.AppendAssistantMessage(reply)

        # Speak the reply on its own background thread. speak() is a
        # blocking network + playback call, so it can't run on the UI
        # thread -- and _FinishDispatch() touches Qt widgets, so it can't
        # run on speak()'s thread either. SpeakWorker.Finished is a Qt
        # signal, so connecting it to _FinishDispatch below automatically
        # marshals that call back onto the UI thread.
        thread = QThread(self)
        worker = SpeakWorker(reply)
        worker.moveToThread(thread)

        thread.started.connect(worker.Run)
        worker.Finished.connect(self._FinishDispatch)
        worker.Finished.connect(thread.quit)

        self._StartThread(thread, worker)

    def _HandleBrainError(self, message: str):
        self.chatLog.HideTyping()
        self.chatLog.AppendErrorLine(message)
        self._FinishDispatch()

    def _FinishDispatch(self):
        elapsedMs = int((datetime.now() - self._dispatchStart).total_seconds() * 1000)
        self._commandCount += 1
        self.sidePanel.commandsRow.SetValue(str(self._commandCount))
        self.sidePanel.lastLatencyRow.SetValue(f"{elapsedMs} ms")
        self.sidePanel.brainPill.SetActive(True, VarvisTheme.AccentCyan)
        self.commandBar.SetBusy(False)

    # --- Voice command path ------------------------------------------------ #
    def _HandleVoiceRequested(self):
        self.chatLog.AppendSystemLine("Listening…")
        self.commandBar.SetBusy(True)

        thread = QThread(self)
        worker = VoiceWorker()
        worker.moveToThread(thread)

        thread.started.connect(worker.Run)
        worker.TextReady.connect(self._HandleVoiceResult)
        worker.ErrorRaised.connect(self._HandleVoiceError)
        worker.TextReady.connect(thread.quit)
        worker.ErrorRaised.connect(thread.quit)

        self._StartThread(thread, worker)

    def _HandleVoiceResult(self, text: str):
        # Hand off to the exact same path text-input commands use.
        self._HandleCommandSubmitted(text)

    def _HandleVoiceError(self, message: str):
        self.commandBar.SetBusy(False)
        self.chatLog.AppendErrorLine(message)

    # --- Shutdown ------------------------------------------------ #
    def closeEvent(self, event):
        # Don't let the window close while a background thread is mid-flight;
        # this is what causes "QThread: Destroyed while thread is still running".
        for thread in list(self._activeThreads):
            if thread.isRunning():
                thread.quit()
                thread.wait(2000)
        super().closeEvent(event)

    def _UpdateUptime(self):
        elapsed = datetime.now() - self._startTime
        totalSeconds = int(elapsed.total_seconds())
        hours, remainder = divmod(totalSeconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.sidePanel.uptimeRow.SetValue(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def LaunchApp():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    window = VarvisMainWindow()
    window.show()

    # Fires once the event loop is up. Runs off the UI thread since speak()
    # blocks for the duration of playback. This replaced a
    # speak("Good Evening Sir") call that sat after sys.exit(app.exec())
    # below, which meant it could never actually run -- sys.exit() raises
    # SystemExit immediately, so nothing after it executes.
    QTimer.singleShot(
        300,
        lambda: threading.Thread(
            target=speak, args=("Good Evening Sir",), daemon=True
        ).start(),
    )

    return window



if __name__ == "__main__":
    LaunchApp()