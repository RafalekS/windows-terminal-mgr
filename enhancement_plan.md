# Windows Terminal Manager - Enhancement Plan

**Branch:** `enhancements` (branched from `main` at tag `v1.0-stable`)
**Date:** 11/02/2026
**Author:** Claude Opus 4.6

---

## Code Review Summary

### Bugs Found

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| B1 | **HIGH** | `moveFolderItemUp/Down` (lines 2661-2813) | **Separator move is broken.** `findActualEntry()` always returns the FIRST separator it finds (all separator dicts `{'type': 'separator'}` are identical). Then `entries.index(actual_entry)` also finds the first matching separator. Result: wrong separator gets moved, or nothing happens. Same root cause affects all identical-looking entries. |
| B2 | **HIGH** | `findActualEntry()` (line 2239) | Uses `==` equality matching for separators which means it always returns the first one. Should use `is` identity comparison since tree items already store the actual dict references from `data_schemes`. |
| B3 | **MEDIUM** | `deleteFolderItem()` (lines 2651-2656) | `parent_entry['entries'].remove(entry)` uses `==` comparison. For separators, this removes the FIRST separator in the list, not necessarily the selected one. |
| B4 | **MEDIUM** | `changedProfile()` / font handling (lines 1096, 940) | Uses deprecated `fontFace` and `fontSize` top-level properties. Modern Windows Terminal uses nested `font.face` and `font.size`. The app won't read/write font settings for profiles that use the modern format. |
| B5 | **MEDIUM** | `deleteAction()` (line 1657-1660) | Unbound key deletion dialog uses Save/Discard/Cancel buttons instead of Yes/No. Confusing UX - "Save" means "delete" in this context. |
| B6 | **LOW** | `updateProfileOrder()` (lines 1165-1175) | If two profiles have the same name, only the first one is found per name, causing data loss of the duplicate. |
| B7 | **LOW** | Startup (lines 30-37) | If `HOMEPATH` env var is not set, code crashes with path `C:None\\...`. No graceful error handling. |
| B8 | **LOW** | `updateFolderItem()` (lines 2602, 2614) | Sets `icon` to `None` (writes JSON `null`) instead of removing the key entirely. Could cause issues with WT parsing. |
| B9 | **LOW** | `addTreeItem()` remainingProfiles (line 2168-2174) | Creates virtual `{'type': 'profile', ...}` entries for unassigned profiles that aren't actually in `data_schemes`. If user tries to move/update these, it will fail silently. |

---

## Enhancement Tasks

### Phase 1: Bug Fixes & Foundation

#### 1.1 Fix separator identity tracking (B1, B2, B3)
**Problem:** All separator dicts look identical (`{'type': 'separator'}`), so `findActualEntry()`, `list.index()`, and `list.remove()` match the wrong one.

**Solution:** Stop using `findActualEntry()` for move/delete operations. The tree item's UserRole data already holds the actual dict reference from `data_schemes`. Use `is` identity comparison instead of `==`:
```python
# Replace entries.index(actual_entry) with:
idx = next(i for i, e in enumerate(entries) if e is entry)

# Replace entries.remove(entry) with:
idx = next(i for i, e in enumerate(entries) if e is entry)
entries.pop(idx)
```

Also refactor `moveFolderItemUp/Down` to use `entry` directly (from UserRole) rather than calling `findActualEntry()`. The entry IS the actual object.

For finding the parent list, walk `data_schemes['newTabMenu']` recursively using `is` to locate which list contains the entry.

#### 1.2 Fix font property handling (B4)
**Problem:** App reads/writes `fontFace`/`fontSize` (deprecated) instead of `font.face`/`font.size` (current).

**Solution:** Support both formats:
- Read: Check `profile.get('font', {}).get('face')` first, fall back to `profile.get('fontFace')`
- Write: Write to `font.face` / `font.size` (modern format). Remove deprecated keys if present.

#### 1.3 Fix minor bugs (B5-B8)
- B5: Change delete unbound key dialog to use Yes/No buttons
- B6: Use index-based profile reordering instead of name-based lookup
- B7: Add try/except around settings path detection with user-friendly error
- B8: Use `del actual_entry['icon']` instead of setting to `None` when icon is empty

---

### Phase 2: Visual & UI Improvements

#### 2.1 Global stylesheet / theme
Apply a consistent dark-friendly Fusion style with proper colours throughout. Currently the app has:
- Hardcoded `#f0f0f0` backgrounds on help labels (looks bad in dark mode)
- No consistent colour palette
- Inconsistent button styling

**Changes:**
- Add a global QSS stylesheet applied at startup
- Consistent colour palette: backgrounds, borders, accent colours
- Proper group box styling with borders
- Styled buttons (primary action = accent colour, destructive = red, secondary = neutral)
- Styled list/tree widgets with alternating row colours
- Better font sizes for headers vs body text

#### 2.2 Status bar improvements
- Replace the plain QLabel status with a proper QStatusBar
- Add permanent indicators: profile count, unsaved state icon
- Colour-coded status messages with auto-fade

#### 2.3 Tab icons
Add icons to tab headers for quick visual identification:
- Profiles: user icon
- Folders & New Tab Menu: folder icon
- Actions & Key Bindings: keyboard icon
- WT Command Builder: terminal icon

---

### Phase 3: Expand remainingProfiles display

#### 3.1 Show unassigned profiles in Folders tab tree
**Current:** `remainingProfiles` shows as a single grey node with virtual children that can't be interacted with.

**Improvements:**
- Show count in the node label: "Remaining Profiles (5 unassigned)"
- Expand by default so user sees what's there
- Make virtual profile entries clearly non-editable (italic text, different icon)
- Add right-click context menu: "Add to root" / "Add to folder..." which converts them to explicit profile entries
- Show a summary section: "X profiles assigned, Y in remainingProfiles, Z completely unassigned"

#### 3.2 Profile assignment indicator
- In the Profiles tab list, add a small indicator showing where each profile appears in the newTabMenu (e.g., tooltip: "In folder: SSH Tools" or "In: remainingProfiles" or "Not in menu")

---

### Phase 4: Fix separator move up/down (builds on 1.1)

This is already addressed in Phase 1.1. Additional work:

#### 4.1 Improve re-selection after move
**Problem:** After moving a separator, `reselectItemByEntry()` matches the first separator it finds (wrong one).

**Solution:** Track position (parent + index) instead of entry identity for re-selection:
```python
def reselectItemByPosition(self, parent_item_ref, target_index):
    # After reload, find item at same parent + index position
```

#### 4.2 Visual feedback for moves
- Briefly highlight the moved item (flash background colour)
- Disable Move Up when item is first, Move Down when item is last

---

### Phase 5: Simplify Actions & Key Bindings tab

#### 5.1 Current problems
- List shows cryptic format: `🔗 [ctrl+shift+t] Open New Tab → newTab (ID: User.newTab.abc123)`
- User must understand the relationship between actions, commands, IDs, and keybindings
- Arguments field requires raw JSON editing
- Action Name vs Action ID is confusing
- Unbound keys shown separately with no clear distinction

#### 5.2 Redesigned layout

**Left panel - Actions table (replace QListWidget with QTableWidget):**
| Shortcut | Action | Command |
|----------|--------|---------|
| Ctrl+Shift+T | Open New Tab | newTab |
| Ctrl+Shift+W | Close Tab | closeTab |
| (none) | My Custom Action | sendInput |
| Ctrl+C | (disabled) | - |

- Sortable columns
- Filter/search box at top
- Colour coding: bound (normal), unbound (grey), disabled (strikethrough)

**Right panel - Simplified editor:**
```
Action Name:    [Open New Tab          ]
Shortcut Key:   [Ctrl+Shift+T    ] [Record...]
Command:        [newTab            ▼]

── Advanced (collapsed by default) ──
Action ID:      [User.newTab.abc123    ]
Arguments:      [{                     }]
                [  "index": 0          ]
Icon Path:      [path/to/icon    ] [Browse]
```

- "Record..." button: press a key combo and it fills the field (key recorder)
- Command dropdown shows friendly names with descriptions
- Arguments section hidden by default, shown only when command has args
- Auto-generate ID from command name (user doesn't need to touch it)

#### 5.3 Key recorder widget
- Click "Record..." button
- Dialog captures next key press
- Shows the captured combo (e.g., "ctrl+shift+t")
- Warns if shortcut conflicts with existing binding

---

### Phase 6: Simplify Command Builder tab

#### 6.1 Current problems
- Too many options visible at once
- "Apply to selected step" workflow is unintuitive (edit fields, then click Apply)
- Global options take up a lot of space even when unused
- "Step editor" shows all fields regardless of step type

#### 6.2 Redesigned layout

**Global Options - Collapsible section (collapsed by default):**
```
▸ Global Options (--maximized)     [expand to edit]
```
When expanded, show the current options in a more compact layout.

**Command Steps - Main area:**
Replace the flat list + separate editor with an inline-editing approach:

Each step shown as a card/row:
```
┌─ Step 1: new-tab ──────────────────────────────────┐
│ Profile: [PowerShell    ▼]  Scheme: [Campbell    ▼] │
│ Title:   [My Tab          ]  Tab Color: [#FF0000 🎨]│
│ Directory: [C:\Users\...   📁]                      │
│                                    [Remove] [▲] [▼] │
└─────────────────────────────────────────────────────┘
┌─ Step 2: split-pane -H (50%) ──────────────────────┐
│ Profile: [Ubuntu        ▼]  Scheme: [           ▼] │
│ Size:    [0.50    ]  Commandline: [wsl.exe        ] │
│                                    [Remove] [▲] [▼] │
└─────────────────────────────────────────────────────┘

[+ Add Tab] [+ Split Horizontal] [+ Split Vertical]
```

- Each step is self-contained - no separate "Apply" button needed
- Changes are applied immediately as user types
- Show only relevant fields per step type (hide "Size" for new-tab, hide "Commandline" unless used)
- More compact, less cognitive load

**Preview section - stays at bottom:**
```
Command: wt --maximized new-tab -p "PowerShell" `; split-pane -H --size 0.5 wsl.exe
                                          [Parse] [Copy] [Run]
```

---

### Phase 7: Drag and Drop

#### 7.1 Folders tab drag and drop
**Implementation:**
- Enable on `foldersTreeWidget`:
  ```python
  self.foldersTreeWidget.setDragEnabled(True)
  self.foldersTreeWidget.setAcceptDrops(True)
  self.foldersTreeWidget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
  self.foldersTreeWidget.setDefaultDropAction(Qt.DropAction.MoveAction)
  ```
- Override `dropEvent` to:
  1. Determine source item, source parent list, source index
  2. Determine drop target and position (before/after/into folder)
  3. Remove from source list, insert at target position in `data_schemes`
  4. Reload tree and re-select the moved item
- Constraints:
  - Profiles/separators can be dropped into folders or root
  - Folders can be dropped at root level or into other folders
  - `remainingProfiles` node cannot be dragged
  - Virtual (unassigned) profiles: dragging into a folder converts them to explicit entries

#### 7.2 Visual drop indicators
- Show drop line between items (above/below)
- Show folder highlight when hovering over a folder (drop into)
- Cursor changes to indicate valid/invalid drop targets

#### 7.3 Command Builder drag and drop (optional)
- Allow reordering steps by drag in the steps list
- Simpler implementation since it's a flat list

---

### Phase 8: Add remaining profile fields

#### 8.1 Missing fields to add

**General Settings (high value):**
| Field | JSON Key | Type | Default |
|-------|----------|------|---------|
| Opacity | `opacity` | Integer 0-100 | 100 |
| History Size | `historySize` | Integer 0-32767 | 9001 |
| Close on Exit | `closeOnExit` | Enum: graceful/always/never | graceful |
| Bell Style | `bellStyle` | Enum: none/audible/visual/all | audible |
| Suppress App Title | `suppressApplicationTitle` | Boolean | false |
| Antialiasing Mode | `antialiasingMode` | Enum: grayscale/cleartype/aliased | grayscale |

**Appearance Settings (medium value):**
| Field | JSON Key | Type | Default |
|-------|----------|------|---------|
| Foreground Colour | `foreground` | Colour (#RRGGBB) | from scheme |
| Background Colour | `background` | Colour (#RRGGBB) | from scheme |
| Selection Background | `selectionBackground` | Colour (#RRGGBB) | from scheme |
| Cursor Colour | `cursorColor` | Colour (#RRGGBB) | from scheme |
| Font Weight | `font.weight` | Enum/Integer | normal |
| BG Image Stretch Mode | `backgroundImageStretchMode` | Enum | uniformToFill |
| BG Image Alignment | `backgroundImageAlignment` | Enum | center |
| Intense Text Style | `intenseTextStyle` | Enum: bold/bright/all/none | all |

**Advanced Settings (lower value):**
| Field | JSON Key | Type | Default |
|-------|----------|------|---------|
| AltGr Aliasing | `altGrAliasing` | Boolean | true |
| Adjust Indistinguishable Colours | `adjustIndistinguishableColors` | Enum | always |
| Retro Terminal Effect | `experimental.retroTerminalEffect` | Boolean | false |

#### 8.2 UI organisation
Group the profile editor fields into collapsible sections:
```
▾ General
    Name | Command Line | Starting Directory | Tab Title | Icon | Hidden

▾ Appearance
    Color Scheme | Font (face, size, weight)
    Foreground | Background | Selection Background | Cursor (shape, colour)
    Tab Color | Opacity | Use Acrylic

▾ Background Image
    Image Path | Opacity | Stretch Mode | Alignment

▾ Advanced
    History Size | Close on Exit | Bell Style | Antialiasing
    Suppress App Title | Snap on Input | Run as Admin
    Padding | Scrollbar State | AltGr Aliasing
    Intense Text Style | Retro Terminal Effect
```

#### 8.3 Read/write implementation
For each new field:
1. Add UI widget in the appropriate collapsible section
2. Add to `changedProfile()` to load from data
3. Add change handler to write to `data_schemes`
4. Support both read and write with proper defaults

---

## Implementation Order

| Phase | Task | Effort | Priority |
|-------|------|--------|----------|
| 1.1 | Fix separator identity tracking | Small | **Critical** |
| 1.2 | Fix font property handling | Small | **High** |
| 1.3 | Fix minor bugs | Small | **High** |
| 2.1 | Global stylesheet | Medium | **Medium** |
| 2.2 | Status bar improvements | Small | **Low** |
| 2.3 | Tab icons | Small | **Low** |
| 3.1 | Expand remainingProfiles | Medium | **High** |
| 3.2 | Profile assignment indicator | Small | **Medium** |
| 4.1 | Improve re-selection after move | Small | **High** |
| 4.2 | Visual feedback for moves | Small | **Medium** |
| 5.1-5.3 | Simplify Actions tab | Large | **High** |
| 6.1-6.2 | Simplify Command Builder | Large | **High** |
| 7.1-7.2 | Drag and drop (Folders) | Medium | **Medium** |
| 7.3 | Drag and drop (Command Builder) | Small | **Low** |
| 8.1-8.3 | Add remaining profile fields | Large | **High** |

**Recommended order:** 1.1 → 1.2 → 1.3 → 8.1-8.3 → 2.1 → 3.1 → 4.1 → 5.1-5.3 → 6.1-6.2 → 7.1-7.2 → remaining

---

## Testing Strategy

Each phase should be tested on Windows 11 before moving to the next:

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
