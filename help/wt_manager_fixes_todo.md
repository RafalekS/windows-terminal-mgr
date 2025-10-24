# Windows Terminal Manager - Folders & New Tab Menu Fixes

## Critical Issues to Fix

### 1. Command Parser Bug
**Issue**: When parsing `wt --maximized new-tab -p "PS7" --colorScheme "Arthur" ; split-pane -H --size 0.05 wsl.exe`
- Ignores the `new-tab` command
- Only creates the `split-pane` command
- Result: `wt --maximized split-pane -H --size 0.05 wsl.exe`

**Fix Required**: Update the regex parsing logic to properly handle all command types in sequence.

---

### 2. Profile Dropdown Confusion
**Current Behavior**:
- Folder Name field appears for folders (correct)
- Folder Icon field appears for folders (correct)
- Profile dropdown appears for profile entries (confusing)
- Profile dropdown is disabled for folders (correct but confusing)

**Issues**:
- Users don't understand the purpose of the Profile dropdown
- They expect to be able to "assign" profiles TO folders
- The dropdown is actually for selecting WHICH profile to add to the menu

**Fix Required**:
- Redesign the UI to make it clear that:
  - When adding a profile, you SELECT which profile to add from the dropdown
  - Folders don't have profiles assigned to them, they CONTAIN profile entries
  - Each profile entry references a profile by GUID

---

### 3. Add Folder - Name Changes Don't Update
**Current Behavior**:
- Click "Add Folder" → creates folder named "New Folder"
- Type new name in "Folder Name" field
- Tree doesn't update with new name
- Clicking "Update Item" doesn't update the name

**Fix Required**:
- "Update Item" button should update the selected folder/profile with values from the editor
- Should refresh the tree immediately after update

---

### 4. Add Profile Button Issues
**Current Behavior**:
- If folder/separator is selected: Can't add profile (dropdown disabled)
- If profile is selected: Adds duplicate of same profile below remainingProfiles

**Expected Behavior**:
- Should allow selecting ANY profile from dropdown
- Should add the selected profile to:
  - The currently selected folder (if folder selected)
  - Root level (if nothing or root item selected)
  - Parent folder (if profile/separator selected)

**Fix Required**:
- Enable profile dropdown regardless of selection
- Add profile to correct location based on selection
- Clear selection or show where it was added

---

### 5. Missing Profiles Display
**Current Behavior**:
- Only shows profiles that are explicitly in newTabMenu
- Doesn't show profiles that are in "remainingProfiles" entry
- Doesn't show profiles that aren't in newTabMenu at all

**Expected Behavior**:
- Should display ALL profiles from settings.json
- Show which profiles are assigned to folders
- Show which profiles are in remainingProfiles
- Show which profiles aren't in newTabMenu at all
- Allow drag-and-drop from unassigned to folders

**Fix Required**:
- Expand remainingProfiles to show actual profile list
- Add section for completely unassigned profiles
- Make it visual which profiles are where

---

### 6. Drag and Drop Not Working
**Current Behavior**:
- Help text says "Drag items to reorder them within their parent"
- Dragging does nothing

**Fix Required**:
- Implement drag and drop with QTreeWidget
- Enable setDragEnabled(True)
- Enable setAcceptDrops(True)
- Enable setDragDropMode(QAbstractItemView.InternalMove)
- Implement dropEvent to reorder items in data structure
- Alternative: Remove the misleading instruction if too complex

---

### 7. Move Up/Down Only Work on Folders
**Current Behavior**:
- Move Up/Down work on folders at root level
- Move Up/Down don't work on profiles within folders
- No feedback when it doesn't work

**Fix Required**:
- Make Move Up/Down work on ANY selected item
- Should move item within its parent's children list
- Should work for:
  - Folders at root
  - Profiles at root
  - Profiles within folders
  - Separators within folders

---

### 8. Update Item Button Purpose Unclear
**Current Issue**:
- Button exists but users don't know when to use it
- Doesn't seem to work when clicked

**Fix Required**:
- Make it work: Update selected item with editor values
- OR: Auto-update on field changes (remove button)
- Add tooltip explaining what it does

---

## UI/UX Improvements Needed

### A. Clearer Folder Editor Layout
**Current**:
```
Item Type: Profile
Folder Name: [disabled/enabled based on type]
Folder Icon: [disabled/enabled based on type]
Profile: [dropdown - confusing purpose]
Profile Icon: [optional icon override]
Allow Empty: [checkbox]
Inline: [checkbox]
```

**Proposed**:
```
[Show different panels based on item type]

IF FOLDER SELECTED:
  Folder Details:
    Name: [text field]
    Icon: [text field] [Browse]
    Options:
      ☑ Allow Empty (show even if no entries)
      ☐ Inline (don't create nested menu if single entry)

IF PROFILE SELECTED:
  Profile Details:
    Profile: [disabled - shows current profile name]
    Icon Override: [text field] [Browse] (optional)

IF SEPARATOR SELECTED:
  Separator
  (No editable properties)
```

### B. Better Visual Feedback
- Show icon next to actual folder/profile name in tree
- Color code: folders (yellow), profiles (blue), separators (gray)
- Show GUID or profile name in tree for clarity
- Expand remainingProfiles to show what it contains

### C. Workflow Improvements
1. **Add Profile to Folder**:
   - Select folder in tree
   - Click "Add Profile"
   - Select profile from dropdown dialog
   - Profile added to folder

2. **Create New Folder**:
   - Click "Add Folder"
   - Dialog appears asking for folder name
   - Folder created with that name (not "New Folder")

3. **Reorder Items**:
   - Either drag-drop OR
   - Select item, use Move Up/Down

---

## Implementation Priority

1. **HIGH**: Fix command parser (breaks functionality)
2. **HIGH**: Fix Update Item button (breaks workflow)
3. **HIGH**: Display all profiles including remainingProfiles
4. **MEDIUM**: Redesign UI to be clearer
5. **MEDIUM**: Fix Add Profile workflow
6. **MEDIUM**: Fix Move Up/Down for profiles
7. **LOW**: Implement drag-and-drop
8. **LOW**: Add visual improvements

---

## Testing Checklist

- [ ] Parse command with new-tab works
- [ ] Parse command with multiple steps works
- [ ] Add folder and change name works
- [ ] Update Item updates folder name
- [ ] Add Profile to root works
- [ ] Add Profile to folder works
- [ ] All profiles are visible in tree
- [ ] remainingProfiles shows actual profiles
- [ ] Move Up/Down works on folders
- [ ] Move Up/Down works on profiles in folders
- [ ] Move Up/Down works on separators
- [ ] Drag-drop works (if implemented)
- [ ] Update Item shows visual feedback
- [ ] Icons display correctly in tree
- [ ] Save and reload preserves structure
