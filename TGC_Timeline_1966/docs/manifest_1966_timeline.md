# TGC Timeline 1966 submod manifest

`TGC_Timeline_1966/` is the stable runtime submod that extends
`TGC - The Grand Combination` to an end date of `1966.1.1`. The base `TGC/`
mod remains the non-1966 core layer; the extended timeline is active only when
the launcher enables both `TGC - The Grand Combination` and
`TGC Timeline 1966`.

## Descriptor

- `TGC_Timeline_1966.mod` declares `dependencies = { "TGC - The Grand Combination" }`.
- The descriptor does not use `replace_path`; the submod relies on Victoria 2's
  normal dependency and file override behavior.
- Runtime files in this submod should be treated as the 1966 layer, not as
  generic core fixes. Generic fixes belong in `TGC/` unless there is a specific
  reason for the 1966 layer to carry them.

## Runtime contents

- **Technologies:** five full technology branch files in `technologies/`
  (`army`, `navy`, `commerce`, `culture`, `industry`). Each branch keeps the
  existing TGC tree and extends its five areas to twelve tiers, ending in 1966.
- **Inventions:** five additive `NEW_*_inventions.txt` files provide late
  1966-layer inventions. `inventions/navy_inventions.txt` is a carrier override
  for base navy inventions that need submarine-specific 1966 effects.
- **Units:** `units/submarine.txt` and `units/aircraftcarrier.txt` define the
  timeline-only naval unit types used by late inventions and UI assets.
- **Buildings:** `common/buildings.txt` carries the 1966 building-level
  extension for forts, naval bases, and infrastructure.
- **UI/interface:** interface carrier files support the 1966 end-date label,
  the extended technology tree layout, additional unit folders, expanded unit
  strips, naval combat frame counts, and level 7-8 building strips.
- **GFX:** the submod carries carrier/submarine models and animations, unit
  folder and strip assets, naval combat strip assets, extended building strips,
  and late-technology pictures.
- **Localisation:** `localisation/1966_SUP_technology.csv` and
  `localisation/1966_other_tech.csv` contain labels and descriptions for
  1966-layer technologies, inventions, and units.
- **Tooling:** the submod is covered by 1966-aware validation, balance audit,
  and core/submod drift checks under `TGC/tools/`.

## Full override and carrier inventory

These files intentionally duplicate or carry full definitions because Victoria 2
loads many data and interface definitions at file scope. Do not split,
minimize, or "simplify" these files without a focused loader check and the
submod drift checker. A smaller-looking file can silently drop inherited TGC or
Vanilla definitions when the submod is active.

| Submod file | Core/TGC source | Category | Why it exists |
|---|---|---|---|
| `TGC_Timeline_1966/common/defines.lua` | `TGC/common/defines.lua` | 1966 extension override | Sets the active end date to `1966.1.1` for the submod while core TGC keeps its non-1966 end-date behavior. |
| `TGC_Timeline_1966/common/buildings.txt` | `TGC/common/buildings.txt` | 1966 extension override | Carries level 7-8 building support for forts, naval bases, and infrastructure. |
| `TGC_Timeline_1966/decisions/00_Setup.txt` | `TGC/decisions/00_Setup.txt` | 1966 extension + TGC compatibility carrier | Preserves the full TGC setup decision file while changing `option_end_game` to the 1966 date. |
| `TGC_Timeline_1966/technologies/army_tech.txt` | `TGC/technologies/army_tech.txt` | 1966 extension + TGC compatibility override | Keeps the full TGC army technology branch and extends each area to twelve tiers. |
| `TGC_Timeline_1966/technologies/navy_tech.txt` | `TGC/technologies/navy_tech.txt` | 1966 extension + TGC compatibility override | Keeps the full TGC navy technology branch and adds late naval, carrier, and submarine-era progression. |
| `TGC_Timeline_1966/technologies/commerce_tech.txt` | `TGC/technologies/commerce_tech.txt` | 1966 extension + TGC compatibility override | Keeps the full TGC commerce technology branch and extends it through 1966 economic systems. |
| `TGC_Timeline_1966/technologies/culture_tech.txt` | `TGC/technologies/culture_tech.txt` | 1966 extension + TGC compatibility override | Keeps the full TGC culture technology branch and extends social, political, and intellectual development. |
| `TGC_Timeline_1966/technologies/industry_tech.txt` | `TGC/technologies/industry_tech.txt` | 1966 extension + TGC compatibility override | Keeps the full TGC industry technology branch and extends industrial, infrastructure, power, and materials progression. |
| `TGC_Timeline_1966/inventions/navy_inventions.txt` | `TGC/inventions/navy_inventions.txt` | 1966 extension + TGC compatibility carrier | Preserves base navy inventions while adding submarine-specific effects that should not exist in core TGC alone. |
| `TGC_Timeline_1966/interface/backend.gui` | `TGC/interface/backend.gui` | 1966 extension UI override | Changes the backend scenario label to `The World in 1966`. |
| `TGC_Timeline_1966/interface/country_technology.gui` | `TGC/interface/country_technology.gui` | TGC compatibility UI override | Adjusts technology-window positioning and sizing for the extended tree presentation. |
| `TGC_Timeline_1966/interface/buildings.gfx` | `TGC/interface/buildings.gfx` | Victoria 2 loader UI carrier | Adds level 7-8 fort and naval-base actor definitions while preserving the rest of the building actor file. |
| `TGC_Timeline_1966/interface/buildunit.gui` | `TGC/interface/buildunit.gui` | Victoria 2 loader UI carrier | Carries the full build-unit interface layout for additional submarine/carrier folders and the adjusted queue/list spacing. |
| `TGC_Timeline_1966/interface/combat.gfx` | `TGC/interface/combat.gfx` | Victoria 2 loader UI carrier | Increases naval combat unit strip frame counts to include the 1966 naval unit icons. |
| `TGC_Timeline_1966/interface/country_military.gfx` | `TGC/interface/country_military.gfx` | Victoria 2 loader UI carrier | Defines the additional submarine and aircraft carrier unit-folder sprites while preserving military UI sprite definitions. |
| `TGC_Timeline_1966/interface/province_interface.gfx` | `TGC/interface/province_interface.gfx` | Victoria 2 loader UI carrier | Increases province building strip frame counts for level 7-8 fort, naval-base, and infrastructure display. |
| `TGC_Timeline_1966/interface/ships.gfx` | `TGC/interface/ships.gfx` | 1966 extension UI/GFX carrier | Adds carrier and submarine ship actor bindings for the timeline-only naval units. |
| `TGC_Timeline_1966/interface/unitpanel.gfx` | `TGC/interface/unitpanel.gfx` | Victoria 2 loader UI carrier | Increases the unit strip frame count so the unit panel can address the added unit icons. |

## Additive and asset carrier files

The following entries are not full textual overrides like `common/buildings.txt`,
`technologies/*.txt`, or `interface/*.gfx`. Some are purely additive 1966-layer
files, while others are asset carriers or replacement assets that can share a
path with core/TGC assets when the submod is active. Treat the `gfx/interface/`
assets with the same care as their UI references: they support extended unit
folders, unit strips, naval combat strips, and building strips, and should not
be treated as harmless standalone additions without checking UI/GFX references
and frame counts.

- `TGC_Timeline_1966/inventions/NEW_army_inventions.txt`
- `TGC_Timeline_1966/inventions/NEW_commerce_inventions.txt`
- `TGC_Timeline_1966/inventions/NEW_culture_inventions.txt`
- `TGC_Timeline_1966/inventions/NEW_industry_inventions.txt`
- `TGC_Timeline_1966/inventions/NEW_navy_inventions.txt`
- `TGC_Timeline_1966/units/aircraftcarrier.txt`
- `TGC_Timeline_1966/units/submarine.txt`
- `TGC_Timeline_1966/localisation/1966_SUP_technology.csv`
- `TGC_Timeline_1966/localisation/1966_other_tech.csv`
- `TGC_Timeline_1966/gfx/anims/Carrier*`
- `TGC_Timeline_1966/gfx/anims/Submarine*`
- `TGC_Timeline_1966/gfx/interface/*`
- `TGC_Timeline_1966/gfx/pictures/tech/*.tga`

## Maintenance guardrails

- Review the full override/carrier inventory whenever the corresponding
  `TGC/` file changes. A core-only fix can be hidden by the submod while the
  1966 layer is active.
- Run `TGC/tools/check_1966_submod_drift.py` after relevant core edits and
  `TGC/tools/check_1966_submod_drift.py --reverse` after relevant submod edits.
- Run `TGC/tools/validate_1966_extension.py` after changes that affect the
  declared 1966 runtime scope.
- Keep balance changes separate from organizational cleanup. Technology,
  invention, unit, building, and UI values in the runtime files affect gameplay
  or loading behavior and should not be changed as part of documentation work.
