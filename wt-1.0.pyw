from shutil import copyfile
from PyQt5 import QtCore, QtGui, QtWidgets
import commentjson
import os
import matplotlib.font_manager
import datetime

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

class Ui_MainWindow(object):
    def __init__(self):
        self.unsaved_changes = False
        self.ui_initialized = False
        
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Windows Terminal Settings")
        MainWindow.resize(1400, 900)
        MainWindow.setWindowTitle("Windows Terminal Settings Editor")
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
        self.tabWidget.addTab(self.profilesTab, "Profiles")
        self.tabWidget.addTab(self.actionsTab, "Actions & Key Bindings")
        
        self.setupProfilesTab()
        self.setupActionsTab()
        
        # Bottom panel with save button and status
        bottom_layout = QtWidgets.QHBoxLayout()
        
        # Status label
        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setAlignment(QtCore.Qt.AlignCenter)
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
        profiles_label.setFont(QtGui.QFont("", 10, QtGui.QFont.Bold))
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
        left_layout.addStretch()
        
        main_layout.addWidget(left_widget)
        
        # Right side - Profile details
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        
        # Profile details in scroll area
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
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
        self.horizontalSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
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
        
        self.iconEdit = QtWidgets.QLineEdit()
        scroll_layout.addRow("Icon:", self.iconEdit)
        
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
        self.comboBox.activated[int].connect(self.changeScheme)
        self.fontBox.activated[int].connect(self.changeFont)
        self.fontSize.valueChanged[int].connect(self.changeFontSize)
        self.pushButton.clicked.connect(self.changeBackgroundImage)
        self.horizontalSlider.sliderReleased.connect(self.changeOpacity)
        self.commandLineEdit.textChanged[str].connect(self.changeCommandLine)
        self.startingDirectoryEdit.textChanged[str].connect(self.changeStartingDirectory)
        self.tabTitleEdit.textChanged[str].connect(self.changeTabTitle)
        self.iconEdit.textChanged[str].connect(self.changeIcon)
        self.paddingEdit.textChanged[str].connect(self.changePadding)
        self.cursorShapeBox.activated[str].connect(self.changeCursorShape)
        self.scrollbarBox.activated[str].connect(self.changeScrollbarState)
        self.runAsAdminCheckBox.stateChanged.connect(self.changeRunAsAdmin)
        self.useAcrylicCheckBox.stateChanged.connect(self.changeUseAcrylic)
        self.hiddenCheckBox.stateChanged.connect(self.changeHidden)
        self.snapOnInputCheckBox.stateChanged.connect(self.changeSnapOnInput)
        self.defaultButton.clicked.connect(self.changeDefault)
        self.moveUpButton.clicked.connect(self.moveProfileUp)
        self.moveDownButton.clicked.connect(self.moveProfileDown)
        self.renameButton.clicked.connect(self.renameProfile)
        
        # Set initial selection
        index_listWidget = self.listWidget.findItems(default_profile, QtCore.Qt.MatchFixedString)
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
        actions_label.setFont(QtGui.QFont("", 10, QtGui.QFont.Bold))
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
        self.keyHelperLabel.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        
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
                                                     QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
                if reply == QtWidgets.QMessageBox.Save:
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
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
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
            data_schemes['profiles']['list'][currentProfileIndex]['elevate'] = (state == QtCore.Qt.Checked)
            self.setUnsavedChanges()

    def changeUseAcrylic(self, state):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['useAcrylic'] = (state == QtCore.Qt.Checked)
            self.setUnsavedChanges()

    def changeHidden(self, state):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['hidden'] = (state == QtCore.Qt.Checked)
            self.setUnsavedChanges()

    def changeSnapOnInput(self, state):
        currentProfileIndex = self.getCurrentIndex()
        if currentProfileIndex >= 0:
            data_schemes['profiles']['list'][currentProfileIndex]['snapOnInput'] = (state == QtCore.Qt.Checked)
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
        index = self.comboBox.findText(colorScheme, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.comboBox.setCurrentIndex(index)
        
        # Update font
        fontFace = profile.get('fontFace', 'Cascadia Mono')
        index_fontBox = self.fontBox.findText(fontFace, QtCore.Qt.MatchFixedString)
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
        index = self.cursorShapeBox.findText(cursorShape, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.cursorShapeBox.setCurrentIndex(index)
        
        # Update scrollbar state
        scrollbarState = profile.get('scrollbarState', 'visible')
        index = self.scrollbarBox.findText(scrollbarState, QtCore.Qt.MatchFixedString)
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
                                                          QtWidgets.QLineEdit.Normal, currentItem.text())
            if ok and newName.strip():
                currentItem.setText(newName.strip())
                data_schemes['profiles']['list'][currentRow]['name'] = newName.strip()
                self.profileNameEdit.setText(newName.strip())
                self.setUnsavedChanges()

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
    import sys
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
                                                   QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Save:
                ui.dumpOnSave()
                event.accept()
            elif reply == QtWidgets.QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    
    MainWindow.closeEvent = closeEvent
    sys.exit(app.exec_())