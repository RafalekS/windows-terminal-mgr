# TODO

Open items only. Completed work is archived under `help/history/`.

## Pending user testing (Windows 11)

The modularisation + WT knowledge refresh (branch `refactor/modularize`) is
**not verified** until tested on Windows:

- App launches; all 6 tabs render.
- Profiles: change **Bell Style** (now `all / audible / window / taskbar / none`
  - `visual` removed, it was never a valid WT value) and **Close on Exit** (now
  includes `automatic`, the current WT default); Save; reopen; confirm persisted
  and that Windows Terminal accepts the resulting `settings.json`.
- Actions: "Built-in Action" dropdown shows the full ~70-name action list; add an
  action using e.g. `setColorScheme`; Save; reopen.
- Command Builder: build + Parse round-trip.
- Folders: drag-drop, Move Up/Down (incl. inside folders), Update Item.
- Settings + Fragment Extensions tabs behave as before.
- `--debug` still prints diagnostics.

After a clean test: bump `VERSION` in `modules/main_window.py` to `1.1.1`.

## Bell style - lossy combo mapping

`bellStyle` can be a list (`["audible", "window"]` etc.). The editor collapses
any list to the single nearest combo item (`_normalise_bell_style` in
`profiles_tab.py`). Combos like `["window", "taskbar"]` (visual only, both ways)
have no exact combo value. A proper fix is a multi-select control. Low priority.

## Profile fields not yet surfaced in the editor

All valid per current WT docs, none currently editable:

- `bellSound` (file path / array)
- `pathTranslationStyle` (`none | wsl | cygwin | msys2 | mingw`) - Preview
- `experimental.useAtlasEngine`
- `experimental.repositionCursorWithMouse` - needs shell integration

## Notes

- `matplotlib` is a heavy dependency used only for `fontManager.ttflist`.
  Consider replacing with a lighter font enumeration (e.g. `QFontDatabase`).
