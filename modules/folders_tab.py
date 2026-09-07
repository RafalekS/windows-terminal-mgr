"""Folders & New Tab Menu tab: tree view of ``newTabMenu`` with add / move /
delete / drag-drop, plus the profile-menu-location lookups."""

import uuid as _uuid

from PyQt6 import QtCore, QtGui, QtWidgets

from modules import app_state
from modules.app_state import debug_print, _UID_KEY
from modules import themes
from modules.widgets import DragDropTreeWidget


class FoldersMixin:
    """Folders tab UI + behaviour. Mixed into ``Ui_MainWindow``."""

    # ────────────────────────────────────────────────────────────────────
    #  UI construction
    # ────────────────────────────────────────────────────────────────────
    def setupFoldersTab(self):
        profiles_list = app_state.profiles_list

        main_layout = QtWidgets.QHBoxLayout(self.foldersTab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ── Left: folder tree ──
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
        self.foldersTreeWidget.setColumnWidth(0, 250)
        self.foldersTreeWidget.setColumnWidth(1, 100)
        left_layout.addWidget(self.foldersTreeWidget)

        folder_buttons_layout = QtWidgets.QVBoxLayout()

        row1_layout = QtWidgets.QHBoxLayout()
        self.addFolderButton = QtWidgets.QPushButton("Add Folder")
        self.addSeparatorButton = QtWidgets.QPushButton("Add Separator")
        row1_layout.addWidget(self.addFolderButton)
        row1_layout.addWidget(self.addSeparatorButton)
        folder_buttons_layout.addLayout(row1_layout)

        self.addProfileToMenuButton = QtWidgets.QPushButton("Move Profile")
        folder_buttons_layout.addWidget(self.addProfileToMenuButton)

        separator1 = QtWidgets.QFrame()
        separator1.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        folder_buttons_layout.addWidget(separator1)

        row3_layout = QtWidgets.QHBoxLayout()
        self.moveFolderUpButton = QtWidgets.QPushButton("Move Up")
        self.moveFolderDownButton = QtWidgets.QPushButton("Move Down")
        row3_layout.addWidget(self.moveFolderUpButton)
        row3_layout.addWidget(self.moveFolderDownButton)
        folder_buttons_layout.addLayout(row3_layout)

        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        folder_buttons_layout.addWidget(separator2)

        delete_layout = QtWidgets.QHBoxLayout()
        delete_layout.addStretch()
        self.deleteFolderButton = QtWidgets.QPushButton("Delete Item")
        self.deleteFolderButton.setObjectName("btn-delete")
        delete_layout.addWidget(self.deleteFolderButton)
        delete_layout.addStretch()
        folder_buttons_layout.addLayout(delete_layout)

        left_layout.addLayout(folder_buttons_layout)
        main_layout.addWidget(left_widget)

        # ── Right: item details ──
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        details_group = QtWidgets.QGroupBox("Item Details")
        self._detailsForm = QtWidgets.QFormLayout(details_group)
        self._detailsForm.setSpacing(10)

        self.itemTypeLabel = QtWidgets.QLabel("")
        self.itemTypeLabel.setStyleSheet("QLabel { font-weight: bold; }")
        self._detailsForm.addRow("Item Type:", self.itemTypeLabel)

        # Location: which folder this entry sits in. Changing it + Update Item
        # (or "Add to menu" for an auto entry) moves/creates the entry there.
        self.locationCombo = QtWidgets.QComboBox()
        self.locationCombo.setToolTip(
            "The folder this item lives in. Change it and click Update Item to move it.")
        self._locationRowLabel = QtWidgets.QLabel("Location:")
        self._detailsForm.addRow(self._locationRowLabel, self.locationCombo)

        self.folderNameEdit = QtWidgets.QLineEdit()
        self.folderNameEdit.setPlaceholderText("Enter folder name")
        self._folderNameRowLabel = QtWidgets.QLabel("Folder Name:")
        self._detailsForm.addRow(self._folderNameRowLabel, self.folderNameEdit)

        folder_icon_layout = QtWidgets.QHBoxLayout()
        self.folderIconEdit = QtWidgets.QLineEdit()
        self.folderIconEdit.setPlaceholderText("Path to icon")
        self.folderIconBrowseButton = QtWidgets.QPushButton("Browse...")
        self.folderIconBrowseButton.clicked.connect(self.browseFolderIcon)
        folder_icon_layout.addWidget(self.folderIconEdit)
        folder_icon_layout.addWidget(self.folderIconBrowseButton)
        self._folderIconRowLabel = QtWidgets.QLabel("Folder Icon:")
        self._folderIconRowWidget = QtWidgets.QWidget()
        self._folderIconRowWidget.setLayout(folder_icon_layout)
        folder_icon_layout.setContentsMargins(0, 0, 0, 0)
        self._detailsForm.addRow(self._folderIconRowLabel, self._folderIconRowWidget)

        profile_pick_layout = QtWidgets.QHBoxLayout()
        profile_pick_layout.setContentsMargins(0, 0, 0, 0)
        self.menuProfileCombo = QtWidgets.QComboBox()
        self.menuProfileCombo.addItems([""] + profiles_list)
        self.menuProfileCombo.setToolTip(
            "Which profile this menu entry points to. Use 'Edit in Profiles' to rename "
            "the profile itself.")
        self.editInProfilesButton = QtWidgets.QPushButton("Edit in Profiles ▸")
        self.editInProfilesButton.setToolTip("Jump to this profile on the Profiles tab")
        self.editInProfilesButton.clicked.connect(self._editSelectedProfileEntry)
        profile_pick_layout.addWidget(self.menuProfileCombo)
        profile_pick_layout.addWidget(self.editInProfilesButton)
        self._profilePickRowLabel = QtWidgets.QLabel("Shows profile:")
        self._profilePickRowWidget = QtWidgets.QWidget()
        self._profilePickRowWidget.setLayout(profile_pick_layout)
        self._detailsForm.addRow(self._profilePickRowLabel, self._profilePickRowWidget)

        profile_icon_layout = QtWidgets.QHBoxLayout()
        profile_icon_layout.setContentsMargins(0, 0, 0, 0)
        self.profileIconEdit = QtWidgets.QLineEdit()
        self.profileIconEdit.setPlaceholderText("Path to icon (optional)")
        self.profileIconBrowseButton = QtWidgets.QPushButton("Browse...")
        self.profileIconBrowseButton.clicked.connect(self.browseProfileIcon)
        profile_icon_layout.addWidget(self.profileIconEdit)
        profile_icon_layout.addWidget(self.profileIconBrowseButton)
        self._profileIconRowLabel = QtWidgets.QLabel("Profile Icon:")
        self._profileIconRowWidget = QtWidgets.QWidget()
        self._profileIconRowWidget.setLayout(profile_icon_layout)
        self._detailsForm.addRow(self._profileIconRowLabel, self._profileIconRowWidget)

        self.allowEmptyCheckBox = QtWidgets.QCheckBox("Allow Empty (show even if no entries)")
        self.inlineCheckBox = QtWidgets.QCheckBox("Inline (don't create nested menu if single entry)")
        self._detailsForm.addRow("", self.allowEmptyCheckBox)
        self._detailsForm.addRow("", self.inlineCheckBox)

        update_button_layout = QtWidgets.QHBoxLayout()
        self.updateFolderButton = QtWidgets.QPushButton("Update Item")
        self.updateFolderButton.setMinimumHeight(35)
        update_button_layout.addStretch()
        update_button_layout.addWidget(self.updateFolderButton)
        update_button_layout.addStretch()
        self._updateButtonRowWidget = QtWidgets.QWidget()
        self._updateButtonRowWidget.setLayout(update_button_layout)
        self._detailsForm.addRow("", self._updateButtonRowWidget)
        right_layout.addWidget(details_group)

        help_group = QtWidgets.QGroupBox("Folder Management Help")
        help_layout = QtWidgets.QVBoxLayout(help_group)
        help_label = QtWidgets.QLabel(
            "New Tab Menu Structure:\n"
            "\U0001F4C1 Folder: organizes profiles in a dropdown submenu\n"
            "\U0001F464 Profile: a menu entry that points to one profile\n"
            "➖ Separator: visual divider\n"
            "\U0001F4CB Remaining Profiles: auto-lists every profile not placed "
            "explicitly (stays in the menu)\n\n"
            "Location: the folder an item lives in. Change it and click "
            "Update Item to move the item there.\n\n"
            "Auto-listed profiles (blue): select one, pick a Location and click "
            "'Add to menu' to turn it into a real entry you can move and style.\n\n"
            "Folder Options:\n"
            "• Allow Empty: show the folder even if it has no entries\n"
            "• Inline: if the folder has one item, show it directly (no submenu)\n\n"
            "Tips:\n"
            "• Drag items to reorder them within their parent\n"
            "• 'Shows profile' re-points an entry; use 'Edit in Profiles' to "
            "rename the profile itself")
        help_label.setWordWrap(True)
        help_label.setObjectName("help-panel")
        help_layout.addWidget(help_label)
        right_layout.addWidget(help_group)
        main_layout.addWidget(right_widget)

        self.loadFolders()
        self._persist.bind_tree(self.foldersTreeWidget, "folders")

        self.foldersTreeWidget.currentItemChanged.connect(self.onFolderSelectionChanged)
        self.addFolderButton.clicked.connect(self.addFolder)
        self.addProfileToMenuButton.clicked.connect(self.addProfileToMenu)
        self.addSeparatorButton.clicked.connect(self.addSeparator)
        self.updateFolderButton.clicked.connect(self.updateFolderItem)
        self.deleteFolderButton.clicked.connect(self.deleteFolderItem)
        self.moveFolderUpButton.clicked.connect(self.moveFolderItemUp)
        self.moveFolderDownButton.clicked.connect(self.moveFolderItemDown)

    # ────────────────────────────────────────────────────────────────────
    #  Tree building
    # ────────────────────────────────────────────────────────────────────
    def _getExpandedUids(self):
        expanded = set()

        def walk(parent_item):
            count = (parent_item.childCount() if parent_item
                     else self.foldersTreeWidget.topLevelItemCount())
            for i in range(count):
                item = (parent_item.child(i) if parent_item
                        else self.foldersTreeWidget.topLevelItem(i))
                if item.isExpanded():
                    entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if entry and entry.get(_UID_KEY):
                        expanded.add(entry[_UID_KEY])
                walk(item)

        walk(None)
        return expanded

    def _restoreExpandedUids(self, expanded_uids):
        def walk(parent_item):
            count = (parent_item.childCount() if parent_item
                     else self.foldersTreeWidget.topLevelItemCount())
            for i in range(count):
                item = (parent_item.child(i) if parent_item
                        else self.foldersTreeWidget.topLevelItem(i))
                entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if entry and entry.get(_UID_KEY) in expanded_uids:
                    item.setExpanded(True)
                walk(item)

        walk(None)

    def loadFolders(self):
        data_schemes = app_state.data_schemes
        debug_print("DEBUG loadFolders: Clearing tree and reloading from data_schemes")
        debug_print(f"DEBUG loadFolders: data_schemes has "
                    f"{len(data_schemes.get('newTabMenu', []))} root items")

        expanded_uids = self._getExpandedUids()
        app_state.stamp_uids(data_schemes.get("newTabMenu", []))

        self.foldersTreeWidget.clear()
        for i, entry in enumerate(data_schemes.get("newTabMenu", [])):
            debug_print(f"DEBUG loadFolders: Adding item {i}: type={entry.get('type')}, "
                        f"name={entry.get('name', 'N/A')}")
            self.addTreeItem(entry, self.foldersTreeWidget)

        self._restoreExpandedUids(expanded_uids)
        debug_print(f"DEBUG loadFolders: Tree now has "
                    f"{self.foldersTreeWidget.topLevelItemCount()} top-level items")

        if self.ui_initialized:
            self.updateProfileMenuIndicators()

    def addTreeItem(self, entry: dict, parent):
        data_schemes = app_state.data_schemes
        entry_type = entry.get("type", "unknown")

        if entry_type == "folder":
            name = entry.get("name", "Unnamed Folder")
            debug_print(f"DEBUG addTreeItem: Creating folder item with name='{name}', "
                        f"entry_id={id(entry)}")
            item = QtWidgets.QTreeWidgetItem(parent, [name, "\U0001F4C1 Folder"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)
            for child_entry in entry.get("entries", []):
                self.addTreeItem(child_entry, item)

        elif entry_type == "profile":
            profile_name = self.getProfileNameByGuid(entry.get("profile", ""))
            item = QtWidgets.QTreeWidgetItem(parent, [profile_name, "\U0001F464 Profile"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)

        elif entry_type == "separator":
            item = QtWidgets.QTreeWidgetItem(parent, ["───────",
                                                     "➖ Separator"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)

        elif entry_type == "remainingProfiles":
            assigned_guids = self.getAssignedProfileGuids()
            unassigned = [p for p in data_schemes.get("profiles", {}).get("list", [])
                          if p.get("guid") and p.get("guid") not in assigned_guids]
            item = QtWidgets.QTreeWidgetItem(
                parent, [f"Remaining Profiles ({len(unassigned)} auto-listed)", "\U0001F4CB Auto"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)
            item.setForeground(0, QtGui.QBrush(QtGui.QColor(
                themes.CURRENT_THEME_COLORS.get("muted_text", "#8580a0"))))
            item.setToolTip(0, "Profiles not explicitly in the menu. WT shows these automatically.")

            for profile in unassigned:
                guid = profile.get("guid")
                name = profile.get("name", "Unknown")
                child_item = QtWidgets.QTreeWidgetItem(item, [f"  {name}", "\U0001F464 Auto"])
                child_item.setData(0, QtCore.Qt.ItemDataRole.UserRole,
                                   {"type": "_virtual_remaining", "profile": guid})
                child_item.setForeground(0, QtGui.QBrush(QtGui.QColor(
                    themes.CURRENT_THEME_COLORS.get("accent_text", "#5b8bd4"))))
                child_item.setToolTip(0, f"GUID: {guid}\n"
                                         "Right-click or use 'Move Profile' to assign explicitly")
            item.setExpanded(True)

        else:
            item = QtWidgets.QTreeWidgetItem(parent, [entry_type, f"⚙️ {entry_type}"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry)

    # ────────────────────────────────────────────────────────────────────
    #  Lookups
    # ────────────────────────────────────────────────────────────────────
    def getAssignedProfileGuids(self) -> set:
        assigned = set()

        def walk_entries(entries):
            for entry in entries:
                if isinstance(entry, dict):
                    if entry.get("type") == "profile":
                        guid = entry.get("profile")
                        if guid:
                            assigned.add(guid)
                    elif entry.get("type") == "folder":
                        walk_entries(entry.get("entries", []))

        walk_entries(app_state.data_schemes.get("newTabMenu", []))
        return assigned

    def getProfileMenuLocation(self, guid: str) -> str:
        def search(entries, parent_name=None):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") == "profile" and entry.get("profile") == guid:
                    return f"In folder: {parent_name}" if parent_name else "Root level"
                if entry.get("type") == "folder":
                    result = search(entry.get("entries", []), entry.get("name", "Unnamed"))
                    if result:
                        return result
                if entry.get("type") == "remainingProfiles":
                    if guid not in self.getAssignedProfileGuids():
                        return "In: remainingProfiles (auto)"
            return None

        return search(app_state.data_schemes.get("newTabMenu", [])) or "Not in menu"

    def getProfileNameByGuid(self, guid: str) -> str:
        for profile in app_state.data_schemes.get("profiles", {}).get("list", []):
            if profile.get("guid") == guid:
                return profile.get("name", guid)
        return guid

    def getProfileGuidByName(self, name: str) -> str:
        for profile in app_state.data_schemes.get("profiles", {}).get("list", []):
            if profile.get("name") == name:
                return profile.get("guid", "")
        return ""

    def findParentList(self, entry: dict) -> tuple:
        """Find the list containing *entry* by its ``_wt_uid``.

        Returns ``(parent_list, index)`` or ``(None, -1)``.
        """
        uid = entry.get(_UID_KEY)
        if not uid:
            debug_print(f"DEBUG findParentList: Entry has no UID! type={entry.get('type')}")
            return (None, -1)

        def search(entries_list):
            for i, e in enumerate(entries_list):
                if e.get(_UID_KEY) == uid:
                    return (entries_list, i)
                if e.get("type") == "folder" and "entries" in e:
                    result = search(e["entries"])
                    if result[0] is not None:
                        return result
            return (None, -1)

        return search(app_state.data_schemes.get("newTabMenu", []))

    # ────────────────────────────────────────────────────────────────────
    #  Location dropdown helpers
    # ────────────────────────────────────────────────────────────────────
    _ROOT_LABEL = "(top level)"

    def _folderPaths(self, exclude_uid: str = None):
        """List every folder as ``(display_path, entries_list, folder_entry)``.

        A folder is skipped (with its whole subtree) when its uid == *exclude_uid*
        so a folder can't be moved into itself or a descendant.
        """
        out = []

        def walk(entries, prefix):
            for e in entries:
                if e.get("type") != "folder":
                    continue
                if exclude_uid and e.get(_UID_KEY) == exclude_uid:
                    continue
                name = e.get("name", "Unnamed")
                path = f"{prefix} / {name}" if prefix else name
                e.setdefault("entries", [])
                out.append((path, e["entries"], e))
                walk(e["entries"], path)

        walk(app_state.data_schemes.get("newTabMenu", []), "")
        return out

    def _populateLocationCombo(self, current_parent_entry, exclude_uid=None):
        """Fill locationCombo with (top level) + every folder path. userData is
        the folder's ``_wt_uid`` ("" for the top level) - resolve it with
        ``_listForLocationKey`` (PyQt does not preserve list identity in
        userData)."""
        self.locationCombo.blockSignals(True)
        self.locationCombo.clear()
        self.locationCombo.addItem(self._ROOT_LABEL, "")
        for path, _entries_list, folder in self._folderPaths(exclude_uid):
            self.locationCombo.addItem(path, folder.get(_UID_KEY))

        target_uid = (current_parent_entry.get(_UID_KEY)
                      if current_parent_entry else "")
        idx = self.locationCombo.findData(target_uid)
        self.locationCombo.setCurrentIndex(idx if idx >= 0 else 0)
        self.locationCombo.blockSignals(False)

    def _listForLocationKey(self, key):
        """Return the entries list for a locationCombo userData value."""
        root = app_state.data_schemes.setdefault("newTabMenu", [])
        if not key:
            return root
        for _path, entries_list, folder in self._folderPaths():
            if folder.get(_UID_KEY) == key:
                return entries_list
        return root

    def _currentParentEntry(self, entry):
        """The folder dict that directly contains *entry*, or None for root."""
        parent_list, _idx = self.findParentList(entry)
        if parent_list is None:
            return None
        for _path, entries_list, folder in self._folderPaths():
            if entries_list is parent_list:
                return folder
        return None

    # ────────────────────────────────────────────────────────────────────
    #  Row visibility
    # ────────────────────────────────────────────────────────────────────
    def _showDetailRows(self, *, location, folder_fields, profile_fields, update_button):
        form = self._detailsForm

        def vis(field_widget, show):
            try:
                form.setRowVisible(field_widget, show)
            except (AttributeError, RuntimeError):
                field_widget.setVisible(show)
                lbl = form.labelForField(field_widget)
                if lbl is not None:
                    lbl.setVisible(show)

        vis(self.locationCombo, location)
        vis(self.folderNameEdit, folder_fields)
        vis(self._folderIconRowWidget, folder_fields)
        vis(self.allowEmptyCheckBox, folder_fields)
        vis(self.inlineCheckBox, folder_fields)
        vis(self._profilePickRowWidget, profile_fields)
        vis(self._profileIconRowWidget, profile_fields)
        vis(self._updateButtonRowWidget, update_button)

    # ────────────────────────────────────────────────────────────────────
    #  Selection handler
    # ────────────────────────────────────────────────────────────────────
    def onFolderSelectionChanged(self):
        current_item = self.foldersTreeWidget.currentItem()

        can_move_up = can_move_down = can_delete = False
        if current_item:
            entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if entry and entry.get("type") not in ("remainingProfiles", "_virtual_remaining"):
                can_delete = True
                parent_list, idx = self.findParentList(entry)
                if parent_list is not None:
                    can_move_up = idx > 0
                    can_move_down = idx < len(parent_list) - 1
        self.moveFolderUpButton.setEnabled(can_move_up)
        self.moveFolderDownButton.setEnabled(can_move_down)
        self.deleteFolderButton.setEnabled(can_delete)

        self.folderNameEdit.clear()
        self.folderIconEdit.clear()
        self.menuProfileCombo.setCurrentText("")
        self.profileIconEdit.clear()
        self.allowEmptyCheckBox.setChecked(True)
        self.inlineCheckBox.setChecked(False)
        self.updateFolderButton.setText("Update Item")

        if not current_item:
            self.itemTypeLabel.setText("")
            self._showDetailRows(location=False, folder_fields=False,
                                 profile_fields=False, update_button=False)
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return
        entry_type = entry.get("type", "unknown")

        if entry_type == "folder":
            self.itemTypeLabel.setText("\U0001F4C1 Folder")
            self._showDetailRows(location=True, folder_fields=True,
                                 profile_fields=False, update_button=True)
            self._populateLocationCombo(self._currentParentEntry(entry),
                                        exclude_uid=entry.get(_UID_KEY))
            self.folderNameEdit.setText(entry.get("name", ""))
            self.folderIconEdit.setText(entry.get("icon", "") or "")
            self.allowEmptyCheckBox.setChecked(entry.get("allowEmpty", True))
            inline_value = entry.get("inline", False)
            self.inlineCheckBox.setChecked(inline_value is True or inline_value == "always")

        elif entry_type == "profile":
            self.itemTypeLabel.setText("\U0001F464 Profile")
            self._showDetailRows(location=True, folder_fields=False,
                                 profile_fields=True, update_button=True)
            self._populateLocationCombo(self._currentParentEntry(entry))
            self.menuProfileCombo.setCurrentText(self.getProfileNameByGuid(entry.get("profile", "")))
            self.profileIconEdit.setText(entry.get("icon", "") or "")

        elif entry_type == "separator":
            self.itemTypeLabel.setText("➖ Separator")
            self._showDetailRows(location=True, folder_fields=False,
                                 profile_fields=False, update_button=True)
            self._populateLocationCombo(self._currentParentEntry(entry))

        elif entry_type == "remainingProfiles":
            self.itemTypeLabel.setText(
                "\U0001F4CB Remaining Profiles (auto-generated - kept in the menu)")
            self._showDetailRows(location=False, folder_fields=False,
                                 profile_fields=False, update_button=False)

        elif entry_type == "_virtual_remaining":
            name = self.getProfileNameByGuid(entry.get("profile", ""))
            self.itemTypeLabel.setText(
                f"\U0001F464 {name} (auto-listed - pick a location and click "
                f"'Add to menu' to make it a real entry)")
            self._showDetailRows(location=True, folder_fields=False,
                                 profile_fields=False, update_button=True)
            self._populateLocationCombo(None)
            self.updateFolderButton.setText("Add to menu")
            self.deleteFolderButton.setEnabled(False)

    def _editSelectedProfileEntry(self):
        """Jump to the Profiles tab and select the profile this entry points to."""
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            return
        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry or entry.get("type") not in ("profile", "_virtual_remaining"):
            return
        name = self.getProfileNameByGuid(entry.get("profile", ""))
        self.tabWidget.setCurrentIndex(0)  # Profiles tab
        matches = self.listWidget.findItems(name, QtCore.Qt.MatchFlag.MatchFixedString)
        if matches:
            self.listWidget.setCurrentItem(matches[0])

    # ────────────────────────────────────────────────────────────────────
    #  Icon browsers
    # ────────────────────────────────────────────────────────────────────
    def _browseIconInto(self, line_edit):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Icon", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.ico);;Executables (*.exe);;All Files (*.*)")
        if filename:
            line_edit.setText(filename.replace("/", "\\"))

    def browseFolderIcon(self):
        self._browseIconInto(self.folderIconEdit)

    def browseProfileIcon(self):
        self._browseIconInto(self.profileIconEdit)

    # ────────────────────────────────────────────────────────────────────
    #  Add / move / delete
    # ────────────────────────────────────────────────────────────────────
    def _targetListForNewEntry(self, current_item, action_tag):
        """Resolve where a new entry should be appended based on selection.

        Returns ``(target_list, parent_entry_or_None, location_label)`` or
        ``(None, None, None)`` if the folder could not be resolved (an error box
        has already been shown).
        """
        data_schemes = app_state.data_schemes
        root = data_schemes.setdefault("newTabMenu", [])

        if not current_item:
            debug_print(f"DEBUG {action_tag}: Added to root (nothing selected)")
            return root, None, "root"

        current_entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if current_entry and current_entry.get("type") == "folder":
            parent_list, idx = self.findParentList(current_entry)
            if parent_list is None:
                QtWidgets.QMessageBox.warning(None, "Error", "Could not find folder in settings data.")
                return None, None, None
            folder = parent_list[idx]
            folder.setdefault("entries", [])
            return folder["entries"], folder, f"folder '{folder.get('name')}'"

        parent_item = current_item.parent()
        if parent_item:
            parent_entry = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if parent_entry and parent_entry.get("type") == "folder":
                parent_list, idx = self.findParentList(parent_entry)
                if parent_list is None:
                    QtWidgets.QMessageBox.warning(
                        None, "Error", "Could not find parent folder in settings data.")
                    return None, None, None
                folder = parent_list[idx]
                folder.setdefault("entries", [])
                return folder["entries"], folder, f"parent folder '{folder.get('name')}'"

        debug_print(f"DEBUG {action_tag}: Added to root")
        return root, None, "root"

    def addFolder(self):
        folder_name, ok = QtWidgets.QInputDialog.getText(
            None, "New Folder", "Enter folder name:",
            QtWidgets.QLineEdit.EchoMode.Normal, "New Folder")
        if not ok or not folder_name.strip():
            return

        new_folder = {
            "type": "folder",
            "name": folder_name.strip(),
            "icon": None,
            "entries": [],
            "allowEmpty": True,
            "inline": "never",
            _UID_KEY: str(_uuid.uuid4()),
        }
        target_list, parent_entry, _ = self._targetListForNewEntry(
            self.foldersTreeWidget.currentItem(), "addFolder")
        if target_list is None:
            return
        target_list.append(new_folder)

        self.loadFolders()
        self.setUnsavedChanges()
        self.selectFolderByName(folder_name.strip(), parent_entry)

    def addProfileToMenu(self):
        profile_name, ok = QtWidgets.QInputDialog.getItem(
            None, "Add Profile", "Select profile to add:",
            app_state.profiles_list, 0, False)
        if not ok or not profile_name:
            return

        profile_guid = self.getProfileGuidByName(profile_name)
        if not profile_guid:
            QtWidgets.QMessageBox.warning(
                None, "Profile Not Found", f"Could not find GUID for profile '{profile_name}'.")
            return

        new_entry = {
            "type": "profile",
            "profile": profile_guid,
            "icon": None,
            _UID_KEY: str(_uuid.uuid4()),
        }
        target_list, parent_entry, location = self._targetListForNewEntry(
            self.foldersTreeWidget.currentItem(), "addProfileToMenu")
        if target_list is None:
            return
        target_list.append(new_entry)

        self.loadFolders()
        self.setUnsavedChanges()
        self.selectProfileByGuid(profile_guid, parent_entry)
        QtWidgets.QMessageBox.information(
            None, "Profile Added", f"Added profile '{profile_name}' to {location}.")

    def addSeparator(self):
        new_separator = {"type": "separator", _UID_KEY: str(_uuid.uuid4())}
        target_list, _, location = self._targetListForNewEntry(
            self.foldersTreeWidget.currentItem(), "addSeparator")
        if target_list is None:
            return
        target_list.append(new_separator)

        self.loadFolders()
        self.setUnsavedChanges()
        QtWidgets.QMessageBox.information(
            None, "Separator Added", f"Added separator to {location}.")

    def updateFolderItem(self):
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(None, "No Selection", "Please select an item to update.")
            return

        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return
        entry_type = entry.get("type", "unknown")

        # Auto-listed profile -> promote it to a real, explicit menu entry.
        if entry_type == "_virtual_remaining":
            self._promoteAutoProfile(entry)
            return

        old_name = entry.get("name", "") if entry_type == "folder" else ""

        parent_list, idx = self.findParentList(entry)
        if parent_list is None:
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find entry in settings data.")
            debug_print(f"DEBUG updateFolderItem: Could not find entry in data_schemes: {entry}")
            return
        actual_entry = parent_list[idx]

        if entry_type == "folder":
            new_name = self.folderNameEdit.text().strip()
            if not new_name:
                QtWidgets.QMessageBox.warning(None, "Invalid Name", "Folder name cannot be empty.")
                return
            actual_entry["name"] = new_name
            icon_text = self.folderIconEdit.text().strip()
            if icon_text:
                actual_entry["icon"] = icon_text
            else:
                actual_entry.pop("icon", None)
            actual_entry["allowEmpty"] = self.allowEmptyCheckBox.isChecked()
            actual_entry["inline"] = "always" if self.inlineCheckBox.isChecked() else "never"

        elif entry_type == "profile":
            profile_guid = self.getProfileGuidByName(self.menuProfileCombo.currentText())
            if profile_guid:
                actual_entry["profile"] = profile_guid
            icon_text = self.profileIconEdit.text().strip()
            if icon_text:
                actual_entry["icon"] = icon_text
            else:
                actual_entry.pop("icon", None)

        # Location move (folder / profile / separator).
        moved_to = self._applyLocationChange(actual_entry, parent_list)

        self.loadFolders()
        self.setUnsavedChanges()
        self.reselectItemByIdentity(actual_entry)

        if entry_type == "folder":
            msg = (f"Folder updated.\nOld name: '{old_name}'\n"
                   f"New name: '{actual_entry.get('name', '')}'.")
        else:
            msg = f"{entry_type.capitalize()} updated."
        if moved_to:
            msg += f"\nMoved to: {moved_to}."
        QtWidgets.QMessageBox.information(None, "Updated", msg)

    def _applyLocationChange(self, actual_entry, current_list):
        """If the Location combo points at a different list, move *actual_entry*
        there (appended at the end). Returns the destination label, or None."""
        dest_list = self._listForLocationKey(self.locationCombo.currentData())
        if dest_list is current_list:
            return None
        try:
            current_list.remove(actual_entry)
        except ValueError:
            return None
        dest_list.append(actual_entry)
        return self.locationCombo.currentText()

    def _promoteAutoProfile(self, virtual_entry):
        """Turn an auto-listed ('_virtual_remaining') profile into a real
        ``{"type":"profile", ...}`` entry in the chosen Location.
        ``remainingProfiles`` is left untouched - that profile simply stops
        being auto-listed because it now has an explicit entry."""
        guid = virtual_entry.get("profile")
        if not guid:
            return
        dest_list = self._listForLocationKey(self.locationCombo.currentData())
        new_entry = {
            "type": "profile",
            "profile": guid,
            "icon": None,
            _UID_KEY: str(_uuid.uuid4()),
        }
        dest_list.append(new_entry)
        self.loadFolders()
        self.setUnsavedChanges()
        self.reselectItemByIdentity(new_entry)
        QtWidgets.QMessageBox.information(
            None, "Added to menu",
            f"'{self.getProfileNameByGuid(guid)}' is now an explicit entry in "
            f"{self.locationCombo.currentText()}.\n"
            "It no longer appears under Remaining Profiles.")

    def deleteFolderItem(self):
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            return
        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return

        reply = QtWidgets.QMessageBox.question(
            None, "Delete Item", "Are you sure you want to delete this item?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

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

    def _moveFolderItem(self, delta: int, tag: str):
        current_item = self.foldersTreeWidget.currentItem()
        if not current_item:
            return
        entry = current_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not entry:
            return

        debug_print(f"DEBUG {tag}: Moving {entry.get('type')} id={id(entry)}")
        parent_list, idx = self.findParentList(entry)
        if parent_list is None:
            debug_print(f"DEBUG {tag}: Could not find entry in data_schemes")
            QtWidgets.QMessageBox.warning(None, "Error", "Could not find item in settings data.")
            return

        new_idx = idx + delta
        if 0 <= new_idx < len(parent_list):
            parent_list[idx], parent_list[new_idx] = parent_list[new_idx], parent_list[idx]
            debug_print(f"DEBUG {tag}: Swapped {idx} <-> {new_idx}")
            self.loadFolders()
            self.setUnsavedChanges()
            self.reselectItemByIdentity(entry)
        else:
            debug_print(f"DEBUG {tag}: At boundary")

    def moveFolderItemUp(self):
        self._moveFolderItem(-1, "moveFolderItemUp")

    def moveFolderItemDown(self):
        self._moveFolderItem(+1, "moveFolderItemDown")

    # ────────────────────────────────────────────────────────────────────
    #  Tree re-selection helpers
    # ────────────────────────────────────────────────────────────────────
    def _findTreeItem(self, predicate, parent_item=None):
        count = (parent_item.childCount() if parent_item
                 else self.foldersTreeWidget.topLevelItemCount())
        for i in range(count):
            item = (parent_item.child(i) if parent_item
                    else self.foldersTreeWidget.topLevelItem(i))
            if predicate(item, parent_item):
                return item
            found = self._findTreeItem(predicate, item)
            if found:
                return found
        return None

    def _selectTreeItem(self, item):
        if item:
            self.foldersTreeWidget.setCurrentItem(item)
            self.foldersTreeWidget.scrollToItem(item)

    def selectFolderByName(self, folder_name: str, parent_entry=None):
        def match(item, parent_item):
            entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if not (entry and entry.get("type") == "folder" and entry.get("name") == folder_name):
                return False
            if parent_entry is None and parent_item is None:
                return True
            if parent_entry and parent_item:
                return parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole) == parent_entry
            return False

        self._selectTreeItem(self._findTreeItem(match))

    def selectProfileByGuid(self, profile_guid: str, parent_entry=None):
        def match(item, parent_item):
            entry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if not (entry and entry.get("type") == "profile" and entry.get("profile") == profile_guid):
                return False
            if parent_entry is None and parent_item is None:
                return True
            if parent_entry and parent_item:
                return parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole) == parent_entry
            return False

        self._selectTreeItem(self._findTreeItem(match))

    def reselectItemByIdentity(self, entry: dict):
        """Re-select an item after a tree reload using its ``_wt_uid``."""
        uid = entry.get(_UID_KEY)
        if not uid:
            return

        def match(item, _parent):
            e = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            return bool(e and e.get(_UID_KEY) == uid)

        self._selectTreeItem(self._findTreeItem(match))
