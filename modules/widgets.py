"""Reusable Qt widget subclasses and value objects.

- ``CommandStep``          value object for the WT Command Builder
- ``DragDropTreeWidget``   drag-and-drop reordering for the Folders tree
- ``KeyRecorderDialog``    captures a keyboard shortcut into a WT key string
"""

from typing import Optional

from PyQt6 import QtCore, QtWidgets

from modules import app_state


class CommandStep:
    """A single step (new-tab or split-pane) in the WT Command Builder."""

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
        parts = ["new-tab" if self.kind == "new-tab" else "split-pane"]
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
    """QTreeWidget with drag-and-drop reordering for the folders tree."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.setDropIndicatorShown(True)
        self._ui = None  # set to the Ui_MainWindow instance by setupFoldersTab

    def _getEntry(self, item):
        if item is None:
            return None
        return item.data(0, QtCore.Qt.ItemDataRole.UserRole)

    def startDrag(self, supportedActions):
        """Prevent dragging remainingProfiles and virtual entries."""
        entry = self._getEntry(self.currentItem())
        if entry and entry.get("type") in ("remainingProfiles", "_virtual_remaining"):
            return
        super().startDrag(supportedActions)

    def dropEvent(self, event):
        """Update ``data_schemes`` for the drop, then reload the tree."""
        data_schemes = app_state.data_schemes
        dragged_item = self.currentItem()
        if not dragged_item:
            event.ignore()
            return

        dragged_entry = self._getEntry(dragged_item)
        if not dragged_entry or dragged_entry.get("type") in ("remainingProfiles", "_virtual_remaining"):
            event.ignore()
            return

        drop_pos = self.dropIndicatorPosition()
        target_item = self.itemAt(event.position().toPoint())
        target_entry = self._getEntry(target_item) if target_item else None

        if target_entry and target_entry.get("type") in ("remainingProfiles", "_virtual_remaining"):
            event.ignore()
            return

        if not self._ui:
            event.ignore()
            return

        parent_list, idx = self._ui.findParentList(dragged_entry)
        if parent_list is None:
            event.ignore()
            return
        parent_list.pop(idx)

        root_menu = data_schemes.get("newTabMenu", [])
        Pos = QtWidgets.QAbstractItemView.DropIndicatorPosition

        if target_item is None:
            root_menu.append(dragged_entry)
        elif drop_pos == Pos.OnItem:
            if target_entry and target_entry.get("type") == "folder":
                target_entry.setdefault("entries", []).append(dragged_entry)
            else:
                tgt_list, tgt_idx = self._ui.findParentList(target_entry)
                if tgt_list is not None:
                    tgt_list.insert(tgt_idx + 1, dragged_entry)
                else:
                    root_menu.append(dragged_entry)
        elif drop_pos == Pos.AboveItem:
            tgt_list, tgt_idx = self._ui.findParentList(target_entry)
            if tgt_list is not None:
                tgt_list.insert(tgt_idx, dragged_entry)
            else:
                root_menu.append(dragged_entry)
        elif drop_pos == Pos.BelowItem:
            tgt_list, tgt_idx = self._ui.findParentList(target_entry)
            if tgt_list is not None:
                tgt_list.insert(tgt_idx + 1, dragged_entry)
            else:
                root_menu.append(dragged_entry)
        else:
            root_menu.append(dragged_entry)

        event.setDropAction(QtCore.Qt.DropAction.IgnoreAction)
        event.accept()

        self._ui.loadFolders()
        self._ui.reselectItemByIdentity(dragged_entry)
        self._ui.setUnsavedChanges()


class KeyRecorderDialog(QtWidgets.QDialog):
    """Capture a keyboard shortcut and turn it into a WT key string."""

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

        key_name = self._qtKeyToWtName(key)
        if key_name:
            parts.append(key_name)
            self.recorded_keys = "+".join(parts)
            self.result_label.setText(self.recorded_keys)
            self.ok_btn.setEnabled(True)

    @staticmethod
    def _qtKeyToWtName(key) -> str:
        """Map a Qt key code to a Windows Terminal shortcut key name."""
        K = QtCore.Qt.Key
        mapping = {
            K.Key_A: "a", K.Key_B: "b", K.Key_C: "c", K.Key_D: "d", K.Key_E: "e",
            K.Key_F: "f", K.Key_G: "g", K.Key_H: "h", K.Key_I: "i", K.Key_J: "j",
            K.Key_K: "k", K.Key_L: "l", K.Key_M: "m", K.Key_N: "n", K.Key_O: "o",
            K.Key_P: "p", K.Key_Q: "q", K.Key_R: "r", K.Key_S: "s", K.Key_T: "t",
            K.Key_U: "u", K.Key_V: "v", K.Key_W: "w", K.Key_X: "x", K.Key_Y: "y",
            K.Key_Z: "z",
            K.Key_0: "0", K.Key_1: "1", K.Key_2: "2", K.Key_3: "3", K.Key_4: "4",
            K.Key_5: "5", K.Key_6: "6", K.Key_7: "7", K.Key_8: "8", K.Key_9: "9",
            K.Key_F1: "f1", K.Key_F2: "f2", K.Key_F3: "f3", K.Key_F4: "f4",
            K.Key_F5: "f5", K.Key_F6: "f6", K.Key_F7: "f7", K.Key_F8: "f8",
            K.Key_F9: "f9", K.Key_F10: "f10", K.Key_F11: "f11", K.Key_F12: "f12",
            K.Key_F13: "f13", K.Key_F14: "f14", K.Key_F15: "f15", K.Key_F16: "f16",
            K.Key_F17: "f17", K.Key_F18: "f18", K.Key_F19: "f19", K.Key_F20: "f20",
            K.Key_F21: "f21", K.Key_F22: "f22", K.Key_F23: "f23", K.Key_F24: "f24",
            K.Key_Return: "enter", K.Key_Enter: "enter",
            K.Key_Tab: "tab", K.Key_Space: "space",
            K.Key_Escape: "esc", K.Key_Backspace: "backspace",
            K.Key_Delete: "delete", K.Key_Insert: "insert",
            K.Key_Home: "home", K.Key_End: "end",
            K.Key_PageUp: "pgup", K.Key_PageDown: "pgdn",
            K.Key_Up: "up", K.Key_Down: "down",
            K.Key_Left: "left", K.Key_Right: "right",
            K.Key_Plus: "plus", K.Key_Minus: "minus",
            K.Key_Equal: "=", K.Key_Comma: ",",
            K.Key_Period: ".", K.Key_Slash: "/",
            K.Key_Backslash: "\\", K.Key_BracketLeft: "[",
            K.Key_BracketRight: "]", K.Key_Semicolon: ";",
            K.Key_Apostrophe: "'", K.Key_QuoteLeft: "`",
        }
        return mapping.get(key, "")
