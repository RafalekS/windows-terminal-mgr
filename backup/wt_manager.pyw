from shutil import copyfile
from PyQt6 import QtCore, QtGui, QtWidgets
import commentjson
import os
import matplotlib.font_manager
import datetime
import subprocess
import sys
import argparse
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

# Place in the "settings.json" directory
homePath = os.getenv("HOMEPATH")

if os.path.isdir(f"C:{homePath}\\LocalAppData\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState"):
    os.chdir(f"C:{homePath}\\LocalAppData\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState")
    settingsPath = f"C:{homePath}\\LocalAppData\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState"
else:
    os.chdir(f"C:{homePath}\\AppData\\Local\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState")
    settingsPath = f"C:{homePath}\\AppData\\Local\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState"

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

        with open("settings.json", "w", encoding='utf-8') as file:
            commentjson.dump(data_schemes, file, indent=2, ensure_ascii=False)
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
        if self.starting_directory:
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

        self.tabWidget.addTab(self.profilesTab, "Profiles")
        self.tabWidget.addTab(self.foldersTab, "Folders && New Tab Menu")
        self.tabWidget.addTab(self.actionsTab, "Actions && Key Bindings")
        self.tabWidget.addTab(self.commandBuilderTab, "WT Command Builder")

        self.setupProfilesTab()
        self.setupActionsTab()
        self.setupCommandBuilderTab()
        self.setupFoldersTab()

        # Bottom panel with save button and status
        bottom_layout = QtWidgets.QHBoxLayout()

        # Status label
        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.statusLabel)

        # Save button
        self.saveButton = QtWidgets.QPushButton("Save")
        self.saveButton.setMinimumSize(120, 40)
        self.saveButton.setMaximumSize(120, 40)
        self.saveButton.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        bottom_layout.addWidget(self.saveButton)

        main_layout.addLayout(bottom_layout)

        # Connect save button
        self.saveButton.clicked.connect(self.dumpOnSave)

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
        scroll_layout = QtWidgets.QFormLayout(scroll_widget)
        scroll_layout.setSpacing(10)

        # Profile details fields
        self.profileNameEdit = QtWidgets.QLineEdit()
        self.profileNameEdit.setReadOnly(True)
        scroll_layout.addRow("Profile Name:", self.profileNameEdit)

        self.comboBox = QtWidgets.QComboBox()
        for item in data_list:
            self.comboBox.addItem(item)
        scroll_layout.addRow("Color Scheme:", self.comboBox)

        # Font selection
        font_layout = QtWidgets.QHBoxLayout()
        self.fontBox = QtWidgets.QComboBox()
        self.fontBox.setMinimumWidth(200)
        for item in font_list:
            self.fontBox.addItem(item)
        self.fontSize = QtWidgets.QSpinBox()
        self.fontSize.setMinimum(4)
        self.fontSize.setMaximum(72)
        self.fontSize.setValue(12)
        font_layout.addWidget(self.fontBox)
        font_layout.addWidget(QtWidgets.QLabel("Size:"))
        font_layout.addWidget(self.fontSize)
        font_layout.addStretch()
        scroll_layout.addRow("Font:", font_layout)

        # Background image
        bg_layout = QtWidgets.QHBoxLayout()
        self.backgroundImageEdit = QtWidgets.QLineEdit()
        self.backgroundImageEdit.setReadOnly(False)
        self.pushButton = QtWidgets.QPushButton("Browse...")
        bg_layout.addWidget(self.backgroundImageEdit)
        bg_layout.addWidget(self.pushButton)
        scroll_layout.addRow("Background Image:", bg_layout)

        # Opacity slider
        opacity_layout = QtWidgets.QHBoxLayout()
        self.horizontalSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.horizontalSlider.setMaximum(10)
        self.horizontalSlider.setValue(10)
        self.opacityValueLabel = QtWidgets.QLabel("1.0")
        opacity_layout.addWidget(self.horizontalSlider)
        opacity_layout.addWidget(self.opacityValueLabel)
        scroll_layout.addRow("Background Opacity:", opacity_layout)

        # Text fields
        self.commandLineEdit = QtWidgets.QLineEdit()
        scroll_layout.addRow("Command Line:", self.commandLineEdit)

        self.startingDirectoryEdit = QtWidgets.QLineEdit()
        scroll_layout.addRow("Starting Directory:", self.startingDirectoryEdit)

        self.tabTitleEdit = QtWidgets.QLineEdit()
        scroll_layout.addRow("Tab Title:", self.tabTitleEdit)

        # Icon field with browse button
        icon_layout = QtWidgets.QHBoxLayout()
        self.iconEdit = QtWidgets.QLineEdit()
        self.iconBrowseButton = QtWidgets.QPushButton("Browse...")
        icon_layout.addWidget(self.iconEdit)
        icon_layout.addWidget(self.iconBrowseButton)
        scroll_layout.addRow("Icon:", icon_layout)

        self.paddingEdit = QtWidgets.QLineEdit()
        scroll_layout.addRow("Padding:", self.paddingEdit)

        # Dropdowns
        self.cursorShapeBox = QtWidgets.QComboBox()
        self.cursorShapeBox.addItems(["bar", "vintage", "underscore", "filledBox", "emptyBox", "doubleUnderscore"])
        scroll_layout.addRow("Cursor Shape:", self.cursorShapeBox)

        self.scrollbarBox = QtWidgets.QComboBox()
        self.scrollbarBox.addItems(["visible", "hidden"])
        scroll_layout.addRow("Scrollbar State:", self.scrollbarBox)

        # Checkboxes
        self.runAsAdminCheckBox = QtWidgets.QCheckBox("Run as Administrator")
        self.useAcrylicCheckBox = QtWidgets.QCheckBox("Use Acrylic")
        self.hiddenCheckBox = QtWidgets.QCheckBox("Hidden")
        self.snapOnInputCheckBox = QtWidgets.QCheckBox("Snap On Input")

        scroll_layout.addRow("", self.runAsAdminCheckBox)
        scroll_layout.addRow("", self.useAcrylicCheckBox)
        scroll_layout.addRow("", self.hiddenCheckBox)
        scroll_layout.addRow("", self.snapOnInputCheckBox)

        scroll_area.setWidget(scroll_widget)
        right_layout.addWidget(scroll_area)

        main_layout.addWidget(right_widget)

        # Connect profile signals
        self.listWidget.currentItemChanged.connect(self.changedProfile)
        self.comboBox.activated.connect(self.changeScheme)
        self.fontBox.activated.connect(self.changeFont)
        self.fontSize.valueChanged.connect(self.changeFontSize)
        self.pushButton.clicked.connect(self.changeBackgroundImage)
        self.horizontalSlider.sliderReleased.connect(self.changeOpacity)
        self.commandLineEdit.textChanged.connect(self.changeCommandLine)
        self.startingDirectoryEdit.textChanged.connect(self.changeStartingDirectory)
        self.tabTitleEdit.textChanged.connect(self.changeTabTitle)
        self.iconEdit.textChanged.connect(self.changeIcon)
        self.iconBrowseButton.clicked.connect(self.browseIcon)
        self.paddingEdit.textChanged.connect(self.changePadding)
        self.cursorShapeBox.textActivated.connect(self.changeCursorShape)
        self.scrollbarBox.textActivated.connect(self.changeScrollbarState)
        self.runAsAdminCheckBox.stateChanged.connect(self.changeRunAsAdmin)
        self.useAcrylicCheckBox.stateChanged.connect(self.changeUseAcrylic)
        self.hiddenCheckBox.stateChanged.connect(self.changeHidden)
        self.snapOnInputCheckBox.stateChanged.connect(self.changeSnapOnInput)
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
        # Main horizontal layout
        main_layout = QtWidgets.QHBoxLayout(self.actionsTab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left side - Actions list
        left_widget = QtWidgets.QWidget()
        left_widget.setMinimumWidth(450)
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        actions_label = QtWidgets.QLabel("Actions & Key Bindings:")
        actions_label.setFont(QtGui.QFont("", 10, QtGui.QFont.Weight.Bold))
        left_layout.addWidget(actions_label)

        self.actionsListWidget = QtWidgets.QListWidget()
        self.actionsListWidget.setMinimumHeight(400)
        left_layout.addWidget(self.actionsListWidget)

        # Action control buttons
        action_buttons_layout = QtWidgets.QGridLayout()

        self.addActionButton = QtWidgets.QPushButton("Add Action")
        self.updateActionButton = QtWidgets.QPushButton("Update Action")
        self.deleteActionButton = QtWidgets.QPushButton("Delete Action")
        self.moveActionUpButton = QtWidgets.QPushButton("Move Up")
        self.moveActionDownButton = QtWidgets.QPushButton("Move Down")
        self.clearFieldsButton = QtWidgets.QPushButton("Clear Fields")

        action_buttons_layout.addWidget(self.addActionButton, 0, 0)
        action_buttons_layout.addWidget(self.updateActionButton, 0, 1)
        action_buttons_layout.addWidget(self.deleteActionButton, 1, 0)
        action_buttons_layout.addWidget(self.clearFieldsButton, 1, 1)
        action_buttons_layout.addWidget(self.moveActionUpButton, 2, 0)
        action_buttons_layout.addWidget(self.moveActionDownButton, 2, 1)

        left_layout.addLayout(action_buttons_layout)
        main_layout.addWidget(left_widget)

        # Right side - Action details
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        # Action details group
        details_group = QtWidgets.QGroupBox("Action Details")
        details_layout = QtWidgets.QFormLayout(details_group)
        details_layout.setSpacing(10)

        # Action fields
        name_id_layout = QtWidgets.QHBoxLayout()
        self.actionNameEdit = QtWidgets.QLineEdit()
        self.actionIdEdit = QtWidgets.QLineEdit()
        self.actionIdEdit.setPlaceholderText("e.g., User.newTab.1234")
        name_id_layout.addWidget(self.actionNameEdit)
        name_id_layout.addWidget(QtWidgets.QLabel("ID:"))
        name_id_layout.addWidget(self.actionIdEdit)
        details_layout.addRow("Action Name:", name_id_layout)

        self.commandActionCombo = QtWidgets.QComboBox()
        self.commandActionCombo.setEditable(True)
        for action in COMMON_ACTIONS:
            self.commandActionCombo.addItem(action)
        details_layout.addRow("Command:", self.commandActionCombo)

        self.keysEdit = QtWidgets.QLineEdit()
        self.keysEdit.setPlaceholderText("e.g., ctrl+shift+t")
        details_layout.addRow("Keys:", self.keysEdit)

        self.actionArgsEdit = QtWidgets.QTextEdit()
        self.actionArgsEdit.setMaximumHeight(100)
        self.actionArgsEdit.setPlaceholderText('e.g., {"action": "newTab", "index": 0}')
        details_layout.addRow("Arguments (JSON):", self.actionArgsEdit)

        self.iconPathEdit = QtWidgets.QLineEdit()
        details_layout.addRow("Icon Path:", self.iconPathEdit)

        right_layout.addWidget(details_group)

        # Help section
        help_group = QtWidgets.QGroupBox("Key Combination Help")
        help_layout = QtWidgets.QVBoxLayout(help_group)

        self.keyHelperLabel = QtWidgets.QLabel("""Key Combination Examples:
• ctrl+shift+t (New Tab)
• ctrl+shift+w (Close Tab)
• alt+shift+plus (Split Pane Vertical)
• ctrl+shift+f (Find)
• ctrl+comma (Open Settings)
• f11 (Toggle Fullscreen)

Modifiers: ctrl, shift, alt, win
Special keys: enter, tab, space, esc, backspace, delete,
insert, home, end, pageup, pagedown, f1-f24
Arrow keys: up, down, left, right

Action/Key Binding Structure:
🔗 Bound: Action with key binding
⚪ Unbound: Action without key binding
❌ Disabled: Key binding with null ID

Note: Actions and key bindings are separate!
- Actions define what to do (stored in 'actions' array)
- Key bindings link keys to action IDs (stored in 'keybindings' array)""")
        self.keyHelperLabel.setWordWrap(True)
        self.keyHelperLabel.setStyleSheet("QLabel { background-color: #f0f0f0; color: #000000; padding: 10px; border: 1px solid #ccc; }")

        help_layout.addWidget(self.keyHelperLabel)
        right_layout.addWidget(help_group)

        main_layout.addWidget(right_widget)

        # Load actions
        self.loadActions()

        # Connect action signals
        self.actionsListWidget.currentItemChanged.connect(self.onActionSelectionChanged)
        self.addActionButton.clicked.connect(self.addAction)
        self.updateActionButton.clicked.connect(self.updateAction)
        self.deleteActionButton.clicked.connect(self.deleteAction)
        self.moveActionUpButton.clicked.connect(self.moveActionUp)
        self.moveActionDownButton.clicked.connect(self.moveActionDown)
        self.clearFieldsButton.clicked.connect(self.clearActionFields)

    def setupCommandBuilderTab(self):
        """Setup the command builder tab from wt_cline.pyw"""
        root = QtWidgets.QVBoxLayout(self.commandBuilderTab)

        # Extract profiles and schemes for command builder
        self.profile_names = [item['name'] for item in data_schemes.get('profiles', {}).get('list', [])]
        user_schemes = [s.get('name') for s in data_schemes.get('schemes', []) if isinstance(s, dict) and s.get('name')]
        self.scheme_names = sorted(set(user_schemes + BUILTIN_SCHEMES))

        # Global window options
        global_box = QtWidgets.QGroupBox("Global window options")
        g_layout = QtWidgets.QHBoxLayout()

        size_box = QtWidgets.QGroupBox("--size (columns, rows)")
        s_layout = QtWidgets.QHBoxLayout()
        self.global_size_cols = QtWidgets.QSpinBox()
        self.global_size_rows = QtWidgets.QSpinBox()
        self.global_size_cols.setRange(0, 1000)
        self.global_size_rows.setRange(0, 1000)
        s_layout.addWidget(QtWidgets.QLabel("Columns"))
        s_layout.addWidget(self.global_size_cols)
        s_layout.addWidget(QtWidgets.QLabel("Rows"))
        s_layout.addWidget(self.global_size_rows)
        size_box.setLayout(s_layout)

        pos_box = QtWidgets.QGroupBox("--pos (x, y)")
        p_layout = QtWidgets.QHBoxLayout()
        self.global_pos_x = QtWidgets.QSpinBox()
        self.global_pos_y = QtWidgets.QSpinBox()
        self.global_pos_x.setRange(0, 10000)
        self.global_pos_y.setRange(0, 10000)
        p_layout.addWidget(QtWidgets.QLabel("X"))
        p_layout.addWidget(self.global_pos_x)
        p_layout.addWidget(QtWidgets.QLabel("Y"))
        p_layout.addWidget(self.global_pos_y)
        pos_box.setLayout(p_layout)

        window_box = QtWidgets.QGroupBox("--window")
        w_layout = QtWidgets.QHBoxLayout()
        self.window_combo = QtWidgets.QComboBox()
        self.window_combo.setEditable(True)
        self.window_combo.addItems(["", "new", "last"])
        self.window_combo.setEditText("")
        w_layout.addWidget(QtWidgets.QLabel("Target"))
        w_layout.addWidget(self.window_combo)
        window_box.setLayout(w_layout)

        state_box = QtWidgets.QGroupBox("State")
        st_layout = QtWidgets.QVBoxLayout()
        self.global_maximized = QtWidgets.QCheckBox("Maximized")
        self.global_fullscreen = QtWidgets.QCheckBox("Fullscreen")
        self.global_focus = QtWidgets.QCheckBox("Focus mode")

        # Make maximized and fullscreen mutually exclusive
        self.global_maximized.stateChanged.connect(lambda state: self.global_fullscreen.setChecked(False) if state else None)
        self.global_fullscreen.stateChanged.connect(lambda state: self.global_maximized.setChecked(False) if state else None)

        st_layout.addWidget(self.global_maximized)
        st_layout.addWidget(self.global_fullscreen)
        st_layout.addWidget(self.global_focus)
        state_box.setLayout(st_layout)

        g_layout.addWidget(size_box)
        g_layout.addWidget(pos_box)
        g_layout.addWidget(window_box)
        g_layout.addWidget(state_box)
        global_box.setLayout(g_layout)
        root.addWidget(global_box)

        # Steps sequence and editor
        steps_box = QtWidgets.QGroupBox("Command sequence")
        sb_layout = QtWidgets.QVBoxLayout()

        btn_row = QtWidgets.QHBoxLayout()
        add_tab_btn = QtWidgets.QPushButton("Add new-tab")
        add_pane_h_btn = QtWidgets.QPushButton("Add split-pane -H")
        add_pane_v_btn = QtWidgets.QPushButton("Add split-pane -V")
        remove_btn = QtWidgets.QPushButton("Remove selected")
        move_up_btn = QtWidgets.QPushButton("Move up")
        move_down_btn = QtWidgets.QPushButton("Move down")
        for b in (add_tab_btn, add_pane_h_btn, add_pane_v_btn, remove_btn, move_up_btn, move_down_btn):
            btn_row.addWidget(b)

        sb_layout.addLayout(btn_row)
        self.steps_list = QtWidgets.QListWidget()
        sb_layout.addWidget(self.steps_list)

        editor_box = QtWidgets.QGroupBox("Step editor")
        ed_layout = QtWidgets.QHBoxLayout()

        self.profile_combo = QtWidgets.QComboBox()
        self.profile_combo.setEditable(True)
        self.profile_combo.addItems([""] + self.profile_names)

        self.scheme_combo = QtWidgets.QComboBox()
        self.scheme_combo.setEditable(True)
        self.scheme_combo.addItems([""] + self.scheme_names)

        self.title_edit = QtWidgets.QLineEdit()
        self.title_edit.setPlaceholderText("Optional title")

        self.tab_color_edit = QtWidgets.QLineEdit()
        self.tab_color_edit.setPlaceholderText("#RRGGBB or #RGB")
        pick_btn = QtWidgets.QPushButton("Pick…")
        pick_btn.clicked.connect(self.pick_color)

        self.dir_edit = QtWidgets.QLineEdit()
        self.dir_edit.setPlaceholderText("Starting directory")
        dir_btn = QtWidgets.QPushButton("Browse…")
        dir_btn.clicked.connect(self.browse_dir)

        self.cmdline_edit = QtWidgets.QLineEdit()
        self.cmdline_edit.setPlaceholderText("Optional raw commandline (overrides -p)")

        self.pane_size_spin = QtWidgets.QDoubleSpinBox()
        self.pane_size_spin.setRange(0.05, 0.95)
        self.pane_size_spin.setSingleStep(0.05)
        self.pane_size_spin.setDecimals(2)
        self.pane_size_spin.setValue(0.5)

        apply_btn = QtWidgets.QPushButton("Apply to selected step")

        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Profile (-p)"))
        left.addWidget(self.profile_combo)
        left.addWidget(QtWidgets.QLabel("Color scheme (--colorScheme)"))
        left.addWidget(self.scheme_combo)
        left.addWidget(QtWidgets.QLabel("Title (--title)"))
        left.addWidget(self.title_edit)

        mid = QtWidgets.QVBoxLayout()
        mid.addWidget(QtWidgets.QLabel("Tab color (--tabColor)"))
        trow = QtWidgets.QHBoxLayout()
        trow.addWidget(self.tab_color_edit)
        trow.addWidget(pick_btn)
        mid.addLayout(trow)
        mid.addWidget(QtWidgets.QLabel("Starting directory (-d)"))
        drow = QtWidgets.QHBoxLayout()
        drow.addWidget(self.dir_edit)
        drow.addWidget(dir_btn)
        mid.addLayout(drow)
        mid.addWidget(QtWidgets.QLabel("Raw commandline (overrides -p)"))
        mid.addWidget(self.cmdline_edit)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("Split pane size (--size, fraction)"))
        right.addWidget(self.pane_size_spin)
        right.addStretch()
        right.addWidget(apply_btn)

        ed_layout.addLayout(left)
        ed_layout.addLayout(mid)
        ed_layout.addLayout(right)
        editor_box.setLayout(ed_layout)

        sb_layout.addWidget(editor_box)
        steps_box.setLayout(sb_layout)
        root.addWidget(steps_box)

        # Preview / actions
        preview_box = QtWidgets.QGroupBox("Command preview")
        pv_layout = QtWidgets.QVBoxLayout()
        self.preview = QtWidgets.QTextEdit()
        self.preview.setReadOnly(False)
        self.preview.setPlaceholderText("Command preview - You can also paste or type commands here and click 'Parse Command'")
        pv_layout.addWidget(self.preview)
        run_row = QtWidgets.QHBoxLayout()
        parse_btn = QtWidgets.QPushButton("Parse Command")
        parse_btn.setToolTip("Parse the command from the preview box and populate the builder")
        copy_btn = QtWidgets.QPushButton("Copy")
        run_btn = QtWidgets.QPushButton("Run")
        self.shell_combo = QtWidgets.QComboBox()
        self.shell_combo.addItems(["PowerShell (escape `;)", "CMD (plain ;)"])
        run_row.addWidget(QtWidgets.QLabel("Shell:"))
        run_row.addWidget(self.shell_combo)
        run_row.addStretch(1)
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
        apply_btn.clicked.connect(self.apply_step)
        self.steps_list.currentItemChanged.connect(self.populate_editor_from_selection)
        self.shell_combo.currentIndexChanged.connect(self.refresh_preview)
        parse_btn.clicked.connect(self.parse_command)
        copy_btn.clicked.connect(self.copy_command)
        run_btn.clicked.connect(self.run_command)

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

        self.foldersTreeWidget = QtWidgets.QTreeWidget()
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
        self.deleteFolderButton.setStyleSheet("QPushButton { background-color: #d32f2f; color: white; }")
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
        help_label.setStyleSheet("QLabel { background-color: #f0f0f0; color: #000000; padding: 10px; border: 1px solid #ccc; }")

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

    def setUnsavedChanges(self):
        self.unsaved_changes = True
        self.statusLabel.setText("Unsaved changes - Click Save to apply")
        self.statusLabel.setStyleSheet("QLabel { color: orange; }")

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
            data_schemes['profiles']['list'][currentProfileIndex]['fontSize'] = param
            self.setUnsavedChanges()

    def changeFont(self, param):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['fontFace'] = self.fontBox.itemText(param)
            self.setUnsavedChanges()

    def changeOpacity(self):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            sliderValue = self.horizontalSlider.value()
            opacity = sliderValue / 10
            data_schemes["profiles"]["list"][currentProfileIndex]["backgroundImageOpacity"] = opacity
            self.opacityValueLabel.setText(str(opacity))
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

        # Update font
        fontFace = profile.get('fontFace', 'Cascadia Mono')
        index_fontBox = self.fontBox.findText(fontFace, QtCore.Qt.MatchFlag.MatchFixedString)
        if index_fontBox >= 0:
            self.fontBox.setCurrentIndex(index_fontBox)

        # Update font size
        self.fontSize.setValue(profile.get('fontSize', 12))

        # Update background image
        self.backgroundImageEdit.setText(profile.get('backgroundImage', ''))

        # Update opacity
        opacity = profile.get('backgroundImageOpacity', 1.0)
        self.horizontalSlider.setValue(int(opacity * 10))
        self.opacityValueLabel.setText(str(opacity))

        # Update command line
        self.commandLineEdit.setText(profile.get('commandline', ''))

        # Update starting directory
        self.startingDirectoryEdit.setText(profile.get('startingDirectory', ''))

        # Update tab title
        self.tabTitleEdit.setText(profile.get('tabTitle', ''))

        # Update icon
        self.iconEdit.setText(profile.get('icon', ''))

        # Update padding
        self.paddingEdit.setText(profile.get('padding', ''))

        # Update cursor shape
        cursorShape = profile.get('cursorShape', 'bar')
        index = self.cursorShapeBox.findText(cursorShape, QtCore.Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.cursorShapeBox.setCurrentIndex(index)

        # Update scrollbar state
        scrollbarState = profile.get('scrollbarState', 'visible')
        index = self.scrollbarBox.findText(scrollbarState, QtCore.Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.scrollbarBox.setCurrentIndex(index)

        # Update checkboxes
        self.runAsAdminCheckBox.setChecked(profile.get('elevate', False))
        self.useAcrylicCheckBox.setChecked(profile.get('useAcrylic', False))
        self.hiddenCheckBox.setChecked(profile.get('hidden', False))
        self.snapOnInputCheckBox.setChecked(profile.get('snapOnInput', True))

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
        updated_profiles = []
        for name in new_order:
            for profile in profiles:
                if profile.get('name') == name:
                    updated_profiles.append(profile)
                    break
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
        self.actionsListWidget.clear()
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
                # Handle unbound keys (id: null)
                if 'UNBOUND_KEYS' not in id_to_keys:
                    id_to_keys['UNBOUND_KEYS'] = []
                id_to_keys['UNBOUND_KEYS'].append(keys)

        # Display actions with their associated key bindings
        for i, action in enumerate(actions):
            if isinstance(action, dict):
                # Get action details
                action_id = action.get('id', '')
                name = action.get('name', '')
                command = action.get('command', '')

                # Get command string for display
                command_str = ''
                if isinstance(command, dict):
                    command_str = command.get('action', 'complex_command')
                    if not command_str or command_str == 'complex_command':
                        if command:
                            command_str = list(command.keys())[0] if command else 'unknown'
                elif isinstance(command, str):
                    command_str = command
                else:
                    command_str = str(command) if command else 'unbound'

                # Get associated key bindings for this action ID
                associated_keys = id_to_keys.get(action_id, [])
                keys_display = ', '.join(associated_keys) if associated_keys else ''

                # Create display text
                if keys_display:
                    display_text = f"🔗 [{keys_display}] {name or action_id} → {command_str}"
                else:
                    display_text = f"⚪ [UNBOUND] {name or action_id} → {command_str}"

                # Add ID info for reference
                if action_id:
                    display_text += f" (ID: {action_id})"

                self.actionsListWidget.addItem(display_text)

        # Also show unbound key bindings (keys without valid action IDs)
        unbound_keys = id_to_keys.get('UNBOUND_KEYS', [])
        for key in unbound_keys:
            display_text = f"❌ [{key}] DISABLED/UNBOUND → null"
            self.actionsListWidget.addItem(display_text)

    def onActionSelectionChanged(self):
        current_row = self.actionsListWidget.currentRow()
        actions = data_schemes.get('actions', [])
        keybindings = data_schemes.get('keybindings', [])

        # Clear fields first
        self.actionNameEdit.clear()
        self.commandActionCombo.setCurrentText('')
        self.keysEdit.clear()
        self.actionArgsEdit.clear()
        self.iconPathEdit.clear()
        self.actionIdEdit.clear()

        # Check if this is an unbound key entry (these appear after regular actions)
        if current_row >= len(actions):
            # This is an unbound key entry
            unbound_index = current_row - len(actions)
            unbound_keys = []
            for binding in keybindings:
                if binding.get('id') is None:
                    unbound_keys.append(binding.get('keys', ''))

            if unbound_index < len(unbound_keys):
                self.keysEdit.setText(unbound_keys[unbound_index])
                self.actionNameEdit.setText("DISABLED/UNBOUND")
                self.commandActionCombo.setCurrentText("null")
            return

        # Regular action entry
        if current_row >= 0 and current_row < len(actions):
            action = actions[current_row]

            # Get action details
            action_id = action.get('id', '')
            self.actionIdEdit.setText(action_id)
            self.actionNameEdit.setText(action.get('name', ''))

            # Find associated key bindings for this action ID
            associated_keys = []
            for binding in keybindings:
                if binding.get('id') == action_id:
                    key = binding.get('keys', '')
                    if key:
                        associated_keys.append(key)

            # Display keys
            self.keysEdit.setText(', '.join(associated_keys))

            # Populate command and arguments
            command = action.get('command', '')
            if isinstance(command, dict):
                # Complex command with arguments
                command_action = command.get('action', '')
                if command_action:
                    self.commandActionCombo.setCurrentText(command_action)
                else:
                    # If no 'action' key, use the first key as command
                    if command:
                        first_key = list(command.keys())[0]
                        self.commandActionCombo.setCurrentText(first_key)

                # Show full JSON in arguments field
                self.actionArgsEdit.setPlainText(commentjson.dumps(command, indent=2))
            elif isinstance(command, str):
                # Simple string command
                self.commandActionCombo.setCurrentText(command)
                self.actionArgsEdit.setPlainText('')
            else:
                # Handle other types
                self.commandActionCombo.setCurrentText(str(command) if command else '')
                if command and not isinstance(command, str):
                    self.actionArgsEdit.setPlainText(commentjson.dumps(command, indent=2))

            # Populate icon path
            self.iconPathEdit.setText(action.get('icon', ''))

    def updateAction(self):
        current_row = self.actionsListWidget.currentRow()
        actions = data_schemes.get('actions', [])
        keybindings = data_schemes.get('keybindings', [])

        # Check if this is an unbound key entry
        if current_row >= len(actions):
            # Handle unbound key modification
            unbound_index = current_row - len(actions)
            unbound_bindings = [b for b in keybindings if b.get('id') is None]

            if unbound_index < len(unbound_bindings):
                binding = unbound_bindings[unbound_index]
                new_keys = self.keysEdit.text().strip()
                if new_keys:
                    binding['keys'] = new_keys
                else:
                    # Remove the binding if no keys
                    keybindings.remove(binding)

            self.loadActions()
            self.setUnsavedChanges()
            return

        # Regular action update
        if current_row >= 0 and current_row < len(actions):
            action = actions[current_row]
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
                    # Try to parse as JSON for complex commands
                    args = commentjson.loads(args_text)
                    action['command'] = args
                except:
                    # If JSON parsing fails, use simple command
                    simple_command = self.commandActionCombo.currentText().strip()
                    if simple_command:
                        action['command'] = simple_command
                    else:
                        action['command'] = args_text
            else:
                # Use simple command from combo box
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
                # Split multiple keys
                key_list = [key.strip() for key in keys_text.split(',') if key.strip()]
                for key in key_list:
                    new_binding = {
                        'id': new_action_id,
                        'keys': key
                    }
                    keybindings.append(new_binding)

            self.loadActions()
            self.actionsListWidget.setCurrentRow(current_row)
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
        # Select the newly added action
        self.actionsListWidget.setCurrentRow(len(data_schemes['actions']) - 1)
        self.setUnsavedChanges()

    def deleteAction(self):
        current_row = self.actionsListWidget.currentRow()
        actions = data_schemes.get('actions', [])
        keybindings = data_schemes.get('keybindings', [])

        # Check if this is an unbound key entry
        if current_row >= len(actions):
            # Handle deleting unbound key
            unbound_index = current_row - len(actions)
            unbound_bindings = [b for b in keybindings if b.get('id') is None]

            if unbound_index < len(unbound_bindings):
                reply = QtWidgets.QMessageBox.question(None, 'Delete Unbound Key',
                                                     'Are you sure you want to delete this unbound key binding?',
                                                     QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Discard | QtWidgets.QMessageBox.StandardButton.Cancel)
                if reply == QtWidgets.QMessageBox.StandardButton.Save:
                    binding_to_remove = unbound_bindings[unbound_index]
                    keybindings.remove(binding_to_remove)
                    self.loadActions()
                    self.setUnsavedChanges()
                    self.clearActionFields()
            return

        # Regular action deletion
        if current_row >= 0 and current_row < len(actions):
            # Ask for confirmation
            action = actions[current_row]
            action_name = action.get('name', action.get('id', f'Action {current_row + 1}'))
            reply = QtWidgets.QMessageBox.question(None, 'Delete Action',
                                                 f'Are you sure you want to delete "{action_name}" and all its key bindings?',
                                                 QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                action_id = action.get('id')

                # Remove the action
                del actions[current_row]

                # Remove associated key bindings
                if action_id:
                    keybindings[:] = [b for b in keybindings if b.get('id') != action_id]

                self.loadActions()
                self.setUnsavedChanges()
                self.clearActionFields()

                # Select next available item
                if current_row < self.actionsListWidget.count():
                    self.actionsListWidget.setCurrentRow(current_row)
                elif self.actionsListWidget.count() > 0:
                    self.actionsListWidget.setCurrentRow(self.actionsListWidget.count() - 1)

    def moveActionUp(self):
        current_row = self.actionsListWidget.currentRow()
        if current_row > 0:
            actions = data_schemes.get('actions', [])
            actions[current_row], actions[current_row - 1] = actions[current_row - 1], actions[current_row]
            self.loadActions()
            self.actionsListWidget.setCurrentRow(current_row - 1)
            self.setUnsavedChanges()

    def moveActionDown(self):
        current_row = self.actionsListWidget.currentRow()
        actions = data_schemes.get('actions', [])
        if current_row >= 0 and current_row < len(actions) - 1:
            actions[current_row], actions[current_row + 1] = actions[current_row + 1], actions[current_row]
            self.loadActions()
            self.actionsListWidget.setCurrentRow(current_row + 1)
            self.setUnsavedChanges()

    def clearActionFields(self):
        """Helper method to clear all action input fields"""
        self.actionNameEdit.clear()
        self.actionIdEdit.clear()
        self.commandActionCombo.setCurrentText('')
        self.keysEdit.clear()
        self.actionArgsEdit.clear()
        self.iconPathEdit.clear()

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
        if step.starting_directory:
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
        step: CommandStep = current.data(QtCore.Qt.ItemDataRole.UserRole)
        self.profile_combo.setCurrentText(step.profile_name or "")
        self.scheme_combo.setCurrentText(step.color_scheme or "")
        self.title_edit.setText(step.title or "")
        self.tab_color_edit.setText(step.tab_color or "")
        self.dir_edit.setText(step.starting_directory or "")
        self.cmdline_edit.setText(step.commandline or "")
        if step.kind == "split-pane" and step.pane_size is not None:
            self.pane_size_spin.setValue(step.pane_size)
        else:
            self.pane_size_spin.setValue(0.5)

    def apply_step(self):
        item = self.steps_list.currentItem()
        if not item:
            return
        step: CommandStep = item.data(QtCore.Qt.ItemDataRole.UserRole)
        step.profile_name = self.profile_combo.currentText().strip()
        step.color_scheme = self.scheme_combo.currentText().strip()
        step.title = self.title_edit.text().strip()
        step.tab_color = self.tab_color_edit.text().strip()
        step.starting_directory = self.dir_edit.text().strip()
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

            # Starting directory
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
                           r'--colorScheme\s+"[^"]+"', r'--size\s+[\d.]+']:
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

    def loadFolders(self):
        """Load the newTabMenu structure into the tree widget"""
        debug_print(f"DEBUG loadFolders: Clearing tree and reloading from data_schemes")
        debug_print(f"DEBUG loadFolders: data_schemes has {len(data_schemes.get('newTabMenu', []))} root items")

        self.foldersTreeWidget.clear()
        new_tab_menu = data_schemes.get('newTabMenu', [])

        for i, entry in enumerate(new_tab_menu):
            debug_print(f"DEBUG loadFolders: Adding item {i}: type={entry.get('type')}, name={entry.get('name', 'N/A')}")
            self.addTreeItem(entry, self.foldersTreeWidget)

        debug_print(f"DEBUG loadFolders: Tree now has {self.foldersTreeWidget.topLevelItemCount()} top-level items")

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
            # Expand remainingProfiles to show actual profiles
            item = QtWidgets.QTreeWidgetItem(parent, ["Remaining Profiles", "📋 Auto-Generated"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)
            item.setForeground(0, QtGui.QBrush(QtGui.QColor("#888888")))  # Gray text

            # Find which profiles are already in the menu
            assigned_guids = self.getAssignedProfileGuids()

            # Add all unassigned profiles as children
            for profile in data_schemes.get('profiles', {}).get('list', []):
                guid = profile.get('guid')
                name = profile.get('name', 'Unknown')
                if guid and guid not in assigned_guids:
                    # Create a virtual profile entry
                    virtual_entry = {
                        'type': 'profile',
                        'profile': guid,
                        'icon': None
                    }
                    child_item = QtWidgets.QTreeWidgetItem(item, [name, "👤 Unassigned"])
                    child_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, virtual_entry)
                    child_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#0066CC")))  # Blue text

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

    def onFolderSelectionChanged(self):
        """Handle folder tree selection change"""
        current_item = self.foldersTreeWidget.currentItem()

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
            'inline': 'never'
        }

        # Determine where to add
        current_item = self.foldersTreeWidget.currentItem()
        parent_entry = None
        if current_item:
            parent_entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if parent_entry and parent_entry.get('type') == 'folder':
                # Add to selected folder - find the actual folder in data_schemes
                actual_folder = self.findActualEntry(parent_entry)
                if actual_folder:
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
            'icon': None
        }

        # Determine where to add based on selection
        current_item = self.foldersTreeWidget.currentItem()
        target_parent = None
        added_location = "unknown"

        if current_item:
            current_entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            debug_print(f"DEBUG addProfileToMenu: Current selection type: {current_entry.get('type') if current_entry else 'None'}")

            if current_entry and current_entry.get('type') == 'folder':
                # Selected item is a folder - find the actual folder in data_schemes
                actual_folder = self.findActualEntry(current_entry)
                if actual_folder:
                    if 'entries' not in actual_folder:
                        actual_folder['entries'] = []
                    actual_folder['entries'].append(new_profile_entry)
                    target_parent = actual_folder
                    added_location = f"folder '{actual_folder.get('name')}'"
                    debug_print(f"DEBUG addProfileToMenu: Added to folder: {actual_folder.get('name')}, now has {len(actual_folder['entries'])} entries")
                else:
                    debug_print(f"DEBUG addProfileToMenu: Could not find actual folder entry")
                    QtWidgets.QMessageBox.warning(None, "Error", "Could not find folder in settings data.")
                    return
            else:
                # Selected item is NOT a folder - try to add to parent folder
                parent_item = current_item.parent()
                if parent_item:
                    parent_entry = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if parent_entry and parent_entry.get('type') == 'folder':
                        # Find the actual parent folder in data_schemes
                        actual_parent = self.findActualEntry(parent_entry)
                        if actual_parent:
                            if 'entries' not in actual_parent:
                                actual_parent['entries'] = []
                            actual_parent['entries'].append(new_profile_entry)
                            target_parent = actual_parent
                            added_location = f"parent folder '{actual_parent.get('name')}'"
                            debug_print(f"DEBUG addProfileToMenu: Added to parent folder: {actual_parent.get('name')}")
                        else:
                            debug_print(f"DEBUG addProfileToMenu: Could not find actual parent folder entry")
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
            'type': 'separator'
        }

        # Determine where to add based on selection
        current_item = self.foldersTreeWidget.currentItem()
        added_location = "unknown"

        if current_item:
            current_entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

            if current_entry and current_entry.get('type') == 'folder':
                # Selected item is a folder - add to this folder
                actual_folder = self.findActualEntry(current_entry)
                if actual_folder:
                    if 'entries' not in actual_folder:
                        actual_folder['entries'] = []
                    actual_folder['entries'].append(new_separator)
                    added_location = f"folder '{actual_folder.get('name')}'"
                    debug_print(f"DEBUG addSeparator: Added to folder: {actual_folder.get('name')}")
                else:
                    debug_print("DEBUG addSeparator: Could not find actual folder entry")
                    QtWidgets.QMessageBox.warning(None, "Error", "Could not find folder in settings data.")
                    return
            else:
                # Selected item is NOT a folder - try to add to parent folder
                parent_item = current_item.parent()
                if parent_item:
                    parent_entry = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if parent_entry and parent_entry.get('type') == 'folder':
                        # Find the actual parent folder in data_schemes
                        actual_parent = self.findActualEntry(parent_entry)
                        if actual_parent:
                            if 'entries' not in actual_parent:
                                actual_parent['entries'] = []
                            actual_parent['entries'].append(new_separator)
                            added_location = f"parent folder '{actual_parent.get('name')}'"
                            debug_print(f"DEBUG addSeparator: Added to parent folder: {actual_parent.get('name')}")
                        else:
                            debug_print("DEBUG addSeparator: Could not find actual parent folder entry")
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

        # Find the actual entry in data_schemes BEFORE modifying anything
        actual_entry = self.findActualEntry(entry)
        if not actual_entry:
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find entry in settings data.")
            debug_print(f"DEBUG updateFolderItem: Could not find entry in data_schemes: {entry}")
            return

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
            actual_entry['icon'] = icon_text if icon_text else None
            actual_entry['allowEmpty'] = self.allowEmptyCheckBox.isChecked()
            actual_entry['inline'] = 'always' if self.inlineCheckBox.isChecked() else 'never'

            debug_print(f"DEBUG updateFolderItem: Actual entry updated: {actual_entry}")

        elif entry_type == 'profile':
            profile_name = self.menuProfileCombo.currentText()
            profile_guid = self.getProfileGuidByName(profile_name)
            if profile_guid:
                actual_entry['profile'] = profile_guid
            icon_text = self.profileIconEdit.text().strip()
            actual_entry['icon'] = icon_text if icon_text else None

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

        # Find and remove the entry
        parent_item = current_item.parent()
        if parent_item:
            # Entry is in a folder
            parent_entry = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if parent_entry and 'entries' in parent_entry:
                parent_entry['entries'].remove(entry)
        else:
            # Entry is in root
            if 'newTabMenu' in data_schemes:
                data_schemes['newTabMenu'].remove(entry)

        self.loadFolders()
        self.setUnsavedChanges()

    def moveFolderItemUp(self):
        """Move selected item up in its parent's list"""
        debug_print("DEBUG moveFolderItemUp: Function called")
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            debug_print("DEBUG moveFolderItemUp: No item selected")
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            debug_print("DEBUG moveFolderItemUp: No entry data")
            return

        debug_print(f"DEBUG moveFolderItemUp: Moving {entry.get('type')} {entry.get('name', entry.get('profile', 'unknown'))}")

        # Find the actual entry in data_schemes
        actual_entry = self.findActualEntry(entry)
        if not actual_entry:
            debug_print(f"DEBUG moveFolderItemUp: Could not find actual entry in data_schemes")
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find item in settings data.")
            return

        debug_print(f"DEBUG moveFolderItemUp: Found actual entry, id={id(actual_entry)}")

        parent_item = current_item.parent()
        moved = False

        if parent_item:
            # Entry is in a folder - find the actual parent folder
            debug_print("DEBUG moveFolderItemUp: Item is in a folder")
            parent_entry = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            actual_parent = self.findActualEntry(parent_entry)

            if actual_parent and 'entries' in actual_parent:
                entries = actual_parent['entries']
                try:
                    # Find actual_entry in the entries list (should be by object identity now)
                    idx = entries.index(actual_entry)
                    debug_print(f"DEBUG moveFolderItemUp: Current index: {idx}, list length: {len(entries)}")
                    if idx > 0:
                        entries[idx], entries[idx - 1] = entries[idx - 1], entries[idx]
                        moved = True
                        debug_print(f"DEBUG moveFolderItemUp: Moved from {idx} to {idx-1}")
                    else:
                        debug_print("DEBUG moveFolderItemUp: Already at top of list")
                except ValueError as e:
                    debug_print(f"DEBUG moveFolderItemUp: ValueError: {e}")
            else:
                debug_print("DEBUG moveFolderItemUp: Could not find actual parent folder or it has no entries")
        else:
            # Entry is in root
            debug_print("DEBUG moveFolderItemUp: Item is at root level")
            if 'newTabMenu' in data_schemes:
                entries = data_schemes['newTabMenu']
                try:
                    # Find actual_entry in the entries list
                    idx = entries.index(actual_entry)
                    debug_print(f"DEBUG moveFolderItemUp: Current index: {idx}, list length: {len(entries)}")
                    if idx > 0:
                        entries[idx], entries[idx - 1] = entries[idx - 1], entries[idx]
                        moved = True
                        debug_print(f"DEBUG moveFolderItemUp: Moved from {idx} to {idx-1}")
                    else:
                        debug_print("DEBUG moveFolderItemUp: Already at top of list")
                except ValueError as e:
                    debug_print(f"DEBUG moveFolderItemUp: ValueError: {e}")

        if moved:
            debug_print("DEBUG moveFolderItemUp: Reloading folders")
            self.loadFolders()
            self.setUnsavedChanges()
            # Try to re-select the item (skip for separators as they're indistinguishable)
            if actual_entry.get('type') != 'separator':
                self.reselectItemByEntry(actual_entry)
        else:
            debug_print("DEBUG moveFolderItemUp: Nothing moved")

    def moveFolderItemDown(self):
        """Move selected item down in its parent's list"""
        debug_print("DEBUG moveFolderItemDown: Function called")
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            debug_print("DEBUG moveFolderItemDown: No item selected")
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            debug_print("DEBUG moveFolderItemDown: No entry data")
            return

        debug_print(f"DEBUG moveFolderItemDown: Moving {entry.get('type')} {entry.get('name', entry.get('profile', 'unknown'))}")

        # Find the actual entry in data_schemes
        actual_entry = self.findActualEntry(entry)
        if not actual_entry:
            debug_print(f"DEBUG moveFolderItemDown: Could not find actual entry in data_schemes")
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find item in settings data.")
            return

        debug_print(f"DEBUG moveFolderItemDown: Found actual entry, id={id(actual_entry)}")

        parent_item = current_item.parent()
        moved = False

        if parent_item:
            # Entry is in a folder - find the actual parent folder
            debug_print("DEBUG moveFolderItemDown: Item is in a folder")
            parent_entry = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            actual_parent = self.findActualEntry(parent_entry)

            if actual_parent and 'entries' in actual_parent:
                entries = actual_parent['entries']
                try:
                    # Find actual_entry in the entries list
                    idx = entries.index(actual_entry)
                    debug_print(f"DEBUG moveFolderItemDown: Current index: {idx}, list length: {len(entries)}")
                    if idx < len(entries) - 1:
                        entries[idx], entries[idx + 1] = entries[idx + 1], entries[idx]
                        moved = True
                        debug_print(f"DEBUG moveFolderItemDown: Moved from {idx} to {idx+1}")
                    else:
                        debug_print("DEBUG moveFolderItemDown: Already at bottom of list")
                except ValueError as e:
                    debug_print(f"DEBUG moveFolderItemDown: ValueError: {e}")
            else:
                debug_print("DEBUG moveFolderItemDown: Could not find actual parent folder or it has no entries")
        else:
            # Entry is in root
            debug_print("DEBUG moveFolderItemDown: Item is at root level")
            if 'newTabMenu' in data_schemes:
                entries = data_schemes['newTabMenu']
                try:
                    # Find actual_entry in the entries list
                    idx = entries.index(actual_entry)
                    debug_print(f"DEBUG moveFolderItemDown: Current index: {idx}, list length: {len(entries)}")
                    if idx < len(entries) - 1:
                        entries[idx], entries[idx + 1] = entries[idx + 1], entries[idx]
                        moved = True
                        debug_print(f"DEBUG moveFolderItemDown: Moved from {idx} to {idx+1}")
                    else:
                        debug_print("DEBUG moveFolderItemDown: Already at bottom of list")
                except ValueError as e:
                    debug_print(f"DEBUG moveFolderItemDown: ValueError: {e}")

        if moved:
            debug_print("DEBUG moveFolderItemDown: Reloading folders")
            self.loadFolders()
            self.setUnsavedChanges()
            # Try to re-select the item (skip for separators as they're indistinguishable)
            if actual_entry.get('type') != 'separator':
                self.reselectItemByEntry(actual_entry)
        else:
            debug_print("DEBUG moveFolderItemDown: Nothing moved")

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
        """Re-select an item in the tree after reload"""
        def findItem(parent_item, target_entry):
            for i in range(parent_item.childCount() if parent_item else self.foldersTreeWidget.topLevelItemCount()):
                item = parent_item.child(i) if parent_item else self.foldersTreeWidget.topLevelItem(i)
                item_entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)

                # Use identity comparison to match exact object (important for separators)
                # Since UserRole stores a copy, we need to match by properties
                entry_type = target_entry.get('type')
                if entry_type == 'separator':
                    # For separators, we can't distinguish them, so just match any separator
                    # This is a known limitation
                    if item_entry.get('type') == 'separator':
                        return item
                elif entry_type == 'folder':
                    # Match folder by name
                    if item_entry.get('type') == 'folder' and item_entry.get('name') == target_entry.get('name'):
                        return item
                elif entry_type == 'profile':
                    # Match profile by GUID
                    if item_entry.get('type') == 'profile' and item_entry.get('profile') == target_entry.get('profile'):
                        return item

                # Recursively search children
                found = findItem(item, target_entry)
                if found:
                    return found
            return None

        item = findItem(None, entry)
        if item:
            self.foldersTreeWidget.setCurrentItem(item)
            self.foldersTreeWidget.scrollToItem(item)

    # ========== Save Method ==========

    def dumpOnSave(self):
        if dumpJson():
            self.unsaved_changes = False
            self.statusLabel.setText("Settings saved successfully!")
            self.statusLabel.setStyleSheet("QLabel { color: green; }")
            QtCore.QTimer.singleShot(3000, lambda: self.statusLabel.setText(""))
        else:
            self.statusLabel.setText("Error saving settings!")
            self.statusLabel.setStyleSheet("QLabel { color: red; }")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    app.setStyle('Fusion')

    # Try to load the icon
    icon_path = 'wt3.ico'
    if os.path.exists(icon_path):
        icon = QtGui.QIcon(icon_path)
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
