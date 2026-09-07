"""Static Windows Terminal option data used to populate combos and dropdowns.

Action names verified against Microsoft Learn:
https://learn.microsoft.com/en-us/windows/terminal/customize-settings/actions
Profile enum values verified against:
https://learn.microsoft.com/en-us/windows/terminal/customize-settings/profile-advanced
"""

# ── Built-in Windows Terminal action / command names ───────────────────────────
# The "Built-in Action" combo is editable, so any string is still accepted -
# this list is only the suggestion set. Grouped as in the MS Learn docs.
COMMON_ACTIONS = [
    # Application
    "quit", "closeWindow", "find", "findMatch", "openNewTabDropdown", "openSettings",
    "openSystemMenu", "toggleFullscreen", "toggleFocusMode", "toggleAlwaysOnTop", "sendInput",
    # Tab management
    "closeTab", "closeOtherTabs", "closeTabsAfter", "duplicateTab", "newTab", "nextTab",
    "prevTab", "tabSearch", "switchToTab", "renameTab", "openTabRenamer", "setTabColor",
    "openTabColorPicker", "moveTab", "toggleBroadcastInput", "showContextMenu", "openAbout",
    "searchWeb",
    # Window management
    "newWindow", "renameWindow", "openWindowRenamer", "identifyWindow", "identifyWindows",
    # Pane management
    "splitPane", "closePane", "moveFocus", "movePane", "swapPane", "togglePaneZoom",
    "resizePane", "toggleReadOnlyMode", "enableReadOnlyMode", "disableReadOnlyMode",
    "restartConnection",
    # Clipboard & selection
    "copy", "paste", "expandSelectionToWord", "selectAll", "markMode",
    "switchSelectionEndpoint", "toggleBlockSelection",
    # Scrollback
    "scrollUp", "scrollDown", "scrollUpPage", "scrollDownPage", "scrollToTop",
    "scrollToBottom", "clearBuffer",
    # Visual adjustments
    "adjustFontSize", "resetFontSize", "adjustOpacity", "toggleShaderEffects", "setColorScheme",
    # Scroll marks
    "addMark", "scrollToMark", "clearMark", "clearAllMarks",
    # Other
    "showSuggestions", "exportBuffer", "globalSummon", "quakeMode", "multipleActions",
]

# ── Direction options for pane actions ────────────────────────────────────────
# moveFocus also accepts parent/child (pane-tree navigation).
PANE_DIRECTIONS = ["down", "left", "right", "up", "previous", "previousInOrder",
                   "nextInOrder", "first", "parent", "child"]
RESIZE_DIRECTIONS = ["down", "left", "right", "up"]
SWAP_DIRECTIONS = ["down", "left", "right", "up", "previous", "previousInOrder",
                   "nextInOrder", "first"]

# ── Built-in colour schemes shipped with Windows Terminal ─────────────────────
BUILTIN_SCHEMES = [
    "Campbell", "Campbell Powershell", "Vintage", "One Half Dark",
    "One Half Light", "Solarized Dark", "Solarized Light",
    "Tango Dark", "Arthur",
]

# ── Profile editor enum option lists ─────────────────────────────────────────
FONT_WEIGHTS = ["normal", "thin", "extra-light", "light", "semi-light",
                "medium", "semi-bold", "bold", "extra-bold", "black"]
CURSOR_SHAPES = ["bar", "vintage", "underscore", "filledBox", "emptyBox", "doubleUnderscore"]
INTENSE_TEXT_STYLES = ["all", "bold", "bright", "none"]
BG_STRETCH_MODES = ["uniformToFill", "none", "fill", "uniform"]
BG_ALIGNMENTS = ["center", "left", "top", "right", "bottom",
                 "topLeft", "topRight", "bottomLeft", "bottomRight"]
# closeOnExit: "automatic" is the current default (added when WT became the default
# terminal). true/false are accepted as synonyms for graceful/never.
CLOSE_ON_EXIT_MODES = ["automatic", "graceful", "always", "never"]
CLOSE_ON_EXIT_DEFAULT = "automatic"
# bellStyle: "visual" is NOT valid - the split values are "window" and "taskbar".
BELL_STYLES = ["all", "audible", "window", "taskbar", "none"]
BELL_STYLE_DEFAULT = "audible"
ANTIALIASING_MODES = ["grayscale", "cleartype", "aliased"]
SCROLLBAR_STATES = ["visible", "hidden"]
