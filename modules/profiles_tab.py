"""Profiles tab: per-profile editor, the "Defaults" pseudo-profile,
environment variables, pixel shader, and profile templates."""

import copy
import uuid as _uuid

from PyQt6 import QtCore, QtGui, QtWidgets

from modules import app_state
from modules.config import APP_CONFIG
from modules import constants


class ProfilesMixin:
    """Profiles tab UI + behaviour. Mixed into ``Ui_MainWindow``."""

    # ────────────────────────────────────────────────────────────────────
    #  UI construction
    # ────────────────────────────────────────────────────────────────────
    def setupProfilesTab(self):
        data_list = app_state.data_list
        font_list = app_state.font_list
        profiles_list = app_state.profiles_list
        default_profile = app_state.default_profile

        main_layout = QtWidgets.QHBoxLayout(self.profilesTab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ── Left: profile list + controls ──
        left_widget = QtWidgets.QWidget()
        _pp = APP_CONFIG.get("profiles_panel", {})
        left_widget.setMinimumWidth(_pp.get("min_width", 250))
        left_widget.setMaximumWidth(_pp.get("max_width", 300))
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        profiles_label = QtWidgets.QLabel("Profiles:")
        profiles_label.setFont(QtGui.QFont("", 10, QtGui.QFont.Weight.Bold))
        left_layout.addWidget(profiles_label)

        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setMinimumHeight(400)
        defaults_item = QtWidgets.QListWidgetItem("\u2699 Defaults (all profiles)")
        defaults_item.setToolTip("Edit default settings applied to all profiles (profiles.defaults)")
        self.listWidget.addItem(defaults_item)
        for item in profiles_list:
            self.listWidget.addItem(item)
        self.updateProfileMenuIndicators()
        left_layout.addWidget(self.listWidget)

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

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        left_layout.addWidget(separator)

        profile_mgmt_layout = QtWidgets.QGridLayout()
        self.newProfileButton = QtWidgets.QPushButton("New Profile")
        self.duplicateProfileButton = QtWidgets.QPushButton("Duplicate Profile")
        self.templateProfileButton = QtWidgets.QPushButton("From Template...")
        self.deleteProfileButton = QtWidgets.QPushButton("Delete Profile")
        self.deleteProfileButton.setObjectName("btn-delete")
        profile_mgmt_layout.addWidget(self.newProfileButton, 0, 0)
        profile_mgmt_layout.addWidget(self.duplicateProfileButton, 0, 1)
        profile_mgmt_layout.addWidget(self.templateProfileButton, 1, 0, 1, 2)
        profile_mgmt_layout.addWidget(self.deleteProfileButton, 2, 0, 1, 2)
        left_layout.addLayout(profile_mgmt_layout)

        # The Save button lives in the shared bottom bar (main_window.setupUi) so
        # it is reachable from every tab.
        left_layout.addStretch()
        main_layout.addWidget(left_widget)

        # ── Right: profile details (scroll area) ──
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_widget = QtWidgets.QWidget()
        scroll_main = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_main.setSpacing(6)

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

        # ── General ──
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

        general_layout.addRow("Tab Color:", makeColorRow("tabColorEdit"))

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

        # ── Appearance ──
        appearance_group = QtWidgets.QGroupBox("Appearance")
        appearance_layout = QtWidgets.QFormLayout(appearance_group)
        appearance_layout.setSpacing(6)

        self.comboBox = QtWidgets.QComboBox()
        for item in data_list:
            self.comboBox.addItem(item)
        appearance_layout.addRow("Color Scheme:", self.comboBox)

        font_layout = QtWidgets.QHBoxLayout()
        self.fontBox = QtWidgets.QComboBox()
        self.fontBox.setMinimumWidth(180)
        for item in font_list:
            self.fontBox.addItem(item)
        self.fontSize = QtWidgets.QSpinBox()
        self.fontSize.setMinimum(4)
        self.fontSize.setMaximum(72)
        self.fontSize.setValue(APP_CONFIG.get("defaults", {}).get("font_size", 12))
        self.fontWeightBox = QtWidgets.QComboBox()
        self.fontWeightBox.addItems(constants.FONT_WEIGHTS)
        font_layout.addWidget(self.fontBox, 3)
        font_layout.addWidget(QtWidgets.QLabel("Size:"))
        font_layout.addWidget(self.fontSize, 1)
        font_layout.addWidget(QtWidgets.QLabel("Weight:"))
        font_layout.addWidget(self.fontWeightBox, 1)
        appearance_layout.addRow("Font:", font_layout)

        cursor_layout = QtWidgets.QHBoxLayout()
        self.cursorShapeBox = QtWidgets.QComboBox()
        self.cursorShapeBox.addItems(constants.CURSOR_SHAPES)
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

        appearance_layout.addRow("Foreground:", makeColorRow("foregroundEdit"))
        appearance_layout.addRow("Background:", makeColorRow("backgroundColorEdit"))
        appearance_layout.addRow("Selection BG:", makeColorRow("selectionBackgroundEdit"))

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
        self.intenseTextBox.addItems(constants.INTENSE_TEXT_STYLES)
        appearance_layout.addRow("Intense Text:", self.intenseTextBox)

        shader_layout = QtWidgets.QHBoxLayout()
        self.pixelShaderEdit = QtWidgets.QLineEdit()
        self.pixelShaderEdit.setPlaceholderText("Path to .hlsl shader file (optional)")
        self.pixelShaderEdit.setToolTip(
            "experimental.pixelShaderPath: Apply a custom HLSL pixel shader to this profile")
        shader_browse_btn = QtWidgets.QPushButton("Browse...")
        shader_browse_btn.setMaximumWidth(90)
        shader_browse_btn.clicked.connect(self._browsePixelShader)
        shader_layout.addWidget(self.pixelShaderEdit)
        shader_layout.addWidget(shader_browse_btn)
        appearance_layout.addRow("Pixel Shader:", shader_layout)
        scroll_main.addWidget(appearance_group)

        # ── Background Image ──
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
        self.bgStretchBox.addItems(constants.BG_STRETCH_MODES)
        bgimg_opts.addWidget(self.bgStretchBox, 1)
        bgimg_opts.addWidget(QtWidgets.QLabel("Align:"))
        self.bgAlignBox = QtWidgets.QComboBox()
        self.bgAlignBox.addItems(constants.BG_ALIGNMENTS)
        bgimg_opts.addWidget(self.bgAlignBox, 1)
        bgimg_layout.addRow("Opacity:", bgimg_opts)
        scroll_main.addWidget(bgimg_group)

        # ── Advanced ──
        advanced_group = QtWidgets.QGroupBox("Advanced")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
        advanced_layout = QtWidgets.QFormLayout(advanced_group)
        advanced_layout.setSpacing(6)

        self.historySizeSpinBox = QtWidgets.QSpinBox()
        self.historySizeSpinBox.setMinimum(0)
        self.historySizeSpinBox.setMaximum(32767)
        self.historySizeSpinBox.setValue(APP_CONFIG.get("defaults", {}).get("history_size", 9001))
        advanced_layout.addRow("History Size:", self.historySizeSpinBox)

        self.closeOnExitBox = QtWidgets.QComboBox()
        self.closeOnExitBox.addItems(constants.CLOSE_ON_EXIT_MODES)
        advanced_layout.addRow("Close on Exit:", self.closeOnExitBox)

        self.bellStyleBox = QtWidgets.QComboBox()
        self.bellStyleBox.addItems(constants.BELL_STYLES)
        advanced_layout.addRow("Bell Style:", self.bellStyleBox)

        self.antialiasingBox = QtWidgets.QComboBox()
        self.antialiasingBox.addItems(constants.ANTIALIASING_MODES)
        advanced_layout.addRow("Antialiasing:", self.antialiasingBox)

        self.scrollbarBox = QtWidgets.QComboBox()
        self.scrollbarBox.addItems(constants.SCROLLBAR_STATES)
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

        advanced_layout.addRow(QtWidgets.QLabel("Environment Variables:"))
        self.envVarsTable = QtWidgets.QTableWidget()
        self.envVarsTable.setColumnCount(2)
        self.envVarsTable.setHorizontalHeaderLabels(["Variable Name", "Value"])
        self.envVarsTable.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.envVarsTable.horizontalHeader().setSectionsMovable(True)
        self.envVarsTable.verticalHeader().setVisible(False)
        self.envVarsTable.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.envVarsTable.setAlternatingRowColors(True)
        self.envVarsTable.setMaximumHeight(150)
        advanced_layout.addRow(self.envVarsTable)

        env_btn_row = QtWidgets.QHBoxLayout()
        self.addEnvVarButton = QtWidgets.QPushButton("Add Variable")
        self.removeEnvVarButton = QtWidgets.QPushButton("Remove Selected")
        self.removeEnvVarButton.setObjectName("btn-delete")
        env_btn_row.addWidget(self.addEnvVarButton)
        env_btn_row.addWidget(self.removeEnvVarButton)
        env_btn_row.addStretch()
        advanced_layout.addRow(env_btn_row)

        self.addEnvVarButton.clicked.connect(self._addEnvVar)
        self.removeEnvVarButton.clicked.connect(self._removeEnvVar)
        self.envVarsTable.itemChanged.connect(self._onEnvVarChanged)
        # Row order is meaningful for env vars - persist width/order only.
        self._persist.bind_table(self.envVarsTable, "env_vars", sortable=False)

        scroll_main.addWidget(advanced_group)
        scroll_main.addStretch()
        scroll_area.setWidget(scroll_widget)
        right_layout.addWidget(scroll_area)
        main_layout.addWidget(right_widget)

        # ── Signals ──
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
        self.pixelShaderEdit.textChanged.connect(self.changePixelShader)
        self.defaultButton.clicked.connect(self.changeDefault)
        self.moveUpButton.clicked.connect(self.moveProfileUp)
        self.moveDownButton.clicked.connect(self.moveProfileDown)
        self.renameButton.clicked.connect(self.renameProfile)
        self.newProfileButton.clicked.connect(self.createNewProfile)
        self.duplicateProfileButton.clicked.connect(self.duplicateProfile)
        self.templateProfileButton.clicked.connect(self.createProfileFromTemplate)
        self.deleteProfileButton.clicked.connect(self.deleteProfile)

        index_listWidget = self.listWidget.findItems(
            default_profile, QtCore.Qt.MatchFlag.MatchFixedString)
        if index_listWidget:
            self.listWidget.setCurrentRow(self.listWidget.row(index_listWidget[0]))
        elif self.listWidget.count() > 1:
            self.listWidget.setCurrentRow(1)

    # ────────────────────────────────────────────────────────────────────
    #  Shared helpers
    # ────────────────────────────────────────────────────────────────────
    def _pickColorInto(self, line_edit):
        col = QtWidgets.QColorDialog.getColor()
        if col.isValid():
            line_edit.setText(col.name())

    def getCurrentIndex(self):
        """Index into the profiles list. Row 0 is 'Defaults', so subtract 1."""
        if self.listWidget.currentItem():
            row = self.listWidget.currentRow()
            if row == 0:
                return -1
            current = self.listWidget.currentItem().text()
            for i, dic in enumerate(app_state.data_schemes.get("profiles", {}).get("list", [])):
                if dic.get("name") == current:
                    return i
        return -1

    def isDefaultsSelected(self):
        return self.listWidget.currentRow() == 0

    def _setProfileField(self, key, value, sub_key=None):
        """Set (or, when *value* is empty/None/False-ish, remove) a profile key.

        Routes to ``profiles.defaults`` when the Defaults pseudo-profile is
        selected.
        """
        if self.isDefaultsSelected():
            self._setDefaultsField(key, value, sub_key)
            return
        idx = self.getCurrentIndex()
        if idx < 0:
            return
        profile = app_state.data_schemes["profiles"]["list"][idx]
        if sub_key:
            if value:
                profile.setdefault(key, {})[sub_key] = value
            elif key in profile and sub_key in profile[key]:
                del profile[key][sub_key]
                if not profile[key]:
                    del profile[key]
        else:
            if value is not None and value != "":
                profile[key] = value
            else:
                profile.pop(key, None)
        self.setUnsavedChanges()

    # ────────────────────────────────────────────────────────────────────
    #  Profile-field change handlers
    # ────────────────────────────────────────────────────────────────────
    def changeDefault(self):
        current = self.listWidget.currentItem().text()
        for item in app_state.data_schemes.get("profiles", {}).get("list", []):
            if item.get("name") == current:
                app_state.data_schemes["defaultProfile"] = item.get("guid")
                self.setUnsavedChanges()
                break

    def changeScheme(self, param):
        idx = self.getCurrentIndex()
        if idx >= 0:
            app_state.data_schemes["profiles"]["list"][idx]["colorScheme"] = self.comboBox.itemText(param)
            self.setUnsavedChanges()

    def changeFontSize(self, param):
        idx = self.getCurrentIndex()
        if idx >= 0:
            profile = app_state.data_schemes["profiles"]["list"][idx]
            profile.setdefault("font", {})["size"] = param
            profile.pop("fontSize", None)  # drop deprecated key
            self.setUnsavedChanges()

    def changeFont(self, param):
        idx = self.getCurrentIndex()
        if idx >= 0:
            profile = app_state.data_schemes["profiles"]["list"][idx]
            profile.setdefault("font", {})["face"] = self.fontBox.itemText(param)
            profile.pop("fontFace", None)  # drop deprecated key
            self.setUnsavedChanges()

    def changeFontWeight(self, text):
        self._setProfileField("font", text if text != "normal" else None, "weight")

    def changeBgImageOpacity(self):
        idx = self.getCurrentIndex()
        if idx >= 0:
            opacity = self.horizontalSlider.value() / 10
            app_state.data_schemes["profiles"]["list"][idx]["backgroundImageOpacity"] = opacity
            self.bgOpacityLabel.setText(str(opacity))
            self.setUnsavedChanges()

    def changeBackgroundImage(self):
        idx = self.getCurrentIndex()
        if idx >= 0:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                None, "Open File", "", "Images (*.png *.jpg *.jpeg *.gif *.bmp)")
            if filename:
                filename = filename.replace("/", "\\")
                app_state.data_schemes["profiles"]["list"][idx]["backgroundImage"] = filename
                self.backgroundImageEdit.setText(filename)
                self.setUnsavedChanges()

    def changeCommandLine(self, text):
        if self.ui_initialized:
            self._setProfileField("commandline", text or None)

    def changeStartingDirectory(self, text):
        if self.ui_initialized:
            self._setProfileField("startingDirectory", text or None)

    def changeTabTitle(self, text):
        if self.ui_initialized:
            self._setProfileField("tabTitle", text or None)

    def changeTabColor(self, text):
        if self.ui_initialized:
            self._setProfileField("tabColor", text or None)

    def changeIcon(self, text):
        if self.ui_initialized:
            self._setProfileField("icon", text or None)

    def changePadding(self, text):
        if self.ui_initialized:
            self._setProfileField("padding", text or None)

    def changeCursorShape(self, text):
        idx = self.getCurrentIndex()
        if idx >= 0:
            app_state.data_schemes["profiles"]["list"][idx]["cursorShape"] = text
            self.setUnsavedChanges()

    def changeScrollbarState(self, text):
        idx = self.getCurrentIndex()
        if idx >= 0:
            app_state.data_schemes["profiles"]["list"][idx]["scrollbarState"] = text
            self.setUnsavedChanges()

    def _checked(self, state):
        return state == QtCore.Qt.CheckState.Checked.value

    def changeRunAsAdmin(self, state):
        idx = self.getCurrentIndex()
        if idx >= 0:
            app_state.data_schemes["profiles"]["list"][idx]["elevate"] = self._checked(state)
            self.setUnsavedChanges()

    def changeUseAcrylic(self, state):
        idx = self.getCurrentIndex()
        if idx >= 0:
            app_state.data_schemes["profiles"]["list"][idx]["useAcrylic"] = self._checked(state)
            self.setUnsavedChanges()

    def changeHidden(self, state):
        idx = self.getCurrentIndex()
        if idx >= 0:
            app_state.data_schemes["profiles"]["list"][idx]["hidden"] = self._checked(state)
            self.setUnsavedChanges()

    def changeSnapOnInput(self, state):
        idx = self.getCurrentIndex()
        if idx >= 0:
            app_state.data_schemes["profiles"]["list"][idx]["snapOnInput"] = self._checked(state)
            self.setUnsavedChanges()

    def changeSuppressTitle(self, state):
        val = self._checked(state)
        self._setProfileField("suppressApplicationTitle", val if val else None)

    def changeForeground(self, text):
        if self.ui_initialized:
            self._setProfileField("foreground", text.strip() or None)

    def changeBackgroundColor(self, text):
        if self.ui_initialized:
            self._setProfileField("background", text.strip() or None)

    def changeSelectionBackground(self, text):
        if self.ui_initialized:
            self._setProfileField("selectionBackground", text.strip() or None)

    def changeCursorColor(self, text):
        if self.ui_initialized:
            self._setProfileField("cursorColor", text.strip() or None)

    def changeOpacity(self):
        idx = self.getCurrentIndex()
        if idx >= 0:
            val = self.opacitySlider.value()
            self.opacityValueLabel.setText(str(val))
            app_state.data_schemes["profiles"]["list"][idx]["opacity"] = val
            self.setUnsavedChanges()

    def changeIntenseText(self, text):
        self._setProfileField("intenseTextStyle", text if text != "all" else None)

    def changeBgStretchMode(self, text):
        self._setProfileField("backgroundImageStretchMode",
                              text if text != "uniformToFill" else None)

    def changeBgAlignment(self, text):
        self._setProfileField("backgroundImageAlignment", text if text != "center" else None)

    def changeHistorySize(self, value):
        if self.ui_initialized:
            self._setProfileField("historySize", value if value != 9001 else None)

    def changeCloseOnExit(self, text):
        self._setProfileField(
            "closeOnExit", text if text != constants.CLOSE_ON_EXIT_DEFAULT else None)

    def changeBellStyle(self, text):
        self._setProfileField(
            "bellStyle", text if text != constants.BELL_STYLE_DEFAULT else None)

    def changeAntialiasing(self, text):
        self._setProfileField("antialiasingMode", text if text != "grayscale" else None)

    def changeRetroEffect(self, state):
        val = self._checked(state)
        self._setProfileField("experimental.retroTerminalEffect", val if val else None)

    def changeAltGr(self, state):
        # altGrAliasing defaults to True - only write when explicitly False.
        val = self._checked(state)
        self._setProfileField("altGrAliasing", False if not val else None)

    def changePixelShader(self, text):
        if self.ui_initialized:
            self._setProfileField("experimental.pixelShaderPath", text.strip() or None)

    # ────────────────────────────────────────────────────────────────────
    #  Load a profile into the editor
    # ────────────────────────────────────────────────────────────────────
    @staticmethod
    def _normalise_bell_style(value):
        """Map a WT bellStyle value (string or legacy list) to a combo item."""
        if isinstance(value, list):
            has = set(value)
            if {"audible", "window", "taskbar"} <= has or "all" in has:
                return "all"
            if "window" in has:
                return "window"
            if "taskbar" in has:
                return "taskbar"
            if "audible" in has:
                return "audible"
            return "none"
        # Legacy single value "visual" mapped to the modern "window".
        if value == "visual":
            return "window"
        return str(value)

    def changedProfile(self):
        if not self.ui_initialized:
            return
        if self.isDefaultsSelected():
            self._loadDefaultsProfile()
            return

        idx = self.getCurrentIndex()
        if idx < 0:
            return
        profile = app_state.data_schemes["profiles"]["list"][idx]

        self.ui_initialized = False

        self.profileNameEdit.setText(profile.get("name", ""))

        self._selectCombo(self.comboBox, profile.get("colorScheme", "Campbell"))

        font_obj = profile.get("font", {})
        font_face = font_obj.get("face") if isinstance(font_obj, dict) else None
        if not font_face:
            font_face = profile.get("fontFace", "Cascadia Mono")
        self._selectCombo(self.fontBox, font_face)

        font_size = font_obj.get("size") if isinstance(font_obj, dict) else None
        if font_size is None:
            font_size = profile.get("fontSize", 12)
        self.fontSize.setValue(font_size)

        self.commandLineEdit.setText(profile.get("commandline", ""))
        self.startingDirectoryEdit.setText(profile.get("startingDirectory", ""))
        self.tabTitleEdit.setText(profile.get("tabTitle", ""))
        self.tabColorEdit.setText(profile.get("tabColor", ""))
        self.iconEdit.setText(profile.get("icon", ""))
        self.hiddenCheckBox.setChecked(profile.get("hidden", False))
        self.runAsAdminCheckBox.setChecked(profile.get("elevate", False))
        self.suppressTitleCheckBox.setChecked(profile.get("suppressApplicationTitle", False))

        font_weight = font_obj.get("weight", "normal") if isinstance(font_obj, dict) else "normal"
        idx_w = self.fontWeightBox.findText(str(font_weight), QtCore.Qt.MatchFlag.MatchFixedString)
        self.fontWeightBox.setCurrentIndex(idx_w if idx_w >= 0 else 0)

        self._selectCombo(self.cursorShapeBox, profile.get("cursorShape", "bar"))
        self.cursorColorEdit.setText(profile.get("cursorColor", ""))

        self.foregroundEdit.setText(profile.get("foreground", ""))
        self.backgroundColorEdit.setText(profile.get("background", ""))
        self.selectionBackgroundEdit.setText(profile.get("selectionBackground", ""))

        self.opacitySlider.setValue(profile.get("opacity", 100))
        self.opacityValueLabel.setText(str(profile.get("opacity", 100)))
        self.useAcrylicCheckBox.setChecked(profile.get("useAcrylic", False))

        self._selectCombo(self.intenseTextBox, profile.get("intenseTextStyle", "all"))

        self.backgroundImageEdit.setText(profile.get("backgroundImage", ""))
        bg_opacity = profile.get("backgroundImageOpacity", 1.0)
        self.horizontalSlider.setValue(int(bg_opacity * 10))
        self.bgOpacityLabel.setText(str(bg_opacity))
        self._selectCombo(self.bgStretchBox, profile.get("backgroundImageStretchMode", "uniformToFill"))
        self._selectCombo(self.bgAlignBox, profile.get("backgroundImageAlignment", "center"))

        self.historySizeSpinBox.setValue(profile.get("historySize", 9001))
        self._selectCombo(self.closeOnExitBox, str(profile.get("closeOnExit", constants.CLOSE_ON_EXIT_DEFAULT)))
        self._selectCombo(self.bellStyleBox, self._normalise_bell_style(profile.get("bellStyle", "audible")))
        self._selectCombo(self.antialiasingBox, profile.get("antialiasingMode", "grayscale"))
        self._selectCombo(self.scrollbarBox, profile.get("scrollbarState", "visible"))

        self.paddingEdit.setText(profile.get("padding", ""))
        self.snapOnInputCheckBox.setChecked(profile.get("snapOnInput", True))
        self.retroEffectCheckBox.setChecked(profile.get("experimental.retroTerminalEffect", False))
        self.altGrCheckBox.setChecked(profile.get("altGrAliasing", True))
        self.pixelShaderEdit.setText(profile.get("experimental.pixelShaderPath", ""))

        self._loadEnvVarsTable(profile.get("environment", {}))

        self.ui_initialized = True

    @staticmethod
    def _selectCombo(combo, text):
        i = combo.findText(str(text), QtCore.Qt.MatchFlag.MatchFixedString)
        if i >= 0:
            combo.setCurrentIndex(i)

    # ────────────────────────────────────────────────────────────────────
    #  Profile list management
    # ────────────────────────────────────────────────────────────────────
    def moveProfileUp(self):
        row = self.listWidget.currentRow()
        if row > 1:  # can't move above Defaults (row 0)
            self.listWidget.insertItem(row - 1, self.listWidget.takeItem(row))
            self.listWidget.setCurrentRow(row - 1)
            self.updateProfileOrder()

    def moveProfileDown(self):
        row = self.listWidget.currentRow()
        if 1 <= row < self.listWidget.count() - 1:
            self.listWidget.insertItem(row + 1, self.listWidget.takeItem(row))
            self.listWidget.setCurrentRow(row + 1)
            self.updateProfileOrder()

    def updateProfileOrder(self):
        new_order = [self.listWidget.item(i).text() for i in range(1, self.listWidget.count())]
        profiles = app_state.data_schemes["profiles"]["list"]
        name_to_profiles = {}
        for profile in profiles:
            name_to_profiles.setdefault(profile.get("name", ""), []).append(profile)
        updated = []
        for name in new_order:
            if name_to_profiles.get(name):
                updated.append(name_to_profiles[name].pop(0))
        app_state.data_schemes["profiles"]["list"] = updated
        self.setUnsavedChanges()

    def renameProfile(self):
        if self.isDefaultsSelected():
            return
        row = self.listWidget.currentRow()
        if row >= 1:
            item = self.listWidget.currentItem()
            new_name, ok = QtWidgets.QInputDialog.getText(
                None, "Rename Profile", "New Name:",
                QtWidgets.QLineEdit.EchoMode.Normal, item.text())
            if ok and new_name.strip():
                item.setText(new_name.strip())
                app_state.data_schemes["profiles"]["list"][row - 1]["name"] = new_name.strip()
                self.profileNameEdit.setText(new_name.strip())
                self.setUnsavedChanges()

    def browseIcon(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Icon", "",
            "Icon Files (*.ico *.png *.jpg *.svg);;All Files (*.*)")
        if filename:
            self.iconEdit.setText(filename.replace("/", "\\"))

    def createNewProfile(self):
        new_name, ok = QtWidgets.QInputDialog.getText(
            None, "New Profile", "Enter profile name:",
            QtWidgets.QLineEdit.EchoMode.Normal, "New Profile")
        if not ok or not new_name.strip():
            return

        new_profile = {
            "guid": "{" + str(_uuid.uuid4()) + "}",
            "name": new_name.strip(),
            "commandline": "powershell.exe",
            "hidden": False,
        }
        ds = app_state.data_schemes
        ds.setdefault("profiles", {}).setdefault("list", []).append(new_profile)

        self.listWidget.addItem(new_name.strip())
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)
        self.setUnsavedChanges()
        app_state.profiles_list.append(new_name.strip())

        QtWidgets.QMessageBox.information(
            None, "Profile Created", f"New profile '{new_name.strip()}' created successfully.")

    def duplicateProfile(self):
        if self.isDefaultsSelected():
            QtWidgets.QMessageBox.warning(
                None, "Cannot Duplicate", "Please select a specific profile to duplicate.")
            return
        row = self.listWidget.currentRow()
        if row < 1:
            QtWidgets.QMessageBox.warning(None, "No Selection", "Please select a profile to duplicate.")
            return

        current_profile = app_state.data_schemes["profiles"]["list"][row - 1]
        current_name = current_profile.get("name", "Profile")
        new_name, ok = QtWidgets.QInputDialog.getText(
            None, "Duplicate Profile", "Enter name for duplicated profile:",
            QtWidgets.QLineEdit.EchoMode.Normal, f"{current_name} (Copy)")
        if not ok or not new_name.strip():
            return

        new_profile = copy.deepcopy(current_profile)
        new_profile["name"] = new_name.strip()
        new_profile["guid"] = "{" + str(_uuid.uuid4()) + "}"
        app_state.data_schemes["profiles"]["list"].append(new_profile)

        self.listWidget.addItem(new_name.strip())
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)
        self.setUnsavedChanges()
        app_state.profiles_list.append(new_name.strip())

        QtWidgets.QMessageBox.information(
            None, "Profile Duplicated", f"Profile duplicated as '{new_name.strip()}'.")

    def deleteProfile(self):
        if self.isDefaultsSelected():
            QtWidgets.QMessageBox.warning(None, "Cannot Delete", "The Defaults entry cannot be deleted.")
            return
        row = self.listWidget.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(None, "No Selection", "Please select a profile to delete.")
            return

        list_row = row - 1
        current_profile = app_state.data_schemes["profiles"]["list"][list_row]
        current_name = current_profile.get("name", "Profile")

        if current_profile.get("guid", "") == app_state.data_schemes.get("defaultProfile", ""):
            QtWidgets.QMessageBox.warning(
                None, "Cannot Delete",
                "Cannot delete the default profile. Please set another profile as default first.")
            return

        reply = QtWidgets.QMessageBox.question(
            None, "Delete Profile",
            f"Are you sure you want to delete profile '{current_name}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        del app_state.data_schemes["profiles"]["list"][list_row]
        self.listWidget.takeItem(row)
        if current_name in app_state.profiles_list:
            app_state.profiles_list.remove(current_name)
        self.setUnsavedChanges()

        QtWidgets.QMessageBox.information(
            None, "Profile Deleted", f"Profile '{current_name}' deleted successfully.")

    # ────────────────────────────────────────────────────────────────────
    #  Profile Defaults (profiles.defaults pseudo-profile)
    # ────────────────────────────────────────────────────────────────────
    def _loadDefaultsProfile(self):
        defaults = app_state.data_schemes.get("profiles", {}).get("defaults", {})
        self.ui_initialized = False

        self.profileNameEdit.setText("(Defaults \u2014 applied to all profiles)")
        self._selectCombo(self.comboBox, defaults.get("colorScheme", ""))

        font_obj = defaults.get("font", {})
        font_face = font_obj.get("face") if isinstance(font_obj, dict) else defaults.get("fontFace", "")
        if font_face:
            self._selectCombo(self.fontBox, font_face)
        font_size = font_obj.get("size") if isinstance(font_obj, dict) else defaults.get("fontSize")
        if font_size:
            self.fontSize.setValue(font_size)

        self.commandLineEdit.setText(defaults.get("commandline", ""))
        self.startingDirectoryEdit.setText(defaults.get("startingDirectory", ""))
        self.tabTitleEdit.setText(defaults.get("tabTitle", ""))
        self.tabColorEdit.setText(defaults.get("tabColor", ""))
        self.iconEdit.setText(defaults.get("icon", ""))
        self.hiddenCheckBox.setChecked(defaults.get("hidden", False))
        self.runAsAdminCheckBox.setChecked(defaults.get("elevate", False))
        self.suppressTitleCheckBox.setChecked(defaults.get("suppressApplicationTitle", False))
        self.cursorColorEdit.setText(defaults.get("cursorColor", ""))
        self.foregroundEdit.setText(defaults.get("foreground", ""))
        self.backgroundColorEdit.setText(defaults.get("background", ""))
        self.selectionBackgroundEdit.setText(defaults.get("selectionBackground", ""))
        self.opacitySlider.setValue(defaults.get("opacity", 100))
        self.useAcrylicCheckBox.setChecked(defaults.get("useAcrylic", False))
        self.backgroundImageEdit.setText(defaults.get("backgroundImage", ""))
        self.historySizeSpinBox.setValue(
            defaults.get("historySize", APP_CONFIG.get("defaults", {}).get("history_size", 9001)))
        self.snapOnInputCheckBox.setChecked(defaults.get("snapOnInput", True))
        self.retroEffectCheckBox.setChecked(defaults.get("experimental.retroTerminalEffect", False))
        self.altGrCheckBox.setChecked(defaults.get("altGrAliasing", True))
        self.pixelShaderEdit.setText(defaults.get("experimental.pixelShaderPath", ""))
        self._loadEnvVarsTable(defaults.get("environment", {}))

        self.ui_initialized = True

    def _setDefaultsField(self, key, value, sub_key=None):
        ds = app_state.data_schemes
        defaults = ds.setdefault("profiles", {}).setdefault("defaults", {})
        if sub_key:
            if value:
                defaults.setdefault(key, {})[sub_key] = value
            elif key in defaults and sub_key in defaults[key]:
                del defaults[key][sub_key]
                if not defaults[key]:
                    del defaults[key]
        else:
            if value is not None and value != "":
                defaults[key] = value
            else:
                defaults.pop(key, None)
        self.setUnsavedChanges()

    # ────────────────────────────────────────────────────────────────────
    #  Environment variables table
    # ────────────────────────────────────────────────────────────────────
    def _loadEnvVarsTable(self, env_dict: dict):
        self.envVarsTable.blockSignals(True)
        self.envVarsTable.setRowCount(0)
        for name, value in (env_dict or {}).items():
            row = self.envVarsTable.rowCount()
            self.envVarsTable.insertRow(row)
            self.envVarsTable.setItem(row, 0, QtWidgets.QTableWidgetItem(str(name)))
            self.envVarsTable.setItem(row, 1, QtWidgets.QTableWidgetItem(str(value)))
        self.envVarsTable.blockSignals(False)

    def _addEnvVar(self):
        row = self.envVarsTable.rowCount()
        self.envVarsTable.insertRow(row)
        self.envVarsTable.setItem(row, 0, QtWidgets.QTableWidgetItem("VARIABLE_NAME"))
        self.envVarsTable.setItem(row, 1, QtWidgets.QTableWidgetItem("value"))
        self.envVarsTable.editItem(self.envVarsTable.item(row, 0))
        self._saveEnvVarsToProfile()

    def _removeEnvVar(self):
        row = self.envVarsTable.currentRow()
        if row >= 0:
            self.envVarsTable.removeRow(row)
            self._saveEnvVarsToProfile()

    def _onEnvVarChanged(self, _item):
        if self.ui_initialized:
            self._saveEnvVarsToProfile()

    def _saveEnvVarsToProfile(self):
        env = {}
        for row in range(self.envVarsTable.rowCount()):
            name_item = self.envVarsTable.item(row, 0)
            val_item = self.envVarsTable.item(row, 1)
            if name_item and name_item.text().strip():
                env[name_item.text().strip()] = val_item.text() if val_item else ""
        if self.isDefaultsSelected():
            self._setDefaultsField("environment", env or None)
        else:
            idx = self.getCurrentIndex()
            if idx >= 0:
                if env:
                    app_state.data_schemes["profiles"]["list"][idx]["environment"] = env
                else:
                    app_state.data_schemes["profiles"]["list"][idx].pop("environment", None)
                self.setUnsavedChanges()

    # ────────────────────────────────────────────────────────────────────
    #  Pixel shader / templates
    # ────────────────────────────────────────────────────────────────────
    def _browsePixelShader(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Pixel Shader", "", "HLSL Shader Files (*.hlsl);;All Files (*)")
        if path:
            self.pixelShaderEdit.setText(path.replace("/", "\\"))

    _PROFILE_TEMPLATES = [
        {"name": "Git Bash", "commandline": r'"%PROGRAMFILES%\Git\bin\bash.exe" --login -i',
         "icon": r"%PROGRAMFILES%\Git\mingw64\share\git\git-for-windows.ico",
         "startingDirectory": "%USERPROFILE%"},
        {"name": "Anaconda Prompt", "commandline": r'cmd.exe /k "%USERPROFILE%\Anaconda3\Scripts\activate.bat"',
         "icon": r"%USERPROFILE%\Anaconda3\Menu\anaconda-navigator.ico",
         "startingDirectory": "%USERPROFILE%"},
        {"name": "cmder", "commandline": r'"%CMDER_ROOT%\vendor\git-for-windows\bin\bash.exe" --login -i',
         "icon": r"%CMDER_ROOT%\icons\cmder.ico",
         "startingDirectory": "%USERPROFILE%"},
        {"name": "MSYS2 / MinGW64", "commandline": r"C:\msys64\mingw64.exe",
         "icon": r"C:\msys64\mingw64\share\pixmaps\msys2.ico",
         "startingDirectory": r"C:\msys64\home\%USERNAME%"},
        {"name": "Cygwin", "commandline": r"C:\cygwin64\bin\bash.exe --login -i",
         "icon": r"C:\cygwin64\Cygwin-Terminal.ico",
         "startingDirectory": r"C:\cygwin64\home\%USERNAME%"},
        {"name": "PowerShell 7 (Admin)",
         "commandline": r"pwsh.exe -NoExit -Command Start-Process pwsh -Verb RunAs",
         "icon": "ms-appx:///ProfileIcons/{574e775e-4f2a-5b96-ac1e-a2962a402336}.png"},
        {"name": "SSH Remote", "commandline": r"ssh.exe user@hostname",
         "icon": "ms-appx:///ProfileIcons/{0caa0dad-35be-5f56-a8ff-afceeeaa6101}.png",
         "startingDirectory": "%USERPROFILE%"},
    ]

    def createProfileFromTemplate(self):
        template_names = [t["name"] for t in self._PROFILE_TEMPLATES]
        chosen, ok = QtWidgets.QInputDialog.getItem(
            None, "Profile from Template", "Select a template:", template_names, 0, False)
        if not ok:
            return
        template = next((t for t in self._PROFILE_TEMPLATES if t["name"] == chosen), None)
        if not template:
            return
        new_name, ok2 = QtWidgets.QInputDialog.getText(
            None, "Profile Name", "Enter name for new profile:",
            QtWidgets.QLineEdit.EchoMode.Normal, chosen)
        if not ok2 or not new_name.strip():
            return

        new_profile = copy.deepcopy(template)
        new_profile["name"] = new_name.strip()
        new_profile["guid"] = "{" + str(_uuid.uuid4()) + "}"
        new_profile["hidden"] = False
        ds = app_state.data_schemes
        ds.setdefault("profiles", {}).setdefault("list", []).append(new_profile)

        self.listWidget.addItem(new_name.strip())
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)
        app_state.profiles_list.append(new_name.strip())
        self.setUnsavedChanges()

        QtWidgets.QMessageBox.information(
            None, "Profile Created",
            f"Profile '{new_name.strip()}' created from template '{chosen}'.\n"
            "Edit the Command Line to point to the correct path on your system.")

    # ────────────────────────────────────────────────────────────────────
    #  Menu-location indicators (populated from the Folders tab data)
    # ────────────────────────────────────────────────────────────────────
    def updateProfileMenuIndicators(self):
        profiles = app_state.data_schemes.get("profiles", {}).get("list", [])
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if i < len(profiles):
                guid = profiles[i].get("guid", "")
                location = self.getProfileMenuLocation(guid)
                item.setToolTip(f"Menu: {location}\nGUID: {guid}")
