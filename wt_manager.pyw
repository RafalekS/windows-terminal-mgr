from shutil import copyfile
from PyQt6 import QtCore, QtGui, QtWidgets
import commentjson
import os
import matplotlib.font_manager
import datetime
import subprocess
import sys
import argparse
import uuid as _uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Parse command line arguments
parser = argparse.ArgumentParser(description='Windows Terminal Settings Manager')
parser.add_argument('--debug', action='store_true', help='Enable debug output')
args = parser.parse_args()

# Global DEBUG flag
DEBUG = args.debug

def debug_print(*args_print, **kwargs):
    """Print debug messages only if DEBUG flag is enabled"""
    if DEBUG:
        print(*args_print, **kwargs)

# Store the script directory before changing to settings directory
SCRIPT_DIR = Path(__file__).parent.absolute()

# Place in the "settings.json" directory
homePath = os.getenv("HOMEPATH")
if not homePath:
    homePath = os.getenv("USERPROFILE", "")
    if homePath and ":" in homePath:
        # USERPROFILE is full path like C:\Users\name, strip drive letter
        homePath = homePath[2:]

settingsPath = None
for base in [f"C:{homePath}\\LocalAppData", f"C:{homePath}\\AppData\\Local"]:
    candidate = f"{base}\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState"
    if os.path.isdir(candidate):
        settingsPath = candidate
        break

if not settingsPath:
    print("Error: Could not find Windows Terminal settings directory.")
    print(f"Searched with HOMEPATH='{homePath}'")
    print("Expected: %HOMEPATH%\\LocalAppData\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState")
    exit(1)

os.chdir(settingsPath)

# Create a backup of "settings.json" with timestamp
backup_filename = f"{settingsPath}\\settings.json.bak_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
copyfile(f"{settingsPath}\\settings.json", backup_filename)

# Open "settings.json" and load it as an object
try:
    with open("settings.json", "r", encoding='utf-8') as file:
        wt_schemes = file.read()
    data_schemes = commentjson.loads(wt_schemes)
except Exception as e:
    print(f"Error loading settings.json: {e}")
    exit(1)

# Function to dump modifications to "settings.json" only when Save button is clicked
def dumpJson():
    try:
        # Create a backup before saving
        backup_filename = f"{settingsPath}\\settings.json.bak_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        copyfile(f"{settingsPath}\\settings.json", backup_filename)

        # Strip internal UIDs before writing to disk
        clean_data = strip_uids(data_schemes)
        with open("settings.json", "w", encoding='utf-8') as file:
            commentjson.dump(clean_data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving settings.json: {e}")
        return False

# Find the name of the default profile
default_guid = data_schemes.get("defaultProfile", "")

def findDefault():
    for item in data_schemes.get('profiles', {}).get('list', []):
        if item.get('guid') == default_guid:
            return item.get('name', 'Unknown')
    return "Unknown"

default_profile = findDefault()

# Create the list of themes, profiles, and fonts
data_list = [item['name'] for item in data_schemes.get('schemes', [])]
profiles_list = [item['name'] for item in data_schemes.get('profiles', {}).get('list', [])]
fonts = matplotlib.font_manager.fontManager.ttflist
font_list = list(dict.fromkeys(sorted([f.name for f in fonts], key=str.lower)))

# UID key used to track entry identity across tree reloads
_UID_KEY = '_wt_uid'

def stamp_uids(entries):
    """Stamp unique IDs on all newTabMenu entries so we can track identity reliably."""
    for entry in entries:
        if isinstance(entry, dict):
            if _UID_KEY not in entry:
                entry[_UID_KEY] = str(_uuid.uuid4())
            if entry.get('type') == 'folder' and 'entries' in entry:
                stamp_uids(entry['entries'])

def strip_uids(obj):
    """Recursively remove _wt_uid keys before saving to disk."""
    if isinstance(obj, dict):
        return {k: strip_uids(v) for k, v in obj.items() if k != _UID_KEY}
    elif isinstance(obj, list):
        return [strip_uids(item) for item in obj]
    return obj

# Stamp UIDs on existing menu entries at load time
stamp_uids(data_schemes.get('newTabMenu', []))

# Common Windows Terminal actions for dropdown
COMMON_ACTIONS = [
    "copy", "paste", "find", "openSettings", "openNewTabDropdown", "newTab", "duplicateTab",
    "closeTab", "nextTab", "prevTab", "switchToTab", "splitPane", "closePane", "moveFocus",
    "resizePane", "togglePaneZoom", "scrollUp", "scrollDown", "scrollUpPage", "scrollDownPage",
    "adjustFontSize", "resetFontSize", "toggleFullscreen", "toggleFocusMode", "commandPalette",
    "quit", "closeWindow", "newWindow", "toggleAlwaysOnTop", "sendInput", "selectAll",
    "markMode", "switchSelectionEndpoint", "expandSelectionToWord", "clearBuffer", "exportBuffer"
]

# Built-in schemes available in Windows Terminal
BUILTIN_SCHEMES = [
    "Campbell", "Campbell Powershell", "Vintage", "One Half Dark",
    "One Half Light", "Solarized Dark", "Solarized Light",
    "Tango Dark", "Arthur"
]

class CommandStep:
    """Represents a step in the Windows Terminal command builder"""
    def __init__(self, kind: str):
        self.kind = kind  # "new-tab" or "split-pane"
        self.profile_name: str = ""
        self.starting_directory: str = ""
        self.use_parent_dir: bool = False
        self.title: str = ""
        self.tab_color: str = ""
        self.color_scheme: str = ""
        self.commandline: str = ""
        self.split_orientation: str = ""  # 'H' or 'V'
        self.pane_size: Optional[float] = None

    def build(self) -> str:
        parts = []
        cmd = "new-tab" if self.kind == "new-tab" else "split-pane"
        parts.append(cmd)
        if self.kind == "split-pane":
            if self.split_orientation == "H":
                parts.append("-H")
            elif self.split_orientation == "V":
                parts.append("-V")
            if self.pane_size is not None:
                parts.append(f"--size {self.pane_size}")
        if self.profile_name and not self.commandline:
            parts.append(f'-p "{self.profile_name}"')
        if self.use_parent_dir:
            parts.append("--useParentProcessDirectory")
        elif self.starting_directory:
            parts.append(f'-d "{self.starting_directory}"')
        if self.title:
            parts.append(f'--title "{self.title}"')
        if self.tab_color:
            parts.append(f"--tabColor '{self.tab_color}'")
        if self.color_scheme:
            parts.append(f'--colorScheme "{self.color_scheme}"')
        if self.commandline:
            parts.append(self.commandline)
        return " ".join(parts)


class DragDropTreeWidget(QtWidgets.QTreeWidget):
    """QTreeWidget subclass that supports drag-and-drop reordering for the folders tree."""

    # Signal emitted after a successful drop with (moved_entry_dict)
    itemDropped = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.setDropIndicatorShown(True)
        self._ui = None  # Will be set to Ui_MainWindow instance

    def _getEntry(self, item):
        if item is None:
            return None
        return item.data(0, QtCore.Qt.ItemDataRole.UserRole)

    def startDrag(self, supportedActions):
        """Prevent dragging remainingProfiles and virtual entries."""
        item = self.currentItem()
        entry = self._getEntry(item)
        if entry and entry.get('type') in ('remainingProfiles', '_virtual_remaining'):
            return  # Don't allow drag
        super().startDrag(supportedActions)

    def dropEvent(self, event):
        """Handle drop: update data_schemes and reload tree."""
        dragged_item = self.currentItem()
        if not dragged_item:
            event.ignore()
            return

        dragged_entry = self._getEntry(dragged_item)
        if not dragged_entry or dragged_entry.get('type') in ('remainingProfiles', '_virtual_remaining'):
            event.ignore()
            return

        # Determine drop target and position
        drop_pos = self.dropIndicatorPosition()
        target_item = self.itemAt(event.position().toPoint())
        target_entry = self._getEntry(target_item) if target_item else None

        # Don't drop onto remainingProfiles or virtual entries
        if target_entry and target_entry.get('type') in ('remainingProfiles', '_virtual_remaining'):
            event.ignore()
            return

        if not self._ui:
            event.ignore()
            return

        # Find and remove dragged entry from its current location
        parent_list, idx = self._ui.findParentList(dragged_entry)
        if parent_list is None:
            event.ignore()
            return
        parent_list.pop(idx)

        # Determine destination
        root_menu = data_schemes.get('newTabMenu', [])

        if target_item is None:
            # Dropped on empty space -> append to root
            root_menu.append(dragged_entry)
        elif drop_pos == QtWidgets.QAbstractItemView.DropIndicatorPosition.OnItem:
            # Dropped ON an item
            if target_entry and target_entry.get('type') == 'folder':
                # Drop into folder
                if 'entries' not in target_entry:
                    target_entry['entries'] = []
                target_entry['entries'].append(dragged_entry)
            else:
                # Drop on a non-folder -> insert after it
                tgt_list, tgt_idx = self._ui.findParentList(target_entry)
                if tgt_list is not None:
                    tgt_list.insert(tgt_idx + 1, dragged_entry)
                else:
                    root_menu.append(dragged_entry)
        elif drop_pos == QtWidgets.QAbstractItemView.DropIndicatorPosition.AboveItem:
            tgt_list, tgt_idx = self._ui.findParentList(target_entry)
            if tgt_list is not None:
                tgt_list.insert(tgt_idx, dragged_entry)
            else:
                root_menu.append(dragged_entry)
        elif drop_pos == QtWidgets.QAbstractItemView.DropIndicatorPosition.BelowItem:
            tgt_list, tgt_idx = self._ui.findParentList(target_entry)
            if tgt_list is not None:
                tgt_list.insert(tgt_idx + 1, dragged_entry)
            else:
                root_menu.append(dragged_entry)
        else:
            # No indicator -> append to root
            root_menu.append(dragged_entry)

        # Don't let Qt handle the default move (we did it ourselves)
        event.setDropAction(QtCore.Qt.DropAction.IgnoreAction)
        event.accept()

        # Reload tree and re-select
        self._ui.loadFolders()
        self._ui.reselectItemByIdentity(dragged_entry)
        self._ui.setUnsavedChanges()


class KeyRecorderDialog(QtWidgets.QDialog):
    """Dialog that captures a keyboard shortcut by listening for a key press."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Shortcut")
        self.setFixedSize(320, 120)
        self.recorded_keys = ""

        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("Press the key combination you want to record...")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.result_label = QtWidgets.QLabel("")
        self.result_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.result_label)

        btn_row = QtWidgets.QHBoxLayout()
        self.ok_btn = QtWidgets.QPushButton("OK")
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.accept)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def keyPressEvent(self, event):
        key = event.key()
        # Ignore bare modifier keys
        if key in (QtCore.Qt.Key.Key_Control, QtCore.Qt.Key.Key_Shift,
                   QtCore.Qt.Key.Key_Alt, QtCore.Qt.Key.Key_Meta):
            return

        modifiers = event.modifiers()
        parts = []
        if modifiers & QtCore.Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
            parts.append("alt")
        if modifiers & QtCore.Qt.KeyboardModifier.MetaModifier:
            parts.append("win")

        # Map Qt key to WT key name
        key_name = self._qtKeyToWtName(key)
        if key_name:
            parts.append(key_name)
            self.recorded_keys = "+".join(parts)
            self.result_label.setText(self.recorded_keys)
            self.ok_btn.setEnabled(True)

    def _qtKeyToWtName(self, key) -> str:
        """Map a Qt key code to a Windows Terminal shortcut key name."""
        mapping = {
            QtCore.Qt.Key.Key_A: 'a', QtCore.Qt.Key.Key_B: 'b', QtCore.Qt.Key.Key_C: 'c',
            QtCore.Qt.Key.Key_D: 'd', QtCore.Qt.Key.Key_E: 'e', QtCore.Qt.Key.Key_F: 'f',
            QtCore.Qt.Key.Key_G: 'g', QtCore.Qt.Key.Key_H: 'h', QtCore.Qt.Key.Key_I: 'i',
            QtCore.Qt.Key.Key_J: 'j', QtCore.Qt.Key.Key_K: 'k', QtCore.Qt.Key.Key_L: 'l',
            QtCore.Qt.Key.Key_M: 'm', QtCore.Qt.Key.Key_N: 'n', QtCore.Qt.Key.Key_O: 'o',
            QtCore.Qt.Key.Key_P: 'p', QtCore.Qt.Key.Key_Q: 'q', QtCore.Qt.Key.Key_R: 'r',
            QtCore.Qt.Key.Key_S: 's', QtCore.Qt.Key.Key_T: 't', QtCore.Qt.Key.Key_U: 'u',
            QtCore.Qt.Key.Key_V: 'v', QtCore.Qt.Key.Key_W: 'w', QtCore.Qt.Key.Key_X: 'x',
            QtCore.Qt.Key.Key_Y: 'y', QtCore.Qt.Key.Key_Z: 'z',
            QtCore.Qt.Key.Key_0: '0', QtCore.Qt.Key.Key_1: '1', QtCore.Qt.Key.Key_2: '2',
            QtCore.Qt.Key.Key_3: '3', QtCore.Qt.Key.Key_4: '4', QtCore.Qt.Key.Key_5: '5',
            QtCore.Qt.Key.Key_6: '6', QtCore.Qt.Key.Key_7: '7', QtCore.Qt.Key.Key_8: '8',
            QtCore.Qt.Key.Key_9: '9',
            QtCore.Qt.Key.Key_F1: 'f1', QtCore.Qt.Key.Key_F2: 'f2', QtCore.Qt.Key.Key_F3: 'f3',
            QtCore.Qt.Key.Key_F4: 'f4', QtCore.Qt.Key.Key_F5: 'f5', QtCore.Qt.Key.Key_F6: 'f6',
            QtCore.Qt.Key.Key_F7: 'f7', QtCore.Qt.Key.Key_F8: 'f8', QtCore.Qt.Key.Key_F9: 'f9',
            QtCore.Qt.Key.Key_F10: 'f10', QtCore.Qt.Key.Key_F11: 'f11', QtCore.Qt.Key.Key_F12: 'f12',
            QtCore.Qt.Key.Key_F13: 'f13', QtCore.Qt.Key.Key_F14: 'f14', QtCore.Qt.Key.Key_F15: 'f15',
            QtCore.Qt.Key.Key_F16: 'f16', QtCore.Qt.Key.Key_F17: 'f17', QtCore.Qt.Key.Key_F18: 'f18',
            QtCore.Qt.Key.Key_F19: 'f19', QtCore.Qt.Key.Key_F20: 'f20', QtCore.Qt.Key.Key_F21: 'f21',
            QtCore.Qt.Key.Key_F22: 'f22', QtCore.Qt.Key.Key_F23: 'f23', QtCore.Qt.Key.Key_F24: 'f24',
            QtCore.Qt.Key.Key_Return: 'enter', QtCore.Qt.Key.Key_Enter: 'enter',
            QtCore.Qt.Key.Key_Tab: 'tab', QtCore.Qt.Key.Key_Space: 'space',
            QtCore.Qt.Key.Key_Escape: 'esc', QtCore.Qt.Key.Key_Backspace: 'backspace',
            QtCore.Qt.Key.Key_Delete: 'delete', QtCore.Qt.Key.Key_Insert: 'insert',
            QtCore.Qt.Key.Key_Home: 'home', QtCore.Qt.Key.Key_End: 'end',
            QtCore.Qt.Key.Key_PageUp: 'pgup', QtCore.Qt.Key.Key_PageDown: 'pgdn',
            QtCore.Qt.Key.Key_Up: 'up', QtCore.Qt.Key.Key_Down: 'down',
            QtCore.Qt.Key.Key_Left: 'left', QtCore.Qt.Key.Key_Right: 'right',
            QtCore.Qt.Key.Key_Plus: 'plus', QtCore.Qt.Key.Key_Minus: 'minus',
            QtCore.Qt.Key.Key_Equal: '=', QtCore.Qt.Key.Key_Comma: ',',
            QtCore.Qt.Key.Key_Period: '.', QtCore.Qt.Key.Key_Slash: '/',
            QtCore.Qt.Key.Key_Backslash: '\\', QtCore.Qt.Key.Key_BracketLeft: '[',
            QtCore.Qt.Key.Key_BracketRight: ']', QtCore.Qt.Key.Key_Semicolon: ';',
            QtCore.Qt.Key.Key_Apostrophe: "'", QtCore.Qt.Key.Key_QuoteLeft: '`',
        }
        return mapping.get(key, '')


class Ui_MainWindow(object):
    def __init__(self):
        self.unsaved_changes = False
        self.ui_initialized = False

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Windows Terminal Settings")
        MainWindow.resize(1400, 900)
        MainWindow.setWindowTitle("Windows Terminal Manager")
        MainWindow.setMinimumSize(1200, 700)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create tab widget
        self.tabWidget = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabWidget)

        # Setup tabs
        self.profilesTab = QtWidgets.QWidget()
        self.actionsTab = QtWidgets.QWidget()
        self.commandBuilderTab = QtWidgets.QWidget()
        self.foldersTab = QtWidgets.QWidget()

        self.tabWidget.addTab(self.profilesTab, "  Profiles")
        self.tabWidget.addTab(self.foldersTab, "  Folders && New Tab Menu")
        self.tabWidget.addTab(self.actionsTab, "  Actions && Key Bindings")
        self.tabWidget.addTab(self.commandBuilderTab, "  WT Command Builder")

        # Set tab icons using Unicode characters via styled labels
        self.tabWidget.setTabToolTip(0, "Manage terminal profiles")
        self.tabWidget.setTabToolTip(1, "Organize the new tab dropdown menu")
        self.tabWidget.setTabToolTip(2, "Configure keyboard shortcuts and actions")
        self.tabWidget.setTabToolTip(3, "Build complex wt.exe commands")

        self.setupProfilesTab()
        self.setupActionsTab()
        self.setupCommandBuilderTab()
        self.setupFoldersTab()

        # Bottom panel with status
        bottom_layout = QtWidgets.QHBoxLayout()

        # Status label
        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.statusLabel)

        main_layout.addLayout(bottom_layout)

        # Save button will be created in setupProfilesTab and placed in the left panel

        # Mark UI as initialized
        self.ui_initialized = True

    def setupProfilesTab(self):
        # Main horizontal layout
        main_layout = QtWidgets.QHBoxLayout(self.profilesTab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left side - Profile list and controls
        left_widget = QtWidgets.QWidget()
        left_widget.setMinimumWidth(250)
        left_widget.setMaximumWidth(300)
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        # Profile list
        profiles_label = QtWidgets.QLabel("Profiles:")
        profiles_label.setFont(QtGui.QFont("", 10, QtGui.QFont.Weight.Bold))
        left_layout.addWidget(profiles_label)

        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setMinimumHeight(400)
        for item in profiles_list:
            self.listWidget.addItem(item)
        self.updateProfileMenuIndicators()
        left_layout.addWidget(self.listWidget)

        # Profile control buttons
        profile_buttons_layout = QtWidgets.QGridLayout()

        self.moveUpButton = QtWidgets.QPushButton("Move Up")
        self.moveDownButton = QtWidgets.QPushButton("Move Down")
        self.renameButton = QtWidgets.QPushButton("Rename")
        self.defaultButton = QtWidgets.QPushButton("Set as Default")

        profile_buttons_layout.addWidget(self.moveUpButton, 0, 0)
        profile_buttons_layout.addWidget(self.moveDownButton, 0, 1)
        profile_buttons_layout.addWidget(self.renameButton, 1, 0)
        profile_buttons_layout.addWidget(self.defaultButton, 1, 1)

        left_layout.addLayout(profile_buttons_layout)

        # Separator line
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        left_layout.addWidget(separator)

        # Profile management buttons
        profile_mgmt_layout = QtWidgets.QGridLayout()

        self.newProfileButton = QtWidgets.QPushButton("New Profile")
        self.duplicateProfileButton = QtWidgets.QPushButton("Duplicate Profile")
        self.deleteProfileButton = QtWidgets.QPushButton("Delete Profile")

        profile_mgmt_layout.addWidget(self.newProfileButton, 0, 0)
        profile_mgmt_layout.addWidget(self.duplicateProfileButton, 0, 1)
        profile_mgmt_layout.addWidget(self.deleteProfileButton, 1, 0, 1, 2)

        left_layout.addLayout(profile_mgmt_layout)

        # Separator before Save
        save_separator = QtWidgets.QFrame()
        save_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        save_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        left_layout.addWidget(save_separator)

        # Save button - prominent in left panel
        self.saveButton = QtWidgets.QPushButton("Save")
        self.saveButton.setMinimumSize(120, 40)
        self.saveButton.setMaximumSize(300, 40)
        self.saveButton.setStyleSheet("QPushButton { background-color: #6dba65; color: #ffffff; font-weight: bold; } QPushButton:hover { background-color: #5aa852; }")
        self.saveButton.clicked.connect(self.dumpOnSave)
        left_layout.addWidget(self.saveButton)

        left_layout.addStretch()

        main_layout.addWidget(left_widget)

        # Right side - Profile details
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        # Profile details in scroll area
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_widget = QtWidgets.QWidget()
        scroll_main = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_main.setSpacing(6)

        # Helper to create a color field with picker button
        def makeColorRow(edit_attr, placeholder="#RRGGBB"):
            layout = QtWidgets.QHBoxLayout()
            edit = QtWidgets.QLineEdit()
            edit.setPlaceholderText(placeholder)
            btn = QtWidgets.QPushButton("Pick...")
            btn.setMaximumWidth(90)
            btn.clicked.connect(lambda: self._pickColorInto(edit))
            layout.addWidget(edit)
            layout.addWidget(btn)
            setattr(self, edit_attr, edit)
            return layout

        # ── General Section ──
        general_group = QtWidgets.QGroupBox("General")
        general_layout = QtWidgets.QFormLayout(general_group)
        general_layout.setSpacing(6)

        self.profileNameEdit = QtWidgets.QLineEdit()
        self.profileNameEdit.setReadOnly(True)
        general_layout.addRow("Profile Name:", self.profileNameEdit)

        self.commandLineEdit = QtWidgets.QLineEdit()
        general_layout.addRow("Command Line:", self.commandLineEdit)

        self.startingDirectoryEdit = QtWidgets.QLineEdit()
        general_layout.addRow("Starting Directory:", self.startingDirectoryEdit)

        self.tabTitleEdit = QtWidgets.QLineEdit()
        general_layout.addRow("Tab Title:", self.tabTitleEdit)

        tab_color_layout = makeColorRow('tabColorEdit')
        general_layout.addRow("Tab Color:", tab_color_layout)

        icon_layout = QtWidgets.QHBoxLayout()
        self.iconEdit = QtWidgets.QLineEdit()
        self.iconBrowseButton = QtWidgets.QPushButton("Browse...")
        self.iconBrowseButton.setMaximumWidth(90)
        icon_layout.addWidget(self.iconEdit)
        icon_layout.addWidget(self.iconBrowseButton)
        general_layout.addRow("Icon:", icon_layout)

        checks_layout = QtWidgets.QHBoxLayout()
        self.hiddenCheckBox = QtWidgets.QCheckBox("Hidden")
        self.runAsAdminCheckBox = QtWidgets.QCheckBox("Run as Admin")
        self.suppressTitleCheckBox = QtWidgets.QCheckBox("Suppress App Title")
        checks_layout.addWidget(self.hiddenCheckBox)
        checks_layout.addWidget(self.runAsAdminCheckBox)
        checks_layout.addWidget(self.suppressTitleCheckBox)
        checks_layout.addStretch()
        general_layout.addRow("", checks_layout)

        scroll_main.addWidget(general_group)

        # ── Appearance Section ──
        appearance_group = QtWidgets.QGroupBox("Appearance")
        appearance_layout = QtWidgets.QFormLayout(appearance_group)
        appearance_layout.setSpacing(6)

        self.comboBox = QtWidgets.QComboBox()
        for item in data_list:
            self.comboBox.addItem(item)
        appearance_layout.addRow("Color Scheme:", self.comboBox)

        # Font row: face + size + weight
        font_layout = QtWidgets.QHBoxLayout()
        self.fontBox = QtWidgets.QComboBox()
        self.fontBox.setMinimumWidth(180)
        for item in font_list:
            self.fontBox.addItem(item)
        self.fontSize = QtWidgets.QSpinBox()
        self.fontSize.setMinimum(4)
        self.fontSize.setMaximum(72)
        self.fontSize.setValue(12)
        self.fontWeightBox = QtWidgets.QComboBox()
        self.fontWeightBox.addItems(["normal", "thin", "extra-light", "light", "semi-light",
                                     "medium", "semi-bold", "bold", "extra-bold", "black"])
        font_layout.addWidget(self.fontBox, 3)
        font_layout.addWidget(QtWidgets.QLabel("Size:"))
        font_layout.addWidget(self.fontSize, 1)
        font_layout.addWidget(QtWidgets.QLabel("Weight:"))
        font_layout.addWidget(self.fontWeightBox, 1)
        appearance_layout.addRow("Font:", font_layout)

        # Cursor row: shape + color
        cursor_layout = QtWidgets.QHBoxLayout()
        self.cursorShapeBox = QtWidgets.QComboBox()
        self.cursorShapeBox.addItems(["bar", "vintage", "underscore", "filledBox", "emptyBox", "doubleUnderscore"])
        cursor_layout.addWidget(self.cursorShapeBox, 2)
        cursor_layout.addWidget(QtWidgets.QLabel("Color:"))
        self.cursorColorEdit = QtWidgets.QLineEdit()
        self.cursorColorEdit.setPlaceholderText("#RRGGBB")
        cursor_color_btn = QtWidgets.QPushButton("Pick...")
        cursor_color_btn.setMaximumWidth(90)
        cursor_color_btn.clicked.connect(lambda: self._pickColorInto(self.cursorColorEdit))
        cursor_layout.addWidget(self.cursorColorEdit, 2)
        cursor_layout.addWidget(cursor_color_btn)
        appearance_layout.addRow("Cursor:", cursor_layout)

        # Color overrides
        fg_layout = makeColorRow('foregroundEdit')
        appearance_layout.addRow("Foreground:", fg_layout)

        bg_color_layout = makeColorRow('backgroundColorEdit')
        appearance_layout.addRow("Background:", bg_color_layout)

        sel_layout = makeColorRow('selectionBackgroundEdit')
        appearance_layout.addRow("Selection BG:", sel_layout)

        # Opacity + acrylic
        opacity_row = QtWidgets.QHBoxLayout()
        self.opacitySlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.opacitySlider.setMinimum(0)
        self.opacitySlider.setMaximum(100)
        self.opacitySlider.setValue(100)
        self.opacityValueLabel = QtWidgets.QLabel("100")
        self.useAcrylicCheckBox = QtWidgets.QCheckBox("Acrylic")
        opacity_row.addWidget(self.opacitySlider, 3)
        opacity_row.addWidget(self.opacityValueLabel)
        opacity_row.addWidget(self.useAcrylicCheckBox)
        appearance_layout.addRow("Opacity:", opacity_row)

        self.intenseTextBox = QtWidgets.QComboBox()
        self.intenseTextBox.addItems(["all", "bold", "bright", "none"])
        appearance_layout.addRow("Intense Text:", self.intenseTextBox)

        scroll_main.addWidget(appearance_group)

        # ── Background Image Section ──
        bgimg_group = QtWidgets.QGroupBox("Background Image")
        bgimg_layout = QtWidgets.QFormLayout(bgimg_group)
        bgimg_layout.setSpacing(6)

        bg_path_layout = QtWidgets.QHBoxLayout()
        self.backgroundImageEdit = QtWidgets.QLineEdit()
        self.pushButton = QtWidgets.QPushButton("Browse...")
        self.pushButton.setMaximumWidth(90)
        bg_path_layout.addWidget(self.backgroundImageEdit)
        bg_path_layout.addWidget(self.pushButton)
        bgimg_layout.addRow("Image Path:", bg_path_layout)

        bgimg_opts = QtWidgets.QHBoxLayout()
        self.horizontalSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.horizontalSlider.setMaximum(10)
        self.horizontalSlider.setValue(10)
        self.bgOpacityLabel = QtWidgets.QLabel("1.0")
        bgimg_opts.addWidget(self.horizontalSlider, 2)
        bgimg_opts.addWidget(self.bgOpacityLabel)
        bgimg_opts.addWidget(QtWidgets.QLabel("Stretch:"))
        self.bgStretchBox = QtWidgets.QComboBox()
        self.bgStretchBox.addItems(["uniformToFill", "none", "fill", "uniform"])
        bgimg_opts.addWidget(self.bgStretchBox, 1)
        bgimg_opts.addWidget(QtWidgets.QLabel("Align:"))
        self.bgAlignBox = QtWidgets.QComboBox()
        self.bgAlignBox.addItems(["center", "left", "top", "right", "bottom",
                                   "topLeft", "topRight", "bottomLeft", "bottomRight"])
        bgimg_opts.addWidget(self.bgAlignBox, 1)
        bgimg_layout.addRow("Opacity:", bgimg_opts)

        scroll_main.addWidget(bgimg_group)

        # ── Advanced Section ──
        advanced_group = QtWidgets.QGroupBox("Advanced")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
        advanced_layout = QtWidgets.QFormLayout(advanced_group)
        advanced_layout.setSpacing(6)

        self.historySizeSpinBox = QtWidgets.QSpinBox()
        self.historySizeSpinBox.setMinimum(0)
        self.historySizeSpinBox.setMaximum(32767)
        self.historySizeSpinBox.setValue(9001)
        advanced_layout.addRow("History Size:", self.historySizeSpinBox)

        self.closeOnExitBox = QtWidgets.QComboBox()
        self.closeOnExitBox.addItems(["graceful", "always", "never"])
        advanced_layout.addRow("Close on Exit:", self.closeOnExitBox)

        self.bellStyleBox = QtWidgets.QComboBox()
        self.bellStyleBox.addItems(["audible", "none", "visual", "all"])
        advanced_layout.addRow("Bell Style:", self.bellStyleBox)

        self.antialiasingBox = QtWidgets.QComboBox()
        self.antialiasingBox.addItems(["grayscale", "cleartype", "aliased"])
        advanced_layout.addRow("Antialiasing:", self.antialiasingBox)

        self.scrollbarBox = QtWidgets.QComboBox()
        self.scrollbarBox.addItems(["visible", "hidden"])
        advanced_layout.addRow("Scrollbar:", self.scrollbarBox)

        self.paddingEdit = QtWidgets.QLineEdit()
        self.paddingEdit.setPlaceholderText("e.g. 8 or 8,8,8,8")
        advanced_layout.addRow("Padding:", self.paddingEdit)

        adv_checks = QtWidgets.QHBoxLayout()
        self.snapOnInputCheckBox = QtWidgets.QCheckBox("Snap on Input")
        self.retroEffectCheckBox = QtWidgets.QCheckBox("Retro Terminal Effect")
        self.altGrCheckBox = QtWidgets.QCheckBox("AltGr Aliasing")
        adv_checks.addWidget(self.snapOnInputCheckBox)
        adv_checks.addWidget(self.retroEffectCheckBox)
        adv_checks.addWidget(self.altGrCheckBox)
        adv_checks.addStretch()
        advanced_layout.addRow("", adv_checks)

        scroll_main.addWidget(advanced_group)
        scroll_main.addStretch()

        scroll_area.setWidget(scroll_widget)
        right_layout.addWidget(scroll_area)

        main_layout.addWidget(right_widget)

        # Connect profile signals
        self.listWidget.currentItemChanged.connect(self.changedProfile)
        self.comboBox.activated.connect(self.changeScheme)
        self.fontBox.activated.connect(self.changeFont)
        self.fontSize.valueChanged.connect(self.changeFontSize)
        self.fontWeightBox.textActivated.connect(self.changeFontWeight)
        self.pushButton.clicked.connect(self.changeBackgroundImage)
        self.horizontalSlider.sliderReleased.connect(self.changeBgImageOpacity)
        self.commandLineEdit.textChanged.connect(self.changeCommandLine)
        self.startingDirectoryEdit.textChanged.connect(self.changeStartingDirectory)
        self.tabTitleEdit.textChanged.connect(self.changeTabTitle)
        self.tabColorEdit.textChanged.connect(self.changeTabColor)
        self.iconEdit.textChanged.connect(self.changeIcon)
        self.iconBrowseButton.clicked.connect(self.browseIcon)
        self.paddingEdit.textChanged.connect(self.changePadding)
        self.cursorShapeBox.textActivated.connect(self.changeCursorShape)
        self.cursorColorEdit.textChanged.connect(self.changeCursorColor)
        self.scrollbarBox.textActivated.connect(self.changeScrollbarState)
        self.runAsAdminCheckBox.stateChanged.connect(self.changeRunAsAdmin)
        self.useAcrylicCheckBox.stateChanged.connect(self.changeUseAcrylic)
        self.hiddenCheckBox.stateChanged.connect(self.changeHidden)
        self.snapOnInputCheckBox.stateChanged.connect(self.changeSnapOnInput)
        self.suppressTitleCheckBox.stateChanged.connect(self.changeSuppressTitle)
        self.foregroundEdit.textChanged.connect(self.changeForeground)
        self.backgroundColorEdit.textChanged.connect(self.changeBackgroundColor)
        self.selectionBackgroundEdit.textChanged.connect(self.changeSelectionBackground)
        self.opacitySlider.sliderReleased.connect(self.changeOpacity)
        self.intenseTextBox.textActivated.connect(self.changeIntenseText)
        self.bgStretchBox.textActivated.connect(self.changeBgStretchMode)
        self.bgAlignBox.textActivated.connect(self.changeBgAlignment)
        self.historySizeSpinBox.valueChanged.connect(self.changeHistorySize)
        self.closeOnExitBox.textActivated.connect(self.changeCloseOnExit)
        self.bellStyleBox.textActivated.connect(self.changeBellStyle)
        self.antialiasingBox.textActivated.connect(self.changeAntialiasing)
        self.retroEffectCheckBox.stateChanged.connect(self.changeRetroEffect)
        self.altGrCheckBox.stateChanged.connect(self.changeAltGr)
        self.defaultButton.clicked.connect(self.changeDefault)
        self.moveUpButton.clicked.connect(self.moveProfileUp)
        self.moveDownButton.clicked.connect(self.moveProfileDown)
        self.renameButton.clicked.connect(self.renameProfile)
        self.newProfileButton.clicked.connect(self.createNewProfile)
        self.duplicateProfileButton.clicked.connect(self.duplicateProfile)
        self.deleteProfileButton.clicked.connect(self.deleteProfile)

        # Set initial selection
        index_listWidget = self.listWidget.findItems(default_profile, QtCore.Qt.MatchFlag.MatchFixedString)
        if index_listWidget:
            self.listWidget.setCurrentRow(self.listWidget.row(index_listWidget[0]))
        elif self.listWidget.count() > 0:
            self.listWidget.setCurrentRow(0)

    def setupActionsTab(self):
        main_layout = QtWidgets.QVBoxLayout(self.actionsTab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Filter bar
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.actionsFilterEdit = QtWidgets.QLineEdit()
        self.actionsFilterEdit.setPlaceholderText("Type to filter actions...")
        self.actionsFilterEdit.textChanged.connect(self.filterActions)
        filter_layout.addWidget(self.actionsFilterEdit)
        main_layout.addLayout(filter_layout)

        # Actions table (replaces list widget)
        self.actionsTable = QtWidgets.QTableWidget()
        self.actionsTable.setColumnCount(4)
        self.actionsTable.setHorizontalHeaderLabels(["Shortcut", "Name", "Command", "ID"])
        self.actionsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.actionsTable.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.actionsTable.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.actionsTable.setSortingEnabled(True)
        self.actionsTable.horizontalHeader().setStretchLastSection(False)
        self.actionsTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.actionsTable.verticalHeader().setVisible(False)
        self.actionsTable.setAlternatingRowColors(True)

        # Restore column widths from QSettings
        self._restoreActionsColumnWidths()

        main_layout.addWidget(self.actionsTable, 3)

        # Editor panel
        editor_group = QtWidgets.QGroupBox("Edit Action")
        editor_layout = QtWidgets.QFormLayout(editor_group)
        editor_layout.setSpacing(6)

        self.actionNameEdit = QtWidgets.QLineEdit()
        self.actionNameEdit.setPlaceholderText("Display name for the action")
        editor_layout.addRow("Name:", self.actionNameEdit)

        shortcut_row = QtWidgets.QHBoxLayout()
        self.keysEdit = QtWidgets.QLineEdit()
        self.keysEdit.setPlaceholderText("e.g. ctrl+shift+t  (comma-separate for multiple)")
        self.recordKeyButton = QtWidgets.QPushButton("Record...")
        self.recordKeyButton.setMinimumWidth(90)
        self.recordKeyButton.setToolTip("Click to record a key combination")
        self.recordKeyButton.clicked.connect(self.recordShortcut)
        shortcut_row.addWidget(self.keysEdit)
        shortcut_row.addWidget(self.recordKeyButton)
        editor_layout.addRow("Shortcut:", shortcut_row)

        self.commandActionCombo = QtWidgets.QComboBox()
        self.commandActionCombo.setEditable(True)
        for action in COMMON_ACTIONS:
            self.commandActionCombo.addItem(action)
        editor_layout.addRow("Command:", self.commandActionCombo)

        # Advanced section (collapsed)
        adv_group = QtWidgets.QGroupBox("Advanced")
        adv_group.setCheckable(True)
        adv_group.setChecked(False)
        adv_layout = QtWidgets.QFormLayout(adv_group)
        adv_layout.setSpacing(6)

        self.actionIdEdit = QtWidgets.QLineEdit()
        self.actionIdEdit.setPlaceholderText("Auto-generated if left empty")
        adv_layout.addRow("Action ID:", self.actionIdEdit)

        self.actionArgsEdit = QtWidgets.QTextEdit()
        self.actionArgsEdit.setMaximumHeight(80)
        self.actionArgsEdit.setPlaceholderText('JSON arguments, e.g. {"action": "newTab", "index": 0}')
        adv_layout.addRow("Arguments:", self.actionArgsEdit)

        self.iconPathEdit = QtWidgets.QLineEdit()
        self.iconPathEdit.setPlaceholderText("Path to icon (optional)")
        adv_layout.addRow("Icon:", self.iconPathEdit)

        editor_layout.addRow(adv_group)
        main_layout.addWidget(editor_group)

        # Buttons row
        btn_layout = QtWidgets.QHBoxLayout()
        self.addActionButton = QtWidgets.QPushButton("Add New")
        self.addActionButton.setStyleSheet("QPushButton { background-color: #6dba65; color: #ffffff; } QPushButton:hover { background-color: #5aa852; }")
        self.updateActionButton = QtWidgets.QPushButton("Save Changes")
        self.updateActionButton.setStyleSheet("QPushButton { background-color: #5b8bd4; color: #ffffff; } QPushButton:hover { background-color: #4a7ac3; }")
        self.deleteActionButton = QtWidgets.QPushButton("Delete")
        self.deleteActionButton.setStyleSheet("QPushButton { background-color: #d45b5b; color: #ffffff; } QPushButton:hover { background-color: #c34a4a; }")
        self.moveActionUpButton = QtWidgets.QPushButton("Move Up")
        self.moveActionDownButton = QtWidgets.QPushButton("Move Down")
        self.clearFieldsButton = QtWidgets.QPushButton("Clear")

        btn_layout.addWidget(self.addActionButton)
        btn_layout.addWidget(self.updateActionButton)
        btn_layout.addWidget(self.deleteActionButton)
        btn_layout.addStretch()
        btn_layout.addWidget(self.moveActionUpButton)
        btn_layout.addWidget(self.moveActionDownButton)
        btn_layout.addWidget(self.clearFieldsButton)
        main_layout.addLayout(btn_layout)

        # Compact help
        help_label = QtWidgets.QLabel(
            "Modifiers: ctrl, shift, alt, win  |  Keys: enter, tab, space, esc, f1-f24, up/down/left/right  |  "
            "Example: ctrl+shift+t")
        help_label.setStyleSheet("QLabel { color: #8580a0; font-size: 11px; padding: 2px; }")
        main_layout.addWidget(help_label)

        # Keep actionsListWidget as hidden proxy for compatibility with existing methods
        self.actionsListWidget = QtWidgets.QListWidget()
        self.actionsListWidget.setVisible(False)

        # Load actions
        self.loadActions()

        # Connect signals
        self.actionsTable.currentCellChanged.connect(self.onActionTableSelectionChanged)
        self.actionsTable.horizontalHeader().sectionResized.connect(self._saveActionsColumnWidths)
        self.addActionButton.clicked.connect(self.addAction)
        self.updateActionButton.clicked.connect(self.updateAction)
        self.deleteActionButton.clicked.connect(self.deleteAction)
        self.moveActionUpButton.clicked.connect(self.moveActionUp)
        self.moveActionDownButton.clicked.connect(self.moveActionDown)
        self.clearFieldsButton.clicked.connect(self.clearActionFields)

    def _saveActionsColumnWidths(self):
        """Save actions table column widths to QSettings"""
        settings = QtCore.QSettings("WTManager", "ActionsTable")
        header = self.actionsTable.horizontalHeader()
        for col in range(self.actionsTable.columnCount()):
            settings.setValue(f"col{col}", header.sectionSize(col))

    def _restoreActionsColumnWidths(self):
        """Restore actions table column widths from QSettings"""
        settings = QtCore.QSettings("WTManager", "ActionsTable")
        header = self.actionsTable.horizontalHeader()
        defaults = [140, 200, 160, 140]
        for col in range(self.actionsTable.columnCount()):
            width = settings.value(f"col{col}", defaults[col] if col < len(defaults) else 100, type=int)
            header.resizeSection(col, width)

    def setupCommandBuilderTab(self):
        """Setup the command builder tab"""
        root = QtWidgets.QVBoxLayout(self.commandBuilderTab)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Extract profiles and schemes for command builder
        self.profile_names = [item['name'] for item in data_schemes.get('profiles', {}).get('list', [])]
        user_schemes = [s.get('name') for s in data_schemes.get('schemes', []) if isinstance(s, dict) and s.get('name')]
        self.scheme_names = sorted(set(user_schemes + BUILTIN_SCHEMES))

        # Global window options - collapsible, collapsed by default
        global_box = QtWidgets.QGroupBox("Global Window Options  (expand to set --maximized, --size, --pos, --window)")
        global_box.setCheckable(True)
        global_box.setChecked(False)
        g_layout = QtWidgets.QHBoxLayout()
        g_layout.setSpacing(8)

        # State checkboxes
        state_w = QtWidgets.QWidget()
        st_layout = QtWidgets.QVBoxLayout(state_w)
        st_layout.setContentsMargins(0, 0, 0, 0)
        self.global_maximized = QtWidgets.QCheckBox("--maximized")
        self.global_fullscreen = QtWidgets.QCheckBox("--fullscreen")
        self.global_focus = QtWidgets.QCheckBox("--focus")
        self.global_maximized.setToolTip("Start window maximized")
        self.global_fullscreen.setToolTip("Start window in fullscreen")
        self.global_focus.setToolTip("Start window in focus mode (hides tabs)")
        self.global_maximized.stateChanged.connect(lambda state: self.global_fullscreen.setChecked(False) if state else None)
        self.global_fullscreen.stateChanged.connect(lambda state: self.global_maximized.setChecked(False) if state else None)
        st_layout.addWidget(self.global_maximized)
        st_layout.addWidget(self.global_fullscreen)
        st_layout.addWidget(self.global_focus)

        # Window target
        win_w = QtWidgets.QWidget()
        win_l = QtWidgets.QFormLayout(win_w)
        win_l.setContentsMargins(0, 0, 0, 0)
        self.window_combo = QtWidgets.QComboBox()
        self.window_combo.setEditable(True)
        self.window_combo.addItems(["", "new", "last"])
        self.window_combo.setEditText("")
        self.window_combo.setToolTip("--window: 'new' = new window, 'last' = most recent, or window ID")
        win_l.addRow("--window:", self.window_combo)

        # Size & position
        dims_w = QtWidgets.QWidget()
        dims_l = QtWidgets.QFormLayout(dims_w)
        dims_l.setContentsMargins(0, 0, 0, 0)
        self.global_size_cols = QtWidgets.QSpinBox()
        self.global_size_rows = QtWidgets.QSpinBox()
        self.global_size_cols.setRange(0, 1000)
        self.global_size_rows.setRange(0, 1000)
        self.global_size_cols.setToolTip("Number of character columns")
        self.global_size_rows.setToolTip("Number of character rows")
        self.global_pos_x = QtWidgets.QSpinBox()
        self.global_pos_y = QtWidgets.QSpinBox()
        self.global_pos_x.setRange(0, 10000)
        self.global_pos_y.setRange(0, 10000)
        self.global_pos_x.setToolTip("Window X position in pixels")
        self.global_pos_y.setToolTip("Window Y position in pixels")
        size_row = QtWidgets.QHBoxLayout()
        size_row.addWidget(self.global_size_cols)
        size_row.addWidget(QtWidgets.QLabel("x"))
        size_row.addWidget(self.global_size_rows)
        pos_row = QtWidgets.QHBoxLayout()
        pos_row.addWidget(self.global_pos_x)
        pos_row.addWidget(QtWidgets.QLabel(","))
        pos_row.addWidget(self.global_pos_y)
        dims_l.addRow("--size (cols x rows):", size_row)
        dims_l.addRow("--pos (x, y pixels):", pos_row)

        g_layout.addWidget(state_w)
        g_layout.addWidget(win_w)
        g_layout.addWidget(dims_w)
        global_box.setLayout(g_layout)
        root.addWidget(global_box)

        # Command Steps - main area
        steps_box = QtWidgets.QGroupBox("Command Steps  (each step = a new tab or split pane)")
        sb_layout = QtWidgets.QVBoxLayout()
        sb_layout.setSpacing(6)

        # Add/remove buttons
        btn_row = QtWidgets.QHBoxLayout()
        add_tab_btn = QtWidgets.QPushButton("+ New Tab")
        add_tab_btn.setToolTip("Add a new-tab step")
        add_pane_h_btn = QtWidgets.QPushButton("+ Split Horizontal")
        add_pane_h_btn.setToolTip("Add a split-pane -H step (split top/bottom)")
        add_pane_v_btn = QtWidgets.QPushButton("+ Split Vertical")
        add_pane_v_btn.setToolTip("Add a split-pane -V step (split left/right)")
        remove_btn = QtWidgets.QPushButton("Remove Step")
        remove_btn.setToolTip("Remove the selected step")
        remove_btn.setStyleSheet("QPushButton { background-color: #d45b5b; color: #ffffff; } QPushButton:hover { background-color: #c34a4a; }")
        move_up_btn = QtWidgets.QPushButton("Up")
        move_up_btn.setToolTip("Move selected step up in order")
        move_down_btn = QtWidgets.QPushButton("Down")
        move_down_btn.setToolTip("Move selected step down in order")
        btn_row.addWidget(add_tab_btn)
        btn_row.addWidget(add_pane_h_btn)
        btn_row.addWidget(add_pane_v_btn)
        btn_row.addStretch()
        btn_row.addWidget(move_up_btn)
        btn_row.addWidget(move_down_btn)
        btn_row.addWidget(remove_btn)
        sb_layout.addLayout(btn_row)

        # Steps list + editor side by side — use QSplitter for resizable
        step_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        self.steps_list = QtWidgets.QListWidget()
        self.steps_list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.steps_list.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.steps_list.model().rowsMoved.connect(lambda: self.refresh_preview())
        step_splitter.addWidget(self.steps_list)

        # Step editor
        editor_box = QtWidgets.QGroupBox("Edit Selected Step")
        ed_layout = QtWidgets.QFormLayout(editor_box)
        ed_layout.setSpacing(6)

        self.profile_combo = QtWidgets.QComboBox()
        self.profile_combo.setEditable(True)
        self.profile_combo.addItems([""] + self.profile_names)
        self.profile_combo.setToolTip("-p: Which profile to use for this tab/pane")
        ed_layout.addRow("Profile (-p):", self.profile_combo)

        self.scheme_combo = QtWidgets.QComboBox()
        self.scheme_combo.setEditable(True)
        self.scheme_combo.addItems([""] + self.scheme_names)
        self.scheme_combo.setToolTip("--colorScheme: Override the colour scheme")
        ed_layout.addRow("Color Scheme:", self.scheme_combo)

        self.title_edit = QtWidgets.QLineEdit()
        self.title_edit.setPlaceholderText("Text shown in the tab header")
        self.title_edit.setToolTip("--title: Set the tab title")
        ed_layout.addRow("Tab Title (--title):", self.title_edit)

        color_row = QtWidgets.QHBoxLayout()
        self.tab_color_edit = QtWidgets.QLineEdit()
        self.tab_color_edit.setPlaceholderText("#RRGGBB")
        self.tab_color_edit.setToolTip("--tabColor: Set tab accent colour")
        pick_btn = QtWidgets.QPushButton("Pick")
        pick_btn.setMinimumWidth(70)
        pick_btn.setToolTip("Open colour picker")
        pick_btn.clicked.connect(self.pick_color)
        color_row.addWidget(self.tab_color_edit)
        color_row.addWidget(pick_btn)
        ed_layout.addRow("Tab Color:", color_row)

        # Starting directory with Browse and parent-process option
        dir_row = QtWidgets.QHBoxLayout()
        self.dir_edit = QtWidgets.QLineEdit()
        self.dir_edit.setPlaceholderText("e.g. C:\\Users\\me\\projects")
        self.dir_edit.setToolTip("-d: Starting directory for this tab/pane")
        dir_btn = QtWidgets.QPushButton("Browse")
        dir_btn.setMinimumWidth(80)
        dir_btn.setToolTip("Browse for a directory")
        dir_btn.clicked.connect(self.browse_dir)
        dir_row.addWidget(self.dir_edit)
        dir_row.addWidget(dir_btn)
        ed_layout.addRow("Directory (-d):", dir_row)

        self.use_parent_dir_check = QtWidgets.QCheckBox("Use parent process directory")
        self.use_parent_dir_check.setToolTip("Adds --useParentProcessDirectory flag: start in the directory of the calling process")
        ed_layout.addRow("", self.use_parent_dir_check)

        self.cmdline_edit = QtWidgets.QLineEdit()
        self.cmdline_edit.setPlaceholderText("e.g. powershell.exe -c \"echo Hello\"  or  wsl.exe")
        self.cmdline_edit.setToolTip("Executable + args to run instead of the profile default.\nMust be a valid Windows executable path.\nExamples: cmd.exe /c dir, powershell.exe, wsl.exe, ssh.exe user@host")
        ed_layout.addRow("Commandline:", self.cmdline_edit)

        # Pane size - only visible for split-pane steps
        self.pane_size_label = QtWidgets.QLabel("Pane Size (--size):")
        self.pane_size_spin = QtWidgets.QDoubleSpinBox()
        self.pane_size_spin.setRange(0.05, 0.95)
        self.pane_size_spin.setSingleStep(0.05)
        self.pane_size_spin.setDecimals(2)
        self.pane_size_spin.setValue(0.5)
        self.pane_size_spin.setToolTip("Fraction of parent pane size (0.05 to 0.95)")
        ed_layout.addRow(self.pane_size_label, self.pane_size_spin)

        step_splitter.addWidget(editor_box)

        # Set initial splitter sizes: 50/50 split
        step_splitter.setSizes([400, 400])
        step_splitter.setStretchFactor(0, 1)
        step_splitter.setStretchFactor(1, 1)

        sb_layout.addWidget(step_splitter)
        steps_box.setLayout(sb_layout)
        root.addWidget(steps_box, 1)

        # Preview section
        preview_box = QtWidgets.QGroupBox("Command Preview  (edit manually or build above, then Copy/Run)")
        pv_layout = QtWidgets.QVBoxLayout()
        pv_layout.setSpacing(4)
        self.preview = QtWidgets.QTextEdit()
        self.preview.setReadOnly(False)
        self.preview.setMaximumHeight(60)
        self.preview.setPlaceholderText("Paste a wt command here and click Parse, or build one above")
        pv_layout.addWidget(self.preview)
        run_row = QtWidgets.QHBoxLayout()
        self.shell_combo = QtWidgets.QComboBox()
        self.shell_combo.addItems(["PowerShell (escape `;)", "CMD (plain ;)"])
        self.shell_combo.setToolTip("Which shell to use for escaping semicolons and running the command")
        run_row.addWidget(QtWidgets.QLabel("Shell:"))
        run_row.addWidget(self.shell_combo)
        run_row.addStretch(1)
        parse_btn = QtWidgets.QPushButton("Parse")
        parse_btn.setToolTip("Parse the command text above and populate the builder steps")
        copy_btn = QtWidgets.QPushButton("Copy")
        copy_btn.setToolTip("Copy the command to clipboard")
        run_btn = QtWidgets.QPushButton("Run")
        run_btn.setToolTip("Execute the command in the selected shell")
        run_row.addWidget(parse_btn)
        run_row.addWidget(copy_btn)
        run_row.addWidget(run_btn)
        pv_layout.addLayout(run_row)
        preview_box.setLayout(pv_layout)
        root.addWidget(preview_box)

        # Signals
        add_tab_btn.clicked.connect(lambda: self.add_step("new-tab"))
        add_pane_h_btn.clicked.connect(lambda: self.add_step("split-pane", "H"))
        add_pane_v_btn.clicked.connect(lambda: self.add_step("split-pane", "V"))
        remove_btn.clicked.connect(self.remove_selected)
        move_up_btn.clicked.connect(self.move_cmd_up)
        move_down_btn.clicked.connect(self.move_cmd_down)
        self.steps_list.currentItemChanged.connect(self.populate_editor_from_selection)
        self.shell_combo.currentIndexChanged.connect(self.refresh_preview)
        parse_btn.clicked.connect(self.parse_command)
        copy_btn.clicked.connect(self.copy_command)
        run_btn.clicked.connect(self.run_command)

        # Auto-apply: connect editor fields to auto_apply_step
        self.profile_combo.currentTextChanged.connect(self.auto_apply_step)
        self.scheme_combo.currentTextChanged.connect(self.auto_apply_step)
        self.title_edit.textChanged.connect(self.auto_apply_step)
        self.tab_color_edit.textChanged.connect(self.auto_apply_step)
        self.dir_edit.textChanged.connect(self.auto_apply_step)
        self.use_parent_dir_check.stateChanged.connect(self.auto_apply_step)
        self.cmdline_edit.textChanged.connect(self.auto_apply_step)
        self.pane_size_spin.valueChanged.connect(self.auto_apply_step)

        # Initial state: hide pane size
        self.pane_size_label.setVisible(False)
        self.pane_size_spin.setVisible(False)

        self.refresh_preview()

    def setupFoldersTab(self):
        """Setup the folders/new tab menu management tab"""
        main_layout = QtWidgets.QHBoxLayout(self.foldersTab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left side - Folder tree
        left_widget = QtWidgets.QWidget()
        left_widget.setMinimumWidth(350)
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        folders_label = QtWidgets.QLabel("New Tab Menu Structure:")
        folders_label.setFont(QtGui.QFont("", 10, QtGui.QFont.Weight.Bold))
        left_layout.addWidget(folders_label)

        self.foldersTreeWidget = DragDropTreeWidget()
        self.foldersTreeWidget._ui = self
        self.foldersTreeWidget.setHeaderLabels(["Item", "Type"])
        self.foldersTreeWidget.setMinimumHeight(400)

        # Restore column widths from settings
        self.restoreTreeColumnWidths()

        left_layout.addWidget(self.foldersTreeWidget)

        # Folder control buttons
        folder_buttons_layout = QtWidgets.QVBoxLayout()

        # Row 1: Add Folder, Add Separator
        row1_layout = QtWidgets.QHBoxLayout()
        self.addFolderButton = QtWidgets.QPushButton("Add Folder")
        self.addSeparatorButton = QtWidgets.QPushButton("Add Separator")
        row1_layout.addWidget(self.addFolderButton)
        row1_layout.addWidget(self.addSeparatorButton)
        folder_buttons_layout.addLayout(row1_layout)

        # Row 2: Move Profile (stretched)
        self.addProfileToMenuButton = QtWidgets.QPushButton("Move Profile")
        folder_buttons_layout.addWidget(self.addProfileToMenuButton)

        # Separator line
        separator1 = QtWidgets.QFrame()
        separator1.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        folder_buttons_layout.addWidget(separator1)

        # Row 3: Move Up, Move Down
        row3_layout = QtWidgets.QHBoxLayout()
        self.moveFolderUpButton = QtWidgets.QPushButton("Move Up")
        self.moveFolderDownButton = QtWidgets.QPushButton("Move Down")
        row3_layout.addWidget(self.moveFolderUpButton)
        row3_layout.addWidget(self.moveFolderDownButton)
        folder_buttons_layout.addLayout(row3_layout)

        # Separator line
        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        folder_buttons_layout.addWidget(separator2)

        # Row 4: Delete Item (centered, different color)
        delete_layout = QtWidgets.QHBoxLayout()
        delete_layout.addStretch()
        self.deleteFolderButton = QtWidgets.QPushButton("Delete Item")
        self.deleteFolderButton.setStyleSheet("QPushButton { background-color: #d45b5b; color: #ffffff; } QPushButton:hover { background-color: #c34a4a; }")
        delete_layout.addWidget(self.deleteFolderButton)
        delete_layout.addStretch()
        folder_buttons_layout.addLayout(delete_layout)

        left_layout.addLayout(folder_buttons_layout)
        main_layout.addWidget(left_widget)

        # Right side - Folder/Item details
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        # Item details group
        details_group = QtWidgets.QGroupBox("Item Details")
        details_layout = QtWidgets.QFormLayout(details_group)
        details_layout.setSpacing(10)

        # Item type
        self.itemTypeLabel = QtWidgets.QLabel("")
        self.itemTypeLabel.setStyleSheet("QLabel { font-weight: bold; }")
        details_layout.addRow("Item Type:", self.itemTypeLabel)

        # Folder name
        self.folderNameEdit = QtWidgets.QLineEdit()
        self.folderNameEdit.setPlaceholderText("Enter folder name")
        details_layout.addRow("Folder Name:", self.folderNameEdit)

        # Folder icon
        folder_icon_layout = QtWidgets.QHBoxLayout()
        self.folderIconEdit = QtWidgets.QLineEdit()
        self.folderIconEdit.setPlaceholderText("Path to icon")
        self.folderIconBrowseButton = QtWidgets.QPushButton("Browse...")
        self.folderIconBrowseButton.clicked.connect(self.browseFolderIcon)
        folder_icon_layout.addWidget(self.folderIconEdit)
        folder_icon_layout.addWidget(self.folderIconBrowseButton)
        details_layout.addRow("Folder Icon:", folder_icon_layout)

        # Profile selection (for profile entries)
        self.menuProfileCombo = QtWidgets.QComboBox()
        self.menuProfileCombo.addItems([""] + profiles_list)
        details_layout.addRow("Profile:", self.menuProfileCombo)

        # Profile icon
        profile_icon_layout = QtWidgets.QHBoxLayout()
        self.profileIconEdit = QtWidgets.QLineEdit()
        self.profileIconEdit.setPlaceholderText("Path to icon (optional)")
        self.profileIconBrowseButton = QtWidgets.QPushButton("Browse...")
        self.profileIconBrowseButton.clicked.connect(self.browseProfileIcon)
        profile_icon_layout.addWidget(self.profileIconEdit)
        profile_icon_layout.addWidget(self.profileIconBrowseButton)
        details_layout.addRow("Profile Icon:", profile_icon_layout)

        # Folder options
        self.allowEmptyCheckBox = QtWidgets.QCheckBox("Allow Empty (show even if no entries)")
        self.inlineCheckBox = QtWidgets.QCheckBox("Inline (don't create nested menu if single entry)")
        details_layout.addRow("", self.allowEmptyCheckBox)
        details_layout.addRow("", self.inlineCheckBox)

        # Update Item button
        update_button_layout = QtWidgets.QHBoxLayout()
        self.updateFolderButton = QtWidgets.QPushButton("Update Item")
        self.updateFolderButton.setMinimumHeight(35)
        update_button_layout.addStretch()
        update_button_layout.addWidget(self.updateFolderButton)
        update_button_layout.addStretch()
        details_layout.addRow("", update_button_layout)

        right_layout.addWidget(details_group)

        # Help section
        help_group = QtWidgets.QGroupBox("Folder Management Help")
        help_layout = QtWidgets.QVBoxLayout(help_group)

        help_label = QtWidgets.QLabel("""New Tab Menu Structure:
📁 Folder: Organizes profiles in a dropdown submenu
👤 Profile: A specific profile entry
➖ Separator: Visual divider between items

Folder Options:
• Allow Empty: Show folder even if it contains no profiles
• Inline: If folder has only one item, show it directly (no submenu)

Tips:
• Drag items to reorder them within their parent
• Folders can contain profiles, separators, or other folders
• Use separators to group related profiles visually""")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("QLabel { background-color: #ede8f5; color: #5c5470; padding: 10px; border: 1px solid #c8bfe0; border-radius: 4px; }")

        help_layout.addWidget(help_label)
        right_layout.addWidget(help_group)

        main_layout.addWidget(right_widget)

        # Load folders
        self.loadFolders()

        # Connect folder signals
        self.foldersTreeWidget.currentItemChanged.connect(self.onFolderSelectionChanged)
        self.foldersTreeWidget.header().sectionResized.connect(self.saveTreeColumnWidths)
        self.addFolderButton.clicked.connect(self.addFolder)
        self.addProfileToMenuButton.clicked.connect(self.addProfileToMenu)
        self.addSeparatorButton.clicked.connect(self.addSeparator)
        self.updateFolderButton.clicked.connect(self.updateFolderItem)
        self.deleteFolderButton.clicked.connect(self.deleteFolderItem)
        self.moveFolderUpButton.clicked.connect(self.moveFolderItemUp)
        self.moveFolderDownButton.clicked.connect(self.moveFolderItemDown)

    # ========== Profile Tab Methods ==========

    def _pickColorInto(self, line_edit):
        """Open color dialog and put result into a QLineEdit"""
        col = QtWidgets.QColorDialog.getColor()
        if col.isValid():
            line_edit.setText(col.name())

    def _setProfileField(self, key, value, sub_key=None):
        """Set a profile field value. If value is empty/None/False-ish, remove the key."""
        idx = self.getCurrentIndex()
        if idx < 0:
            return
        profile = data_schemes['profiles']['list'][idx]
        if sub_key:
            if value:
                if key not in profile:
                    profile[key] = {}
                profile[key][sub_key] = value
            else:
                if key in profile and sub_key in profile[key]:
                    del profile[key][sub_key]
                    if not profile[key]:
                        del profile[key]
        else:
            if value is not None and value != '':
                profile[key] = value
            else:
                profile.pop(key, None)
        self.setUnsavedChanges()

    def setUnsavedChanges(self):
        self.unsaved_changes = True
        self.statusLabel.setText("Unsaved changes - Click Save to apply")
        self.statusLabel.setStyleSheet("QLabel { color: #fab387; font-weight: bold; }")

    def getCurrentIndex(self):
        if self.listWidget.currentItem():
            currentProfile = self.listWidget.currentItem().text()
            for i, dic in enumerate(data_schemes.get('profiles', {}).get('list', [])):
                if dic.get("name") == currentProfile:
                    return i
        return -1

    def changeDefault(self):
        currentProfile = self.listWidget.currentItem().text()
        for item in data_schemes.get('profiles', {}).get('list', []):
            if item.get('name') == currentProfile:
                data_schemes['defaultProfile'] = item.get('guid')
                self.setUnsavedChanges()
                break

    def changeScheme(self, param):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['colorScheme'] = self.comboBox.itemText(param)
            self.setUnsavedChanges()

    def changeFontSize(self, param):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            profile = data_schemes['profiles']['list'][currentProfileIndex]
            if 'font' not in profile:
                profile['font'] = {}
            profile['font']['size'] = param
            # Remove deprecated key if present
            profile.pop('fontSize', None)
            self.setUnsavedChanges()

    def changeFont(self, param):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            profile = data_schemes['profiles']['list'][currentProfileIndex]
            if 'font' not in profile:
                profile['font'] = {}
            profile['font']['face'] = self.fontBox.itemText(param)
            # Remove deprecated key if present
            profile.pop('fontFace', None)
            self.setUnsavedChanges()

    def changeBgImageOpacity(self):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            sliderValue = self.horizontalSlider.value()
            opacity = sliderValue / 10
            data_schemes["profiles"]["list"][currentProfileIndex]["backgroundImageOpacity"] = opacity
            self.bgOpacityLabel.setText(str(opacity))
            self.setUnsavedChanges()

    def changeBackgroundImage(self):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            getFile = QtWidgets.QFileDialog.getOpenFileName(None, 'Open File', '', 'Images (*.png *.jpg *.jpeg *.gif *.bmp)')
            filename = getFile[0]
            if filename:
                filename = filename.replace(r"/", "\\")
                data_schemes['profiles']['list'][currentProfileIndex]['backgroundImage'] = filename
                self.backgroundImageEdit.setText(filename)
                self.setUnsavedChanges()

    def changeCommandLine(self, text):
        if not self.ui_initialized:
            return
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            if text:
                data_schemes['profiles']['list'][currentProfileIndex]['commandline'] = text
            elif 'commandline' in data_schemes['profiles']['list'][currentProfileIndex]:
                del data_schemes['profiles']['list'][currentProfileIndex]['commandline']
            self.setUnsavedChanges()

    def changeStartingDirectory(self, text):
        if not self.ui_initialized:
            return
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            if text:
                data_schemes['profiles']['list'][currentProfileIndex]['startingDirectory'] = text
            elif 'startingDirectory' in data_schemes['profiles']['list'][currentProfileIndex]:
                del data_schemes['profiles']['list'][currentProfileIndex]['startingDirectory']
            self.setUnsavedChanges()

    def changeTabTitle(self, text):
        if not self.ui_initialized:
            return
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            if text:
                data_schemes['profiles']['list'][currentProfileIndex]['tabTitle'] = text
            elif 'tabTitle' in data_schemes['profiles']['list'][currentProfileIndex]:
                del data_schemes['profiles']['list'][currentProfileIndex]['tabTitle']
            self.setUnsavedChanges()

    def changeTabColor(self, text):
        if not self.ui_initialized:
            return
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            if text:
                data_schemes['profiles']['list'][currentProfileIndex]['tabColor'] = text
            elif 'tabColor' in data_schemes['profiles']['list'][currentProfileIndex]:
                del data_schemes['profiles']['list'][currentProfileIndex]['tabColor']
            self.setUnsavedChanges()

    def changeIcon(self, text):
        if not self.ui_initialized:
            return
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            if text:
                data_schemes['profiles']['list'][currentProfileIndex]['icon'] = text
            elif 'icon' in data_schemes['profiles']['list'][currentProfileIndex]:
                del data_schemes['profiles']['list'][currentProfileIndex]['icon']
            self.setUnsavedChanges()

    def changePadding(self, text):
        if not self.ui_initialized:
            return
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            if text:
                data_schemes['profiles']['list'][currentProfileIndex]['padding'] = text
            elif 'padding' in data_schemes['profiles']['list'][currentProfileIndex]:
                del data_schemes['profiles']['list'][currentProfileIndex]['padding']
            self.setUnsavedChanges()

    def changeCursorShape(self, text):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['cursorShape'] = text
            self.setUnsavedChanges()

    def changeScrollbarState(self, text):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['scrollbarState'] = text
            self.setUnsavedChanges()

    def changeRunAsAdmin(self, state):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['elevate'] = (state == QtCore.Qt.CheckState.Checked.value)
            self.setUnsavedChanges()

    def changeUseAcrylic(self, state):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['useAcrylic'] = (state == QtCore.Qt.CheckState.Checked.value)
            self.setUnsavedChanges()

    def changeHidden(self, state):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['hidden'] = (state == QtCore.Qt.CheckState.Checked.value)
            self.setUnsavedChanges()

    def changeSnapOnInput(self, state):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['snapOnInput'] = (state == QtCore.Qt.CheckState.Checked.value)
            self.setUnsavedChanges()

    def changeFontWeight(self, text):
        self._setProfileField('font', text if text != 'normal' else None, 'weight')

    def changeSuppressTitle(self, state):
        val = state == QtCore.Qt.CheckState.Checked.value
        self._setProfileField('suppressApplicationTitle', val if val else None)

    def changeForeground(self, text):
        if not self.ui_initialized:
            return
        self._setProfileField('foreground', text.strip() if text.strip() else None)

    def changeBackgroundColor(self, text):
        if not self.ui_initialized:
            return
        self._setProfileField('background', text.strip() if text.strip() else None)

    def changeSelectionBackground(self, text):
        if not self.ui_initialized:
            return
        self._setProfileField('selectionBackground', text.strip() if text.strip() else None)

    def changeCursorColor(self, text):
        if not self.ui_initialized:
            return
        self._setProfileField('cursorColor', text.strip() if text.strip() else None)

    def changeOpacity(self):
        idx = self.getCurrentIndex()
        if idx >= 0:
            val = self.opacitySlider.value()
            self.opacityValueLabel.setText(str(val))
            data_schemes['profiles']['list'][idx]['opacity'] = val
            self.setUnsavedChanges()

    def changeIntenseText(self, text):
        self._setProfileField('intenseTextStyle', text if text != 'all' else None)

    def changeBgStretchMode(self, text):
        self._setProfileField('backgroundImageStretchMode', text if text != 'uniformToFill' else None)

    def changeBgAlignment(self, text):
        self._setProfileField('backgroundImageAlignment', text if text != 'center' else None)

    def changeHistorySize(self, value):
        if not self.ui_initialized:
            return
        self._setProfileField('historySize', value if value != 9001 else None)

    def changeCloseOnExit(self, text):
        self._setProfileField('closeOnExit', text if text != 'graceful' else None)

    def changeBellStyle(self, text):
        self._setProfileField('bellStyle', text if text != 'audible' else None)

    def changeAntialiasing(self, text):
        self._setProfileField('antialiasingMode', text if text != 'grayscale' else None)

    def changeRetroEffect(self, state):
        val = state == QtCore.Qt.CheckState.Checked.value
        self._setProfileField('experimental.retroTerminalEffect', val if val else None)

    def changeAltGr(self, state):
        val = state == QtCore.Qt.CheckState.Checked.value
        # altGrAliasing defaults to True, only write if False
        self._setProfileField('altGrAliasing', False if not val else None)

    def changedProfile(self):
        if not self.ui_initialized:
            return

        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex < 0:
            return

        profile = data_schemes['profiles']['list'][currentProfileIndex]

        # Temporarily disable ui_initialized to prevent triggering change events
        self.ui_initialized = False

        # Update profile name
        self.profileNameEdit.setText(profile.get('name', ''))

        # Update color scheme
        colorScheme = profile.get('colorScheme', 'Campbell')
        index = self.comboBox.findText(colorScheme, QtCore.Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.comboBox.setCurrentIndex(index)

        # Update font - support both modern (font.face) and deprecated (fontFace)
        font_obj = profile.get('font', {})
        fontFace = font_obj.get('face') if isinstance(font_obj, dict) else None
        if not fontFace:
            fontFace = profile.get('fontFace', 'Cascadia Mono')
        index_fontBox = self.fontBox.findText(fontFace, QtCore.Qt.MatchFlag.MatchFixedString)
        if index_fontBox >= 0:
            self.fontBox.setCurrentIndex(index_fontBox)

        # Update font size - support both modern (font.size) and deprecated (fontSize)
        fontSize = font_obj.get('size') if isinstance(font_obj, dict) else None
        if fontSize is None:
            fontSize = profile.get('fontSize', 12)
        self.fontSize.setValue(fontSize)

        # General fields
        self.commandLineEdit.setText(profile.get('commandline', ''))
        self.startingDirectoryEdit.setText(profile.get('startingDirectory', ''))
        self.tabTitleEdit.setText(profile.get('tabTitle', ''))
        self.tabColorEdit.setText(profile.get('tabColor', ''))
        self.iconEdit.setText(profile.get('icon', ''))
        self.hiddenCheckBox.setChecked(profile.get('hidden', False))
        self.runAsAdminCheckBox.setChecked(profile.get('elevate', False))
        self.suppressTitleCheckBox.setChecked(profile.get('suppressApplicationTitle', False))

        # Appearance fields
        # Font weight
        fontWeight = font_obj.get('weight', 'normal') if isinstance(font_obj, dict) else 'normal'
        idx_w = self.fontWeightBox.findText(str(fontWeight), QtCore.Qt.MatchFlag.MatchFixedString)
        if idx_w >= 0:
            self.fontWeightBox.setCurrentIndex(idx_w)
        else:
            self.fontWeightBox.setCurrentIndex(0)

        # Cursor
        cursorShape = profile.get('cursorShape', 'bar')
        index = self.cursorShapeBox.findText(cursorShape, QtCore.Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.cursorShapeBox.setCurrentIndex(index)
        self.cursorColorEdit.setText(profile.get('cursorColor', ''))

        # Color overrides
        self.foregroundEdit.setText(profile.get('foreground', ''))
        self.backgroundColorEdit.setText(profile.get('background', ''))
        self.selectionBackgroundEdit.setText(profile.get('selectionBackground', ''))

        # Opacity (window transparency, 0-100)
        self.opacitySlider.setValue(profile.get('opacity', 100))
        self.opacityValueLabel.setText(str(profile.get('opacity', 100)))
        self.useAcrylicCheckBox.setChecked(profile.get('useAcrylic', False))

        # Intense text
        intenseText = profile.get('intenseTextStyle', 'all')
        idx_it = self.intenseTextBox.findText(intenseText, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx_it >= 0:
            self.intenseTextBox.setCurrentIndex(idx_it)

        # Background image
        self.backgroundImageEdit.setText(profile.get('backgroundImage', ''))
        bgOpacity = profile.get('backgroundImageOpacity', 1.0)
        self.horizontalSlider.setValue(int(bgOpacity * 10))
        self.bgOpacityLabel.setText(str(bgOpacity))

        bgStretch = profile.get('backgroundImageStretchMode', 'uniformToFill')
        idx_s = self.bgStretchBox.findText(bgStretch, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx_s >= 0:
            self.bgStretchBox.setCurrentIndex(idx_s)

        bgAlign = profile.get('backgroundImageAlignment', 'center')
        idx_a = self.bgAlignBox.findText(bgAlign, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx_a >= 0:
            self.bgAlignBox.setCurrentIndex(idx_a)

        # Advanced fields
        self.historySizeSpinBox.setValue(profile.get('historySize', 9001))

        closeOnExit = profile.get('closeOnExit', 'graceful')
        idx_c = self.closeOnExitBox.findText(str(closeOnExit), QtCore.Qt.MatchFlag.MatchFixedString)
        if idx_c >= 0:
            self.closeOnExitBox.setCurrentIndex(idx_c)

        bellStyle = profile.get('bellStyle', 'audible')
        idx_b = self.bellStyleBox.findText(bellStyle, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx_b >= 0:
            self.bellStyleBox.setCurrentIndex(idx_b)

        antialiasing = profile.get('antialiasingMode', 'grayscale')
        idx_aa = self.antialiasingBox.findText(antialiasing, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx_aa >= 0:
            self.antialiasingBox.setCurrentIndex(idx_aa)

        scrollbarState = profile.get('scrollbarState', 'visible')
        index = self.scrollbarBox.findText(scrollbarState, QtCore.Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.scrollbarBox.setCurrentIndex(index)

        self.paddingEdit.setText(profile.get('padding', ''))
        self.snapOnInputCheckBox.setChecked(profile.get('snapOnInput', True))
        self.retroEffectCheckBox.setChecked(profile.get('experimental.retroTerminalEffect', False))
        self.altGrCheckBox.setChecked(profile.get('altGrAliasing', True))

        # Re-enable ui_initialized
        self.ui_initialized = True

    def moveProfileUp(self):
        currentRow = self.listWidget.currentRow()
        if currentRow > 0:
            self.listWidget.insertItem(currentRow - 1, self.listWidget.takeItem(currentRow))
            self.listWidget.setCurrentRow(currentRow - 1)
            self.updateProfileOrder()

    def moveProfileDown(self):
        currentRow = self.listWidget.currentRow()
        if currentRow < self.listWidget.count() - 1:
            self.listWidget.insertItem(currentRow + 1, self.listWidget.takeItem(currentRow))
            self.listWidget.setCurrentRow(currentRow + 1)
            self.updateProfileOrder()

    def updateProfileOrder(self):
        new_order = [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        profiles = data_schemes['profiles']['list']
        # Build name->list of profiles mapping to handle duplicate names
        name_to_profiles = {}
        for profile in profiles:
            name = profile.get('name', '')
            if name not in name_to_profiles:
                name_to_profiles[name] = []
            name_to_profiles[name].append(profile)
        updated_profiles = []
        for name in new_order:
            if name in name_to_profiles and name_to_profiles[name]:
                updated_profiles.append(name_to_profiles[name].pop(0))
        data_schemes['profiles']['list'] = updated_profiles
        self.setUnsavedChanges()

    def renameProfile(self):
        currentRow = self.listWidget.currentRow()
        if currentRow >= 0:
            currentItem = self.listWidget.currentItem()
            newName, ok = QtWidgets.QInputDialog.getText(None, "Rename Profile", "New Name:",
                                                          QtWidgets.QLineEdit.EchoMode.Normal, currentItem.text())
            if ok and newName.strip():
                currentItem.setText(newName.strip())
                data_schemes['profiles']['list'][currentRow]['name'] = newName.strip()
                self.profileNameEdit.setText(newName.strip())
                self.setUnsavedChanges()

    def browseIcon(self):
        """Browse for icon file"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Icon", "",
            "Icon Files (*.ico *.png *.jpg *.svg);;All Files (*.*)"
        )
        if filename:
            filename = filename.replace("/", "\\")
            self.iconEdit.setText(filename)

    def createNewProfile(self):
        """Create a new profile"""
        import uuid

        # Ask for profile name
        newName, ok = QtWidgets.QInputDialog.getText(
            None, "New Profile", "Enter profile name:",
            QtWidgets.QLineEdit.EchoMode.Normal, "New Profile"
        )

        if not ok or not newName.strip():
            return

        # Generate new GUID
        new_guid = "{" + str(uuid.uuid4()) + "}"

        # Create new profile based on default profile structure
        new_profile = {
            "guid": new_guid,
            "name": newName.strip(),
            "commandline": "powershell.exe",
            "hidden": False
        }

        # Add to profiles list
        if 'profiles' not in data_schemes:
            data_schemes['profiles'] = {'list': []}
        if 'list' not in data_schemes['profiles']:
            data_schemes['profiles']['list'] = []

        data_schemes['profiles']['list'].append(new_profile)

        # Update UI
        self.listWidget.addItem(newName.strip())
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)
        self.setUnsavedChanges()

        # Update global profiles_list
        global profiles_list
        profiles_list.append(newName.strip())

        QtWidgets.QMessageBox.information(
            None, "Profile Created",
            f"New profile '{newName.strip()}' created successfully."
        )

    def duplicateProfile(self):
        """Duplicate the selected profile"""
        import uuid
        import copy

        currentRow = self.listWidget.currentRow()
        if currentRow < 0:
            QtWidgets.QMessageBox.warning(
                None, "No Selection",
                "Please select a profile to duplicate."
            )
            return

        # Get current profile
        current_profile = data_schemes['profiles']['list'][currentRow]
        currentName = current_profile.get('name', 'Profile')

        # Ask for new name
        newName, ok = QtWidgets.QInputDialog.getText(
            None, "Duplicate Profile",
            "Enter name for duplicated profile:",
            QtWidgets.QLineEdit.EchoMode.Normal,
            f"{currentName} (Copy)"
        )

        if not ok or not newName.strip():
            return

        # Create deep copy of profile
        new_profile = copy.deepcopy(current_profile)

        # Update name and generate new GUID
        new_profile['name'] = newName.strip()
        new_profile['guid'] = "{" + str(uuid.uuid4()) + "}"

        # Add to profiles list
        data_schemes['profiles']['list'].append(new_profile)

        # Update UI
        self.listWidget.addItem(newName.strip())
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)
        self.setUnsavedChanges()

        # Update global profiles_list
        global profiles_list
        profiles_list.append(newName.strip())

        QtWidgets.QMessageBox.information(
            None, "Profile Duplicated",
            f"Profile duplicated as '{newName.strip()}'."
        )

    def deleteProfile(self):
        """Delete the selected profile"""
        currentRow = self.listWidget.currentRow()
        if currentRow < 0:
            QtWidgets.QMessageBox.warning(
                None, "No Selection",
                "Please select a profile to delete."
            )
            return

        current_profile = data_schemes['profiles']['list'][currentRow]
        currentName = current_profile.get('name', 'Profile')
        currentGuid = current_profile.get('guid', '')

        # Check if this is the default profile
        if currentGuid == data_schemes.get('defaultProfile', ''):
            QtWidgets.QMessageBox.warning(
                None, "Cannot Delete",
                "Cannot delete the default profile. Please set another profile as default first."
            )
            return

        # Confirm deletion
        reply = QtWidgets.QMessageBox.question(
            None, "Delete Profile",
            f"Are you sure you want to delete profile '{currentName}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Remove from data
        del data_schemes['profiles']['list'][currentRow]

        # Remove from UI
        self.listWidget.takeItem(currentRow)

        # Update global profiles_list
        global profiles_list
        if currentName in profiles_list:
            profiles_list.remove(currentName)

        self.setUnsavedChanges()

        QtWidgets.QMessageBox.information(
            None, "Profile Deleted",
            f"Profile '{currentName}' deleted successfully."
        )

    # ========== Actions Tab Methods ==========

    def loadActions(self):
        self.actionsTable.setSortingEnabled(False)  # Disable during population
        self.actionsTable.setRowCount(0)
        actions = data_schemes.get('actions', [])
        keybindings = data_schemes.get('keybindings', [])

        # Create a mapping of action IDs to their key bindings
        id_to_keys = {}
        for binding in keybindings:
            action_id = binding.get('id')
            keys = binding.get('keys')
            if action_id and keys:
                if action_id not in id_to_keys:
                    id_to_keys[action_id] = []
                id_to_keys[action_id].append(keys)
            elif action_id is None and keys:
                if 'UNBOUND_KEYS' not in id_to_keys:
                    id_to_keys['UNBOUND_KEYS'] = []
                id_to_keys['UNBOUND_KEYS'].append(keys)

        grey = QtGui.QColor('#9590a8')

        # Display actions with their associated key bindings
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                continue
            action_id = action.get('id', '')
            name = action.get('name', '')
            command = action.get('command', '')

            # Get command string for display
            command_str = ''
            if isinstance(command, dict):
                command_str = command.get('action', '')
                if not command_str:
                    command_str = list(command.keys())[0] if command else 'unknown'
            elif isinstance(command, str):
                command_str = command
            else:
                command_str = str(command) if command else ''

            # Get associated key bindings
            associated_keys = id_to_keys.get(action_id, [])
            keys_display = ', '.join(associated_keys) if associated_keys else ''

            row = self.actionsTable.rowCount()
            self.actionsTable.insertRow(row)

            shortcut_item = QtWidgets.QTableWidgetItem(keys_display)
            name_item = QtWidgets.QTableWidgetItem(name or action_id)
            command_item = QtWidgets.QTableWidgetItem(command_str)
            id_item = QtWidgets.QTableWidgetItem(action_id)

            # Store row type: 'action' and its index in data_schemes['actions']
            shortcut_item.setData(QtCore.Qt.ItemDataRole.UserRole, ('action', i))

            if not keys_display:
                for item in (shortcut_item, name_item, command_item, id_item):
                    item.setForeground(grey)

            self.actionsTable.setItem(row, 0, shortcut_item)
            self.actionsTable.setItem(row, 1, name_item)
            self.actionsTable.setItem(row, 2, command_item)
            self.actionsTable.setItem(row, 3, id_item)

        # Show unbound key bindings (keys with id: null)
        unbound_keys = id_to_keys.get('UNBOUND_KEYS', [])
        for ui, key in enumerate(unbound_keys):
            row = self.actionsTable.rowCount()
            self.actionsTable.insertRow(row)

            shortcut_item = QtWidgets.QTableWidgetItem(key)
            name_item = QtWidgets.QTableWidgetItem('DISABLED/UNBOUND')
            command_item = QtWidgets.QTableWidgetItem('null')
            id_item = QtWidgets.QTableWidgetItem('')

            shortcut_item.setData(QtCore.Qt.ItemDataRole.UserRole, ('unbound', ui))

            strike_font = QtGui.QFont()
            strike_font.setStrikeOut(True)
            for item in (shortcut_item, name_item, command_item, id_item):
                item.setForeground(grey)
                item.setFont(strike_font)

            self.actionsTable.setItem(row, 0, shortcut_item)
            self.actionsTable.setItem(row, 1, name_item)
            self.actionsTable.setItem(row, 2, command_item)
            self.actionsTable.setItem(row, 3, id_item)

        self.actionsTable.setSortingEnabled(True)  # Re-enable after population

    def _getActionRowMeta(self, row: int):
        """Return (row_type, data_index) tuple stored in the table row, or (None, -1)."""
        if row < 0 or row >= self.actionsTable.rowCount():
            return (None, -1)
        item = self.actionsTable.item(row, 0)
        if item is None:
            return (None, -1)
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        return data if data else (None, -1)

    def onActionTableSelectionChanged(self, currentRow, currentCol, prevRow, prevCol):
        row_type, data_idx = self._getActionRowMeta(currentRow)

        # Clear fields first
        self.actionNameEdit.clear()
        self.commandActionCombo.setCurrentText('')
        self.keysEdit.clear()
        self.actionArgsEdit.clear()
        self.iconPathEdit.clear()
        self.actionIdEdit.clear()

        if row_type == 'unbound':
            # Unbound key entry
            keybindings = data_schemes.get('keybindings', [])
            unbound_bindings = [b for b in keybindings if b.get('id') is None]
            if data_idx < len(unbound_bindings):
                self.keysEdit.setText(unbound_bindings[data_idx].get('keys', ''))
                self.actionNameEdit.setText("DISABLED/UNBOUND")
                self.commandActionCombo.setCurrentText("null")
            return

        if row_type == 'action':
            actions = data_schemes.get('actions', [])
            keybindings = data_schemes.get('keybindings', [])
            if data_idx < 0 or data_idx >= len(actions):
                return
            action = actions[data_idx]

            action_id = action.get('id', '')
            self.actionIdEdit.setText(action_id)
            self.actionNameEdit.setText(action.get('name', ''))

            # Find associated key bindings
            associated_keys = []
            for binding in keybindings:
                if binding.get('id') == action_id:
                    key = binding.get('keys', '')
                    if key:
                        associated_keys.append(key)
            self.keysEdit.setText(', '.join(associated_keys))

            # Populate command and arguments
            command = action.get('command', '')
            if isinstance(command, dict):
                command_action = command.get('action', '')
                if command_action:
                    self.commandActionCombo.setCurrentText(command_action)
                elif command:
                    self.commandActionCombo.setCurrentText(list(command.keys())[0])
                self.actionArgsEdit.setPlainText(commentjson.dumps(command, indent=2))
            elif isinstance(command, str):
                self.commandActionCombo.setCurrentText(command)
                self.actionArgsEdit.setPlainText('')
            else:
                self.commandActionCombo.setCurrentText(str(command) if command else '')
                if command and not isinstance(command, str):
                    self.actionArgsEdit.setPlainText(commentjson.dumps(command, indent=2))

            # Populate icon path
            self.iconPathEdit.setText(action.get('icon', ''))

    def filterActions(self, text: str):
        """Show/hide table rows based on filter text."""
        text = text.lower()
        for row in range(self.actionsTable.rowCount()):
            match = False
            if not text:
                match = True
            else:
                for col in range(self.actionsTable.columnCount()):
                    item = self.actionsTable.item(row, col)
                    if item and text in item.text().lower():
                        match = True
                        break
            self.actionsTable.setRowHidden(row, not match)

    def updateAction(self):
        current_row = self.actionsTable.currentRow()
        row_type, data_idx = self._getActionRowMeta(current_row)
        keybindings = data_schemes.get('keybindings', [])

        if row_type == 'unbound':
            # Handle unbound key modification
            unbound_bindings = [b for b in keybindings if b.get('id') is None]
            if data_idx < len(unbound_bindings):
                binding = unbound_bindings[data_idx]
                new_keys = self.keysEdit.text().strip()
                if new_keys:
                    binding['keys'] = new_keys
                else:
                    keybindings.remove(binding)
            self.loadActions()
            self.setUnsavedChanges()
            return

        if row_type == 'action':
            actions = data_schemes.get('actions', [])
            if data_idx < 0 or data_idx >= len(actions):
                return
            action = actions[data_idx]
            old_action_id = action.get('id', '')

            # Update action properties
            action['name'] = self.actionNameEdit.text().strip()
            new_action_id = self.actionIdEdit.text().strip()
            if new_action_id:
                action['id'] = new_action_id

            # Update command
            args_text = self.actionArgsEdit.toPlainText().strip()
            if args_text:
                try:
                    args = commentjson.loads(args_text)
                    action['command'] = args
                except:
                    simple_command = self.commandActionCombo.currentText().strip()
                    if simple_command:
                        action['command'] = simple_command
                    else:
                        action['command'] = args_text
            else:
                simple_command = self.commandActionCombo.currentText().strip()
                if simple_command:
                    action['command'] = simple_command
                else:
                    if 'command' in action:
                        del action['command']

            # Update icon
            icon_text = self.iconPathEdit.text().strip()
            if icon_text:
                action['icon'] = icon_text
            elif 'icon' in action:
                del action['icon']

            # Update key bindings - remove old bindings for this action ID
            if old_action_id:
                keybindings[:] = [b for b in keybindings if b.get('id') != old_action_id]

            # Add new key bindings
            keys_text = self.keysEdit.text().strip()
            if keys_text and new_action_id:
                key_list = [key.strip() for key in keys_text.split(',') if key.strip()]
                for key in key_list:
                    keybindings.append({'id': new_action_id, 'keys': key})

            self.loadActions()
            self.actionsTable.selectRow(current_row)
            self.setUnsavedChanges()

    def addAction(self):
        if 'actions' not in data_schemes:
            data_schemes['actions'] = []
        if 'keybindings' not in data_schemes:
            data_schemes['keybindings'] = []

        # Get values from form
        action_name = self.actionNameEdit.text().strip()
        action_id = self.actionIdEdit.text().strip()
        keys_text = self.keysEdit.text().strip()
        args_text = self.actionArgsEdit.toPlainText().strip()
        simple_command = self.commandActionCombo.currentText().strip()
        icon_text = self.iconPathEdit.text().strip()

        # Generate action ID if not provided
        if not action_id and (action_name or simple_command):
            import uuid
            base_name = action_name or simple_command
            # Create a user-friendly ID
            safe_name = ''.join(c for c in base_name if c.isalnum() or c in '._-')
            action_id = f"User.{safe_name}.{str(uuid.uuid4())[:8]}"

        if not action_id:
            QtWidgets.QMessageBox.warning(None, "Invalid Action",
                                        "Please provide an Action ID or Name.")
            return

        # Build new action
        new_action = {
            'id': action_id
        }

        # Add name if provided
        if action_name:
            new_action['name'] = action_name

        # Add command (prioritize JSON args over simple command)
        if args_text:
            try:
                # Try to parse as JSON for complex commands
                args = commentjson.loads(args_text)
                new_action['command'] = args
            except:
                # If JSON parsing fails, use simple command or raw text
                if simple_command:
                    new_action['command'] = simple_command
                else:
                    new_action['command'] = args_text
        elif simple_command:
            new_action['command'] = simple_command

        # Add icon if provided
        if icon_text:
            new_action['icon'] = icon_text

        # Add the action
        data_schemes['actions'].append(new_action)

        # Add key bindings if provided
        if keys_text:
            key_list = [key.strip() for key in keys_text.split(',') if key.strip()]
            for key in key_list:
                new_binding = {
                    'id': action_id,
                    'keys': key
                }
                data_schemes['keybindings'].append(new_binding)

        self.loadActions()
        # Select the newly added action (last action row before unbound keys)
        actions_count = len(data_schemes.get('actions', []))
        if actions_count > 0:
            self.actionsTable.selectRow(actions_count - 1)
        self.setUnsavedChanges()

    def deleteAction(self):
        current_row = self.actionsTable.currentRow()
        row_type, data_idx = self._getActionRowMeta(current_row)
        keybindings = data_schemes.get('keybindings', [])

        if row_type == 'unbound':
            unbound_bindings = [b for b in keybindings if b.get('id') is None]
            if data_idx < len(unbound_bindings):
                reply = QtWidgets.QMessageBox.question(None, 'Delete Unbound Key',
                                                     'Are you sure you want to delete this unbound key binding?',
                                                     QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    keybindings.remove(unbound_bindings[data_idx])
                    self.loadActions()
                    self.setUnsavedChanges()
                    self.clearActionFields()
            return

        if row_type == 'action':
            actions = data_schemes.get('actions', [])
            if data_idx < 0 or data_idx >= len(actions):
                return
            action = actions[data_idx]
            action_name = action.get('name', action.get('id', f'Action {data_idx + 1}'))
            reply = QtWidgets.QMessageBox.question(None, 'Delete Action',
                                                 f'Are you sure you want to delete "{action_name}" and all its key bindings?',
                                                 QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                action_id = action.get('id')
                del actions[data_idx]

                if action_id:
                    keybindings[:] = [b for b in keybindings if b.get('id') != action_id]

                self.loadActions()
                self.setUnsavedChanges()
                self.clearActionFields()

                # Select next available row
                if current_row < self.actionsTable.rowCount():
                    self.actionsTable.selectRow(current_row)
                elif self.actionsTable.rowCount() > 0:
                    self.actionsTable.selectRow(self.actionsTable.rowCount() - 1)

    def moveActionUp(self):
        current_row = self.actionsTable.currentRow()
        row_type, data_idx = self._getActionRowMeta(current_row)
        if row_type == 'action' and data_idx > 0:
            actions = data_schemes.get('actions', [])
            actions[data_idx], actions[data_idx - 1] = actions[data_idx - 1], actions[data_idx]
            self.loadActions()
            self.actionsTable.selectRow(current_row - 1)
            self.setUnsavedChanges()

    def moveActionDown(self):
        current_row = self.actionsTable.currentRow()
        row_type, data_idx = self._getActionRowMeta(current_row)
        if row_type == 'action':
            actions = data_schemes.get('actions', [])
            if data_idx >= 0 and data_idx < len(actions) - 1:
                actions[data_idx], actions[data_idx + 1] = actions[data_idx + 1], actions[data_idx]
                self.loadActions()
                self.actionsTable.selectRow(current_row + 1)
                self.setUnsavedChanges()

    def clearActionFields(self):
        """Helper method to clear all action input fields"""
        self.actionNameEdit.clear()
        self.actionIdEdit.clear()
        self.commandActionCombo.setCurrentText('')
        self.keysEdit.clear()
        self.actionArgsEdit.clear()
        self.iconPathEdit.clear()

    def recordShortcut(self):
        """Open key recorder dialog and populate the shortcut field."""
        dialog = KeyRecorderDialog()
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted and dialog.recorded_keys:
            recorded = dialog.recorded_keys
            # Check for conflicts with existing bindings
            keybindings = data_schemes.get('keybindings', [])
            conflicts = []
            for binding in keybindings:
                if binding.get('keys', '').lower() == recorded.lower():
                    action_id = binding.get('id', 'unknown')
                    conflicts.append(action_id)
            if conflicts:
                reply = QtWidgets.QMessageBox.warning(None, "Shortcut Conflict",
                    f"'{recorded}' is already bound to: {', '.join(conflicts)}\n\nUse it anyway?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                    return
            # Append to existing keys or set new
            existing = self.keysEdit.text().strip()
            if existing:
                self.keysEdit.setText(f"{existing}, {recorded}")
            else:
                self.keysEdit.setText(recorded)

    # ========== Command Builder Tab Methods ==========

    def pick_color(self):
        col = QtWidgets.QColorDialog.getColor()
        if col.isValid():
            self.tab_color_edit.setText(col.name())

    def browse_dir(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(None, "Select starting directory")
        if d:
            self.dir_edit.setText(d)

    def add_step(self, kind: str, orientation: str = ""):
        step = CommandStep(kind)
        step.split_orientation = orientation if kind == "split-pane" else ""
        item = QtWidgets.QListWidgetItem(self.describe_step(step))
        item.setData(QtCore.Qt.ItemDataRole.UserRole, step)
        self.steps_list.addItem(item)
        self.steps_list.setCurrentItem(item)
        self.refresh_preview()

    def remove_selected(self):
        row = self.steps_list.currentRow()
        if row >= 0:
            self.steps_list.takeItem(row)
            self.refresh_preview()

    def move_cmd_up(self):
        row = self.steps_list.currentRow()
        if row > 0:
            item = self.steps_list.takeItem(row)
            self.steps_list.insertItem(row - 1, item)
            self.steps_list.setCurrentItem(item)
            self.refresh_preview()

    def move_cmd_down(self):
        row = self.steps_list.currentRow()
        if row >= 0 and row < self.steps_list.count() - 1:
            item = self.steps_list.takeItem(row)
            self.steps_list.insertItem(row + 1, item)
            self.steps_list.setCurrentItem(item)
            self.refresh_preview()

    def describe_step(self, step: CommandStep) -> str:
        base = "new-tab" if step.kind == "new-tab" else f"split-pane{' -H' if step.split_orientation=='H' else (' -V' if step.split_orientation=='V' else '')}"
        attrs = []
        if step.profile_name:
            attrs.append(f'-p "{step.profile_name}"')
        if step.color_scheme:
            attrs.append(f'--colorScheme "{step.color_scheme}"')
        if step.tab_color:
            attrs.append(f"--tabColor '{step.tab_color}'")
        if step.use_parent_dir:
            attrs.append("--useParentProcessDirectory")
        elif step.starting_directory:
            attrs.append(f'-d "{step.starting_directory}"')
        if step.title:
            attrs.append(f'--title "{step.title}"')
        if step.pane_size is not None and step.kind == "split-pane":
            attrs.append(f"--size {step.pane_size}")
        if step.commandline:
            attrs.append(step.commandline)
        return f"{base} {' '.join(attrs)}".strip()

    def populate_editor_from_selection(self, current: Optional[QtWidgets.QListWidgetItem], prev: Optional[QtWidgets.QListWidgetItem]):
        if not current:
            return
        # Block auto-apply signals while populating
        self._populating_editor = True
        step: CommandStep = current.data(QtCore.Qt.ItemDataRole.UserRole)
        self.profile_combo.setCurrentText(step.profile_name or "")
        self.scheme_combo.setCurrentText(step.color_scheme or "")
        self.title_edit.setText(step.title or "")
        self.tab_color_edit.setText(step.tab_color or "")
        self.dir_edit.setText(step.starting_directory or "")
        self.use_parent_dir_check.setChecked(step.use_parent_dir)
        self.dir_edit.setEnabled(not step.use_parent_dir)
        self.cmdline_edit.setText(step.commandline or "")

        # Show/hide pane size based on step type
        is_split = step.kind == "split-pane"
        self.pane_size_label.setVisible(is_split)
        self.pane_size_spin.setVisible(is_split)
        if is_split and step.pane_size is not None:
            self.pane_size_spin.setValue(step.pane_size)
        else:
            self.pane_size_spin.setValue(0.5)
        self._populating_editor = False

    def auto_apply_step(self):
        """Auto-apply editor changes to the selected step (no Apply button needed)."""
        if getattr(self, '_populating_editor', False):
            return
        item = self.steps_list.currentItem()
        if not item:
            return
        step: CommandStep = item.data(QtCore.Qt.ItemDataRole.UserRole)
        step.profile_name = self.profile_combo.currentText().strip()
        step.color_scheme = self.scheme_combo.currentText().strip()
        step.title = self.title_edit.text().strip()
        step.tab_color = self.tab_color_edit.text().strip()
        step.use_parent_dir = self.use_parent_dir_check.isChecked()
        step.starting_directory = self.dir_edit.text().strip()
        # Disable directory field when use parent dir is checked
        self.dir_edit.setEnabled(not step.use_parent_dir)
        step.commandline = self.cmdline_edit.text().strip()
        if step.kind == "split-pane":
            val = self.pane_size_spin.value()
            step.pane_size = float(f"{val:.2f}")
        else:
            step.pane_size = None
        item.setText(self.describe_step(step))
        self.refresh_preview()

    def build_global_options(self) -> List[str]:
        opts = []
        # --size c,r
        c = self.global_size_cols.value()
        r = self.global_size_rows.value()
        if c > 0 or r > 0:
            if c > 0 and r > 0:
                opts.append(f"--size {c},{r}")
            elif c > 0:
                opts.append(f"--size {c},")
            elif r > 0:
                opts.append(f"--size ,{r}")
        # --pos x,y
        x = self.global_pos_x.value()
        y = self.global_pos_y.value()
        if x > 0 or y > 0:
            if x > 0 and y > 0:
                opts.append(f"--pos {x},{y}")
            elif x > 0:
                opts.append(f"--pos {x},")
            elif y > 0:
                opts.append(f"--pos ,{y}")
        # state
        if self.global_maximized.isChecked():
            opts.append("--maximized")
        if self.global_fullscreen.isChecked():
            opts.append("--fullscreen")
        if self.global_focus.isChecked():
            opts.append("--focus")
        # --window
        w = self.window_combo.currentText().strip()
        if w:
            opts.append(f"--window {w}")
        return opts

    def build_sequence(self) -> List[str]:
        seq = []
        for i in range(self.steps_list.count()):
            item = self.steps_list.item(i)
            step: CommandStep = item.data(QtCore.Qt.ItemDataRole.UserRole)
            seq.append(step.build())
        return seq

    def build_command(self) -> str:
        opts = self.build_global_options()
        seq = self.build_sequence()
        delimiter = ";"
        cmd_seq = f" {delimiter} ".join(seq) if seq else ""
        wt = "wt"
        if opts and cmd_seq:
            final = f"{wt} {' '.join(opts)} {cmd_seq}"
        elif opts:
            final = f"{wt} {' '.join(opts)}"
        elif cmd_seq:
            final = f"{wt} {cmd_seq}"
        else:
            final = wt
        # PowerShell needs `; escaping
        if self.shell_combo.currentIndex() == 0:
            final = final.replace(" ; ", " `; ")
        return final

    def refresh_preview(self):
        self.preview.setPlainText(self.build_command())

    def copy_command(self):
        QtWidgets.QApplication.clipboard().setText(self.build_command())
        QtWidgets.QMessageBox.information(None, "Copied", "Command copied to clipboard.")

    def run_command(self):
        cmd = self.build_command()
        try:
            if self.shell_combo.currentIndex() == 0:
                subprocess.Popen(["powershell", "-NoProfile", "-Command", cmd], shell=False)
            else:
                subprocess.Popen(["cmd.exe", "/c", cmd], shell=False)
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Run error", str(e))

    def parse_command(self):
        """Parse a command from the preview box and populate the builder"""
        import re

        cmd = self.preview.toPlainText().strip()
        if not cmd:
            QtWidgets.QMessageBox.warning(None, "Empty Command", "Please enter a command to parse.")
            return

        # Remove PowerShell backtick escapes
        cmd = cmd.replace(" `; ", " ; ")

        # Extract the command after 'wt'
        if cmd.startswith("wt "):
            cmd = cmd[3:].strip()
        elif cmd.startswith("wt.exe "):
            cmd = cmd[7:].strip()

        # Reset global options
        self.global_size_cols.setValue(0)
        self.global_size_rows.setValue(0)
        self.global_pos_x.setValue(0)
        self.global_pos_y.setValue(0)
        self.global_maximized.setChecked(False)
        self.global_fullscreen.setChecked(False)
        self.global_focus.setChecked(False)
        self.window_combo.setCurrentText("")

        # Parse global options - these come BEFORE any commands
        global_opts = ""
        remaining_cmd = cmd

        # Keep matching global options until we hit a command
        while remaining_cmd:
            matched = False

            # Try to match flags (no arguments)
            for flag in ['--maximized', '--fullscreen', '--focus']:
                if remaining_cmd.startswith(flag):
                    global_opts += flag + " "
                    remaining_cmd = remaining_cmd[len(flag):].strip()
                    matched = True
                    break

            # Try to match options with arguments
            if not matched:
                for opt in ['--size', '--pos', '--window']:
                    if remaining_cmd.startswith(opt):
                        # Find the argument
                        temp = remaining_cmd[len(opt):].strip()
                        # Extract argument (everything until next space)
                        match_arg = re.match(r'^([^\s]+)', temp)

                        if match_arg:
                            arg = match_arg.group(1)
                            global_opts += f"{opt} {arg} "
                            remaining_cmd = temp[len(arg):].strip()
                            matched = True
                            break

            # If we didn't match anything, we've reached the commands section
            if not matched:
                break

        cmd = remaining_cmd

        # Apply global options
        if '--size' in global_opts:
            size_match = re.search(r'--size\s+(\d*),(\d*)', global_opts)
            if size_match:
                if size_match.group(1):
                    self.global_size_cols.setValue(int(size_match.group(1)))
                if size_match.group(2):
                    self.global_size_rows.setValue(int(size_match.group(2)))

        if '--pos' in global_opts:
            pos_match = re.search(r'--pos\s+(\d*),(\d*)', global_opts)
            if pos_match:
                if pos_match.group(1):
                    self.global_pos_x.setValue(int(pos_match.group(1)))
                if pos_match.group(2):
                    self.global_pos_y.setValue(int(pos_match.group(2)))

        if '--maximized' in global_opts:
            self.global_maximized.setChecked(True)
        if '--fullscreen' in global_opts:
            self.global_fullscreen.setChecked(True)
        if '--focus' in global_opts:
            self.global_focus.setChecked(True)

        if '--window' in global_opts:
            window_match = re.search(r'--window\s+(\w+)', global_opts)
            if window_match:
                self.window_combo.setCurrentText(window_match.group(1))

        # Clear current steps
        self.steps_list.clear()

        # Split by semicolons to get individual commands
        commands = re.split(r'\s*;\s*', cmd)

        steps_parsed = 0
        for cmd_str in commands:
            if not cmd_str.strip():
                continue

            # Determine if it's new-tab or split-pane
            step = None
            if cmd_str.startswith('new-tab'):
                step = CommandStep('new-tab')
                cmd_str = cmd_str[7:].strip()
            elif cmd_str.startswith('split-pane'):
                step = CommandStep('split-pane')
                cmd_str = cmd_str[10:].strip()

                # Check for -H or -V
                if cmd_str.startswith('-H'):
                    step.split_orientation = 'H'
                    cmd_str = cmd_str[2:].strip()
                elif cmd_str.startswith('-V'):
                    step.split_orientation = 'V'
                    cmd_str = cmd_str[2:].strip()
            else:
                # Not a recognized command, skip it
                continue

            if not step:
                continue

            # Parse options for this step
            # Profile
            profile_match = re.search(r'-p\s+"([^"]+)"', cmd_str)
            if profile_match:
                step.profile_name = profile_match.group(1)

            # Starting directory / parent process directory
            if '--useParentProcessDirectory' in cmd_str:
                step.use_parent_dir = True
                cmd_str = cmd_str.replace('--useParentProcessDirectory', '').strip()
            else:
                dir_match = re.search(r'-d\s+"([^"]+)"', cmd_str)
                if dir_match:
                    step.starting_directory = dir_match.group(1)

            # Title
            title_match = re.search(r'--title\s+"([^"]+)"', cmd_str)
            if title_match:
                step.title = title_match.group(1)

            # Tab color (support both single and double quotes)
            color_match = re.search(r"--tabColor\s+'([^']+)'", cmd_str)
            if not color_match:
                color_match = re.search(r'--tabColor\s+"([^"]+)"', cmd_str)
            if color_match:
                step.tab_color = color_match.group(1)

            # Color scheme
            scheme_match = re.search(r'--colorScheme\s+"([^"]+)"', cmd_str)
            if scheme_match:
                step.color_scheme = scheme_match.group(1)

            # Pane size (for split-pane only)
            if step.kind == 'split-pane':
                size_match = re.search(r'--size\s+([\d.]+)', cmd_str)
                if size_match:
                    step.pane_size = float(size_match.group(1))

            # Remove all parsed options to find raw commandline
            temp_cmd = cmd_str
            for pattern in [r'-p\s+"[^"]+"', r'-d\s+"[^"]+"', r'--title\s+"[^"]+"',
                           r"--tabColor\s+'[^']+'", r'--tabColor\s+"[^"]+"',
                           r'--colorScheme\s+"[^"]+"', r'--size\s+[\d.]+',
                           r'--useParentProcessDirectory']:
                temp_cmd = re.sub(pattern, '', temp_cmd)

            # What's left should be the commandline
            remaining = temp_cmd.strip()
            if remaining:
                step.commandline = remaining

            # Add the step
            item = QtWidgets.QListWidgetItem(self.describe_step(step))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, step)
            self.steps_list.addItem(item)
            steps_parsed += 1

        # Refresh the preview
        self.refresh_preview()

        if steps_parsed > 0:
            QtWidgets.QMessageBox.information(None, "Command Parsed",
                                             f"Successfully parsed {steps_parsed} command step(s).")
        else:
            QtWidgets.QMessageBox.warning(None, "No Commands Found",
                                         "Could not find any valid new-tab or split-pane commands in the input.\n\n" +
                                         "Make sure your command starts with 'new-tab' or 'split-pane'.")

    # ========== Folders Tab Methods ==========

    def saveTreeColumnWidths(self):
        """Save tree column widths to QSettings"""
        settings = QtCore.QSettings("WTManager", "ColumnWidths")
        header = self.foldersTreeWidget.header()
        settings.setValue("column0", header.sectionSize(0))
        settings.setValue("column1", header.sectionSize(1))
        debug_print(f"DEBUG: Saved column widths: {header.sectionSize(0)}, {header.sectionSize(1)}")

    def restoreTreeColumnWidths(self):
        """Restore tree column widths from QSettings"""
        settings = QtCore.QSettings("WTManager", "ColumnWidths")
        header = self.foldersTreeWidget.header()

        # Default widths if not set
        col0_width = settings.value("column0", 250, type=int)
        col1_width = settings.value("column1", 100, type=int)

        header.resizeSection(0, col0_width)
        header.resizeSection(1, col1_width)
        debug_print(f"DEBUG: Restored column widths: {col0_width}, {col1_width}")

    def _getExpandedUids(self):
        """Collect UIDs of all currently expanded tree items."""
        expanded = set()
        def walk(parent_item):
            count = parent_item.childCount() if parent_item else self.foldersTreeWidget.topLevelItemCount()
            for i in range(count):
                item = parent_item.child(i) if parent_item else self.foldersTreeWidget.topLevelItem(i)
                if item.isExpanded():
                    entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if entry and entry.get(_UID_KEY):
                        expanded.add(entry[_UID_KEY])
                walk(item)
        walk(None)
        return expanded

    def _restoreExpandedUids(self, expanded_uids):
        """Re-expand tree items whose UIDs are in the set."""
        def walk(parent_item):
            count = parent_item.childCount() if parent_item else self.foldersTreeWidget.topLevelItemCount()
            for i in range(count):
                item = parent_item.child(i) if parent_item else self.foldersTreeWidget.topLevelItem(i)
                entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if entry and entry.get(_UID_KEY) in expanded_uids:
                    item.setExpanded(True)
                walk(item)
        walk(None)

    def loadFolders(self):
        """Load the newTabMenu structure into the tree widget"""
        debug_print(f"DEBUG loadFolders: Clearing tree and reloading from data_schemes")
        debug_print(f"DEBUG loadFolders: data_schemes has {len(data_schemes.get('newTabMenu', []))} root items")

        # Save expanded state before clearing
        expanded_uids = self._getExpandedUids()

        # Ensure all entries have UIDs
        stamp_uids(data_schemes.get('newTabMenu', []))

        self.foldersTreeWidget.clear()
        new_tab_menu = data_schemes.get('newTabMenu', [])

        for i, entry in enumerate(new_tab_menu):
            debug_print(f"DEBUG loadFolders: Adding item {i}: type={entry.get('type')}, name={entry.get('name', 'N/A')}")
            self.addTreeItem(entry, self.foldersTreeWidget)

        # Restore expanded state
        self._restoreExpandedUids(expanded_uids)

        debug_print(f"DEBUG loadFolders: Tree now has {self.foldersTreeWidget.topLevelItemCount()} top-level items")

        # Refresh profile menu indicators when folders change
        if self.ui_initialized:
            self.updateProfileMenuIndicators()

    def addTreeItem(self, entry: dict, parent):
        """Recursively add tree items for folders and profiles"""
        entry_type = entry.get('type', 'unknown')

        if entry_type == 'folder':
            name = entry.get('name', 'Unnamed Folder')
            debug_print(f"DEBUG addTreeItem: Creating folder item with name='{name}', entry_id={id(entry)}")
            item = QtWidgets.QTreeWidgetItem(parent, [name, "📁 Folder"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)

            # Add child entries
            num_children = len(entry.get('entries', []))
            debug_print(f"DEBUG addTreeItem: Folder '{name}' has {num_children} children")
            for child_entry in entry.get('entries', []):
                self.addTreeItem(child_entry, item)

        elif entry_type == 'profile':
            profile_guid = entry.get('profile', '')
            profile_name = self.getProfileNameByGuid(profile_guid)
            item = QtWidgets.QTreeWidgetItem(parent, [profile_name, "👤 Profile"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)

        elif entry_type == 'separator':
            item = QtWidgets.QTreeWidgetItem(parent, ["───────", "➖ Separator"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)

        elif entry_type == 'remainingProfiles':
            # Expand remainingProfiles to show actual unassigned profiles
            assigned_guids = self.getAssignedProfileGuids()
            unassigned = [p for p in data_schemes.get('profiles', {}).get('list', [])
                          if p.get('guid') and p.get('guid') not in assigned_guids]
            count = len(unassigned)

            item = QtWidgets.QTreeWidgetItem(parent,
                [f"Remaining Profiles ({count} auto-listed)", "📋 Auto"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)
            item.setForeground(0, QtGui.QBrush(QtGui.QColor("#8580a0")))
            item.setToolTip(0, "Profiles not explicitly in the menu. WT shows these automatically.")

            for profile in unassigned:
                guid = profile.get('guid')
                name = profile.get('name', 'Unknown')
                child_item = QtWidgets.QTreeWidgetItem(item, [f"  {name}", "👤 Auto"])
                # Store a marker so we know this is a virtual/auto entry
                child_item.setData(0, QtCore.Qt.ItemDataRole.UserRole,
                    {'type': '_virtual_remaining', 'profile': guid})
                child_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#5b8bd4")))
                child_item.setToolTip(0, f"GUID: {guid}\nRight-click or use 'Move Profile' to assign explicitly")

            # Auto-expand to show what's inside
            item.setExpanded(True)

        else:
            # Handle other types (matchProfiles, etc.)
            item = QtWidgets.QTreeWidgetItem(parent, [entry_type, f"⚙️ {entry_type}"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)

    def getAssignedProfileGuids(self) -> set:
        """Get all profile GUIDs that are currently assigned in newTabMenu"""
        assigned = set()

        def walk_entries(entries):
            for entry in entries:
                if isinstance(entry, dict):
                    if entry.get('type') == 'profile':
                        guid = entry.get('profile')
                        if guid:
                            assigned.add(guid)
                    elif entry.get('type') == 'folder':
                        walk_entries(entry.get('entries', []))

        new_tab_menu = data_schemes.get('newTabMenu', [])
        walk_entries(new_tab_menu)
        return assigned

    def getProfileMenuLocation(self, guid: str) -> str:
        """Find where a profile GUID appears in the newTabMenu structure.
        Returns a descriptive string like 'In folder: SSH Tools' or 'Root level' or 'remainingProfiles'."""
        def search(entries, parent_name=None):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if entry.get('type') == 'profile' and entry.get('profile') == guid:
                    return f"In folder: {parent_name}" if parent_name else "Root level"
                if entry.get('type') == 'folder':
                    result = search(entry.get('entries', []), entry.get('name', 'Unnamed'))
                    if result:
                        return result
                if entry.get('type') == 'remainingProfiles':
                    # Check if this profile would be auto-listed
                    assigned = self.getAssignedProfileGuids()
                    if guid not in assigned:
                        return "In: remainingProfiles (auto)"
            return None

        result = search(data_schemes.get('newTabMenu', []))
        return result if result else "Not in menu"

    def updateProfileMenuIndicators(self):
        """Update tooltips on profile list items showing their menu location."""
        profiles = data_schemes.get('profiles', {}).get('list', [])
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if i < len(profiles):
                guid = profiles[i].get('guid', '')
                location = self.getProfileMenuLocation(guid)
                item.setToolTip(f"Menu: {location}\nGUID: {guid}")

    def getProfileNameByGuid(self, guid: str) -> str:
        """Get profile name from GUID"""
        for profile in data_schemes.get('profiles', {}).get('list', []):
            if profile.get('guid') == guid:
                return profile.get('name', guid)
        return guid

    def getProfileGuidByName(self, name: str) -> str:
        """Get profile GUID from name"""
        for profile in data_schemes.get('profiles', {}).get('list', []):
            if profile.get('name') == name:
                return profile.get('guid', '')
        return ''

    def findActualEntry(self, entry_dict: dict, parent_folder_name: str = None) -> dict:
        """Find the actual entry object in data_schemes that matches the given entry dict.

        Args:
            entry_dict: The entry dictionary to match (usually from UserRole, which is a copy)
            parent_folder_name: Optional parent folder name if the entry is inside a folder

        Returns:
            The actual entry object from data_schemes, or None if not found
        """
        entry_type = entry_dict.get('type')

        def search_entries(entries_list):
            """Recursively search entries list"""
            for actual_entry in entries_list:
                # Match based on type and unique properties
                if actual_entry.get('type') == entry_type:
                    if entry_type == 'folder':
                        # Match folder by name
                        if actual_entry.get('name') == entry_dict.get('name'):
                            return actual_entry
                    elif entry_type == 'profile':
                        # Match profile by GUID
                        if actual_entry.get('profile') == entry_dict.get('profile'):
                            return actual_entry
                    elif entry_type == 'separator':
                        # For separators, return first match (they're identical)
                        return actual_entry

                # Search nested entries in folders
                if actual_entry.get('type') == 'folder' and 'entries' in actual_entry:
                    result = search_entries(actual_entry['entries'])
                    if result:
                        return result

            return None

        # If parent folder name is provided, find the parent first
        if parent_folder_name:
            parent = self.findActualEntry({'type': 'folder', 'name': parent_folder_name})
            if parent and 'entries' in parent:
                return search_entries(parent['entries'])
            return None

        # Search from root
        return search_entries(data_schemes.get('newTabMenu', []))

    def findParentList(self, entry: dict) -> tuple:
        """Find the list that contains this entry using its unique _wt_uid.

        Returns:
            (parent_list, index) where parent_list is the list containing entry,
            and index is the position within that list. Returns (None, -1) if not found.
        """
        uid = entry.get(_UID_KEY)
        if not uid:
            debug_print(f"DEBUG findParentList: Entry has no UID! type={entry.get('type')}")
            return (None, -1)

        def search(entries_list):
            for i, e in enumerate(entries_list):
                if e.get(_UID_KEY) == uid:
                    return (entries_list, i)
                if e.get('type') == 'folder' and 'entries' in e:
                    result = search(e['entries'])
                    if result[0] is not None:
                        return result
            return (None, -1)

        return search(data_schemes.get('newTabMenu', []))

    def onFolderSelectionChanged(self):
        """Handle folder tree selection change"""
        current_item = self.foldersTreeWidget.currentItem()

        # Update move button states based on position
        can_move_up = False
        can_move_down = False
        can_delete = False
        if current_item:
            entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if entry and entry.get('type') not in ('remainingProfiles', '_virtual_remaining'):
                can_delete = True
                parent_list, idx = self.findParentList(entry)
                if parent_list is not None:
                    can_move_up = idx > 0
                    can_move_down = idx < len(parent_list) - 1
        self.moveFolderUpButton.setEnabled(can_move_up)
        self.moveFolderDownButton.setEnabled(can_move_down)
        self.deleteFolderButton.setEnabled(can_delete)

        # Clear all fields
        self.folderNameEdit.clear()
        self.folderIconEdit.clear()
        self.menuProfileCombo.setCurrentText('')
        self.profileIconEdit.clear()
        self.allowEmptyCheckBox.setChecked(True)
        self.inlineCheckBox.setChecked(False)

        # Hide all fields initially
        self.folderNameEdit.setEnabled(False)
        self.folderIconEdit.setEnabled(False)
        self.folderIconBrowseButton.setEnabled(False)
        self.menuProfileCombo.setEnabled(False)
        self.profileIconEdit.setEnabled(False)
        self.profileIconBrowseButton.setEnabled(False)
        self.allowEmptyCheckBox.setEnabled(False)
        self.inlineCheckBox.setEnabled(False)

        if not current_item:
            self.itemTypeLabel.setText("")
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return

        entry_type = entry.get('type', 'unknown')

        if entry_type == 'folder':
            self.itemTypeLabel.setText("📁 Folder")
            self.folderNameEdit.setEnabled(True)
            self.folderIconEdit.setEnabled(True)
            self.folderIconBrowseButton.setEnabled(True)
            self.allowEmptyCheckBox.setEnabled(True)
            self.inlineCheckBox.setEnabled(True)

            self.folderNameEdit.setText(entry.get('name', ''))
            self.folderIconEdit.setText(entry.get('icon', '') or '')
            self.allowEmptyCheckBox.setChecked(entry.get('allowEmpty', True))

            # Handle inline property (could be boolean or string)
            inline_value = entry.get('inline', False)
            if inline_value == "never":
                self.inlineCheckBox.setChecked(False)
            elif inline_value is True or inline_value == "always":
                self.inlineCheckBox.setChecked(True)
            else:
                self.inlineCheckBox.setChecked(False)

        elif entry_type == 'profile':
            self.itemTypeLabel.setText("👤 Profile")
            self.menuProfileCombo.setEnabled(True)
            self.profileIconEdit.setEnabled(True)
            self.profileIconBrowseButton.setEnabled(True)

            profile_guid = entry.get('profile', '')
            profile_name = self.getProfileNameByGuid(profile_guid)
            self.menuProfileCombo.setCurrentText(profile_name)
            self.profileIconEdit.setText(entry.get('icon', '') or '')

        elif entry_type == 'separator':
            self.itemTypeLabel.setText("➖ Separator")

        elif entry_type == 'remainingProfiles':
            self.itemTypeLabel.setText("📋 Remaining Profiles (auto-generated)")

        elif entry_type == '_virtual_remaining':
            profile_guid = entry.get('profile', '')
            profile_name = self.getProfileNameByGuid(profile_guid)
            self.itemTypeLabel.setText(f"👤 {profile_name} (auto-listed, not explicitly in menu)")

    def browseFolderIcon(self):
        """Browse for folder icon"""
        getFile = QtWidgets.QFileDialog.getOpenFileName(None, 'Select Icon', '',
                                                        'Images (*.png *.jpg *.jpeg *.gif *.bmp *.ico);;Executables (*.exe);;All Files (*.*)')
        filename = getFile[0]
        if filename:
            filename = filename.replace(r"/", "\\")
            self.folderIconEdit.setText(filename)

    def browseProfileIcon(self):
        """Browse for profile icon"""
        getFile = QtWidgets.QFileDialog.getOpenFileName(None, 'Select Icon', '',
                                                        'Images (*.png *.jpg *.jpeg *.gif *.bmp *.ico);;Executables (*.exe);;All Files (*.*)')
        filename = getFile[0]
        if filename:
            filename = filename.replace(r"/", "\\")
            self.profileIconEdit.setText(filename)

    def addFolder(self):
        """Add a new folder to the menu"""
        # Ask for folder name
        folder_name, ok = QtWidgets.QInputDialog.getText(
            None, "New Folder", "Enter folder name:",
            QtWidgets.QLineEdit.EchoMode.Normal, "New Folder"
        )

        if not ok or not folder_name.strip():
            return

        if 'newTabMenu' not in data_schemes:
            data_schemes['newTabMenu'] = []

        new_folder = {
            'type': 'folder',
            'name': folder_name.strip(),
            'icon': None,
            'entries': [],
            'allowEmpty': True,
            'inline': 'never',
            _UID_KEY: str(_uuid.uuid4())
        }

        # Determine where to add
        current_item = self.foldersTreeWidget.currentItem()
        parent_entry = None
        if current_item:
            parent_entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if parent_entry and parent_entry.get('type') == 'folder':
                # Add to selected folder - find by UID
                parent_list, idx = self.findParentList(parent_entry)
                if parent_list is not None:
                    actual_folder = parent_list[idx]
                    if 'entries' not in actual_folder:
                        actual_folder['entries'] = []
                    actual_folder['entries'].append(new_folder)
                    parent_entry = actual_folder
                else:
                    debug_print("DEBUG addFolder: Could not find actual folder entry")
                    QtWidgets.QMessageBox.warning(None, "Error", "Could not find folder in settings data.")
                    return
            else:
                # Add to root
                data_schemes['newTabMenu'].append(new_folder)
                parent_entry = None
        else:
            # Add to root
            data_schemes['newTabMenu'].append(new_folder)
            parent_entry = None

        self.loadFolders()
        self.setUnsavedChanges()

        # Select the newly created folder
        self.selectFolderByName(folder_name.strip(), parent_entry)

    def addProfileToMenu(self):
        """Add a profile entry to the menu"""
        # Show dialog to select profile from ALL profiles
        profile_name, ok = QtWidgets.QInputDialog.getItem(
            None, "Add Profile", "Select profile to add:",
            profiles_list, 0, False
        )

        if not ok or not profile_name:
            debug_print("DEBUG addProfileToMenu: Add Profile cancelled")
            return

        debug_print(f"DEBUG addProfileToMenu: Adding profile '{profile_name}'")

        if 'newTabMenu' not in data_schemes:
            data_schemes['newTabMenu'] = []

        profile_guid = self.getProfileGuidByName(profile_name)
        if not profile_guid:
            QtWidgets.QMessageBox.warning(None, "Profile Not Found",
                                         f"Could not find GUID for profile '{profile_name}'.")
            return

        debug_print(f"DEBUG addProfileToMenu: Profile GUID: {profile_guid}")

        new_profile_entry = {
            'type': 'profile',
            'profile': profile_guid,
            'icon': None,
            _UID_KEY: str(_uuid.uuid4())
        }

        # Determine where to add based on selection
        current_item = self.foldersTreeWidget.currentItem()
        target_parent = None
        added_location = "unknown"

        if current_item:
            current_entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            debug_print(f"DEBUG addProfileToMenu: Current selection type: {current_entry.get('type') if current_entry else 'None'}")

            if current_entry and current_entry.get('type') == 'folder':
                # Selected item is a folder - find by UID
                parent_list, idx = self.findParentList(current_entry)
                if parent_list is not None:
                    actual_folder = parent_list[idx]
                    if 'entries' not in actual_folder:
                        actual_folder['entries'] = []
                    actual_folder['entries'].append(new_profile_entry)
                    target_parent = actual_folder
                    added_location = f"folder '{actual_folder.get('name')}'"
                    debug_print(f"DEBUG addProfileToMenu: Added to folder: {actual_folder.get('name')}, now has {len(actual_folder['entries'])} entries")
                else:
                    debug_print(f"DEBUG addProfileToMenu: Could not find actual folder entry by UID")
                    QtWidgets.QMessageBox.warning(None, "Error", "Could not find folder in settings data.")
                    return
            else:
                # Selected item is NOT a folder - try to add to parent folder
                parent_item = current_item.parent()
                if parent_item:
                    parent_entry = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if parent_entry and parent_entry.get('type') == 'folder':
                        parent_list, idx = self.findParentList(parent_entry)
                        if parent_list is not None:
                            actual_parent = parent_list[idx]
                            if 'entries' not in actual_parent:
                                actual_parent['entries'] = []
                            actual_parent['entries'].append(new_profile_entry)
                            target_parent = actual_parent
                            added_location = f"parent folder '{actual_parent.get('name')}'"
                            debug_print(f"DEBUG addProfileToMenu: Added to parent folder: {actual_parent.get('name')}")
                        else:
                            debug_print(f"DEBUG addProfileToMenu: Could not find actual parent folder entry by UID")
                            QtWidgets.QMessageBox.warning(None, "Error", "Could not find parent folder in settings data.")
                            return
                    else:
                        # Parent is root, add to root
                        data_schemes['newTabMenu'].append(new_profile_entry)
                        added_location = "root"
                        debug_print("DEBUG addProfileToMenu: Added to root (parent is root)")
                else:
                    # No parent, add to root
                    data_schemes['newTabMenu'].append(new_profile_entry)
                    added_location = "root"
                    debug_print("DEBUG addProfileToMenu: Added to root (no parent)")
        else:
            # Nothing selected, add to root
            data_schemes['newTabMenu'].append(new_profile_entry)
            added_location = "root"
            debug_print("DEBUG addProfileToMenu: Added to root (nothing selected)")

        self.loadFolders()
        self.setUnsavedChanges()

        # Try to select the newly added profile
        self.selectProfileByGuid(profile_guid, target_parent)

        QtWidgets.QMessageBox.information(None, "Profile Added",
                                         f"Added profile '{profile_name}' to {added_location}.")

    def addSeparator(self):
        """Add a separator to the menu"""
        if 'newTabMenu' not in data_schemes:
            data_schemes['newTabMenu'] = []

        new_separator = {
            'type': 'separator',
            _UID_KEY: str(_uuid.uuid4())
        }

        # Determine where to add based on selection
        current_item = self.foldersTreeWidget.currentItem()
        added_location = "unknown"

        if current_item:
            current_entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

            if current_entry and current_entry.get('type') == 'folder':
                # Selected item is a folder - find it in data_schemes by UID and add to it
                parent_list, idx = self.findParentList(current_entry)
                if parent_list is not None:
                    actual_folder = parent_list[idx]
                    if 'entries' not in actual_folder:
                        actual_folder['entries'] = []
                    actual_folder['entries'].append(new_separator)
                    added_location = f"folder '{actual_folder.get('name')}'"
                    debug_print(f"DEBUG addSeparator: Added to folder: {actual_folder.get('name')}")
                else:
                    debug_print("DEBUG addSeparator: Could not find folder entry by UID")
                    QtWidgets.QMessageBox.warning(None, "Error", "Could not find folder in settings data.")
                    return
            else:
                # Selected item is NOT a folder - try to add to parent folder
                parent_item = current_item.parent()
                if parent_item:
                    parent_entry = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if parent_entry and parent_entry.get('type') == 'folder':
                        parent_list, idx = self.findParentList(parent_entry)
                        if parent_list is not None:
                            actual_parent = parent_list[idx]
                            if 'entries' not in actual_parent:
                                actual_parent['entries'] = []
                            actual_parent['entries'].append(new_separator)
                            added_location = f"parent folder '{actual_parent.get('name')}'"
                            debug_print(f"DEBUG addSeparator: Added to parent folder: {actual_parent.get('name')}")
                        else:
                            debug_print("DEBUG addSeparator: Could not find parent folder by UID")
                            QtWidgets.QMessageBox.warning(None, "Error", "Could not find parent folder in settings data.")
                            return
                    else:
                        # Parent is root, add to root
                        data_schemes['newTabMenu'].append(new_separator)
                        added_location = "root"
                        debug_print("DEBUG addSeparator: Added to root (parent is root)")
                else:
                    # No parent, add to root
                    data_schemes['newTabMenu'].append(new_separator)
                    added_location = "root"
                    debug_print("DEBUG addSeparator: Added to root (no parent)")
        else:
            # Nothing selected, add to root
            data_schemes['newTabMenu'].append(new_separator)
            added_location = "root"
            debug_print("DEBUG addSeparator: Added to root (nothing selected)")

        self.loadFolders()
        self.setUnsavedChanges()

        QtWidgets.QMessageBox.information(None, "Separator Added",
                                         f"Added separator to {added_location}.")

    def updateFolderItem(self):
        """Update the selected folder/profile item"""
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(None, "No Selection", "Please select an item to update.")
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return

        entry_type = entry.get('type', 'unknown')
        old_name = entry.get('name', '') if entry_type == 'folder' else ''

        # Find the actual entry in data_schemes using UID
        parent_list, idx = self.findParentList(entry)
        if parent_list is None:
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find entry in settings data.")
            debug_print(f"DEBUG updateFolderItem: Could not find entry in data_schemes: {entry}")
            return
        actual_entry = parent_list[idx]

        debug_print(f"DEBUG updateFolderItem: Found actual entry, id={id(actual_entry)}")

        if entry_type == 'folder':
            new_name = self.folderNameEdit.text().strip()
            if not new_name:
                QtWidgets.QMessageBox.warning(None, "Invalid Name", "Folder name cannot be empty.")
                return

            debug_print(f"DEBUG updateFolderItem: Updating folder from '{old_name}' to '{new_name}'")

            # Update the ACTUAL entry in data_schemes
            actual_entry['name'] = new_name
            icon_text = self.folderIconEdit.text().strip()
            if icon_text:
                actual_entry['icon'] = icon_text
            else:
                actual_entry.pop('icon', None)
            actual_entry['allowEmpty'] = self.allowEmptyCheckBox.isChecked()
            actual_entry['inline'] = 'always' if self.inlineCheckBox.isChecked() else 'never'

            debug_print(f"DEBUG updateFolderItem: Actual entry updated: {actual_entry}")

        elif entry_type == 'profile':
            profile_name = self.menuProfileCombo.currentText()
            profile_guid = self.getProfileGuidByName(profile_name)
            if profile_guid:
                actual_entry['profile'] = profile_guid
            icon_text = self.profileIconEdit.text().strip()
            if icon_text:
                actual_entry['icon'] = icon_text
            else:
                actual_entry.pop('icon', None)

        # Reload and try to re-select the same item (use updated entry for folder name)
        self.loadFolders()
        self.setUnsavedChanges()

        # Re-select the updated item (use actual_entry so we have the new name)
        self.reselectItemByEntry(actual_entry)

        # Show confirmation
        if entry_type == 'folder':
            QtWidgets.QMessageBox.information(None, "Updated", f"Folder updated successfully.\nOld name: '{old_name}'\nNew name: '{actual_entry.get('name', '')}'.")
        else:
            QtWidgets.QMessageBox.information(None, "Updated", f"{entry_type.capitalize()} updated successfully.")

    def deleteFolderItem(self):
        """Delete the selected folder/profile item"""
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return

        # Ask for confirmation
        reply = QtWidgets.QMessageBox.question(None, 'Delete Item',
                                             'Are you sure you want to delete this item?',
                                             QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Use identity-based lookup to find and remove the exact entry
        parent_list, idx = self.findParentList(entry)
        if parent_list is not None and idx >= 0:
            parent_list.pop(idx)
            debug_print(f"DEBUG deleteFolderItem: Removed entry at index {idx}")
        else:
            debug_print("DEBUG deleteFolderItem: Could not find entry in data_schemes")
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find item in settings data.")
            return

        self.loadFolders()
        self.setUnsavedChanges()

    def moveFolderItemUp(self):
        """Move selected item up in its parent's list"""
        debug_print("DEBUG moveFolderItemUp: Function called")
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return

        debug_print(f"DEBUG moveFolderItemUp: Moving {entry.get('type')} id={id(entry)}")

        # Use identity-based lookup to find the exact entry in its parent list
        parent_list, idx = self.findParentList(entry)
        if parent_list is None:
            debug_print("DEBUG moveFolderItemUp: Could not find entry in data_schemes")
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find item in settings data.")
            return

        debug_print(f"DEBUG moveFolderItemUp: Found at index {idx} of {len(parent_list)} items")

        if idx > 0:
            parent_list[idx], parent_list[idx - 1] = parent_list[idx - 1], parent_list[idx]
            debug_print(f"DEBUG moveFolderItemUp: Swapped {idx} <-> {idx - 1}")
            self.loadFolders()
            self.setUnsavedChanges()
            # Re-select by identity: entry object is still the same reference
            self.reselectItemByIdentity(entry)
        else:
            debug_print("DEBUG moveFolderItemUp: Already at top")

    def moveFolderItemDown(self):
        """Move selected item down in its parent's list"""
        debug_print("DEBUG moveFolderItemDown: Function called")
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return

        debug_print(f"DEBUG moveFolderItemDown: Moving {entry.get('type')} id={id(entry)}")

        # Use identity-based lookup to find the exact entry in its parent list
        parent_list, idx = self.findParentList(entry)
        if parent_list is None:
            debug_print("DEBUG moveFolderItemDown: Could not find entry in data_schemes")
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find item in settings data.")
            return

        debug_print(f"DEBUG moveFolderItemDown: Found at index {idx} of {len(parent_list)} items")

        if idx < len(parent_list) - 1:
            parent_list[idx], parent_list[idx + 1] = parent_list[idx + 1], parent_list[idx]
            debug_print(f"DEBUG moveFolderItemDown: Swapped {idx} <-> {idx + 1}")
            self.loadFolders()
            self.setUnsavedChanges()
            # Re-select by identity: entry object is still the same reference
            self.reselectItemByIdentity(entry)
        else:
            debug_print("DEBUG moveFolderItemDown: Already at bottom")

    def selectFolderByName(self, folder_name: str, parent_entry: Optional[dict] = None):
        """Select a folder in the tree by its name"""
        # Recursively search the tree for the folder
        def findItem(parent_item, target_name, target_parent):
            for i in range(parent_item.childCount() if parent_item else self.foldersTreeWidget.topLevelItemCount()):
                item = parent_item.child(i) if parent_item else self.foldersTreeWidget.topLevelItem(i)
                entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if entry and entry.get('type') == 'folder' and entry.get('name') == target_name:
                    # Check if this is the right parent
                    if target_parent is None and parent_item is None:
                        return item
                    elif target_parent and parent_item:
                        parent_data = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                        if parent_data == target_parent:
                            return item
                # Recursively search children
                found = findItem(item, target_name, target_parent)
                if found:
                    return found
            return None

        item = findItem(None, folder_name, parent_entry)
        if item:
            self.foldersTreeWidget.setCurrentItem(item)
            self.foldersTreeWidget.scrollToItem(item)

    def selectProfileByGuid(self, profile_guid: str, parent_entry: Optional[dict] = None):
        """Select a profile in the tree by its GUID"""
        def findItem(parent_item, target_guid, target_parent):
            for i in range(parent_item.childCount() if parent_item else self.foldersTreeWidget.topLevelItemCount()):
                item = parent_item.child(i) if parent_item else self.foldersTreeWidget.topLevelItem(i)
                entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if entry and entry.get('type') == 'profile' and entry.get('profile') == target_guid:
                    if target_parent is None and parent_item is None:
                        return item
                    elif target_parent and parent_item:
                        parent_data = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                        if parent_data == target_parent:
                            return item
                found = findItem(item, target_guid, target_parent)
                if found:
                    return found
            return None

        item = findItem(None, profile_guid, parent_entry)
        if item:
            self.foldersTreeWidget.setCurrentItem(item)
            self.foldersTreeWidget.scrollToItem(item)

    def reselectItemByEntry(self, entry: dict):
        """Re-select an item in the tree after reload using UID."""
        uid = entry.get(_UID_KEY)
        if uid:
            # Use UID-based reselect (same as reselectItemByIdentity)
            self.reselectItemByIdentity(entry)
            return

        # Fallback: match by properties
        def findItem(parent_item, target_entry):
            for i in range(parent_item.childCount() if parent_item else self.foldersTreeWidget.topLevelItemCount()):
                item = parent_item.child(i) if parent_item else self.foldersTreeWidget.topLevelItem(i)
                item_entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)

                entry_type = target_entry.get('type')
                if entry_type == 'folder':
                    if item_entry.get('type') == 'folder' and item_entry.get('name') == target_entry.get('name'):
                        return item
                elif entry_type == 'profile':
                    if item_entry.get('type') == 'profile' and item_entry.get('profile') == target_entry.get('profile'):
                        return item

                found = findItem(item, target_entry)
                if found:
                    return found
            return None

        item = findItem(None, entry)
        if item:
            self.foldersTreeWidget.setCurrentItem(item)
            self.foldersTreeWidget.scrollToItem(item)

    def reselectItemByIdentity(self, entry: dict):
        """Re-select an item in the tree after reload using _wt_uid.
        Works correctly for separators and all other entry types."""
        uid = entry.get(_UID_KEY)
        if not uid:
            return

        def findItem(parent_item):
            count = parent_item.childCount() if parent_item else self.foldersTreeWidget.topLevelItemCount()
            for i in range(count):
                item = parent_item.child(i) if parent_item else self.foldersTreeWidget.topLevelItem(i)
                item_entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if item_entry and item_entry.get(_UID_KEY) == uid:
                    return item
                found = findItem(item)
                if found:
                    return found
            return None

        item = findItem(None)
        if item:
            self.foldersTreeWidget.setCurrentItem(item)
            self.foldersTreeWidget.scrollToItem(item)

    # ========== Save Method ==========

    def dumpOnSave(self):
        if dumpJson():
            self.unsaved_changes = False
            self.statusLabel.setText("Settings saved successfully!")
            self.statusLabel.setStyleSheet("QLabel { color: #2e8b2e; font-weight: bold; }")
            QtCore.QTimer.singleShot(3000, lambda: self.statusLabel.setText(""))
        else:
            self.statusLabel.setText("Error saving settings!")
            self.statusLabel.setStyleSheet("QLabel { color: #c34a4a; font-weight: bold; }")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    app.setStyle('Fusion')

    # Global stylesheet - pastel light theme
    app.setStyleSheet("""
        QMainWindow { background-color: #f5f0ff; }
        QWidget { background-color: #f5f0ff; color: #2d2d3d; }
        QTabWidget::pane { border: 1px solid #c8bfe0; background: #f5f0ff; }
        QTabBar::tab {
            background: #e8e0f5; color: #3d3555; border: 1px solid #c8bfe0;
            padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected { background: #f5f0ff; color: #2d2d3d; border-bottom-color: #f5f0ff; font-weight: bold; }
        QTabBar::tab:hover { background: #ded5f0; }
        QGroupBox {
            font-weight: bold; border: 1px solid #c8bfe0; border-radius: 6px;
            margin-top: 10px; padding-top: 14px; color: #2d2d3d;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
        QGroupBox::indicator { width: 13px; height: 13px; }
        QGroupBox::indicator:checked { image: none; border: 2px solid #7c6bc4; border-radius: 3px; background: #7c6bc4; }
        QGroupBox::indicator:unchecked { image: none; border: 2px solid #b0a8c8; border-radius: 3px; background: #e8e0f5; }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff; border: 1px solid #c8bfe0; border-radius: 4px;
            padding: 4px 6px; color: #2d2d3d; selection-background-color: #d4cceb;
        }
        QLineEdit:focus, QTextEdit:focus { border-color: #7c6bc4; }
        QLineEdit:read-only { background-color: #ede8f5; color: #6b6580; }
        QComboBox {
            background-color: #ffffff; border: 1px solid #c8bfe0; border-radius: 4px;
            padding: 4px 8px; color: #2d2d3d;
        }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox::down-arrow { image: none; border-left: 4px solid transparent;
            border-right: 4px solid transparent; border-top: 6px solid #5c5470; }
        QComboBox QAbstractItemView {
            background-color: #ffffff; border: 1px solid #c8bfe0; color: #2d2d3d;
            selection-background-color: #d4cceb;
        }
        QSpinBox, QDoubleSpinBox {
            background-color: #ffffff; border: 1px solid #c8bfe0; border-radius: 4px;
            padding: 4px; color: #2d2d3d;
        }
        QPushButton {
            background-color: #e0d8f0; color: #2d2d3d; border: 1px solid #b0a8c8;
            border-radius: 4px; padding: 6px 14px; font-weight: bold;
        }
        QPushButton:hover { background-color: #d0c5e8; }
        QPushButton:pressed { background-color: #c0b5d8; }
        QPushButton:disabled { background-color: #ede8f5; color: #a09ab0; border-color: #d5d0e0; }
        QListWidget, QTreeWidget {
            background-color: #ffffff; border: 1px solid #c8bfe0; border-radius: 4px;
            color: #2d2d3d; alternate-background-color: #f5f0ff;
        }
        QListWidget::item:selected, QTreeWidget::item:selected { background-color: #d4cceb; }
        QListWidget::item:hover, QTreeWidget::item:hover { background-color: #ede8f5; }
        QTableWidget {
            background-color: #ffffff; border: 1px solid #c8bfe0; border-radius: 4px;
            color: #2d2d3d; alternate-background-color: #f5f0ff; gridline-color: #d5d0e0;
        }
        QTableWidget::item:selected { background-color: #d4cceb; color: #2d2d3d; }
        QTableWidget::item:hover { background-color: #ede8f5; }
        QHeaderView::section {
            background-color: #e8e0f5; color: #3d3555; border: 1px solid #c8bfe0;
            padding: 4px; font-weight: bold;
        }
        QScrollBar:vertical {
            background: #f0eaf8; width: 12px; border: none;
        }
        QScrollBar::handle:vertical { background: #c8bfe0; border-radius: 6px; min-height: 20px; }
        QScrollBar::handle:vertical:hover { background: #b0a8c8; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        QScrollBar:horizontal {
            background: #f0eaf8; height: 12px; border: none;
        }
        QScrollBar::handle:horizontal { background: #c8bfe0; border-radius: 6px; min-width: 20px; }
        QScrollBar::handle:horizontal:hover { background: #b0a8c8; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        QSlider::groove:horizontal {
            height: 6px; background: #d5d0e0; border-radius: 3px;
        }
        QSlider::handle:horizontal {
            width: 16px; height: 16px; margin: -5px 0;
            background: #7c6bc4; border-radius: 8px;
        }
        QSlider::handle:horizontal:hover { background: #9585d0; }
        QCheckBox { spacing: 6px; }
        QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 2px solid #b0a8c8; }
        QCheckBox::indicator:checked { background: #7c6bc4; border-color: #7c6bc4; }
        QCheckBox::indicator:unchecked { background: #ffffff; }
        QLabel { color: #3d3555; }
        QScrollArea { border: none; }
        QFrame[frameShape="4"] { color: #c8bfe0; }
        QToolTip { background-color: #ffffff; color: #2d2d3d; border: 1px solid #c8bfe0; padding: 4px; }
    """)

    # Try to load the icon using absolute path from script directory
    icon_path = SCRIPT_DIR / 'WT_config.ico'
    if not icon_path.exists():
        icon_path = SCRIPT_DIR / 'wt3.ico'  # Fallback to old icon
    if icon_path.exists():
        icon = QtGui.QIcon(str(icon_path))
        app.setWindowIcon(icon)
        MainWindow.setWindowIcon(icon)

    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    # Warn about unsaved changes when closing
    def closeEvent(event):
        if ui.unsaved_changes:
            reply = QtWidgets.QMessageBox.question(MainWindow, 'Unsaved Changes',
                                                   'You have unsaved changes. Do you want to save before closing?',
                                                   QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Discard | QtWidgets.QMessageBox.StandardButton.Cancel)
            if reply == QtWidgets.QMessageBox.StandardButton.Save:
                ui.dumpOnSave()
                event.accept()
            elif reply == QtWidgets.QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    MainWindow.closeEvent = closeEvent
    sys.exit(app.exec())
