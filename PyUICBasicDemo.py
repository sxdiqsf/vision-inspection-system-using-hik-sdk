# -*- coding: utf-8 -*-
# Rewritten — proper layouts, 75/25 split, clean object names.
# Styles are NOT set here — they are applied in apply_styles() called from
# the main script AFTER mainWindow.show(), which is the only reliable way
# to override Fusion on Windows.

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 660)
        MainWindow.setMinimumSize(800, 500)

        # ── Central widget ────────────────────────────────────────────────────
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")

        root_h = QtWidgets.QHBoxLayout(self.centralWidget)
        root_h.setContentsMargins(10, 10, 10, 10)
        root_h.setSpacing(10)

        # ══════════════════════════════════════════════════════════════════════
        # LEFT — combo + camera display (75 %)
        # ══════════════════════════════════════════════════════════════════════
        left_v = QtWidgets.QVBoxLayout()
        left_v.setSpacing(6)

        self.ComboDevices = QtWidgets.QComboBox()
        self.ComboDevices.setObjectName("ComboDevices")
        self.ComboDevices.setMinimumHeight(28)
        self.ComboDevices.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        left_v.addWidget(self.ComboDevices)

        self.widgetDisplay = QtWidgets.QWidget()
        self.widgetDisplay.setObjectName("widgetDisplay")
        self.widgetDisplay.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.widgetDisplay.setMinimumSize(400, 300)
        left_v.addWidget(self.widgetDisplay)

        root_h.addLayout(left_v, stretch=3)   # 75 %

        # ══════════════════════════════════════════════════════════════════════
        # RIGHT — controls + inspector (25 %)
        # ══════════════════════════════════════════════════════════════════════
        right_v = QtWidgets.QVBoxLayout()
        right_v.setSpacing(10)
        right_v.setContentsMargins(0, 0, 0, 0)

        # ── Group: Initialization ─────────────────────────────────────────────
        self.groupInit = QtWidgets.QGroupBox("INITIALIZATION")
        self.groupInit.setObjectName("groupInit")
        init_grid = QtWidgets.QGridLayout(self.groupInit)
        init_grid.setSpacing(6)
        init_grid.setContentsMargins(8, 16, 8, 8)

        self.bnEnum  = QtWidgets.QPushButton("Find Device")
        self.bnEnum.setObjectName("bnEnum")
        self.bnEnum.setMinimumHeight(32)
        init_grid.addWidget(self.bnEnum, 0, 0, 1, 2)

        self.bnOpen  = QtWidgets.QPushButton("Open Device")
        self.bnOpen.setObjectName("bnOpen")
        self.bnOpen.setMinimumHeight(32)
        init_grid.addWidget(self.bnOpen, 1, 0)

        self.bnClose = QtWidgets.QPushButton("Close Device")
        self.bnClose.setObjectName("bnClose")
        self.bnClose.setMinimumHeight(32)
        self.bnClose.setEnabled(False)
        init_grid.addWidget(self.bnClose, 1, 1)

        right_v.addWidget(self.groupInit)

        # ── Group: Acquisition ────────────────────────────────────────────────
        self.groupGrab = QtWidgets.QGroupBox("ACQUISITION")
        self.groupGrab.setObjectName("groupGrab")
        self.groupGrab.setEnabled(False)
        grab_grid = QtWidgets.QGridLayout(self.groupGrab)
        grab_grid.setSpacing(6)
        grab_grid.setContentsMargins(8, 16, 8, 8)

        self.radioContinueMode = QtWidgets.QRadioButton("Continuous")
        self.radioContinueMode.setObjectName("radioContinueMode")
        grab_grid.addWidget(self.radioContinueMode, 0, 0)

        self.radioTriggerMode = QtWidgets.QRadioButton("Trigger")
        self.radioTriggerMode.setObjectName("radioTriggerMode")
        grab_grid.addWidget(self.radioTriggerMode, 0, 1)

        self.bnStart = QtWidgets.QPushButton("Start")
        self.bnStart.setObjectName("bnStart")
        self.bnStart.setMinimumHeight(32)
        self.bnStart.setEnabled(False)
        grab_grid.addWidget(self.bnStart, 1, 0)

        self.bnStop  = QtWidgets.QPushButton("Stop")
        self.bnStop.setObjectName("bnStop")
        self.bnStop.setMinimumHeight(32)
        self.bnStop.setEnabled(False)
        grab_grid.addWidget(self.bnStop, 1, 1)

        self.bnSoftwareTrigger = QtWidgets.QPushButton("Trigger Once")
        self.bnSoftwareTrigger.setObjectName("bnSoftwareTrigger")
        self.bnSoftwareTrigger.setMinimumHeight(32)
        self.bnSoftwareTrigger.setEnabled(False)
        grab_grid.addWidget(self.bnSoftwareTrigger, 2, 0, 1, 2)

        self.bnSaveImage = QtWidgets.QPushButton("Save Image")
        self.bnSaveImage.setObjectName("bnSaveImage")
        self.bnSaveImage.setMinimumHeight(32)
        self.bnSaveImage.setEnabled(False)
        grab_grid.addWidget(self.bnSaveImage, 3, 0, 1, 2)

        right_v.addWidget(self.groupGrab)

        # ── GO/NO-GO overlay slot ─────────────────────────────────────────────
        self.gonogoSlot = QtWidgets.QWidget()
        self.gonogoSlot.setObjectName("gonogoSlot")
        self.gonogoSlot.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.gonogoSlotLayout = QtWidgets.QVBoxLayout(self.gonogoSlot)
        self.gonogoSlotLayout.setContentsMargins(0, 0, 0, 0)
        right_v.addWidget(self.gonogoSlot, stretch=1)

        right_container = QtWidgets.QWidget()
        right_container.setLayout(right_v)
        right_container.setMinimumWidth(220)
        root_h.addWidget(right_container, stretch=1)   # 25 %

        MainWindow.setCentralWidget(self.centralWidget)

        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Call this AFTER mainWindow.show() in the main script.
# Applying stylesheets post-show is the only reliable way to override
# Fusion's palette-based rendering on Windows.
# ─────────────────────────────────────────────────────────────────────────────

def apply_styles(ui):
    """
    Applies fonts, colors, and button styles to all controls.
    Must be called after mainWindow.show().
    """

    F_NORMAL = QtGui.QFont("Segoe UI", 9)
    F_BOLD   = QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold)
    F_BTN    = QtGui.QFont("Segoe UI", 9, QtGui.QFont.Medium)

    # ── Group boxes ──────────────────────────────────────────────────────────
    group_style = """
        QGroupBox {
            color: #eeeeee;
            border: 1px solid #555555;
            border-radius: 6px;
            margin-top: 12px;
            font-size: 9pt;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 6px;
            color: #ffffff;
        }
    """
    for grp in (ui.groupInit, ui.groupGrab):
        grp.setStyleSheet(group_style)
        grp.setFont(F_BOLD)

    # ── ComboBox ─────────────────────────────────────────────────────────────
    ui.ComboDevices.setFont(F_NORMAL)
    ui.ComboDevices.setStyleSheet("""
        QComboBox {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 9pt;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background-color: #2d2d2d;
            color: #e0e0e0;
            selection-background-color: #2979ff;
        }
    """)

    # ── Radio buttons ─────────────────────────────────────────────────────────
    radio_style = "QRadioButton { color: #cccccc; font-size: 9pt; }"
    ui.radioContinueMode.setStyleSheet(radio_style)
    ui.radioTriggerMode.setStyleSheet(radio_style)

    # ── Buttons — helper ─────────────────────────────────────────────────────
    def _style_btn(btn, bg_on, bg_off="#3a3a3a"):
        btn.setFont(F_BTN)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_on};
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {bg_on}cc;
            }}
            QPushButton:pressed {{
                background-color: {bg_on}99;
            }}
            QPushButton:disabled {{
                background-color: {bg_off};
                color: #777777;
            }}
        """)

    _style_btn(ui.bnEnum,            "#2979ff")   # blue   — find
    _style_btn(ui.bnOpen,            "#2e7d32")   # green  — open
    _style_btn(ui.bnClose,           "#c62828")   # red    — close
    _style_btn(ui.bnStart,           "#00695c")   # teal   — start
    _style_btn(ui.bnStop,            "#e65100")   # orange — stop
    _style_btn(ui.bnSoftwareTrigger, "#4a148c")   # purple — trigger
    _style_btn(ui.bnSaveImage,       "#37474f")   # slate  — save

    # ── widgetDisplay border ──────────────────────────────────────────────────
    ui.widgetDisplay.setStyleSheet(
        "background-color: #000000; border: 1px solid #444444; border-radius: 4px;")

    # ── Status bar ────────────────────────────────────────────────────────────
    ui.statusBar.setFont(F_NORMAL)
    ui.statusBar.setStyleSheet("background-color: #181818; color: #888888;")