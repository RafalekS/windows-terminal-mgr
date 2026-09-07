"""Fragment Extensions tab: browse / create / edit Windows Terminal JSON
fragment files (user + system Fragments directories)."""

import json
import os
import uuid as _uuid
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from modules import app_state

_UI_ROLE = QtCore.Qt.ItemDataRole.UserRole
_TYPE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1

_REQUIRED_SCHEME_COLORS = [
    "black", "red", "green", "yellow", "blue", "purple", "cyan", "white",
    "brightBlack", "brightRed", "brightGreen", "brightYellow",
    "brightBlue", "brightPurple", "brightCyan", "brightWhite",
]

_SCHEME_TEMPLATE = {
    "name": "My Scheme",
    "background": "#1E1E1E", "foreground": "#D4D4D4",
    "cursorColor": "#FFFFFF", "selectionBackground": "#264F78",
    "black": "#000000", "red": "#CD3131", "green": "#0DBC79", "yellow": "#E5E510",
    "blue": "#2472C8", "purple": "#BC3FBC", "cyan": "#11A8CD", "white": "#E5E5E5",
    "brightBlack": "#666666", "brightRed": "#F14C4C", "brightGreen": "#23D18B",
    "brightYellow": "#F5F543", "brightBlue": "#3B8EEA", "brightPurple": "#D670D6",
    "brightCyan": "#29B8DB", "brightWhite": "#E5E5E5",
}

# Windows Terminal namespace UUID for deriving fragment profile GUIDs.
_WT_FRAGMENT_NAMESPACE = _uuid.UUID("{f65ddb7e-706b-4499-8a50-40313caf510a}")


class FragmentsMixin:
    """Fragment Extensions tab UI + behaviour. Mixed into ``Ui_MainWindow``."""

    def setupFragmentsTab(self):
        try:
            local_app_data = str(Path(app_state.settingsPath).parent.parent.parent)
            self._user_fragments_path = local_app_data + "\\Microsoft\\Windows Terminal\\Fragments"
        except (TypeError, AttributeError):
            self._user_fragments_path = "%LOCALAPPDATA%\\Microsoft\\Windows Terminal\\Fragments"
        self._system_fragments_path = "C:\\ProgramData\\Microsoft\\Windows Terminal\\Fragments"

        main_layout = QtWidgets.QVBoxLayout(self.fragmentsTab)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        info_label = QtWidgets.QLabel(
            "<b>User fragments:</b> " + self._user_fragments_path + "<br>"
            "<b>System fragments:</b> " + self._system_fragments_path + "<br>"
            "Fragment files add profiles/color schemes to Windows Terminal without "
            "modifying settings.json.")
        info_label.setObjectName("hint-label")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        splitter = self._frag_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # ── Left: file tree ──
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        btn_row = QtWidgets.QHBoxLayout()
        new_app_btn = QtWidgets.QPushButton("New App Folder")
        new_app_btn.setToolTip("Create a new application folder under the user fragments directory")
        new_frag_btn = QtWidgets.QPushButton("New File")
        new_frag_btn.setToolTip("Create a new .json fragment file in the selected app folder")
        del_btn = QtWidgets.QPushButton("Delete File")
        del_btn.setToolTip("Delete the selected fragment file")
        refresh_btn = QtWidgets.QPushButton("\u27F3")
        refresh_btn.setToolTip("Refresh the file list")
        refresh_btn.setMaximumWidth(32)
        for b in (new_app_btn, new_frag_btn, del_btn, refresh_btn):
            btn_row.addWidget(b)
        left_layout.addLayout(btn_row)

        self.fragmentTree = QtWidgets.QTreeWidget()
        self.fragmentTree.setHeaderLabel("Fragment Files")
        self.fragmentTree.setMinimumWidth(220)
        left_layout.addWidget(self.fragmentTree, 1)
        splitter.addWidget(left_widget)

        # ── Right: editor ──
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        self.fragFilePath = QtWidgets.QLabel("No file selected")
        self.fragFilePath.setObjectName("hint-label")
        right_layout.addWidget(self.fragFilePath)

        self.fragEditor = QtWidgets.QPlainTextEdit()
        self.fragEditor.setFont(QtGui.QFont("Courier New", 10))
        self.fragEditor.setPlaceholderText(
            "Select a fragment file on the left, or create a new one.\n\n"
            'Fragment files contain "profiles" and/or "schemes" arrays:\n'
            "{\n"
            '  "profiles": [\n'
            '    { "name": "My Profile", "commandline": "cmd.exe" }\n'
            "  ],\n"
            '  "schemes": [\n'
            '    { "name": "My Scheme", "background": "#000000", ... }\n'
            "  ]\n"
            "}")
        right_layout.addWidget(self.fragEditor, 1)

        helper_row = QtWidgets.QHBoxLayout()
        add_profile_btn = QtWidgets.QPushButton("+ New Profile")
        add_profile_btn.setToolTip("Append a new profile entry template to the editor")
        add_update_btn = QtWidgets.QPushButton("+ Update Profile")
        add_update_btn.setToolTip(
            "Append a profile update template (targets existing profile by GUID)")
        add_scheme_btn = QtWidgets.QPushButton("+ New Scheme")
        add_scheme_btn.setToolTip("Append a full color scheme template to the editor")
        guid_btn = QtWidgets.QPushButton("Generate GUID…")
        guid_btn.setToolTip("Open GUID generator for fragment profiles")
        validate_btn = QtWidgets.QPushButton("Validate JSON")
        validate_btn.setToolTip("Check that the JSON in the editor is valid and complete")
        for b in (add_profile_btn, add_update_btn, add_scheme_btn, guid_btn, validate_btn):
            helper_row.addWidget(b)
        helper_row.addStretch()
        right_layout.addLayout(helper_row)

        save_frag_btn = QtWidgets.QPushButton("Save Fragment File")
        save_frag_btn.setObjectName("btn-save")
        save_frag_btn.setMinimumHeight(36)
        right_layout.addWidget(save_frag_btn)

        splitter.addWidget(right_widget)
        splitter.setSizes([260, 640])

        self.fragmentTree.currentItemChanged.connect(self._onFragmentSelected)
        new_app_btn.clicked.connect(self._newFragmentApp)
        new_frag_btn.clicked.connect(self._newFragmentFile)
        del_btn.clicked.connect(self._deleteFragment)
        refresh_btn.clicked.connect(self._refreshFragmentTree)
        add_profile_btn.clicked.connect(self._insertProfileTemplate)
        add_update_btn.clicked.connect(self._insertUpdateTemplate)
        add_scheme_btn.clicked.connect(self._insertSchemeTemplate)
        guid_btn.clicked.connect(self._showGuidDialog)
        validate_btn.clicked.connect(self._validateFragmentJson)
        save_frag_btn.clicked.connect(self._saveFragmentFile)

        self._refreshFragmentTree()
        self._persist.bind_tree(self.fragmentTree, "fragments")
        self._persist.bind_splitter(self._frag_splitter, "fragments")

    # ────────────────────────────────────────────────────────────────────
    #  Tree
    # ────────────────────────────────────────────────────────────────────
    def _refreshFragmentTree(self):
        self.fragmentTree.clear()
        for label, path in (("User", self._user_fragments_path),
                            ("System", self._system_fragments_path)):
            root_item = QtWidgets.QTreeWidgetItem([f"{label} Fragments"])
            root_item.setData(0, _UI_ROLE, path)
            root_item.setData(0, _TYPE_ROLE, "root")
            root_item.setToolTip(0, path)
            self.fragmentTree.addTopLevelItem(root_item)
            try:
                if os.path.isdir(path):
                    for app_name in sorted(os.listdir(path)):
                        app_path = path + "\\" + app_name
                        if not os.path.isdir(app_path):
                            continue
                        app_item = QtWidgets.QTreeWidgetItem([app_name])
                        app_item.setData(0, _UI_ROLE, app_path)
                        app_item.setData(0, _TYPE_ROLE, "app")
                        app_item.setToolTip(0, app_path)
                        root_item.addChild(app_item)
                        for fname in sorted(os.listdir(app_path)):
                            if fname.lower().endswith(".json"):
                                file_path = app_path + "\\" + fname
                                file_item = QtWidgets.QTreeWidgetItem([fname])
                                file_item.setData(0, _UI_ROLE, file_path)
                                file_item.setData(0, _TYPE_ROLE, "file")
                                file_item.setToolTip(0, file_path)
                                app_item.addChild(file_item)
                else:
                    root_item.setToolTip(0, path + "  (directory does not exist yet)")
                    root_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#999999")))
            except PermissionError:
                root_item.setToolTip(0, path + "  (access denied)")
                root_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#cc4444")))
        self.fragmentTree.expandAll()

    def _onFragmentSelected(self, current, _previous):
        if not current:
            return
        if current.data(0, _TYPE_ROLE) != "file":
            self.fragFilePath.setText("Select a .json fragment file to edit")
            return
        file_path = current.data(0, _UI_ROLE)
        self.fragFilePath.setText(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.fragEditor.setPlainText(f.read())
        except OSError as e:
            self.fragEditor.setPlainText(f"// Error loading file: {e}")

    def _getSelectedFilePath(self):
        item = self.fragmentTree.currentItem()
        if item and item.data(0, _TYPE_ROLE) == "file":
            return item.data(0, _UI_ROLE)
        return None

    def _getSelectedAppPath(self):
        item = self.fragmentTree.currentItem()
        if not item:
            return None
        itype = item.data(0, _TYPE_ROLE)
        if itype == "file":
            parent = item.parent()
            return parent.data(0, _UI_ROLE) if parent else None
        if itype == "app":
            return item.data(0, _UI_ROLE)
        return None

    # ────────────────────────────────────────────────────────────────────
    #  File ops
    # ────────────────────────────────────────────────────────────────────
    def _newFragmentApp(self):
        app_name, ok = QtWidgets.QInputDialog.getText(
            None, "New App Folder", "Enter the application name (e.g. 'Git', 'MyApp'):")
        if not ok or not app_name.strip():
            return
        app_path = self._user_fragments_path + "\\" + app_name.strip()
        try:
            os.makedirs(app_path, exist_ok=True)
            self._refreshFragmentTree()
        except OSError as e:
            QtWidgets.QMessageBox.warning(None, "Error", f"Could not create folder:\n{e}")

    def _newFragmentFile(self):
        app_path = self._getSelectedAppPath()
        if not app_path:
            QtWidgets.QMessageBox.information(
                None, "Select App Folder",
                "Select or create an app folder first, then click 'New File'.")
            return
        name, ok = QtWidgets.QInputDialog.getText(
            None, "New Fragment File", "Enter filename (without .json extension):")
        if not ok or not name.strip():
            return
        fname = name.strip()
        if not fname.lower().endswith(".json"):
            fname += ".json"
        file_path = app_path + "\\" + fname
        if os.path.exists(file_path):
            QtWidgets.QMessageBox.warning(None, "File Exists", f"File already exists:\n{file_path}")
            return
        template = json.dumps({"profiles": [], "schemes": []}, indent=2)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template)
            self._refreshFragmentTree()
            self.fragFilePath.setText(file_path)
            self.fragEditor.setPlainText(template)
        except OSError as e:
            QtWidgets.QMessageBox.warning(None, "Error", f"Could not create file:\n{e}")

    def _deleteFragment(self):
        file_path = self._getSelectedFilePath()
        if not file_path:
            QtWidgets.QMessageBox.information(None, "Select File", "Select a fragment file to delete.")
            return
        reply = QtWidgets.QMessageBox.question(
            None, "Delete Fragment File", f"Delete this fragment file?\n\n{file_path}",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            os.remove(file_path)
            self.fragEditor.clear()
            self.fragFilePath.setText("No file selected")
            self._refreshFragmentTree()
        except OSError as e:
            QtWidgets.QMessageBox.warning(None, "Error", f"Could not delete file:\n{e}")

    def _saveFragmentFile(self):
        file_path = self._getSelectedFilePath()
        if not file_path:
            QtWidgets.QMessageBox.information(
                None, "Select File", "Select or create a fragment file first.")
            return
        content = self.fragEditor.toPlainText()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            QtWidgets.QMessageBox.warning(
                None, "Invalid JSON",
                f"Cannot save - the content is not valid JSON:\n{e}")
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QtWidgets.QMessageBox.information(None, "Saved", f"Fragment file saved:\n{file_path}")
        except OSError as e:
            QtWidgets.QMessageBox.warning(None, "Error", f"Could not save file:\n{e}")

    # ────────────────────────────────────────────────────────────────────
    #  JSON helpers
    # ────────────────────────────────────────────────────────────────────
    def _validateFragmentJson(self):
        content = self.fragEditor.toPlainText().strip()
        if not content:
            QtWidgets.QMessageBox.information(None, "Empty", "The editor is empty.")
            return
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            QtWidgets.QMessageBox.critical(None, "Invalid JSON", f"JSON parse error:\n{e}")
            return

        profiles = data.get("profiles", [])
        schemes = data.get("schemes", [])
        warnings = []
        for i, p in enumerate(profiles):
            if "updates" not in p and "name" not in p:
                warnings.append(f"Profile [{i}]: missing 'name' (required for new profiles)")
        for i, s in enumerate(schemes):
            if "name" not in s:
                warnings.append(f"Scheme [{i}]: missing 'name' (required)")
            missing = [c for c in _REQUIRED_SCHEME_COLORS if c not in s]
            if missing:
                warnings.append(
                    f"Scheme [{i}] '{s.get('name', '')}': missing colors: {', '.join(missing)}")

        p_word = "entry" if len(profiles) == 1 else "entries"
        s_word = "entry" if len(schemes) == 1 else "entries"
        msg = f"Valid JSON!\n\n{len(profiles)} profile {p_word}, {len(schemes)} scheme {s_word}."
        if warnings:
            msg += "\n\nWarnings:\n" + "\n".join(f"  • {w}" for w in warnings)
            QtWidgets.QMessageBox.warning(None, "JSON Valid (with warnings)", msg)
        else:
            QtWidgets.QMessageBox.information(None, "JSON Valid", msg)

    def _smartInsertEntry(self, entry: dict, array_key: str):
        content = self.fragEditor.toPlainText().strip()
        if not content:
            content = '{"profiles": [], "schemes": []}'
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            QtWidgets.QMessageBox.warning(
                None, "Invalid JSON",
                "Fix the JSON in the editor before inserting entries.")
            return
        data.setdefault(array_key, []).append(entry)
        self.fragEditor.setPlainText(json.dumps(data, indent=2))

    def _insertProfileTemplate(self):
        self._smartInsertEntry({
            "name": "My Profile", "commandline": "cmd.exe", "icon": "",
            "colorScheme": "", "startingDirectory": "%USERPROFILE%",
        }, "profiles")

    def _insertUpdateTemplate(self):
        self._smartInsertEntry({
            "updates": "{paste-existing-profile-guid-here}",
            "fontSize": 12, "fontWeight": "normal",
        }, "profiles")

    def _insertSchemeTemplate(self):
        self._smartInsertEntry(dict(_SCHEME_TEMPLATE), "schemes")

    def _showGuidDialog(self):
        dlg = QtWidgets.QDialog()
        dlg.setWindowTitle("Generate Fragment Profile GUID")
        dlg.setMinimumWidth(520)
        layout = QtWidgets.QVBoxLayout(dlg)

        note = QtWidgets.QLabel(
            "Generate a GUID for a new fragment profile using the Windows Terminal namespace "
            "UUID. Use this GUID when pre-distributing a profile, or in an 'updates' field to "
            "target a specific existing fragment profile.\n\n"
            "Note: App and profile names should be ASCII for accurate results.")
        note.setWordWrap(True)
        note.setObjectName("hint-label")
        layout.addWidget(note)

        form = QtWidgets.QFormLayout()
        app_edit = QtWidgets.QLineEdit()
        app_edit.setPlaceholderText("e.g. Git, MyApp, VSCode")
        profile_edit = QtWidgets.QLineEdit()
        profile_edit.setPlaceholderText("e.g. Git Bash, My Dev Shell")
        form.addRow("App Name:", app_edit)
        form.addRow("Profile Name:", profile_edit)
        layout.addLayout(form)

        result_edit = QtWidgets.QLineEdit()
        result_edit.setReadOnly(True)
        result_edit.setFont(QtGui.QFont("Courier New", 10))
        result_edit.setPlaceholderText("Generated GUID will appear here")
        layout.addWidget(result_edit)

        btn_row = QtWidgets.QHBoxLayout()
        gen_btn = QtWidgets.QPushButton("Generate")
        copy_btn = QtWidgets.QPushButton("Copy to Clipboard")
        close_btn = QtWidgets.QPushButton("Close")
        btn_row.addWidget(gen_btn)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        def generate():
            app = app_edit.text().strip()
            prof = profile_edit.text().strip()
            if not app or not prof:
                result_edit.setText("Enter both App Name and Profile Name first.")
                return
            try:
                app_ns = _uuid.uuid5(_WT_FRAGMENT_NAMESPACE,
                                     app.encode("UTF-16LE").decode("latin-1"))
                guid = _uuid.uuid5(app_ns, prof.encode("UTF-16LE").decode("latin-1"))
                result_edit.setText(f"{{{guid}}}")
            except (ValueError, UnicodeError) as e:
                result_edit.setText(f"Error: {e}")

        def copy_guid():
            text = result_edit.text()
            if text and not text.startswith(("Error", "Enter")):
                QtWidgets.QApplication.clipboard().setText(text)

        gen_btn.clicked.connect(generate)
        copy_btn.clicked.connect(copy_guid)
        close_btn.clicked.connect(dlg.close)
        app_edit.returnPressed.connect(generate)
        profile_edit.returnPressed.connect(generate)
        dlg.exec()
