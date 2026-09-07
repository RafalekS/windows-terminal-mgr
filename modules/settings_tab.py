"""Settings tab: application config (theme, window, backup, WT settings path)
plus a few global Windows Terminal settings written straight to settings.json."""

from PyQt6 import QtWidgets

from modules import app_state
from modules import themes
from modules.config import APP_CONFIG, save_app_config


class SettingsMixin:
    """Settings tab UI + behaviour. Mixed into ``Ui_MainWindow``."""

    def setupSettingsTab(self):
        data_schemes = app_state.data_schemes

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        outer = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(outer)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        tab_layout = QtWidgets.QVBoxLayout(self.settingsTab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        scroll.setWidget(outer)

        # ── Appearance ──
        appear_group = QtWidgets.QGroupBox("Application Appearance")
        appear_form = QtWidgets.QFormLayout(appear_group)
        appear_form.setSpacing(8)
        theme_row = QtWidgets.QHBoxLayout()
        self.themeLight = QtWidgets.QRadioButton("Light")
        self.themeDark = QtWidgets.QRadioButton("Dark")
        current_theme = APP_CONFIG.get("theme", "light")
        self.themeLight.setChecked(current_theme == "light")
        self.themeDark.setChecked(current_theme == "dark")
        theme_row.addWidget(self.themeLight)
        theme_row.addWidget(self.themeDark)
        theme_row.addStretch()
        appear_form.addRow("Theme:", theme_row)
        self.themeLight.toggled.connect(self._onThemeToggled)
        layout.addWidget(appear_group)

        # ── Window ──
        window_group = QtWidgets.QGroupBox("Window Geometry")
        window_form = QtWidgets.QFormLayout(window_group)
        window_form.setSpacing(8)
        win_cfg = APP_CONFIG.get("window", {})
        size_row = QtWidgets.QHBoxLayout()
        self.settWinWidth = QtWidgets.QSpinBox()
        self.settWinWidth.setRange(800, 7680)
        self.settWinWidth.setValue(win_cfg.get("width", 1400))
        self.settWinHeight = QtWidgets.QSpinBox()
        self.settWinHeight.setRange(600, 4320)
        self.settWinHeight.setValue(win_cfg.get("height", 900))
        size_row.addWidget(QtWidgets.QLabel("W:"))
        size_row.addWidget(self.settWinWidth)
        size_row.addWidget(QtWidgets.QLabel("  H:"))
        size_row.addWidget(self.settWinHeight)
        size_row.addStretch()
        window_form.addRow("Default Size:", size_row)
        layout.addWidget(window_group)

        # ── Backup ──
        backup_group = QtWidgets.QGroupBox("settings.json Backup")
        backup_form = QtWidgets.QFormLayout(backup_group)
        backup_form.setSpacing(8)
        backup_cfg = APP_CONFIG.get("backup", {})
        self.settBackupEnabled = QtWidgets.QCheckBox("Create backup before each save")
        self.settBackupEnabled.setChecked(backup_cfg.get("enabled", True))
        backup_form.addRow(self.settBackupEnabled)
        self.settBackupMaxCount = QtWidgets.QSpinBox()
        self.settBackupMaxCount.setRange(1, 100)
        self.settBackupMaxCount.setValue(backup_cfg.get("max_count", 10))
        self.settBackupMaxCount.setToolTip(
            "Older backups beyond this count are deleted automatically")
        backup_form.addRow("Max backups to keep:", self.settBackupMaxCount)
        layout.addWidget(backup_group)

        # ── WT settings path ──
        path_group = QtWidgets.QGroupBox("Windows Terminal Settings Path")
        path_form = QtWidgets.QFormLayout(path_group)
        path_form.setSpacing(8)
        detected_label = QtWidgets.QLabel(app_state.settingsPath or "Not found")
        detected_label.setWordWrap(True)
        path_form.addRow("Auto-detected:", detected_label)
        override_row = QtWidgets.QHBoxLayout()
        self.settPathOverride = QtWidgets.QLineEdit()
        self.settPathOverride.setPlaceholderText("Leave empty to use auto-detected path")
        self.settPathOverride.setText(APP_CONFIG.get("wt_path_override", ""))
        override_browse = QtWidgets.QPushButton("Browse...")
        override_browse.setMaximumWidth(90)
        override_browse.clicked.connect(self._browseWtPath)
        override_row.addWidget(self.settPathOverride)
        override_row.addWidget(override_browse)
        path_form.addRow("Override Path:", override_row)
        layout.addWidget(path_group)

        # ── Global WT settings ──
        wt_group = QtWidgets.QGroupBox("Global Windows Terminal Settings")
        wt_form = QtWidgets.QFormLayout(wt_group)
        wt_form.setSpacing(8)
        wt_note = QtWidgets.QLabel(
            "These settings are written directly to settings.json when you click 'Apply & Save'.")
        wt_note.setWordWrap(True)
        wt_note.setObjectName("hint-label")
        wt_form.addRow(wt_note)

        self.settCopyOnSelect = QtWidgets.QCheckBox(
            "Copy selected text to clipboard automatically")
        self.settCopyOnSelect.setChecked(bool(data_schemes.get("copyOnSelect", False)))
        wt_form.addRow("Copy on Select:", self.settCopyOnSelect)

        self.settGlobalHistorySize = QtWidgets.QSpinBox()
        self.settGlobalHistorySize.setRange(0, 32767)
        self.settGlobalHistorySize.setValue(int(data_schemes.get("historySize", 9000)))
        self.settGlobalHistorySize.setToolTip(
            "Default history size for all profiles (can be overridden per profile)")
        wt_form.addRow("Default History Size:", self.settGlobalHistorySize)

        wt_form.addRow(QtWidgets.QLabel(
            "Disabled Profile Sources (prevents auto-generation):"))
        disabled_sources = data_schemes.get("disabledProfileSources", [])
        self.settDisableWsl = QtWidgets.QCheckBox("WSL (Windows.Terminal.Wsl)")
        self.settDisablePwsh = QtWidgets.QCheckBox(
            "PowerShell Core (Windows.Terminal.PowershellCore)")
        self.settDisableAzure = QtWidgets.QCheckBox("Azure (Windows.Terminal.Azure)")
        self.settDisableSsh = QtWidgets.QCheckBox("SSH (Windows.Terminal.SSH)")
        self.settDisableWsl.setChecked("Windows.Terminal.Wsl" in disabled_sources)
        self.settDisablePwsh.setChecked("Windows.Terminal.PowershellCore" in disabled_sources)
        self.settDisableAzure.setChecked("Windows.Terminal.Azure" in disabled_sources)
        self.settDisableSsh.setChecked("Windows.Terminal.SSH" in disabled_sources)
        for cb in (self.settDisableWsl, self.settDisablePwsh,
                   self.settDisableAzure, self.settDisableSsh):
            wt_form.addRow(cb)
        layout.addWidget(wt_group)

        # ── Shell integration ──
        shell_group = QtWidgets.QGroupBox("Shell Integration (profiles.defaults)")
        shell_form = QtWidgets.QFormLayout(shell_group)
        shell_form.setSpacing(8)
        shell_note = QtWidgets.QLabel(
            "Enable shell integration features. Requires your shell prompt to emit OSC 133 "
            "sequences. See the WT Shell Integration tutorial for PowerShell / CMD / Bash "
            "setup instructions.")
        shell_note.setWordWrap(True)
        shell_note.setObjectName("hint-label")
        shell_form.addRow(shell_note)

        profile_defaults = data_schemes.get("profiles", {}).get("defaults", {})
        self.settShowMarks = QtWidgets.QCheckBox(
            "Show command marks on scrollbar (showMarksOnScrollbar)")
        self.settShowMarks.setChecked(bool(profile_defaults.get("showMarksOnScrollbar", False)))
        self.settShowMarks.setToolTip(
            "Marks prompt boundaries on the scrollbar - requires shell to emit OSC 133 sequences")
        shell_form.addRow(self.settShowMarks)

        self.settAutoMark = QtWidgets.QCheckBox("Auto-mark prompts (autoMarkPrompts)")
        self.settAutoMark.setChecked(bool(profile_defaults.get("autoMarkPrompts", False)))
        self.settAutoMark.setToolTip(
            "Tell Windows Terminal to automatically mark the start of each prompt")
        shell_form.addRow(self.settAutoMark)

        self.settRightClickMenu = QtWidgets.QCheckBox(
            "Right-click context menu (experimental.rightClickContextMenu)")
        self.settRightClickMenu.setChecked(
            bool(profile_defaults.get("experimental.rightClickContextMenu", False)))
        self.settRightClickMenu.setToolTip(
            "Enables right-click context menu to select command output when shell "
            "integration is active")
        shell_form.addRow(self.settRightClickMenu)
        layout.addWidget(shell_group)

        save_btn = QtWidgets.QPushButton("Apply && Save Settings")
        save_btn.setObjectName("btn-save")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self._saveSettings)
        layout.addWidget(save_btn)
        layout.addStretch()

    def _onThemeToggled(self, checked):
        if not checked:
            return
        theme_name = "light" if self.themeLight.isChecked() else "dark"
        APP_CONFIG["theme"] = theme_name
        themes.CURRENT_THEME_COLORS = themes.load_theme(theme_name)
        QtWidgets.QApplication.instance().setStyleSheet(
            themes.build_stylesheet(themes.CURRENT_THEME_COLORS))

    def _browseWtPath(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select Windows Terminal Settings Directory")
        if path:
            self.settPathOverride.setText(path.replace("/", "\\"))

    def _saveSettings(self):
        data_schemes = app_state.data_schemes
        APP_CONFIG["theme"] = "light" if self.themeLight.isChecked() else "dark"
        APP_CONFIG["window"]["width"] = self.settWinWidth.value()
        APP_CONFIG["window"]["height"] = self.settWinHeight.value()
        APP_CONFIG["backup"]["enabled"] = self.settBackupEnabled.isChecked()
        APP_CONFIG["backup"]["max_count"] = self.settBackupMaxCount.value()
        APP_CONFIG["wt_path_override"] = self.settPathOverride.text().strip()

        if self.settCopyOnSelect.isChecked():
            data_schemes["copyOnSelect"] = True
        else:
            data_schemes.pop("copyOnSelect", None)

        hist = self.settGlobalHistorySize.value()
        if hist != 9000:
            data_schemes["historySize"] = hist
        else:
            data_schemes.pop("historySize", None)

        disabled = []
        if self.settDisableWsl.isChecked():
            disabled.append("Windows.Terminal.Wsl")
        if self.settDisablePwsh.isChecked():
            disabled.append("Windows.Terminal.PowershellCore")
        if self.settDisableAzure.isChecked():
            disabled.append("Windows.Terminal.Azure")
        if self.settDisableSsh.isChecked():
            disabled.append("Windows.Terminal.SSH")
        if disabled:
            data_schemes["disabledProfileSources"] = disabled
        else:
            data_schemes.pop("disabledProfileSources", None)

        pd = data_schemes.setdefault("profiles", {}).setdefault("defaults", {})
        for widget, key in ((self.settShowMarks, "showMarksOnScrollbar"),
                            (self.settAutoMark, "autoMarkPrompts"),
                            (self.settRightClickMenu, "experimental.rightClickContextMenu")):
            if widget.isChecked():
                pd[key] = True
            else:
                pd.pop(key, None)

        if save_app_config(APP_CONFIG):
            QtWidgets.QMessageBox.information(
                None, "Settings Saved",
                "Application settings saved.\n\n"
                "Click the main 'Save' button (Profiles tab) to write WT global settings "
                "to settings.json.")
        else:
            QtWidgets.QMessageBox.warning(
                None, "Save Failed",
                "Could not save application settings to config/settings.json.")
