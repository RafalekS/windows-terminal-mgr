# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Windows Terminal Manager** - A PyQt6 GUI application for managing Windows Terminal settings, profiles, color schemes, keybindings, and command generation. Provides visual editing of the Windows Terminal `settings.json` file.

## Running the Application

```bash
# Normal mode
python wt_manager.pyw

# Debug mode (shows detailed output)
python wt_manager.pyw --debug
```

## Application Architecture

### Single File Application
The entire application is in `wt_manager.pyw` (~2900 lines). This is intentional - it's a single-purpose GUI tool.

### Key Components

1. **CommandStep class** (line ~97): Represents Windows Terminal command builder steps (new-tab, split-pane)
2. **Ui_MainWindow class** (line ~136): Main PyQt6 GUI class containing all UI setup and logic
3. **Global functions**:
   - `debug_print()`: Conditional debug output (controlled by --debug flag)
   - `dumpJson()`: Saves settings.json with automatic backup
   - `findDefault()`: Finds default profile name from GUID

### Settings Management

**Settings Location**: `%HOMEPATH%\LocalAppData\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`
- Alternative path checked: `%HOMEPATH%\AppData\Local\Packages\...`
- Automatically creates timestamped backups before any save: `settings.json.bak_YYYYMMDD_HHMMSS`

**Data Structure**: Global `data_schemes` dict loaded from settings.json using `commentjson` library (supports JSON with comments)

### Four Main Tabs

1. **Profiles Tab**: Edit profile properties (name, commandline, startingDirectory, icon, colors, font, cursor, background image)
2. **Folders & New Tab Menu Tab**: Manage folder structure and profile organization in dropdown menu
3. **Actions & Key Bindings Tab**: Configure keyboard shortcuts and actions
4. **WT Command Builder Tab**: Visual builder for complex `wt.exe` commands with multiple tabs/panes

## Important Implementation Details

### Windows Terminal Settings Structure

**Profiles**: `data_schemes['profiles']['list']` - Array of profile objects with GUIDs
**Color Schemes**: `data_schemes['schemes']` - Array of color scheme definitions
**Actions**: `data_schemes['actions']` - Array of keybinding objects
**New Tab Menu**: `data_schemes['newTabMenu']` - Hierarchical structure with folders/profiles/separators

### newTabMenu Structure
```python
{
    "type": "folder",  # or "profile", "separator", "remainingProfiles"
    "name": "Folder Name",
    "icon": "path/to/icon.png",
    "allowEmpty": False,
    "inline": "never",  # or "always", "auto"
    "entries": [...]  # nested array of profiles/separators
}
```

Profile entries reference profiles by GUID: `{"type": "profile", "profile": "{guid}", "icon": "..."}`

### Known Issues (see help/wt_manager_fixes_todo.md)

**HIGH PRIORITY BUGS**:
1. Update Item button doesn't persist changes to data_schemes - shows "WARNING - Entry not found in data_schemes!" in debug
2. Add Profile to folder doesn't update data_schemes properly - profiles don't appear after save/reload
3. Move Up/Down for profiles within folders may not work consistently

**Testing Protocol**: Always run with `--debug` flag when fixing folders tab issues to see detailed diagnostic output

### Command Parser

Located in `parse_wt_command()` method. Parses Windows Terminal command syntax:
```
wt --maximized new-tab -p "ProfileName" --colorScheme "Arthur" ; split-pane -H --size 0.5 wsl.exe
```

Extracts:
- Global options (--maximized, --window, --focus-tab)
- Command steps (new-tab, split-pane)
- Step options (-p, -d, --title, --tabColor, --colorScheme, --size, -H/-V)
- Raw commandlines

## Development Guidelines

### Debugging
- Always use `debug_print()` instead of `print()` for diagnostic output
- Test changes with `--debug` flag to see detailed state tracking
- Check `entry_id` object IDs to track dictionary references

### Modifying Folders Tab Logic
**Critical**: The folders tab has persistent data synchronization issues between:
- Tree widget display (`foldersTreeWidget`)
- Editor fields (folder name, icons, profile dropdown)
- Underlying `data_schemes['newTabMenu']` structure

When modifying folder/profile operations:
1. Add debug_print statements showing object IDs and before/after states
2. Verify changes persist to data_schemes (check `id(entry)`)
3. Test: change → update → save → reload app → verify in Windows Terminal

### Data Integrity
- `dumpJson()` creates backup before every save
- Test destructive operations with backup safety net
- Backups stored in settings directory: `settings.json.bak_*`

### Testing Workflow
1. Make changes in UI
2. Click "Save" button
3. Close application
4. Reopen application - verify changes loaded
5. Open Windows Terminal - verify changes applied

## Built-in Constants

**COMMON_ACTIONS**: List of ~30 Windows Terminal action names for keybinding dropdown
**BUILTIN_SCHEMES**: List of 9 built-in color schemes (Campbell, Solarized, etc.)

## Dependencies

- PyQt6: GUI framework
- commentjson: JSON parser supporting comments
- matplotlib: Used only for `fontManager.ttflist` to enumerate system fonts
- pathlib, datetime, subprocess, argparse: Standard library

## File Structure
```
.
├── wt_manager.pyw          # Main application (run this)
├── wt3.ico                 # Application icon
├── help/
│   ├── wt_manager_fixes_todo.md       # Known issues and TODO list
│   ├── wt_manager_fixes_completed.md  # Fixed issues documentation
│   ├── tests.md                       # Test output logs
│   └── folder_fixes_summary.txt       # Implementation notes
├── backup/                 # Backup directory (gitignored)
└── log/                    # Log directory (gitignored)
```

## Common Operations

### Adding a New Profile Property
1. Locate `setupProfilesTab()` method
2. Add UI field in appropriate layout section
3. Add field to `loadProfile()` method to populate from data
4. Add field to `saveProfile()` method to persist to data_schemes
5. Connect to `mark_unsaved()` for change tracking

### Fixing Folders Tab Issues
1. Run with `--debug`
2. Locate relevant method: `addFolderItem()`, `addProfileToFolder()`, `updateFolderItem()`, `moveFolderItemUp/Down()`
3. Check debug output for "WARNING - Entry not found" messages
4. Verify `id(entry)` matches between tree items and data_schemes
5. Ensure `loadFolders()` is called after data modifications
6. Use `selectTreeItem(entry)` to reselect item after refresh

### Command Builder Patterns
- Each step is a `CommandStep` object stored in list widget's UserRole
- `build()` method generates command string from CommandStep properties
- `refresh_preview()` combines all steps with global options
- Parser uses regex to extract options from existing commands