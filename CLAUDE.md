# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Overview

**Windows Terminal Manager** - a PyQt6 GUI for visually editing the Windows
Terminal `settings.json` (profiles, folders / new-tab menu, actions & key
bindings, `wt.exe` command builder, global settings, JSON fragment extensions).

Developed on Linux, **run on Windows 11**. After changing project files, commit
and push so the user can pull and test on their machine.

## Running

```bash
python wt_manager.pyw            # normal
python wt_manager.pyw --debug    # verbose diagnostic output (debug_print)
```

Do **not** run the GUI on the Linux dev box. Static checks only here:
`python -m py_compile wt_manager.pyw modules/*.py`.

## Architecture

`wt_manager.pyw` is a **thin entry point** (QApplication + icon + window +
closeEvent). All logic is in the `modules/` package:

| Module | Responsibility |
|---|---|
| `app_state.py` | Shared mutable state. **Importing it has side effects**: locate the WT `LocalState` dir, `chdir` in, back up + load `settings.json` into `data_schemes`; `sys.exit(1)` if not found. Also: `debug_print()`, `dumpJson()`, `stamp_uids()`/`strip_uids()`, `_UID_KEY`, derived lists (`profiles_list`, `data_list`, `font_list`), `default_profile`. |
| `config.py` | `APP_CONFIG` from `config/settings.json`; `load_app_config()`, `save_app_config()`, `SCRIPT_DIR`. |
| `themes.py` | `CURRENT_THEME_COLORS` from `config/themes/<name>.json`; `load_theme()`, `build_stylesheet()`. |
| `constants.py` | `COMMON_ACTIONS` (full WT action list), `PANE/RESIZE/SWAP_DIRECTIONS`, `BUILTIN_SCHEMES`, profile enum option lists (`BELL_STYLES`, `CLOSE_ON_EXIT_MODES`, ...). Verified against MS Learn docs. |
| `table_state.py` | `PersistentUI` - persists table/tree column widths+order+sort, splitter positions, and window geometry via `QSettings("WTManager","UIState")`. Debounced 500 ms, flushed on close/hide. `NumericItem` for numeric-sorting cells. |
| `widgets.py` | `CommandStep`, `DragDropTreeWidget`, `KeyRecorderDialog`. |
| `main_window.py` | `Ui_MainWindow` - subclasses the six tab mixins; owns `setupUi`, `statusLabel`, `saveButton` wiring, `setUnsavedChanges()`, `dumpOnSave()`, `VERSION`. |
| `profiles_tab.py` | `ProfilesMixin` - profile editor, "Defaults" pseudo-profile, env vars, pixel shader, profile templates. |
| `folders_tab.py` | `FoldersMixin` - `newTabMenu` tree, add/move/delete/drag-drop, menu-location lookups. |
| `actions_tab.py` | `ActionsMixin` - actions/keybindings table + type-aware editor + key recorder. Editor has a mode (`_setEditorMode` "new"/"edit"); Add mints a fresh id and clears; `loadActions` dedupes `{id,keys}` keybindings. |
| `command_builder_tab.py` | `CommandBuilderMixin` - visual `wt.exe` builder + command parser. |
| `settings_tab.py` | `SettingsMixin` - app config + a few global WT settings. |
| `fragments_tab.py` | `FragmentsMixin` - browse/create/edit WT JSON fragment files. |

### Shared-state rule (important)

`data_schemes`, `APP_CONFIG`, `CURRENT_THEME_COLORS`, `profiles_list` are
mutated **and reassigned** at runtime. Always reference them through the module
(`app_state.data_schemes`, `themes.CURRENT_THEME_COLORS`), **never**
`from app_state import data_schemes` (that would freeze a stale binding).

### Mixin composition

Every tab is a mixin contributing its `setupXTab()` + handlers.
`Ui_MainWindow(ProfilesMixin, FoldersMixin, ActionsMixin, CommandBuilderMixin,
SettingsMixin, FragmentsMixin, object)`. One runtime object, shared `self.*`
widget namespace. When adding a widget, create it in the same mixin's
`setup*Tab` (or `main_window.setupUi` for genuinely shared widgets).

## Windows Terminal settings structure

- **Profiles**: `data_schemes['profiles']['list']` (objects with `guid`);
  `data_schemes['profiles']['defaults']` applies to all.
- **Color schemes**: `data_schemes['schemes']`.
- **Actions / keybindings**: `data_schemes['actions']` (with `id`) and
  `data_schemes['keybindings']` (`{id, keys}`). A keybinding with `id: null` is
  an explicit unbind.
- **New tab menu**: `data_schemes['newTabMenu']` - list of
  `folder` / `profile` / `separator` / `remainingProfiles` entries; folders
  nest via `entries`. Profile entries reference a profile by `guid`.
  Entries carry an internal `_wt_uid` for tree-identity tracking; stripped on
  save by `strip_uids()`.

### Reference docs (verified for action names / enums)

- https://learn.microsoft.com/en-us/windows/terminal/customize-settings/actions
- https://learn.microsoft.com/en-us/windows/terminal/customize-settings/profile-advanced

## Development guidelines

- Use `debug_print()` (not `print()`) for diagnostics; test with `--debug`.
- Folders tab: identity is tracked by `_wt_uid`; `findParentList(entry)` locates
  an entry's containing list + index. `reselectItemByIdentity(entry)` re-selects
  after a `loadFolders()` reload. The Item Details panel hides rows per item type
  (`_showDetailRows`); the **Location** combo stores each folder's `_wt_uid` as
  userData (PyQt drops list identity in userData) - resolve via
  `_listForLocationKey`. `_virtual_remaining` entries are display-only until
  promoted by `_promoteAutoProfile`.
- `dumpJson()` backs up before every save; backups pruned to
  `APP_CONFIG['backup']['max_count']`.
- Never use bare `except:` / `except: pass`; catch specific exceptions.
- Tables use `Interactive` resize + movable sections; never
  `setStretchLastSection`. Sorting is disabled during population.
- Layout persistence: after a table/tree is populated (and, for a table,
  sorting is about to be enabled), call
  `self._persist.bind_table(widget, "<key>")` / `bind_tree` / `bind_splitter`
  from inside that tab's `setup*Tab`. `bind_table(..., sortable=False)` for
  grids where row order carries meaning (env vars). Window geometry is bound
  once in `main_window.setupUi`. `flush_ui_state()` is called on close/hide.

## Adding a profile property

1. `profiles_tab.py`: add the widget in `setupProfilesTab`, connect its signal.
2. Add a `changeX` handler - route through `self._setProfileField(key, value)`
   where possible (handles Defaults + key removal).
3. Populate it in `changedProfile` and `_loadDefaultsProfile`.

## Versioning

`VERSION` in `modules/main_window.py` (shown in the window title). Bump the
patch once per completed+tested task.

## File structure

```
wt_manager.pyw            # entry point
modules/                  # all logic (see table above)
config/
  settings.json           # app config
  themes/{light,dark}.json
help/
  TODO.md                 # open items only
  history/                # archived planning docs
  tests.md, *.pdf
backup/  log/             # gitignored
```
