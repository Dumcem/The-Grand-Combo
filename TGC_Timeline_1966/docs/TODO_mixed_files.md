# Mixed file maintenance notes

This file is retained for existing documentation and validation references. It
is a stable maintenance note for mixed core/submod files, not a temporary task
list.

## Current split

- `TGC/` is the non-1966 core mod.
- `TGC_Timeline_1966/` is the runtime layer for the 1966 timeline extension.
- Full override and carrier files in the submod preserve the active TGC or
  Victoria 2 definitions while adding the minimum 1966-specific behavior needed
  for the extended timeline.

## Mixed-file boundaries

- `TGC_Timeline_1966/decisions/00_Setup.txt` carries the 1966 end-game decision
  date while core keeps the non-1966 setup behavior.
- `TGC_Timeline_1966/inventions/navy_inventions.txt` carries submarine-specific
  effects while core keeps the generic navy invention behavior.
- Mixed interface carriers such as `buildunit.gui`, `combat.gfx`,
  `province_interface.gfx`, and `unitpanel.gfx` exist because the loader expects
  full interface definitions and frame counts rather than small patch fragments.
- Dedicated 1966 localisation files carry the late technology, invention, and
  unit text for the submod layer.

## Maintenance rule

When a generic bugfix or typo fix touches a file that has a 1966 carrier, review
whether the same non-1966 part must be present in both `TGC/` and
`TGC_Timeline_1966/`. When a change is genuinely 1966-only, keep it in the
submod and leave core unchanged.
