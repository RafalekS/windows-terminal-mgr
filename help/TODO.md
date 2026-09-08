# TODO

Open items only. See `help/CHANGES-2026-09-07.md` for what changed in v1.1.0 and
its test plan. Completed history is in `help/history/`.

---

## 1. Verify v1.1.0 on Windows 11

Not done until tested — checklist in `help/CHANGES-2026-09-07.md`.
After a clean pass: bump `VERSION` in `modules/main_window.py` to `1.1.1`.

## 2. Folders tab — right-hand panel is confusing

**Problem:** when you select a *profile* entry in the tree, the panel shows
Folder Name / Folder Icon / Allow Empty / Inline greyed out, and only the
Profile dropdown + Profile Icon are usable. When you select a *folder*, it's the
other way round. Users expect to see only the fields that apply.

This has been a known complaint since the first fixes list. It is **not** a
regression from v1.1.0 — it's the original design.

**Fix:** hide the irrelevant fields per item type instead of disabling them,
and label the Profile dropdown clearly ("Points to profile:" for an existing
entry). Small change in `modules/folders_tab.py::onFolderSelectionChanged`.

## 3. Bell Style can't represent every combination

Windows Terminal lets `bellStyle` be a list, e.g. `["audible", "window"]`
(sound + flash the window, but not the taskbar). Our dropdown is a single
choice, so on load a list is collapsed to the one closest option
(`_normalise_bell_style` in `modules/profiles_tab.py`). Editing then Saving a
profile that had a list value will replace it with a single value.

**Fix:** replace the dropdown with checkboxes (Sound / Flash window / Flash
taskbar) so any combination round-trips. Low priority unless you use list
values.

## 4. Profile fields Windows Terminal supports but this app can't edit yet

These are all real `settings.json` profile keys per the WT docs. The editor has
no widget for them today — if you need one, it goes in the Profiles tab
"Advanced" group:

| Key | What it does |
|---|---|
| `bellSound` | Path to a `.wav` (or a list of paths, picked at random) played for the bell. |
| `pathTranslationStyle` | When you drag a file onto the terminal, how the path is rewritten: `wsl` → `/mnt/c/…`, `cygwin` → `/cygdrive/c/…`, `msys2` → `/c/…`, `mingw` → `C:/…`, `none` = as-is. WT Preview only. |
| `experimental.useAtlasEngine` | Opt this profile into WT's experimental text renderer. |
| `experimental.repositionCursorWithMouse` | Click on the command line with the mouse to move the text cursor there. Needs shell integration set up. |

## DONE (pending Windows test)

- **Table / splitter / window persistence** (`modules/table_state.py`).
  Actions table (widths + column order + sort), Env Vars table (widths + order),
  Folders tree + Fragment tree (widths + order), Command Builder + Fragments
  splitters, main window size/position. Verify on Windows: resize a column,
  reorder columns, drag a splitter, resize the window -> close -> reopen ->
  everything is where you left it.

- **Folders tab rework.**
  - Item Details panel now *hides* irrelevant rows instead of greying them.
  - New **Location** dropdown: shows which folder an item sits in (path for
    nested, "(top level)" for root). Change it + Update Item -> the item moves
    there. Works for folders, profile entries and separators. A folder can't be
    moved into itself/a descendant.
  - **Auto-listed profiles** (the blue "Remaining Profiles" children): select
    one, pick a Location, click **"Add to menu"** -> it becomes a real
    `{"type":"profile"}` entry. `remainingProfiles` stays in the menu.
  - "Profile" dropdown relabelled **"Shows profile"** + an **"Edit in Profiles ▸"**
    button that jumps to that profile on the Profiles tab (rename happens there,
    not here).
  - "Move Profile" button kept as-is.

- **Actions tab "Add New" fixed.**
  - Buttons: New · Add · Save Changes · Duplicate · Delete · Move Up/Down.
  - Editor has an explicit mode ("New action - not yet saved" vs "Editing: X").
    Add is only enabled in new mode; Save Changes / Duplicate / Delete only when
    a row is selected.
  - **Add** always mints a fresh `User.<slug>.<hex>` id (Action ID field is
    ignored on Add - it's edit-only) and then clears the editor. No more
    accidental clones.
  - **Duplicate** copies the selected action with a fresh id, "(copy)" name and
    no keybinding.
  - Shortcut field is comma-separated; keybindings are rebuilt + deduped on
    every Add/Save.
  - `loadActions()` removes exact-duplicate `{id,keys}` keybindings on open, so
    an already-messed settings.json self-heals on the next save.
  - Move Up/Down are disabled while a column sort is active (visual order would
    not match `actions[]` order).

## Later

## 5. Drop the matplotlib dependency

The app imports `matplotlib` **only** to get the list of installed font names
(`matplotlib.font_manager.fontManager.ttflist`), used to fill the Font dropdown
in the Profiles tab. matplotlib is a large install for that one list.

**Fix:** use Qt's own `QtGui.QFontDatabase().families()` instead and remove
`matplotlib` from the dependencies. One change in `modules/app_state.py`
(`font_list = …`), one line in `README.md` / install docs.
