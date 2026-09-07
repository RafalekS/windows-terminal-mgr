"""WT Command Builder tab: visual builder for ``wt.exe`` command lines, plus a
parser that turns an existing command back into builder steps."""

import re
import subprocess
from typing import List, Optional

from PyQt6 import QtCore, QtWidgets

from modules import app_state
from modules.constants import BUILTIN_SCHEMES
from modules.widgets import CommandStep


class CommandBuilderMixin:
    """Command Builder tab UI + behaviour. Mixed into ``Ui_MainWindow``."""

    # ────────────────────────────────────────────────────────────────────
    #  UI construction
    # ────────────────────────────────────────────────────────────────────
    def setupCommandBuilderTab(self):
        data_schemes = app_state.data_schemes
        root = QtWidgets.QVBoxLayout(self.commandBuilderTab)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.profile_names = [item["name"]
                              for item in data_schemes.get("profiles", {}).get("list", [])]
        user_schemes = [s.get("name") for s in data_schemes.get("schemes", [])
                        if isinstance(s, dict) and s.get("name")]
        self.scheme_names = sorted(set(user_schemes + BUILTIN_SCHEMES))

        # ── Global window options (collapsible) ──
        global_box = QtWidgets.QGroupBox(
            "Global Window Options  (expand to set --maximized, --size, --pos, --window)")
        global_box.setCheckable(True)
        global_box.setChecked(False)
        g_layout = QtWidgets.QHBoxLayout()
        g_layout.setSpacing(8)

        state_w = QtWidgets.QWidget()
        st_layout = QtWidgets.QVBoxLayout(state_w)
        st_layout.setContentsMargins(0, 0, 0, 0)
        self.global_maximized = QtWidgets.QCheckBox("--maximized")
        self.global_fullscreen = QtWidgets.QCheckBox("--fullscreen")
        self.global_focus = QtWidgets.QCheckBox("--focus")
        self.global_maximized.setToolTip("Start window maximized")
        self.global_fullscreen.setToolTip("Start window in fullscreen")
        self.global_focus.setToolTip("Start window in focus mode (hides tabs)")
        self.global_maximized.stateChanged.connect(
            lambda state: self.global_fullscreen.setChecked(False) if state else None)
        self.global_fullscreen.stateChanged.connect(
            lambda state: self.global_maximized.setChecked(False) if state else None)
        st_layout.addWidget(self.global_maximized)
        st_layout.addWidget(self.global_fullscreen)
        st_layout.addWidget(self.global_focus)

        win_w = QtWidgets.QWidget()
        win_l = QtWidgets.QFormLayout(win_w)
        win_l.setContentsMargins(0, 0, 0, 0)
        self.window_combo = QtWidgets.QComboBox()
        self.window_combo.setEditable(True)
        self.window_combo.addItems(["", "new", "last"])
        self.window_combo.setEditText("")
        self.window_combo.setToolTip(
            "--window: 'new' = new window, 'last' = most recent, or window ID")
        win_l.addRow("--window:", self.window_combo)

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

        # ── Command steps ──
        steps_box = QtWidgets.QGroupBox("Command Steps  (each step = a new tab or split pane)")
        sb_layout = QtWidgets.QVBoxLayout()
        sb_layout.setSpacing(6)

        btn_row = QtWidgets.QHBoxLayout()
        add_tab_btn = QtWidgets.QPushButton("+ New Tab")
        add_tab_btn.setToolTip("Add a new-tab step")
        add_pane_h_btn = QtWidgets.QPushButton("+ Split Horizontal")
        add_pane_h_btn.setToolTip("Add a split-pane -H step (split top/bottom)")
        add_pane_v_btn = QtWidgets.QPushButton("+ Split Vertical")
        add_pane_v_btn.setToolTip("Add a split-pane -V step (split left/right)")
        remove_btn = QtWidgets.QPushButton("Remove Step")
        remove_btn.setToolTip("Remove the selected step")
        remove_btn.setObjectName("btn-delete")
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

        step_splitter = self._cmd_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.steps_list = QtWidgets.QListWidget()
        self.steps_list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.steps_list.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.steps_list.model().rowsMoved.connect(lambda *_: self.refresh_preview())
        step_splitter.addWidget(self.steps_list)

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
        self.use_parent_dir_check.setToolTip(
            "Adds --useParentProcessDirectory flag: start in the directory of the calling process")
        ed_layout.addRow("", self.use_parent_dir_check)

        self.cmdline_edit = QtWidgets.QLineEdit()
        self.cmdline_edit.setPlaceholderText('e.g. powershell.exe -c "echo Hello"  or  wsl.exe')
        self.cmdline_edit.setToolTip(
            "Executable + args to run instead of the profile default.\n"
            "Must be a valid Windows executable path.\n"
            "Examples: cmd.exe /c dir, powershell.exe, wsl.exe, ssh.exe user@host")
        ed_layout.addRow("Commandline:", self.cmdline_edit)

        self.pane_size_label = QtWidgets.QLabel("Pane Size (--size):")
        self.pane_size_spin = QtWidgets.QDoubleSpinBox()
        self.pane_size_spin.setRange(0.05, 0.95)
        self.pane_size_spin.setSingleStep(0.05)
        self.pane_size_spin.setDecimals(2)
        self.pane_size_spin.setValue(0.5)
        self.pane_size_spin.setToolTip("Fraction of parent pane size (0.05 to 0.95)")
        ed_layout.addRow(self.pane_size_label, self.pane_size_spin)

        step_splitter.addWidget(editor_box)
        step_splitter.setSizes([400, 400])
        step_splitter.setStretchFactor(0, 1)
        step_splitter.setStretchFactor(1, 1)
        sb_layout.addWidget(step_splitter)
        steps_box.setLayout(sb_layout)
        root.addWidget(steps_box, 1)

        # ── Preview ──
        preview_box = QtWidgets.QGroupBox(
            "Command Preview  (edit manually or build above, then Copy/Run)")
        pv_layout = QtWidgets.QVBoxLayout()
        pv_layout.setSpacing(4)
        self.preview = QtWidgets.QTextEdit()
        self.preview.setReadOnly(False)
        self.preview.setMaximumHeight(60)
        self.preview.setPlaceholderText(
            "Paste a wt command here and click Parse, or build one above")
        pv_layout.addWidget(self.preview)

        run_row = QtWidgets.QHBoxLayout()
        self.shell_combo = QtWidgets.QComboBox()
        self.shell_combo.addItems(["PowerShell (escape `;)", "CMD (plain ;)"])
        self.shell_combo.setToolTip(
            "Which shell to use for escaping semicolons and running the command")
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

        # ── Signals ──
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

        for w in (self.profile_combo, self.scheme_combo):
            w.currentTextChanged.connect(self.auto_apply_step)
        for w in (self.title_edit, self.tab_color_edit, self.dir_edit, self.cmdline_edit):
            w.textChanged.connect(self.auto_apply_step)
        self.use_parent_dir_check.stateChanged.connect(self.auto_apply_step)
        self.pane_size_spin.valueChanged.connect(self.auto_apply_step)

        self.pane_size_label.setVisible(False)
        self.pane_size_spin.setVisible(False)
        self._persist.bind_splitter(self._cmd_splitter, "cmd_builder")
        self.refresh_preview()

    # ────────────────────────────────────────────────────────────────────
    #  Step editing
    # ────────────────────────────────────────────────────────────────────
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

    def _move_step(self, delta: int):
        row = self.steps_list.currentRow()
        new_row = row + delta
        if row >= 0 and 0 <= new_row < self.steps_list.count():
            item = self.steps_list.takeItem(row)
            self.steps_list.insertItem(new_row, item)
            self.steps_list.setCurrentItem(item)
            self.refresh_preview()

    def move_cmd_up(self):
        self._move_step(-1)

    def move_cmd_down(self):
        self._move_step(+1)

    def describe_step(self, step: CommandStep) -> str:
        if step.kind == "new-tab":
            base = "new-tab"
        elif step.split_orientation == "H":
            base = "split-pane -H"
        elif step.split_orientation == "V":
            base = "split-pane -V"
        else:
            base = "split-pane"
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

    def populate_editor_from_selection(self, current, _prev):
        if not current:
            return
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

        is_split = step.kind == "split-pane"
        self.pane_size_label.setVisible(is_split)
        self.pane_size_spin.setVisible(is_split)
        self.pane_size_spin.setValue(step.pane_size if (is_split and step.pane_size is not None) else 0.5)
        self._populating_editor = False

    def auto_apply_step(self):
        if getattr(self, "_populating_editor", False):
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
        self.dir_edit.setEnabled(not step.use_parent_dir)
        step.commandline = self.cmdline_edit.text().strip()
        if step.kind == "split-pane":
            step.pane_size = float(f"{self.pane_size_spin.value():.2f}")
        else:
            step.pane_size = None
        item.setText(self.describe_step(step))
        self.refresh_preview()

    # ────────────────────────────────────────────────────────────────────
    #  Command assembly
    # ────────────────────────────────────────────────────────────────────
    def build_global_options(self) -> List[str]:
        opts = []
        c = self.global_size_cols.value()
        r = self.global_size_rows.value()
        if c > 0 and r > 0:
            opts.append(f"--size {c},{r}")
        elif c > 0:
            opts.append(f"--size {c},")
        elif r > 0:
            opts.append(f"--size ,{r}")

        x = self.global_pos_x.value()
        y = self.global_pos_y.value()
        if x > 0 and y > 0:
            opts.append(f"--pos {x},{y}")
        elif x > 0:
            opts.append(f"--pos {x},")
        elif y > 0:
            opts.append(f"--pos ,{y}")

        if self.global_maximized.isChecked():
            opts.append("--maximized")
        if self.global_fullscreen.isChecked():
            opts.append("--fullscreen")
        if self.global_focus.isChecked():
            opts.append("--focus")
        w = self.window_combo.currentText().strip()
        if w:
            opts.append(f"--window {w}")
        return opts

    def build_sequence(self) -> List[str]:
        seq = []
        for i in range(self.steps_list.count()):
            step: CommandStep = self.steps_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole)
            seq.append(step.build())
        return seq

    def build_command(self) -> str:
        opts = self.build_global_options()
        seq = self.build_sequence()
        cmd_seq = " ; ".join(seq) if seq else ""
        if opts and cmd_seq:
            final = f"wt {' '.join(opts)} {cmd_seq}"
        elif opts:
            final = f"wt {' '.join(opts)}"
        elif cmd_seq:
            final = f"wt {cmd_seq}"
        else:
            final = "wt"
        if self.shell_combo.currentIndex() == 0:  # PowerShell needs `; escaping
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
        except OSError as e:
            QtWidgets.QMessageBox.critical(None, "Run error", str(e))

    # ────────────────────────────────────────────────────────────────────
    #  Parser
    # ────────────────────────────────────────────────────────────────────
    def parse_command(self):
        cmd = self.preview.toPlainText().strip()
        if not cmd:
            QtWidgets.QMessageBox.warning(None, "Empty Command", "Please enter a command to parse.")
            return

        cmd = cmd.replace(" `; ", " ; ")
        if cmd.startswith("wt "):
            cmd = cmd[3:].strip()
        elif cmd.startswith("wt.exe "):
            cmd = cmd[7:].strip()

        self.global_size_cols.setValue(0)
        self.global_size_rows.setValue(0)
        self.global_pos_x.setValue(0)
        self.global_pos_y.setValue(0)
        self.global_maximized.setChecked(False)
        self.global_fullscreen.setChecked(False)
        self.global_focus.setChecked(False)
        self.window_combo.setCurrentText("")

        global_opts = ""
        remaining_cmd = cmd
        while remaining_cmd:
            matched = False
            for flag in ("--maximized", "--fullscreen", "--focus"):
                if remaining_cmd.startswith(flag):
                    global_opts += flag + " "
                    remaining_cmd = remaining_cmd[len(flag):].strip()
                    matched = True
                    break
            if not matched:
                for opt in ("--size", "--pos", "--window"):
                    if remaining_cmd.startswith(opt):
                        temp = remaining_cmd[len(opt):].strip()
                        match_arg = re.match(r"^(\S+)", temp)
                        if match_arg:
                            arg = match_arg.group(1)
                            global_opts += f"{opt} {arg} "
                            remaining_cmd = temp[len(arg):].strip()
                            matched = True
                            break
            if not matched:
                break
        cmd = remaining_cmd

        if "--size" in global_opts:
            m = re.search(r"--size\s+(\d*),(\d*)", global_opts)
            if m:
                if m.group(1):
                    self.global_size_cols.setValue(int(m.group(1)))
                if m.group(2):
                    self.global_size_rows.setValue(int(m.group(2)))
        if "--pos" in global_opts:
            m = re.search(r"--pos\s+(\d*),(\d*)", global_opts)
            if m:
                if m.group(1):
                    self.global_pos_x.setValue(int(m.group(1)))
                if m.group(2):
                    self.global_pos_y.setValue(int(m.group(2)))
        if "--maximized" in global_opts:
            self.global_maximized.setChecked(True)
        if "--fullscreen" in global_opts:
            self.global_fullscreen.setChecked(True)
        if "--focus" in global_opts:
            self.global_focus.setChecked(True)
        if "--window" in global_opts:
            m = re.search(r"--window\s+(\w+)", global_opts)
            if m:
                self.window_combo.setCurrentText(m.group(1))

        self.steps_list.clear()
        steps_parsed = 0
        for cmd_str in re.split(r"\s*;\s*", cmd):
            if not cmd_str.strip():
                continue
            step = self._parse_step(cmd_str)
            if step is None:
                continue
            item = QtWidgets.QListWidgetItem(self.describe_step(step))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, step)
            self.steps_list.addItem(item)
            steps_parsed += 1

        self.refresh_preview()
        if steps_parsed > 0:
            QtWidgets.QMessageBox.information(
                None, "Command Parsed", f"Successfully parsed {steps_parsed} command step(s).")
        else:
            QtWidgets.QMessageBox.warning(
                None, "No Commands Found",
                "Could not find any valid new-tab or split-pane commands in the input.\n\n"
                "Make sure your command starts with 'new-tab' or 'split-pane'.")

    @staticmethod
    def _parse_step(cmd_str: str) -> Optional[CommandStep]:
        if cmd_str.startswith("new-tab"):
            step = CommandStep("new-tab")
            cmd_str = cmd_str[7:].strip()
        elif cmd_str.startswith("split-pane"):
            step = CommandStep("split-pane")
            cmd_str = cmd_str[10:].strip()
            if cmd_str.startswith("-H"):
                step.split_orientation = "H"
                cmd_str = cmd_str[2:].strip()
            elif cmd_str.startswith("-V"):
                step.split_orientation = "V"
                cmd_str = cmd_str[2:].strip()
        else:
            return None

        m = re.search(r'-p\s+"([^"]+)"', cmd_str)
        if m:
            step.profile_name = m.group(1)

        if "--useParentProcessDirectory" in cmd_str:
            step.use_parent_dir = True
            cmd_str = cmd_str.replace("--useParentProcessDirectory", "").strip()
        else:
            m = re.search(r'-d\s+"([^"]+)"', cmd_str)
            if m:
                step.starting_directory = m.group(1)

        m = re.search(r'--title\s+"([^"]+)"', cmd_str)
        if m:
            step.title = m.group(1)

        m = re.search(r"--tabColor\s+'([^']+)'", cmd_str) or re.search(r'--tabColor\s+"([^"]+)"', cmd_str)
        if m:
            step.tab_color = m.group(1)

        m = re.search(r'--colorScheme\s+"([^"]+)"', cmd_str)
        if m:
            step.color_scheme = m.group(1)

        if step.kind == "split-pane":
            m = re.search(r"--size\s+([\d.]+)", cmd_str)
            if m:
                step.pane_size = float(m.group(1))

        temp_cmd = cmd_str
        for pattern in (r'-p\s+"[^"]+"', r'-d\s+"[^"]+"', r'--title\s+"[^"]+"',
                        r"--tabColor\s+'[^']+'", r'--tabColor\s+"[^"]+"',
                        r'--colorScheme\s+"[^"]+"', r"--size\s+[\d.]+",
                        r"--useParentProcessDirectory"):
            temp_cmd = re.sub(pattern, "", temp_cmd)
        remaining = temp_cmd.strip()
        if remaining:
            step.commandline = remaining
        return step
