"""Windows Terminal Manager - PyQt6 GUI for editing the Windows Terminal
settings.json (profiles, folders/new-tab menu, actions, command builder,
global settings, fragment extensions).

This is the entry point only. Everything else lives in the ``modules`` package
(see ``modules/__init__.py`` for the layout). Run with ``--debug`` for verbose
diagnostic output.

    python wt_manager.pyw
    python wt_manager.pyw --debug
"""

import sys

from PyQt6 import QtGui, QtWidgets

# Importing app_state has side effects: it locates the Windows Terminal
# LocalState directory, chdir()s into it, backs up settings.json and loads it.
# If the directory is not found it prints an error and exits(1).
from modules import app_state  # noqa: F401  (imported for its side effects + re-export)
from modules import themes
from modules.config import SCRIPT_DIR
from modules.main_window import Ui_MainWindow


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(themes.build_stylesheet(themes.CURRENT_THEME_COLORS))

    main_window = QtWidgets.QMainWindow()

    icon_path = SCRIPT_DIR / "WT_config.ico"
    if not icon_path.exists():
        icon_path = SCRIPT_DIR / "wt3.ico"  # fallback to old icon
    if icon_path.exists():
        icon = QtGui.QIcon(str(icon_path))
        app.setWindowIcon(icon)
        main_window.setWindowIcon(icon)

    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    main_window.show()

    def close_event(event):
        if not ui.unsaved_changes:
            event.accept()
            return
        reply = QtWidgets.QMessageBox.question(
            main_window, "Unsaved Changes",
            "You have unsaved changes. Do you want to save before closing?",
            QtWidgets.QMessageBox.StandardButton.Save
            | QtWidgets.QMessageBox.StandardButton.Discard
            | QtWidgets.QMessageBox.StandardButton.Cancel)
        if reply == QtWidgets.QMessageBox.StandardButton.Save:
            ui.dumpOnSave()
            event.accept()
        elif reply == QtWidgets.QMessageBox.StandardButton.Discard:
            event.accept()
        else:
            event.ignore()

    main_window.closeEvent = close_event
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
