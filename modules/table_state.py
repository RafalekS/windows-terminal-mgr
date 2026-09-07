"""Persistence for tables, trees, splitters and the main window.

Coding-standard contract (see ~/.claude/skills/coding/SKILL.md):

* Every column is ``Interactive`` and movable; never ``Stretch`` /
  ``setStretchLastSection``.
* Startup order: build UI -> configure headers -> populate -> enable sorting
  -> restore state (once).
* Saves are debounced 500ms (single-shot QTimer, restarted on every change) and
  forced immediately on ``hideEvent`` / ``closeEvent``.
* Signals are blocked around a restore.

Usage
-----
    from modules.table_state import PersistentUI, NumericItem

    self._persist = PersistentUI(main_window)          # once, in setupUi
    ...
    self._persist.bind_window(main_window)
    self._persist.bind_table(self.actionsTable, "actions")     # after populate + sorting
    self._persist.bind_tree(self.foldersTreeWidget, "folders")
    self._persist.bind_splitter(step_splitter, "cmd_builder")

``key`` is any short unique string; state is stored under
``QSettings("WTManager", "UIState")``.
"""

from PyQt6 import QtCore, QtWidgets

_ORG = "WTManager"
_APP = "UIState"
_DEBOUNCE_MS = 500


class NumericItem(QtWidgets.QTableWidgetItem):
    """QTableWidgetItem that sorts by a numeric key, not lexically.

    Use for any column that shows formatted numbers (counts, sizes, durations,
    IDs) so "9" sorts before "10".
    """

    def __init__(self, text: str, value: float):
        super().__init__(text)
        self._value = value

    def __lt__(self, other):
        if isinstance(other, NumericItem):
            return self._value < other._value
        return super().__lt__(other)


def _settings() -> QtCore.QSettings:
    return QtCore.QSettings(_ORG, _APP)


class PersistentUI:
    """Tracks a set of widgets and persists their layout state."""

    def __init__(self, parent: QtCore.QObject):
        self._parent = parent
        self._timers: dict[str, QtCore.QTimer] = {}
        self._savers: dict[str, callable] = {}

    # ── debounce plumbing ────────────────────────────────────────────────
    def _timer_for(self, key: str) -> QtCore.QTimer:
        t = self._timers.get(key)
        if t is None:
            t = QtCore.QTimer(self._parent)
            t.setSingleShot(True)
            t.setInterval(_DEBOUNCE_MS)
            t.timeout.connect(lambda k=key: self._savers[k]())
            self._timers[key] = t
        return t

    def _schedule(self, key: str):
        self._timer_for(key).start()

    def flush(self):
        """Save every tracked widget immediately (call from close/hide)."""
        for key, saver in self._savers.items():
            t = self._timers.get(key)
            if t is not None:
                t.stop()
            saver()

    # ── main window geometry ────────────────────────────────────────────
    def bind_window(self, window: QtWidgets.QWidget, key: str = "main_window"):
        s = _settings()
        geo = s.value(f"{key}/geometry")
        if geo is not None:
            window.restoreGeometry(geo)
        state = s.value(f"{key}/windowState")
        if state is not None and hasattr(window, "restoreState"):
            window.restoreState(state)

        def save():
            st = _settings()
            st.setValue(f"{key}/geometry", window.saveGeometry())
            if hasattr(window, "saveState"):
                st.setValue(f"{key}/windowState", window.saveState())

        self._savers[key] = save
        window.installEventFilter(_ResizeMoveFilter(self._parent, lambda: self._schedule(key)))

    # ── tables ──────────────────────────────────────────────────────────
    def bind_table(self, table: QtWidgets.QTableWidget, key: str, sortable: bool = True):
        """Persist column widths + order (+ sort state when *sortable*).

        Call AFTER the table is populated once. When *sortable*, this enables
        sorting - so the caller must have populated with sorting disabled
        (coding-standard: never sort during population).
        """
        header = table.horizontalHeader()
        for i in range(table.columnCount()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        if sortable:
            table.setSortingEnabled(True)

        state_key = f"table/{key}/headerState"
        widths_key = f"table/{key}/widths"
        s = _settings()

        table.blockSignals(True)
        header.blockSignals(True)
        blob = s.value(state_key)
        if blob is not None:
            header.restoreState(blob)
        widths = s.value(widths_key)
        if isinstance(widths, list):
            for i, w in enumerate(widths):
                if i < table.columnCount():
                    try:
                        table.setColumnWidth(i, int(w))
                    except (TypeError, ValueError):
                        pass
        header.blockSignals(False)
        table.blockSignals(False)

        def save():
            st = _settings()
            st.setValue(state_key, header.saveState())
            st.setValue(widths_key,
                        [table.columnWidth(i) for i in range(table.columnCount())])

        self._savers[key] = save
        header.sectionResized.connect(lambda *_: self._schedule(key))
        header.sectionMoved.connect(lambda *_: self._schedule(key))
        if sortable:
            header.sortIndicatorChanged.connect(lambda *_: self._schedule(key))

    # ── trees ───────────────────────────────────────────────────────────
    def bind_tree(self, tree: QtWidgets.QTreeWidget, key: str):
        header = tree.header()
        for i in range(tree.columnCount()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(tree.columnCount() > 1)
        header.setSectionsClickable(True)
        tree.setSortingEnabled(False)  # folders tree order is meaningful; sorting off

        state_key = f"tree/{key}/headerState"
        widths_key = f"tree/{key}/widths"
        s = _settings()

        header.blockSignals(True)
        blob = s.value(state_key)
        if blob is not None:
            header.restoreState(blob)
        widths = s.value(widths_key)
        if isinstance(widths, list):
            for i, w in enumerate(widths):
                if i < tree.columnCount():
                    try:
                        tree.setColumnWidth(i, int(w))
                    except (TypeError, ValueError):
                        pass
        header.blockSignals(False)

        def save():
            st = _settings()
            st.setValue(state_key, header.saveState())
            st.setValue(widths_key,
                        [tree.columnWidth(i) for i in range(tree.columnCount())])

        self._savers[key] = save
        header.sectionResized.connect(lambda *_: self._schedule(key))
        header.sectionMoved.connect(lambda *_: self._schedule(key))

    # ── splitters ───────────────────────────────────────────────────────
    def bind_splitter(self, splitter: QtWidgets.QSplitter, key: str):
        state_key = f"splitter/{key}/state"
        blob = _settings().value(state_key)
        if blob is not None:
            splitter.restoreState(blob)

        def save():
            _settings().setValue(state_key, splitter.saveState())

        self._savers[key] = save
        splitter.splitterMoved.connect(lambda *_: self._schedule(key))


class _ResizeMoveFilter(QtCore.QObject):
    """Fires a callback on window resize / move events."""

    def __init__(self, parent, on_change):
        super().__init__(parent)
        self._on_change = on_change

    def eventFilter(self, obj, event):
        et = event.type()
        if et in (QtCore.QEvent.Type.Resize, QtCore.QEvent.Type.Move):
            self._on_change()
        return False
