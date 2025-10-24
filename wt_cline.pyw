import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QCheckBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QMessageBox, QGroupBox, QFileDialog, QColorDialog
)

# Built-in schemes available in Windows Terminal (not always present in settings.json)
BUILTIN_SCHEMES = [
    "Campbell", "Campbell Powershell", "Vintage", "One Half Dark",
    "One Half Light", "Solarized Dark", "Solarized Light",
    "Tango Dark", "Arthur"
]

def candidate_paths() -> List[Path]:
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    return [
        local / "Microsoft" / "Windows Terminal" / "settings.json",  # unpackaged
        local / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json",  # packaged
    ]

def read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # strip simple // comments
            cleaned = []
            for line in text.splitlines():
                if not line.strip().startswith("//"):
                    cleaned.append(line)
            return json.loads("\n".join(cleaned))
    except Exception:
        return None

def load_merged_settings() -> Dict[str, Any]:
    # Merge profiles.list and schemes from both locations (unpackaged may override packaged)
    base: Dict[str, Any] = {"profiles": {"list": []}, "schemes": []}
    for p in candidate_paths():
        if p.exists():
            data = read_json_file(p)
            if not data:
                continue
            # Merge schemes
            if "schemes" in data and isinstance(data["schemes"], list):
                base["schemes"].extend([s for s in data["schemes"] if isinstance(s, dict)])
            # Merge profiles.list
            profs = data.get("profiles", {})
            if isinstance(profs, dict) and isinstance(profs.get("list"), list):
                base["profiles"]["list"].extend([e for e in profs["list"] if isinstance(e, dict)])
    # Deduplicate schemes by name
    seen = set()
    uniq_schemes = []
    for s in base["schemes"]:
        nm = s.get("name")
        if nm and nm not in seen:
            seen.add(nm)
            uniq_schemes.append(s)
    base["schemes"] = uniq_schemes
    # Deduplicate profiles by guid if present; otherwise by name
    seenp = set()
    uniq_profiles = []
    for e in base["profiles"]["list"]:
        key = e.get("guid") or e.get("name")
        if key and key not in seenp:
            seenp.add(key)
            uniq_profiles.append(e)
    base["profiles"]["list"] = uniq_profiles
    return base

class CommandStep:
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
            parts.append(f"-p \"{self.profile_name}\"")
        if self.starting_directory:
            parts.append(f"-d \"{self.starting_directory}\"")
        if self.title:
            parts.append(f"--title \"{self.title}\"")
        if self.tab_color:
            parts.append(f"--tabColor '{self.tab_color}'")
        if self.color_scheme:
            parts.append(f"--colorScheme \"{self.color_scheme}\"")
        if self.commandline:
            parts.append(self.commandline)
        return " ".join(parts)

class WTBuilder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Terminal Command Builder")
        self.settings = load_merged_settings()
        self.profile_names, self.guid_map = self._extract_profiles(self.settings, include_hidden=True)
        self.scheme_names = self._extract_scheme_names(self.settings)

        # Global window options
        self.global_size_cols = QSpinBox()
        self.global_size_rows = QSpinBox()
        self.global_pos_x = QSpinBox()
        self.global_pos_y = QSpinBox()
        self.global_maximized = QCheckBox("Maximized")
        self.global_fullscreen = QCheckBox("Fullscreen")
        self.global_focus = QCheckBox("Focus mode")
        self.window_combo = QComboBox()
        self.window_combo.setEditable(True)
        self.window_combo.addItems(["", "new", "last"])
        self.window_combo.setEditText("")

        # Sequence and preview
        self.steps_list = QListWidget()
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.shell_combo = QComboBox()
        self.shell_combo.addItems(["PowerShell (escape `;)", "CMD (plain ;)"])

        # Step editor widgets
        self.profile_combo = QComboBox()
        self.scheme_combo = QComboBox()
        self.title_edit = QLineEdit()
        self.tab_color_edit = QLineEdit()
        self.dir_edit = QLineEdit()
        self.cmdline_edit = QLineEdit()
        self.pane_size_spin = QDoubleSpinBox()

        self.init_ui()
        self.refresh_preview()
        self._init_example()

    def _extract_profiles(self, data: Dict[str, Any], include_hidden: bool = True) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
        profiles_section = data.get("profiles", {})
        items = profiles_section.get("list", [])
        guid_map: Dict[str, Dict[str, Any]] = {p.get("guid"): p for p in items if isinstance(p, dict) and p.get("guid")}
        names: List[str] = []

        def add_profile_obj(prof_obj: Dict[str, Any]):
            if not include_hidden and prof_obj.get("hidden") is True:
                return
            nm = prof_obj.get("name") or prof_obj.get("tabTitle") or prof_obj.get("guid")
            if nm:
                names.append(nm)

        def walk(entries: List[Dict[str, Any]]):
            for e in entries:
                if not isinstance(e, dict):
                    continue
                t = e.get("type")
                if t == "profile":
                    prof_obj = None
                    if "profile" in e and e["profile"] in guid_map:
                        prof_obj = guid_map[e["profile"]]
                    elif "guid" in e:
                        prof_obj = e
                    if prof_obj:
                        add_profile_obj(prof_obj)
                elif t == "folder":
                    walk(e.get("entries", []))
                elif t in (None,):  # classic top-level profile
                    if "guid" in e or "name" in e:
                        add_profile_obj(e)
                # ignore separators

        walk(items)
        # Also ensure all standalone profiles appear even if not referenced in folders
        for p in items:
            if isinstance(p, dict) and (p.get("guid") or p.get("name")) and p.get("type") not in ("folder", "profile", "separator"):
                add_profile_obj(p)

        names = sorted(set(names))
        return names, guid_map

    def _extract_scheme_names(self, data: Dict[str, Any]) -> List[str]:
        user_schemes = [s.get("name") for s in data.get("schemes", []) if isinstance(s, dict) and s.get("name")]
        # Merge built-ins and user-defined
        return sorted(set(user_schemes + BUILTIN_SCHEMES))

    def init_ui(self):
        root = QVBoxLayout(self)

        # Global window options
        global_box = QGroupBox("Global window options")
        g_layout = QHBoxLayout()

        size_box = QGroupBox("--size (columns, rows)")
        s_layout = QHBoxLayout()
        self.global_size_cols.setRange(0, 1000)
        self.global_size_rows.setRange(0, 1000)
        s_layout.addWidget(QLabel("Columns"))
        s_layout.addWidget(self.global_size_cols)
        s_layout.addWidget(QLabel("Rows"))
        s_layout.addWidget(self.global_size_rows)
        size_box.setLayout(s_layout)

        pos_box = QGroupBox("--pos (x, y)")
        p_layout = QHBoxLayout()
        self.global_pos_x.setRange(0, 10000)
        self.global_pos_y.setRange(0, 10000)
        p_layout.addWidget(QLabel("X"))
        p_layout.addWidget(self.global_pos_x)
        p_layout.addWidget(QLabel("Y"))
        p_layout.addWidget(self.global_pos_y)
        pos_box.setLayout(p_layout)

        window_box = QGroupBox("--window")
        w_layout = QHBoxLayout()
        w_layout.addWidget(QLabel("Target"))
        w_layout.addWidget(self.window_combo)
        window_box.setLayout(w_layout)

        state_box = QGroupBox("State")
        st_layout = QVBoxLayout()
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
        steps_box = QGroupBox("Command sequence")
        sb_layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        add_tab_btn = QPushButton("Add new-tab")
        add_pane_h_btn = QPushButton("Add split-pane -H")
        add_pane_v_btn = QPushButton("Add split-pane -V")
        remove_btn = QPushButton("Remove selected")
        move_up_btn = QPushButton("Move up")
        move_down_btn = QPushButton("Move down")
        for b in (add_tab_btn, add_pane_h_btn, add_pane_v_btn, remove_btn, move_up_btn, move_down_btn):
            btn_row.addWidget(b)

        sb_layout.addLayout(btn_row)
        sb_layout.addWidget(self.steps_list)

        editor_box = QGroupBox("Step editor")
        ed_layout = QHBoxLayout()

        self.profile_combo.setEditable(True)
        self.profile_combo.addItems([""] + self.profile_names)

        self.scheme_combo.setEditable(True)
        self.scheme_combo.addItems([""] + self.scheme_names)

        self.title_edit.setPlaceholderText("Optional title")

        self.tab_color_edit.setPlaceholderText("#RRGGBB or #RGB")
        pick_btn = QPushButton("Pick…")
        pick_btn.clicked.connect(self.pick_color)

        self.dir_edit.setPlaceholderText("Starting directory")
        dir_btn = QPushButton("Browse…")
        dir_btn.clicked.connect(self.browse_dir)

        self.cmdline_edit.setPlaceholderText("Optional raw commandline (overrides -p)")

        self.pane_size_spin.setRange(0.05, 0.95)
        self.pane_size_spin.setSingleStep(0.05)
        self.pane_size_spin.setDecimals(2)
        self.pane_size_spin.setValue(0.5)

        apply_btn = QPushButton("Apply to selected step")

        left = QVBoxLayout()
        left.addWidget(QLabel("Profile (-p)"))
        left.addWidget(self.profile_combo)
        left.addWidget(QLabel("Color scheme (--colorScheme)"))
        left.addWidget(self.scheme_combo)
        left.addWidget(QLabel("Title (--title)"))
        left.addWidget(self.title_edit)

        mid = QVBoxLayout()
        mid.addWidget(QLabel("Tab color (--tabColor)"))
        trow = QHBoxLayout()
        trow.addWidget(self.tab_color_edit)
        trow.addWidget(pick_btn)
        mid.addLayout(trow)
        mid.addWidget(QLabel("Starting directory (-d)"))
        drow = QHBoxLayout()
        drow.addWidget(self.dir_edit)
        drow.addWidget(dir_btn)
        mid.addLayout(drow)
        mid.addWidget(QLabel("Raw commandline (overrides -p)"))
        mid.addWidget(self.cmdline_edit)

        right = QVBoxLayout()
        right.addWidget(QLabel("Split pane size (--size, fraction)"))
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
        preview_box = QGroupBox("Command preview")
        pv_layout = QVBoxLayout()
        pv_layout.addWidget(self.preview)
        run_row = QHBoxLayout()
        copy_btn = QPushButton("Copy")
        run_btn = QPushButton("Run")
        run_row.addWidget(QLabel("Shell:"))
        run_row.addWidget(self.shell_combo)
        run_row.addStretch(1)
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
        move_up_btn.clicked.connect(self.move_up)
        move_down_btn.clicked.connect(self.move_down)
        apply_btn.clicked.connect(self.apply_step)
        self.steps_list.currentItemChanged.connect(self.populate_editor_from_selection)
        self.shell_combo.currentIndexChanged.connect(self.refresh_preview)
        copy_btn.clicked.connect(self.copy_command)
        run_btn.clicked.connect(self.run_command)

    def _init_example(self):
        # Initial example sequence (matches your PS7 / PS5 / WSL)
        self.add_step("new-tab")
        self.profile_combo.setCurrentText("PS7")
        self.scheme_combo.setCurrentText("Arthur")
        self.apply_step()

        self.add_step("split-pane", "V")
        self.profile_combo.setCurrentText("PS5")
        self.tab_color_edit.setText("#f59218")
        self.apply_step()

        self.add_step("split-pane", "H")
        self.scheme_combo.setCurrentText("Arthur")
        self.cmdline_edit.setText("wsl.exe")
        self.apply_step()

    def pick_color(self):
        col = QColorDialog.getColor()
        if col.isValid():
            self.tab_color_edit.setText(col.name())  # #RRGGBB

    def browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select starting directory")
        if d:
            self.dir_edit.setText(d)

    def add_step(self, kind: str, orientation: str = ""):
        step = CommandStep(kind)
        step.split_orientation = orientation if kind == "split-pane" else ""
        item = QListWidgetItem(self.describe_step(step))
        item.setData(Qt.ItemDataRole.UserRole, step)
        self.steps_list.addItem(item)
        self.steps_list.setCurrentItem(item)
        self.refresh_preview()

    def remove_selected(self):
        row = self.steps_list.currentRow()
        if row >= 0:
            self.steps_list.takeItem(row)
            self.refresh_preview()

    def move_up(self):
        row = self.steps_list.currentRow()
        if row > 0:
            item = self.steps_list.takeItem(row)
            self.steps_list.insertItem(row - 1, item)
            self.steps_list.setCurrentItem(item)
            self.refresh_preview()

    def move_down(self):
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
            attrs.append(f"-p \"{step.profile_name}\"")
        if step.color_scheme:
            attrs.append(f"--colorScheme \"{step.color_scheme}\"")
        if step.tab_color:
            attrs.append(f"--tabColor '{step.tab_color}'")
        if step.starting_directory:
            attrs.append(f"-d \"{step.starting_directory}\"")
        if step.title:
            attrs.append(f"--title \"{step.title}\"")
        if step.pane_size is not None and step.kind == "split-pane":
            attrs.append(f"--size {step.pane_size}")
        if step.commandline:
            attrs.append(step.commandline)
        return f"{base} {' '.join(attrs)}".strip()

    def populate_editor_from_selection(self, current: Optional[QListWidgetItem], prev: Optional[QListWidgetItem]):
        if not current:
            return
        step: CommandStep = current.data(Qt.ItemDataRole.UserRole)
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
        step: CommandStep = item.data(Qt.ItemDataRole.UserRole)
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
            step: CommandStep = item.data(Qt.ItemDataRole.UserRole)
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
        QApplication.clipboard().setText(self.build_command())
        QMessageBox.information(self, "Copied", "Command copied to clipboard.")

    def run_command(self):
        cmd = self.build_command()
        try:
            if self.shell_combo.currentIndex() == 0:
                subprocess.Popen(["powershell", "-NoProfile", "-Command", cmd], shell=False)
            else:
                subprocess.Popen(["cmd.exe", "/c", cmd], shell=False)
        except Exception as e:
            QMessageBox.critical(self, "Run error", str(e))


def main():
    app = QApplication(sys.argv)
    w = WTBuilder()
    w.resize(1000, 750)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()