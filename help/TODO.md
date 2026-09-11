# TODO

Open items only. See `help/CHANGES-2026-09-07.md` for the v1.1.0 change list.
Completed history is in `help/history/`.

---

## 1. Bell Style can't represent every combination

Windows Terminal lets `bellStyle` be a list, e.g. `["audible", "window"]`
(sound + flash the window, but not the taskbar). Our dropdown is a single
choice, so on load a list is collapsed to the one closest option
(`_normalise_bell_style` in `modules/profiles_tab.py`). Editing then Saving a
profile that had a list value will replace it with a single value.

**Fix:** replace the dropdown with checkboxes (Sound / Flash window / Flash
taskbar) so any combination round-trips. Low priority unless you use list
values.

## 2. Profile fields Windows Terminal supports but this app can't edit yet

These are all real `settings.json` profile keys per the WT docs. The editor has
no widget for them today — if you need one, it goes in the Profiles tab
"Advanced" group:

| Key | What it does |
|---|---|
| `bellSound` | Path to a `.wav` (or a list of paths, picked at random) played for the bell. |
| `pathTranslationStyle` | When you drag a file onto the terminal, how the path is rewritten: `wsl` → `/mnt/c/…`, `cygwin` → `/cygdrive/c/…`, `msys2` → `/c/…`, `mingw` → `C:/…`, `none` = as-is. WT Preview only. |
| `experimental.useAtlasEngine` | Opt this profile into WT's experimental text renderer. |
| `experimental.repositionCursorWithMouse` | Click on the command line with the mouse to move the text cursor there. Needs shell integration set up. |

## 3. Drop the matplotlib dependency

The app imports `matplotlib` **only** to get the list of installed font names
(`matplotlib.font_manager.fontManager.ttflist`), used to fill the Font dropdown
in the Profiles tab. matplotlib is a large install for that one list.

**Fix:** use Qt's own `QtGui.QFontDatabase().families()` instead and remove
`matplotlib` from the dependencies. One change in `modules/app_state.py`
(`font_list = …`), one line in `README.md` / install docs.
