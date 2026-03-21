# Windows Terminal Manager - Enhancement Plan

**Branch:** `enhancements` (branched from `main` at tag `v1.0-stable`)
**Date:** 11/02/2026
**Author:** Claude Opus 4.6

---

## Code Review Summary

### Bugs Found

| # | Severity | Location | Description | Status |
|---|----------|----------|-------------|--------|
| B1 | **HIGH** | `moveFolderItemUp/Down` | **Separator move is broken.** `findActualEntry()` always returns the FIRST separator it finds. | FIXED (Phase 1.1) |
| B2 | **HIGH** | `findActualEntry()` | Uses `==` equality matching for separators which means it always returns the first one. | FIXED (Phase 1.1) |
| B3 | **MEDIUM** | `deleteFolderItem()` | `parent_entry['entries'].remove(entry)` uses `==` comparison. For separators, removes the wrong one. | FIXED (Phase 1.1) |
| B4 | **MEDIUM** | `changedProfile()` / font handling | Uses deprecated `fontFace`/`fontSize` instead of modern `font.face`/`font.size`. | FIXED (Phase 1.2) |
| B5 | **MEDIUM** | `deleteAction()` | Unbound key deletion dialog uses Save/Discard/Cancel buttons instead of Yes/No. | FIXED (Phase 1.3) |
| B6 | **LOW** | `updateProfileOrder()` | If two profiles have the same name, data loss of the duplicate. | FIXED (Phase 1.3) |
| B7 | **LOW** | Startup | If `HOMEPATH` env var is not set, code crashes with `C:None\\...`. | FIXED (Phase 1.3) |
| B8 | **LOW** | `updateFolderItem()` | Sets `icon` to `None` instead of removing the key entirely. | FIXED (Phase 1.3) |
| B9 | **LOW** | `addTreeItem()` remainingProfiles | Creates virtual entries that fail silently on move/update. | FIXED (Phase 3) |

---

## Enhancement Tasks

### Phase 1: Bug Fixes & Foundation -- COMPLETED

#### 1.1 Fix separator identity tracking (B1, B2, B3) -- COMPLETED
- Added `findParentList()` using `is` identity comparison
- Rewrote `moveFolderItemUp/Down` to use identity-based lookup
- Fixed `deleteFolderItem` to use `list.pop(idx)` instead of `list.remove()`
- Added `reselectItemByIdentity()` method

#### 1.2 Fix font property handling (B4) -- COMPLETED
- Read: Check `font.face`/`font.size` first, fall back to deprecated `fontFace`/`fontSize`
- Write: Write to modern `font` dict format, remove deprecated keys

#### 1.3 Fix minor bugs (B5-B8) -- COMPLETED
- B5: Changed delete unbound key dialog to Yes/No buttons
- B6: Used index-based profile reordering instead of name-based lookup
- B7: Added graceful error handling for missing HOMEPATH with USERPROFILE fallback
- B8: Use `pop()` instead of setting to `None` when removing icon

---

### Phase 2: Visual & UI Improvements -- COMPLETED

#### 2.1 Global stylesheet / theme -- COMPLETED (REVISED)
- Initially applied Catppuccin Mocha dark theme, then replaced with pastel light theme
- Light lavender/purple palette with white inputs, visible dark text on all elements
- Accent buttons: green Save, blue Save Changes, red Delete - all with white text
- Styled all widgets: tabs, buttons, inputs, combos, lists, trees, tables, scrollbars, sliders, checkboxes, tooltips, group boxes

#### 2.2 Status bar improvements -- COMPLETED
- Updated status message colors for success/error feedback

#### 2.3 Tab icons -- COMPLETED
- Added tab tooltips for quick identification

---

### Phase 3: Expand remainingProfiles display -- COMPLETED

#### 3.1 Show unassigned profiles in Folders tab tree -- COMPLETED
- Shows count: "Remaining Profiles (N auto-listed)"
- Auto-expands to show unassigned profile names
- Virtual entries styled in blue with tooltips showing GUID
- Selection handler shows info for virtual entries
- Prevents move/delete operations on virtual entries

#### 3.2 Profile assignment indicator -- COMPLETED
- Added `getProfileMenuLocation()` to find where each profile GUID appears in newTabMenu
- Added `updateProfileMenuIndicators()` to set tooltips on profile list items
- Tooltips show: "Menu: In folder: X" or "Menu: Root level" or "Menu: In: remainingProfiles (auto)" or "Menu: Not in menu"
- Indicators refresh automatically when folder structure changes

---

### Phase 4: Fix separator move up/down (builds on 1.1) -- COMPLETED

#### 4.1 Improve re-selection after move -- COMPLETED
- `reselectItemByIdentity()` uses `is` comparison to re-find moved item after tree reload

#### 4.2 Visual feedback for moves -- COMPLETED
- Move Up/Down buttons disabled at boundaries (first/last item)
- Delete button disabled for remainingProfiles and virtual entries
- Uses `findParentList()` for accurate boundary detection

---

### Phase 5: Simplify Actions & Key Bindings tab -- COMPLETED

#### 5.1-5.2 Redesigned layout -- COMPLETED
- Replaced QListWidget with QTableWidget (4 columns: Shortcut, Name, Command, ID)
- Added filter bar for searching/filtering actions
- Simplified editor with Name, Shortcut, Command fields
- Added collapsible Advanced section (Action ID, Arguments JSON, Icon)
- Styled Save Changes (blue accent) and Delete (red) buttons
- Grey text for unbound actions, strikethrough for disabled/unbound keys
- Compact help text at bottom with modifier/key reference

#### 5.3 Key recorder widget -- COMPLETED
- Added `KeyRecorderDialog` class that captures key press combinations
- Maps Qt key codes to Windows Terminal shortcut names (a-z, 0-9, f1-f24, arrow keys, etc.)
- Handles modifier keys: ctrl, shift, alt, win
- "Record..." button next to Shortcut field opens the dialog
- Warns if recorded shortcut conflicts with existing keybinding
- Appends to existing shortcuts when field already has a value

---

### Phase 6: Simplify Command Builder tab -- COMPLETED

#### 6.1-6.2 Redesigned layout -- COMPLETED
- Made Global Window Options collapsible (collapsed by default)
- Compact layout: state checkboxes, window target, size/position in one row
- Replaced "Apply to selected step" with auto-apply on field change
- Side-by-side list + editor layout
- Show/hide pane size field based on step type (hidden for new-tab)
- Preview section at bottom with compact height
- Styled Remove button with red accent

---

### Phase 7: Drag and Drop -- COMPLETED

#### 7.1 Folders tab drag and drop -- COMPLETED
- Created `DragDropTreeWidget` subclass with custom `dropEvent`
- Supports dropping above/below items and into folders
- Prevents dragging of `remainingProfiles` and virtual entries
- Updates `data_schemes` on drop, reloads tree, re-selects moved item
- Drop indicator shown during drag

#### 7.2 Visual drop indicators -- COMPLETED
- Built-in Qt drop indicator line shown between items
- Folder highlight when hovering over a folder (drop-into)

#### 7.3 Command Builder drag and drop -- COMPLETED
- Enabled InternalMove drag-drop on steps_list QListWidget
- Drag to reorder command steps; preview auto-refreshes after drop

---

### Phase 8: Add remaining profile fields -- COMPLETED

#### 8.1-8.3 Missing fields added -- COMPLETED
Profile editor completely rewritten with 4 collapsible group box sections:

**General:** Name, Command Line, Starting Directory, Tab Title, Icon, Hidden, Suppress App Title

**Appearance:** Color Scheme, Font (face, size, weight), Foreground, Background, Selection Background, Cursor Color, Cursor Shape, Tab Color, Opacity (slider), Intense Text Style, Use Acrylic

**Background Image:** Image Path, Background Image Opacity, Stretch Mode, Alignment

**Advanced:** History Size, Close on Exit, Bell Style, Antialiasing Mode, Retro Terminal Effect, AltGr Aliasing

Helper methods added: `_pickColorInto()`, `_setProfileField()`

---

## Implementation Order -- COMPLETED

| Phase | Task | Effort | Priority | Status |
|-------|------|--------|----------|--------|
| 1.1 | Fix separator identity tracking | Small | **Critical** | DONE |
| 1.2 | Fix font property handling | Small | **High** | DONE |
| 1.3 | Fix minor bugs | Small | **High** | DONE |
| 8.1-8.3 | Add remaining profile fields | Large | **High** | DONE |
| 2.1 | Global stylesheet | Medium | **Medium** | DONE |
| 3.1 | Expand remainingProfiles | Medium | **High** | DONE |
| 4.1-4.2 | Improve move operations | Small | **High** | DONE |
| 5.1-5.2 | Simplify Actions tab | Large | **High** | DONE |
| 6.1-6.2 | Simplify Command Builder | Large | **High** | DONE |
| 7.1-7.2 | Drag and drop (Folders) | Medium | **Medium** | DONE |

**All items completed.** No deferred items remaining.

---

## Testing Strategy

Each phase should be tested on Windows 11 before merging to main:

1. **Bug fixes:** Run with `--debug`, verify separator moves, font reading/writing, delete operations
2. **Visual:** Visual inspection on Windows 11 with both light and dark system themes
3. **remainingProfiles:** Create profiles, add some to folders, verify unassigned list is correct
4. **Actions tab:** Create, edit, delete actions. Verify keybindings persist after save/reload
5. **Command Builder:** Build commands, parse them back, verify round-trip accuracy
6. **Drag and drop:** Drag profiles between folders, reorder items, verify data_schemes integrity
7. **Profile fields:** Set each new field, save, reload, verify values persist. Open Windows Terminal to confirm effect.

---

## Rollback Plan

- `v1.0-stable` tag on `main` branch preserves the working version
- All work happens on `enhancements` branch
- Merge to `main` only after testing passes on Windows 11
- If issues found post-merge: `git checkout v1.0-stable -- wt_manager.pyw`
