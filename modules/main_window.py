"""``Ui_MainWindow`` - composes the per-tab mixins into a single window class.

The mixins share one runtime object and the module-level state in
``modules.app_state`` / ``modules.config`` / ``modules.themes``.
"""

from PyQt6 import QtCore, QtWidgets

from modules import app_state
from modules import themes
from modules.config import APP_CONFIG
from modules.table_state import PersistentUI
from modules.actions_tab import ActionsMixin
from modules.command_builder_tab import CommandBuilderMixin
from modules.folders_tab import FoldersMixin
from modules.fragments_tab import FragmentsMixin
from modules.profiles_tab import ProfilesMixin
from modules.settings_tab import SettingsMixin

VERSION = "1.1.0"


class Ui_MainWindow(ProfilesMixin, FoldersMixin, ActionsMixin,
                    CommandBuilderMixin, SettingsMixin, FragmentsMixin, object):
    """Main window: builds all six tabs and owns the shared status bar / Save."""

    def __init__(self):
        self.unsaved_changes = False
        self.ui_initialized = False

    def setupUi(self, MainWindow):
        self._main_window = MainWindow
        self._persist = PersistentUI(MainWindow)

        MainWindow.setObjectName("Windows Terminal Settings")
        cfg_win = APP_CONFIG.get("window", {})
        MainWindow.resize(cfg_win.get("width", 1400), cfg_win.get("height", 900))
        MainWindow.setWindowTitle(f"Windows Terminal Manager  v{VERSION}")
        MainWindow.setMinimumSize(cfg_win.get("min_width", 1200), cfg_win.get("min_height", 700))

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.tabWidget = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabWidget)

        self.profilesTab = QtWidgets.QWidget()
        self.foldersTab = QtWidgets.QWidget()
        self.actionsTab = QtWidgets.QWidget()
        self.commandBuilderTab = QtWidgets.QWidget()
        self.settingsTab = QtWidgets.QWidget()
        self.fragmentsTab = QtWidgets.QWidget()

        self.tabWidget.addTab(self.profilesTab, "  Profiles")
        self.tabWidget.addTab(self.foldersTab, "  Folders && New Tab Menu")
        self.tabWidget.addTab(self.actionsTab, "  Actions && Key Bindings")
        self.tabWidget.addTab(self.commandBuilderTab, "  WT Command Builder")
        self.tabWidget.addTab(self.settingsTab, "  Settings")
        self.tabWidget.addTab(self.fragmentsTab, "  Fragment Extensions")

        for i, tip in enumerate((
                "Manage terminal profiles",
                "Organize the new tab dropdown menu",
                "Configure keyboard shortcuts and actions",
                "Build complex wt.exe commands",
                "Application and Windows Terminal global settings",
                "Create and manage JSON fragment extension files")):
            self.tabWidget.setTabToolTip(i, tip)

        self.setupProfilesTab()
        self.setupActionsTab()
        self.setupCommandBuilderTab()
        self.setupFoldersTab()
        self.setupSettingsTab()
        self.setupFragmentsTab()

        bottom_layout = QtWidgets.QHBoxLayout()
        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.statusLabel)
        main_layout.addLayout(bottom_layout)

        # Restore window geometry last, once every child widget exists. The
        # per-tab widgets (tables, trees, splitters) register themselves with
        # self._persist from inside their own setup*Tab methods.
        self._persist.bind_window(MainWindow)

        self.ui_initialized = True

    def flush_ui_state(self):
        """Persist all tracked layout state immediately (call on close/hide)."""
        self._persist.flush()

    # ── Shared status / save ────────────────────────────────────────────
    def setUnsavedChanges(self):
        self.unsaved_changes = True
        c = themes.CURRENT_THEME_COLORS
        self.statusLabel.setText("Unsaved changes - Click Save to apply")
        self.statusLabel.setStyleSheet(
            f"QLabel {{ color: {c['status_unsaved']}; font-weight: bold; }}")

    def dumpOnSave(self):
        c = themes.CURRENT_THEME_COLORS
        if app_state.dumpJson():
            self.unsaved_changes = False
            self.statusLabel.setText("Settings saved successfully!")
            self.statusLabel.setStyleSheet(
                f"QLabel {{ color: {c['status_saved']}; font-weight: bold; }}")
            QtCore.QTimer.singleShot(3000, lambda: self.statusLabel.setText(""))
        else:
            self.statusLabel.setText("Error saving settings!")
            self.statusLabel.setStyleSheet(
                f"QLabel {{ color: {c['status_error']}; font-weight: bold; }}")
