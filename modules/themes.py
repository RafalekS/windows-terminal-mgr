"""Theme colours (config/themes/<name>.json) and the Qt stylesheet builder.

``CURRENT_THEME_COLORS`` is a module attribute reassigned when the user switches
theme in the Settings tab. Always reference it as ``themes.CURRENT_THEME_COLORS``.
"""

import json

from modules.config import SCRIPT_DIR, APP_CONFIG, _deep_merge

_DEFAULT_LIGHT_COLORS = {
    "bg_main": "#f5f0ff", "bg_widget": "#ffffff", "bg_alt": "#f5f0ff",
    "bg_input": "#ffffff", "bg_readonly": "#ede8f5",
    "bg_tab": "#e8e0f5", "bg_tab_selected": "#f5f0ff", "bg_tab_hover": "#ded5f0",
    "bg_header": "#e8e0f5", "bg_tooltip": "#ffffff",
    "bg_scrollbar": "#f0eaf8", "bg_scrollbar_handle": "#c8bfe0", "bg_scrollbar_handle_hover": "#b0a8c8",
    "border": "#c8bfe0", "border_focus": "#7c6bc4",
    "text_primary": "#2d2d3d", "text_secondary": "#3d3555", "text_muted": "#6b6580", "text_tab": "#3d3555",
    "selection_bg": "#d4cceb",
    "slider_handle": "#7c6bc4", "slider_handle_hover": "#9585d0", "slider_groove": "#d5d0e0",
    "checkbox_checked": "#7c6bc4",
    "groupbox_indicator_checked": "#7c6bc4", "groupbox_indicator_unchecked_bg": "#e8e0f5",
    "groupbox_indicator_border": "#b0a8c8",
    "btn_bg": "#e0d8f0", "btn_hover": "#d0c5e8", "btn_pressed": "#c0b5d8",
    "btn_disabled_bg": "#ede8f5", "btn_disabled_text": "#a09ab0", "btn_disabled_border": "#d5d0e0",
    "btn_border": "#b0a8c8",
    "btn_save_bg": "#6dba65", "btn_save_hover": "#5aa852",
    "btn_add_bg": "#6dba65", "btn_add_hover": "#5aa852",
    "btn_update_bg": "#5b8bd4", "btn_update_hover": "#4a7ac3",
    "btn_delete_bg": "#d45b5b", "btn_delete_hover": "#c34a4a",
    "status_unsaved": "#d4790a", "status_saved": "#2e8b2e", "status_error": "#c34a4a",
    "help_bg": "#ede8f5", "help_text": "#5c5470", "help_border": "#c8bfe0",
    "muted_text": "#8580a0", "accent_text": "#5b8bd4",
    "gridline": "#d5d0e0", "frame_color": "#c8bfe0",
    "tag_bg": "#e0d8f0", "tag_text": "#3d3555",
}


def load_theme(theme_name: str) -> dict:
    theme_path = SCRIPT_DIR / "config" / "themes" / f"{theme_name}.json"
    if theme_path.exists():
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return _deep_merge(_DEFAULT_LIGHT_COLORS, data.get("colors", {}))
        except (OSError, ValueError) as e:
            print(f"Theme load error: {e}")
    return _DEFAULT_LIGHT_COLORS.copy()


def build_stylesheet(c: dict) -> str:
    """Build the full application stylesheet from a theme colours dict."""
    return f"""
        QMainWindow {{ background-color: {c['bg_main']}; }}
        QWidget {{ background-color: {c['bg_main']}; color: {c['text_primary']}; }}
        QTabWidget::pane {{ border: 1px solid {c['border']}; background: {c['bg_main']}; }}
        QTabBar::tab {{
            background: {c['bg_tab']}; color: {c['text_tab']}; border: 1px solid {c['border']};
            padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{ background: {c['bg_tab_selected']}; color: {c['text_primary']}; border-bottom-color: {c['bg_tab_selected']}; font-weight: bold; }}
        QTabBar::tab:hover {{ background: {c['bg_tab_hover']}; }}
        QGroupBox {{
            font-weight: bold; border: 1px solid {c['border']}; border-radius: 6px;
            margin-top: 10px; padding-top: 14px; color: {c['text_primary']};
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; }}
        QGroupBox::indicator {{ width: 13px; height: 13px; }}
        QGroupBox::indicator:checked {{ image: none; border: 2px solid {c['groupbox_indicator_checked']}; border-radius: 3px; background: {c['groupbox_indicator_checked']}; }}
        QGroupBox::indicator:unchecked {{ image: none; border: 2px solid {c['groupbox_indicator_border']}; border-radius: 3px; background: {c['groupbox_indicator_unchecked_bg']}; }}
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c['bg_input']}; border: 1px solid {c['border']}; border-radius: 4px;
            padding: 4px 6px; color: {c['text_primary']}; selection-background-color: {c['selection_bg']};
        }}
        QLineEdit:focus, QTextEdit:focus {{ border-color: {c['border_focus']}; }}
        QLineEdit:read-only {{ background-color: {c['bg_readonly']}; color: {c['text_muted']}; }}
        QComboBox {{
            background-color: {c['bg_input']}; border: 1px solid {c['border']}; border-radius: 4px;
            padding: 4px 8px; color: {c['text_primary']};
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox::down-arrow {{ image: none; border-left: 4px solid transparent;
            border-right: 4px solid transparent; border-top: 6px solid {c['text_muted']}; }}
        QComboBox QAbstractItemView {{
            background-color: {c['bg_input']}; border: 1px solid {c['border']}; color: {c['text_primary']};
            selection-background-color: {c['selection_bg']};
        }}
        QSpinBox, QDoubleSpinBox {{
            background-color: {c['bg_input']}; border: 1px solid {c['border']}; border-radius: 4px;
            padding: 4px; color: {c['text_primary']};
        }}
        QPushButton {{
            background-color: {c['btn_bg']}; color: {c['text_primary']}; border: 1px solid {c['btn_border']};
            border-radius: 4px; padding: 6px 14px; font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {c['btn_hover']}; }}
        QPushButton:pressed {{ background-color: {c['btn_pressed']}; }}
        QPushButton:disabled {{ background-color: {c['btn_disabled_bg']}; color: {c['btn_disabled_text']}; border-color: {c['btn_disabled_border']}; }}
        QPushButton#btn-save {{ background-color: {c['btn_save_bg']}; color: #ffffff; }}
        QPushButton#btn-save:hover {{ background-color: {c['btn_save_hover']}; }}
        QPushButton#btn-add {{ background-color: {c['btn_add_bg']}; color: #ffffff; }}
        QPushButton#btn-add:hover {{ background-color: {c['btn_add_hover']}; }}
        QPushButton#btn-update {{ background-color: {c['btn_update_bg']}; color: #ffffff; }}
        QPushButton#btn-update:hover {{ background-color: {c['btn_update_hover']}; }}
        QPushButton#btn-delete {{ background-color: {c['btn_delete_bg']}; color: #ffffff; }}
        QPushButton#btn-delete:hover {{ background-color: {c['btn_delete_hover']}; }}
        QListWidget, QTreeWidget {{
            background-color: {c['bg_widget']}; border: 1px solid {c['border']}; border-radius: 4px;
            color: {c['text_primary']}; alternate-background-color: {c['bg_alt']};
        }}
        QListWidget::item:selected, QTreeWidget::item:selected {{ background-color: {c['selection_bg']}; color: {c['text_primary']}; }}
        QListWidget::item:hover, QTreeWidget::item:hover {{ background-color: {c['bg_readonly']}; }}
        QTableWidget {{
            background-color: {c['bg_widget']}; border: 1px solid {c['border']}; border-radius: 4px;
            color: {c['text_primary']}; alternate-background-color: {c['bg_alt']}; gridline-color: {c['gridline']};
        }}
        QTableWidget::item:selected {{ background-color: {c['selection_bg']}; color: {c['text_primary']}; }}
        QTableWidget::item:hover {{ background-color: {c['bg_readonly']}; }}
        QHeaderView::section {{
            background-color: {c['bg_header']}; color: {c['text_secondary']}; border: 1px solid {c['border']};
            padding: 4px; font-weight: bold;
        }}
        QScrollBar:vertical {{ background: {c['bg_scrollbar']}; width: 12px; border: none; }}
        QScrollBar::handle:vertical {{ background: {c['bg_scrollbar_handle']}; border-radius: 6px; min-height: 20px; }}
        QScrollBar::handle:vertical:hover {{ background: {c['bg_scrollbar_handle_hover']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        QScrollBar:horizontal {{ background: {c['bg_scrollbar']}; height: 12px; border: none; }}
        QScrollBar::handle:horizontal {{ background: {c['bg_scrollbar_handle']}; border-radius: 6px; min-width: 20px; }}
        QScrollBar::handle:horizontal:hover {{ background: {c['bg_scrollbar_handle_hover']}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
        QSlider::groove:horizontal {{ height: 6px; background: {c['slider_groove']}; border-radius: 3px; }}
        QSlider::handle:horizontal {{
            width: 16px; height: 16px; margin: -5px 0;
            background: {c['slider_handle']}; border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{ background: {c['slider_handle_hover']}; }}
        QCheckBox {{ spacing: 6px; }}
        QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 3px; border: 2px solid {c['groupbox_indicator_border']}; }}
        QCheckBox::indicator:checked {{ background: {c['checkbox_checked']}; border-color: {c['checkbox_checked']}; }}
        QCheckBox::indicator:unchecked {{ background: {c['bg_widget']}; }}
        QLabel {{ color: {c['text_secondary']}; }}
        QScrollArea {{ border: none; }}
        QFrame[frameShape="4"] {{ color: {c['frame_color']}; }}
        QToolTip {{ background-color: {c['bg_tooltip']}; color: {c['text_primary']}; border: 1px solid {c['border']}; padding: 4px; }}
        QRadioButton {{ color: {c['text_primary']}; spacing: 6px; }}
        QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 7px; border: 2px solid {c['groupbox_indicator_border']}; }}
        QRadioButton::indicator:checked {{ background: {c['checkbox_checked']}; border-color: {c['checkbox_checked']}; }}
        QRadioButton::indicator:unchecked {{ background: {c['bg_widget']}; }}
        QLabel#hint-label {{ color: {c['muted_text']}; font-size: 11px; padding: 2px; }}
        QLabel#help-panel {{
            background-color: {c['help_bg']}; color: {c['help_text']}; padding: 10px;
            border: 1px solid {c['help_border']}; border-radius: 4px;
        }}
    """


CURRENT_THEME_COLORS = load_theme(APP_CONFIG.get("theme", "light"))
