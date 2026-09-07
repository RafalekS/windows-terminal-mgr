"""Actions & Key Bindings tab: table of actions/keybindings with a
type-aware editor, key recorder, and column-width persistence."""

import uuid as _uuid

import commentjson
from PyQt6 import QtCore, QtGui, QtWidgets

from modules import app_state
from modules import themes
from modules.constants import COMMON_ACTIONS, PANE_DIRECTIONS, RESIZE_DIRECTIONS, SWAP_DIRECTIONS
from modules.widgets import KeyRecorderDialog

_ACTIONS_COL_DEFAULTS = [140, 200, 160, 140]


class ActionsMixin:
    """Actions tab UI + behaviour. Mixed into ``Ui_MainWindow``."""

    # ────────────────────────────────────────────────────────────────────
    #  UI construction
    # ────────────────────────────────────────────────────────────────────
    def setupActionsTab(self):
        profiles_list = app_state.profiles_list

        main_layout = QtWidgets.QVBoxLayout(self.actionsTab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.actionsFilterEdit = QtWidgets.QLineEdit()
        self.actionsFilterEdit.setPlaceholderText("Type to filter actions...")
        self.actionsFilterEdit.textChanged.connect(self.filterActions)
        filter_layout.addWidget(self.actionsFilterEdit)
        main_layout.addLayout(filter_layout)

        self.actionsTable = QtWidgets.QTableWidget()
        self.actionsTable.setColumnCount(4)
        self.actionsTable.setHorizontalHeaderLabels(["Shortcut", "Name", "Command", "ID"])
        self.actionsTable.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.actionsTable.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.actionsTable.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.actionsTable.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.actionsTable.horizontalHeader().setSectionsMovable(True)
        self.actionsTable.verticalHeader().setVisible(False)
        self.actionsTable.setAlternatingRowColors(True)
        for i, w in enumerate(_ACTIONS_COL_DEFAULTS):
            self.actionsTable.setColumnWidth(i, w)
        main_layout.addWidget(self.actionsTable, 3)

        # ── Editor ──
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

        self.actionTypeCombo = QtWidgets.QComboBox()
        self.actionTypeCombo.addItems([
            "Run Command (New Tab)", "Run Command (Split Pane)", "Send Text to Terminal",
            "Built-in Action", "Pane: Move Focus", "Pane: Resize", "Pane: Swap",
            "Pane: Move to Tab",
        ])
        editor_layout.addRow("Action Type:", self.actionTypeCombo)

        self.actionStack = QtWidgets.QStackedWidget()

        # Page 0: Run Command (New Tab / Split Pane)
        run_page = QtWidgets.QWidget()
        run_layout = QtWidgets.QFormLayout(run_page)
        run_layout.setSpacing(6)
        run_layout.setContentsMargins(0, 0, 0, 0)

        cmd_row = QtWidgets.QHBoxLayout()
        self.actCmdEdit = QtWidgets.QLineEdit()
        self.actCmdEdit.setPlaceholderText("e.g. cmd.exe /c c:\\Scripts\\start.cmd  or  wsl.exe")
        self.actCmdEdit.setToolTip("The executable + args to run. For scripts use: cmd.exe /c script.cmd")
        act_cmd_browse = QtWidgets.QPushButton("Browse...")
        act_cmd_browse.setMinimumWidth(90)
        act_cmd_browse.setToolTip("Browse for a script or executable")
        act_cmd_browse.clicked.connect(self._browseActionScript)
        cmd_row.addWidget(self.actCmdEdit)
        cmd_row.addWidget(act_cmd_browse)
        run_layout.addRow("Command/Script:", cmd_row)

        self.actProfileCombo = QtWidgets.QComboBox()
        self.actProfileCombo.setEditable(True)
        self.actProfileCombo.addItems(["(default)"] + profiles_list)
        self.actProfileCombo.setToolTip(
            "Which profile to use (leave as default for current default profile)")
        run_layout.addRow("Profile:", self.actProfileCombo)

        dir_row = QtWidgets.QHBoxLayout()
        self.actDirEdit = QtWidgets.QLineEdit()
        self.actDirEdit.setPlaceholderText("Working directory (optional)")
        act_dir_browse = QtWidgets.QPushButton("Browse...")
        act_dir_browse.setMinimumWidth(90)
        act_dir_browse.setToolTip("Browse for a working directory")
        act_dir_browse.clicked.connect(self._browseActionDir)
        dir_row.addWidget(self.actDirEdit)
        dir_row.addWidget(act_dir_browse)
        run_layout.addRow("Working Dir:", dir_row)

        self.actTitleEdit = QtWidgets.QLineEdit()
        self.actTitleEdit.setPlaceholderText("Tab title (optional)")
        run_layout.addRow("Tab Title:", self.actTitleEdit)

        self.splitOptsWidget = QtWidgets.QWidget()
        split_opts_layout = QtWidgets.QHBoxLayout(self.splitOptsWidget)
        split_opts_layout.setContentsMargins(0, 0, 0, 0)
        self.actSplitH = QtWidgets.QRadioButton("Horizontal")
        self.actSplitV = QtWidgets.QRadioButton("Vertical")
        self.actSplitH.setChecked(True)
        split_opts_layout.addWidget(self.actSplitH)
        split_opts_layout.addWidget(self.actSplitV)
        split_opts_layout.addWidget(QtWidgets.QLabel("Size:"))
        self.actSplitSize = QtWidgets.QDoubleSpinBox()
        self.actSplitSize.setRange(0.05, 0.95)
        self.actSplitSize.setSingleStep(0.05)
        self.actSplitSize.setValue(0.5)
        self.actSplitSize.setToolTip("Fraction of parent pane (0.05 to 0.95)")
        split_opts_layout.addWidget(self.actSplitSize)
        split_opts_layout.addStretch()
        run_layout.addRow("Split:", self.splitOptsWidget)
        self.splitOptsWidget.setVisible(False)
        self.actionStack.addWidget(run_page)  # 0

        # Page 1: Send Text
        send_page = QtWidgets.QWidget()
        send_layout = QtWidgets.QFormLayout(send_page)
        send_layout.setSpacing(6)
        send_layout.setContentsMargins(0, 0, 0, 0)
        self.actSendText = QtWidgets.QLineEdit()
        self.actSendText.setPlaceholderText("e.g. git status  or  tmux  or  ping 192.168.0.1")
        self.actSendText.setToolTip("Text that will be typed into the current terminal")
        send_layout.addRow("Text:", self.actSendText)
        self.actSendEnter = QtWidgets.QCheckBox("Press Enter after sending")
        self.actSendEnter.setChecked(True)
        self.actSendEnter.setToolTip("Append a newline so the command runs immediately")
        send_layout.addRow("", self.actSendEnter)
        self.actionStack.addWidget(send_page)  # 1

        # Page 2: Built-in Action
        builtin_page = QtWidgets.QWidget()
        builtin_layout = QtWidgets.QFormLayout(builtin_page)
        builtin_layout.setSpacing(6)
        builtin_layout.setContentsMargins(0, 0, 0, 0)
        self.commandActionCombo = QtWidgets.QComboBox()
        self.commandActionCombo.setEditable(True)
        for action in COMMON_ACTIONS:
            self.commandActionCombo.addItem(action)
        self.commandActionCombo.setToolTip("Select or type a Windows Terminal built-in action")
        builtin_layout.addRow("Command:", self.commandActionCombo)
        self.actionStack.addWidget(builtin_page)  # 2

        # Pages 3-6: pane direction / index
        self.moveFocusDirCombo = self._simpleComboPage(PANE_DIRECTIONS,
                                                       "Direction to move focus between panes")
        self.resizePaneDirCombo = self._simpleComboPage(RESIZE_DIRECTIONS,
                                                        "Direction to expand the pane")
        self.swapPaneDirCombo = self._simpleComboPage(SWAP_DIRECTIONS,
                                                      "Direction to swap pane with")

        move_tab_page = QtWidgets.QWidget()
        mt_layout = QtWidgets.QFormLayout(move_tab_page)
        mt_layout.setSpacing(6)
        mt_layout.setContentsMargins(0, 0, 0, 0)
        self.movePaneIndexSpin = QtWidgets.QSpinBox()
        self.movePaneIndexSpin.setRange(0, 8)
        self.movePaneIndexSpin.setToolTip("Target tab index (0-8, zero-based)")
        mt_layout.addRow("Tab Index (0-8):", self.movePaneIndexSpin)
        self.actionStack.addWidget(move_tab_page)  # 6

        editor_layout.addRow(self.actionStack)
        self.actionTypeCombo.currentIndexChanged.connect(self._onActionTypeChanged)

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
        self.actionArgsEdit.setPlaceholderText(
            "Raw JSON override - if filled, this takes priority over the fields above")
        adv_layout.addRow("JSON Override:", self.actionArgsEdit)
        self.iconPathEdit = QtWidgets.QLineEdit()
        self.iconPathEdit.setPlaceholderText("Path to icon (optional)")
        adv_layout.addRow("Icon:", self.iconPathEdit)
        editor_layout.addRow(adv_group)
        main_layout.addWidget(editor_group)

        btn_layout = QtWidgets.QHBoxLayout()
        self.addActionButton = QtWidgets.QPushButton("Add New")
        self.addActionButton.setObjectName("btn-add")
        self.updateActionButton = QtWidgets.QPushButton("Save Changes")
        self.updateActionButton.setObjectName("btn-update")
        self.deleteActionButton = QtWidgets.QPushButton("Delete")
        self.deleteActionButton.setObjectName("btn-delete")
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

        help_label = QtWidgets.QLabel(
            "Modifiers: ctrl, shift, alt, win  |  Keys: enter, tab, space, esc, f1-f24, "
            "up/down/left/right  |  Example: ctrl+shift+t")
        help_label.setObjectName("hint-label")
        main_layout.addWidget(help_label)

        self.loadActions()
        # Coding-standard order: populate -> enable sorting -> restore state.
        self._persist.bind_table(self.actionsTable, "actions")

        self.actionsTable.currentCellChanged.connect(self.onActionTableSelectionChanged)
        self.addActionButton.clicked.connect(self.addAction)
        self.updateActionButton.clicked.connect(self.updateAction)
        self.deleteActionButton.clicked.connect(self.deleteAction)
        self.moveActionUpButton.clicked.connect(self.moveActionUp)
        self.moveActionDownButton.clicked.connect(self.moveActionDown)
        self.clearFieldsButton.clicked.connect(self.clearActionFields)

    def _simpleComboPage(self, items, tooltip):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(page)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        combo = QtWidgets.QComboBox()
        combo.addItems(items)
        combo.setToolTip(tooltip)
        layout.addRow("Direction:", combo)
        self.actionStack.addWidget(page)
        return combo

    # ────────────────────────────────────────────────────────────────────
    #  Table population
    # ────────────────────────────────────────────────────────────────────
    def loadActions(self):
        data_schemes = app_state.data_schemes
        self.actionsTable.setSortingEnabled(False)
        self.actionsTable.setRowCount(0)
        actions = data_schemes.get("actions", [])
        keybindings = data_schemes.get("keybindings", [])

        id_to_keys = {}
        for binding in keybindings:
            action_id = binding.get("id")
            keys = binding.get("keys")
            if keys:
                id_to_keys.setdefault(action_id if action_id else "UNBOUND_KEYS", []).append(keys)

        grey = QtGui.QColor(themes.CURRENT_THEME_COLORS.get("muted_text", "#9590a8"))

        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                continue
            action_id = action.get("id", "")
            name = action.get("name", "")
            command = action.get("command", "")

            if isinstance(command, dict):
                command_str = command.get("action", "")
                if not command_str:
                    command_str = list(command.keys())[0] if command else "unknown"
            elif isinstance(command, str):
                command_str = command
            else:
                command_str = str(command) if command else ""

            associated = id_to_keys.get(action_id, [])
            keys_display = ", ".join(associated) if associated else ""

            row = self.actionsTable.rowCount()
            self.actionsTable.insertRow(row)
            shortcut_item = QtWidgets.QTableWidgetItem(keys_display)
            name_item = QtWidgets.QTableWidgetItem(name or action_id)
            command_item = QtWidgets.QTableWidgetItem(command_str)
            id_item = QtWidgets.QTableWidgetItem(action_id)
            shortcut_item.setData(QtCore.Qt.ItemDataRole.UserRole, ("action", i))
            if not keys_display:
                for item in (shortcut_item, name_item, command_item, id_item):
                    item.setForeground(grey)
            self.actionsTable.setItem(row, 0, shortcut_item)
            self.actionsTable.setItem(row, 1, name_item)
            self.actionsTable.setItem(row, 2, command_item)
            self.actionsTable.setItem(row, 3, id_item)

        for ui, key in enumerate(id_to_keys.get("UNBOUND_KEYS", [])):
            row = self.actionsTable.rowCount()
            self.actionsTable.insertRow(row)
            shortcut_item = QtWidgets.QTableWidgetItem(key)
            name_item = QtWidgets.QTableWidgetItem("DISABLED/UNBOUND")
            command_item = QtWidgets.QTableWidgetItem("null")
            id_item = QtWidgets.QTableWidgetItem("")
            shortcut_item.setData(QtCore.Qt.ItemDataRole.UserRole, ("unbound", ui))
            strike_font = QtGui.QFont()
            strike_font.setStrikeOut(True)
            for item in (shortcut_item, name_item, command_item, id_item):
                item.setForeground(grey)
                item.setFont(strike_font)
            self.actionsTable.setItem(row, 0, shortcut_item)
            self.actionsTable.setItem(row, 1, name_item)
            self.actionsTable.setItem(row, 2, command_item)
            self.actionsTable.setItem(row, 3, id_item)

        self.actionsTable.setSortingEnabled(True)

    def _getActionRowMeta(self, row: int):
        if row < 0 or row >= self.actionsTable.rowCount():
            return (None, -1)
        item = self.actionsTable.item(row, 0)
        if item is None:
            return (None, -1)
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        return data if data else (None, -1)

    # ────────────────────────────────────────────────────────────────────
    #  Selection -> editor
    # ────────────────────────────────────────────────────────────────────
    def onActionTableSelectionChanged(self, current_row, _col, _prev_row, _prev_col):
        data_schemes = app_state.data_schemes
        row_type, data_idx = self._getActionRowMeta(current_row)
        self.clearActionFields()

        if row_type == "unbound":
            unbound = [b for b in data_schemes.get("keybindings", []) if b.get("id") is None]
            if data_idx < len(unbound):
                self.keysEdit.setText(unbound[data_idx].get("keys", ""))
                self.actionNameEdit.setText("DISABLED/UNBOUND")
                self.actionTypeCombo.setCurrentIndex(3)
                self.commandActionCombo.setCurrentText("null")
            return

        if row_type != "action":
            return

        actions = data_schemes.get("actions", [])
        keybindings = data_schemes.get("keybindings", [])
        if not 0 <= data_idx < len(actions):
            return
        action = actions[data_idx]

        action_id = action.get("id", "")
        self.actionIdEdit.setText(action_id)
        self.actionNameEdit.setText(action.get("name", ""))

        associated = [b.get("keys", "") for b in keybindings
                      if b.get("id") == action_id and b.get("keys", "")]
        self.keysEdit.setText(", ".join(associated))

        command = action.get("command", "")
        if isinstance(command, dict):
            cmd_action = command.get("action", "")
            if cmd_action == "newTab":
                self.actionTypeCombo.setCurrentIndex(0)
                self.actCmdEdit.setText(command.get("commandline", ""))
                profile = command.get("profile", "")
                self.actProfileCombo.setCurrentText(profile if profile else "(default)")
                self.actDirEdit.setText(command.get("startingDirectory", ""))
                self.actTitleEdit.setText(command.get("tabTitle", ""))
            elif cmd_action == "splitPane":
                self.actionTypeCombo.setCurrentIndex(1)
                self.actCmdEdit.setText(command.get("commandline", ""))
                profile = command.get("profile", "")
                self.actProfileCombo.setCurrentText(profile if profile else "(default)")
                self.actDirEdit.setText(command.get("startingDirectory", ""))
                self.actTitleEdit.setText(command.get("tabTitle", ""))
                if command.get("split", "horizontal") == "vertical":
                    self.actSplitV.setChecked(True)
                else:
                    self.actSplitH.setChecked(True)
                self.actSplitSize.setValue(command.get("size", 0.5))
            elif cmd_action == "sendInput":
                self.actionTypeCombo.setCurrentIndex(2)
                input_text = command.get("input", "")
                if input_text.endswith("\n"):
                    self.actSendText.setText(input_text[:-1])
                    self.actSendEnter.setChecked(True)
                else:
                    self.actSendText.setText(input_text)
                    self.actSendEnter.setChecked(False)
            elif cmd_action == "moveFocus":
                self.actionTypeCombo.setCurrentIndex(4)
                self._selectComboText(self.moveFocusDirCombo, command.get("direction", "down"))
            elif cmd_action == "resizePane":
                self.actionTypeCombo.setCurrentIndex(5)
                self._selectComboText(self.resizePaneDirCombo, command.get("direction", "down"))
            elif cmd_action == "swapPane":
                self.actionTypeCombo.setCurrentIndex(6)
                self._selectComboText(self.swapPaneDirCombo, command.get("direction", "down"))
            elif cmd_action == "movePane":
                self.actionTypeCombo.setCurrentIndex(7)
                self.movePaneIndexSpin.setValue(command.get("index", 0))
            else:
                self.actionTypeCombo.setCurrentIndex(3)
                self.commandActionCombo.setCurrentText(cmd_action or "")
                self.actionArgsEdit.setPlainText(commentjson.dumps(command, indent=2))
        elif isinstance(command, str):
            self.actionTypeCombo.setCurrentIndex(3)
            self.commandActionCombo.setCurrentText(command)
        else:
            self.actionTypeCombo.setCurrentIndex(3)
            if command:
                self.commandActionCombo.setCurrentText(str(command))

        self.iconPathEdit.setText(action.get("icon", ""))

    @staticmethod
    def _selectComboText(combo, text):
        idx = combo.findText(text)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def filterActions(self, text: str):
        text = text.lower()
        for row in range(self.actionsTable.rowCount()):
            if not text:
                match = True
            else:
                match = any(
                    (item := self.actionsTable.item(row, col)) and text in item.text().lower()
                    for col in range(self.actionsTable.columnCount()))
            self.actionsTable.setRowHidden(row, not match)

    # ────────────────────────────────────────────────────────────────────
    #  CRUD
    # ────────────────────────────────────────────────────────────────────
    def updateAction(self):
        data_schemes = app_state.data_schemes
        current_row = self.actionsTable.currentRow()
        row_type, data_idx = self._getActionRowMeta(current_row)
        keybindings = data_schemes.get("keybindings", [])

        if row_type == "unbound":
            unbound = [b for b in keybindings if b.get("id") is None]
            if data_idx < len(unbound):
                binding = unbound[data_idx]
                new_keys = self.keysEdit.text().strip()
                if new_keys:
                    binding["keys"] = new_keys
                else:
                    keybindings.remove(binding)
            self.loadActions()
            self.setUnsavedChanges()
            return

        if row_type != "action":
            return

        actions = data_schemes.get("actions", [])
        if not 0 <= data_idx < len(actions):
            return
        action = actions[data_idx]
        old_action_id = action.get("id", "")

        action["name"] = self.actionNameEdit.text().strip()
        new_action_id = self.actionIdEdit.text().strip()
        if new_action_id:
            action["id"] = new_action_id

        command = self._buildCommandFromFields()
        if command is not None:
            action["command"] = command
        elif "command" in action:
            del action["command"]

        icon_text = self.iconPathEdit.text().strip()
        if icon_text:
            action["icon"] = icon_text
        elif "icon" in action:
            del action["icon"]

        if old_action_id:
            keybindings[:] = [b for b in keybindings if b.get("id") != old_action_id]

        keys_text = self.keysEdit.text().strip()
        if keys_text and new_action_id:
            for key in (k.strip() for k in keys_text.split(",") if k.strip()):
                keybindings.append({"id": new_action_id, "keys": key})

        self.loadActions()
        self.actionsTable.selectRow(current_row)
        self.setUnsavedChanges()

    def addAction(self):
        data_schemes = app_state.data_schemes
        data_schemes.setdefault("actions", [])
        data_schemes.setdefault("keybindings", [])

        action_name = self.actionNameEdit.text().strip()
        action_id = self.actionIdEdit.text().strip()
        keys_text = self.keysEdit.text().strip()
        icon_text = self.iconPathEdit.text().strip()
        command = self._buildCommandFromFields()

        if not action_id and (action_name or command):
            base_name = action_name or (command if isinstance(command, str) else "action")
            safe_name = "".join(c for c in str(base_name) if c.isalnum() or c in "._-")
            action_id = f"User.{safe_name}.{str(_uuid.uuid4())[:8]}"

        if not action_id:
            QtWidgets.QMessageBox.warning(
                None, "Invalid Action", "Please provide a Name or fill in some fields.")
            return

        new_action = {"id": action_id}
        if action_name:
            new_action["name"] = action_name
        if command is not None:
            new_action["command"] = command
        if icon_text:
            new_action["icon"] = icon_text
        data_schemes["actions"].append(new_action)

        if keys_text:
            for key in (k.strip() for k in keys_text.split(",") if k.strip()):
                data_schemes["keybindings"].append({"id": action_id, "keys": key})

        self.loadActions()
        count = len(data_schemes.get("actions", []))
        if count > 0:
            self.actionsTable.selectRow(count - 1)
        self.setUnsavedChanges()

    def deleteAction(self):
        data_schemes = app_state.data_schemes
        current_row = self.actionsTable.currentRow()
        row_type, data_idx = self._getActionRowMeta(current_row)
        keybindings = data_schemes.get("keybindings", [])
        yes_no = QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No

        if row_type == "unbound":
            unbound = [b for b in keybindings if b.get("id") is None]
            if data_idx < len(unbound):
                reply = QtWidgets.QMessageBox.question(
                    None, "Delete Unbound Key",
                    "Are you sure you want to delete this unbound key binding?", yes_no)
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    keybindings.remove(unbound[data_idx])
                    self.loadActions()
                    self.setUnsavedChanges()
                    self.clearActionFields()
            return

        if row_type != "action":
            return

        actions = data_schemes.get("actions", [])
        if not 0 <= data_idx < len(actions):
            return
        action = actions[data_idx]
        action_name = action.get("name", action.get("id", f"Action {data_idx + 1}"))
        reply = QtWidgets.QMessageBox.question(
            None, "Delete Action",
            f'Are you sure you want to delete "{action_name}" and all its key bindings?', yes_no)
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        action_id = action.get("id")
        del actions[data_idx]
        if action_id:
            keybindings[:] = [b for b in keybindings if b.get("id") != action_id]

        self.loadActions()
        self.setUnsavedChanges()
        self.clearActionFields()
        if current_row < self.actionsTable.rowCount():
            self.actionsTable.selectRow(current_row)
        elif self.actionsTable.rowCount() > 0:
            self.actionsTable.selectRow(self.actionsTable.rowCount() - 1)

    def _moveAction(self, delta: int):
        current_row = self.actionsTable.currentRow()
        row_type, data_idx = self._getActionRowMeta(current_row)
        if row_type != "action":
            return
        actions = app_state.data_schemes.get("actions", [])
        new_idx = data_idx + delta
        if 0 <= new_idx < len(actions):
            actions[data_idx], actions[new_idx] = actions[new_idx], actions[data_idx]
            self.loadActions()
            self.actionsTable.selectRow(current_row + delta)
            self.setUnsavedChanges()

    def moveActionUp(self):
        self._moveAction(-1)

    def moveActionDown(self):
        self._moveAction(+1)

    def _onActionTypeChanged(self, index):
        if index <= 1:
            self.actionStack.setCurrentIndex(0)
            self.splitOptsWidget.setVisible(index == 1)
        else:
            # index 2..7 -> stack page 1..6
            self.actionStack.setCurrentIndex(index - 1)

    def _browseActionScript(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Script or Executable", "",
            "Scripts & Executables (*.cmd *.bat *.exe *.ps1 *.py *.sh);;All Files (*)")
        if not path:
            return
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext in ("cmd", "bat"):
            self.actCmdEdit.setText(f'cmd.exe /c "{path}"')
        elif ext == "ps1":
            self.actCmdEdit.setText(f'powershell.exe -File "{path}"')
        else:
            self.actCmdEdit.setText(f'"{path}"')

    def _browseActionDir(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Working Directory")
        if path:
            self.actDirEdit.setText(path)

    def _buildCommandFromFields(self):
        """Build the command dict/string for an action from the editor fields."""
        raw = self.actionArgsEdit.toPlainText().strip()
        if raw:
            try:
                return commentjson.loads(raw)
            except (ValueError, TypeError):
                pass  # fall through to field-based build

        action_type = self.actionTypeCombo.currentIndex()

        if action_type <= 1:
            cmd = {"action": "newTab" if action_type == 0 else "splitPane"}
            cmdline = self.actCmdEdit.text().strip()
            if cmdline:
                cmd["commandline"] = cmdline
            profile = self.actProfileCombo.currentText().strip()
            if profile and profile != "(default)":
                cmd["profile"] = profile
            work_dir = self.actDirEdit.text().strip()
            if work_dir:
                cmd["startingDirectory"] = work_dir
            title = self.actTitleEdit.text().strip()
            if title:
                cmd["tabTitle"] = title
            if action_type == 1:
                cmd["split"] = "horizontal" if self.actSplitH.isChecked() else "vertical"
                size = self.actSplitSize.value()
                if abs(size - 0.5) > 0.01:
                    cmd["size"] = round(size, 2)
            return cmd

        if action_type == 2:
            text = self.actSendText.text()
            if not text:
                return None
            if self.actSendEnter.isChecked():
                text += "\n"
            return {"action": "sendInput", "input": text}

        if action_type == 3:
            simple = self.commandActionCombo.currentText().strip()
            return simple or None

        if action_type == 4:
            return {"action": "moveFocus", "direction": self.moveFocusDirCombo.currentText()}
        if action_type == 5:
            return {"action": "resizePane", "direction": self.resizePaneDirCombo.currentText()}
        if action_type == 6:
            return {"action": "swapPane", "direction": self.swapPaneDirCombo.currentText()}
        if action_type == 7:
            return {"action": "movePane", "index": self.movePaneIndexSpin.value()}
        return None

    def clearActionFields(self):
        self.actionNameEdit.clear()
        self.actionIdEdit.clear()
        self.keysEdit.clear()
        self.actionArgsEdit.clear()
        self.iconPathEdit.clear()
        self.actionTypeCombo.setCurrentIndex(0)
        self.actCmdEdit.clear()
        self.actProfileCombo.setCurrentIndex(0)
        self.actDirEdit.clear()
        self.actTitleEdit.clear()
        self.actSendText.clear()
        self.actSendEnter.setChecked(True)
        self.commandActionCombo.setCurrentText("")
        self.actSplitH.setChecked(True)
        self.actSplitSize.setValue(0.5)
        self.splitOptsWidget.setVisible(False)
        self.moveFocusDirCombo.setCurrentIndex(0)
        self.resizePaneDirCombo.setCurrentIndex(0)
        self.swapPaneDirCombo.setCurrentIndex(0)
        self.movePaneIndexSpin.setValue(0)

    def recordShortcut(self):
        dialog = KeyRecorderDialog()
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted or not dialog.recorded_keys:
            return
        recorded = dialog.recorded_keys
        conflicts = [b.get("id", "unknown")
                     for b in app_state.data_schemes.get("keybindings", [])
                     if b.get("keys", "").lower() == recorded.lower()]
        if conflicts:
            reply = QtWidgets.QMessageBox.warning(
                None, "Shortcut Conflict",
                f"'{recorded}' is already bound to: {', '.join(conflicts)}\n\nUse it anyway?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        existing = self.keysEdit.text().strip()
        self.keysEdit.setText(f"{existing}, {recorded}" if existing else recorded)
