# Plau Glyphs Scripts

**English** · [Português](README.pt.md) · [Español](README.es.md) · [日本語](README.ja.md) · [简体中文](README.zh.md)

Python tools for everyday type design work at Plau: building glyphs, positioning components, and setting up font metadata. Created by Rodrigo Saiani with assistance from ChatGPT.

## Requirements

- macOS and Glyphs 4.
- Python scripting support in Glyphs.
- The `vanilla` UI library for Arrow Maker, Center Components, and Fill Font Metadata. If an import fails, check the Python modules available through Glyphs’ Plugin Manager.

Run these scripts **inside Glyphs**, not from Terminal. Basic Math uses the Glyphs 4 API; compatibility with Glyphs 3 is not guaranteed. Menu visibility and Python syntax have been checked, but the collection has not been fully tested across fonts and Glyphs builds. Some dialogs and messages are in Portuguese.

## Installation

Install the scripts from Glyphs’ **Plugin Manager** (**Window → Plugin Manager → Scripts**). Updates also come through the Plugin Manager; reload the scripts afterwards (hold **Option** while opening the Script menu and choose **Reload Scripts**, or restart Glyphs).

To install by hand instead, download or clone this repository, choose **Script → Open Scripts Folder** in Glyphs 4, and copy the repository’s **`Plau` folder** into it with its subfolders intact. Then reload the scripts.

The installed structure should look like this:

```text
Scripts/
└── Plau/
    ├── Build Glyphs/
    │   ├── Arrow Maker.py
    │   ├── Build Basic Math G4.py
    │   ├── Build Letters from Diacritic.py
    │   ├── Build Period Glyphs.py
    │   └── Dashes From Hyphen.py
    ├── Components/
    │   ├── Flip Components.py
    │   ├── Make Segments Parallel.py
    │   ├── Make Segments Symmetric.py
    │   └── Vertically Center Component.py
    ├── Font Info/
    │   └── Font Info Launch.py
    ├── Paths/
    │   └── Create Centerline.py
    ├── Post-Production/
    │   ├── Export Release Package.py
    │   ├── Windows Font Fix.py
    │   └── windows-font-fix.sh
    └── Spacing/
        └── Set Diacritics Sidebearings.py
```

After installation, the tools appear under **Script → Plau**. Menu labels may differ from filenames.

## Using the scripts

Open a font, save a copy, and choose a tool from the menu. Glyph builders generally operate on every master of the current font. Review the generated shapes, spacing, and interpolation before using them in production.

| Menu item | Source glyphs or selection | What it does |
| --- | --- | --- |
| **Build Basic Math G4** | `n`, `hyphen`, `dotaccentcomb`, and `figurespace` or `zero` | Builds `plus`, `minus`, `equal`, `multiply`, `divide`, `logicalnot`, `greater`, `less`, `greaterequal`, and `lessequal`. |
| **Build En and Em Dashes from Hyphen** | `hyphen` | Rebuilds `endash` and `emdash` with horizontally scaled hyphen components. Default widths are 140% and 180% of the hyphen advance width, with sidebearing keys referencing hyphen. |
| **Build Periodcentered and Bullet** | `period` | Rebuilds `periodcentered` and `bullet` from period components. Bullet defaults to 1.4× scale; both use period-based sidebearing keys. |
| **Build Arrows from Hyphen** | `hyphen`; optionally `emdash`; stems in Font Info | Builds `arrowleft`, `arrowright`, `arrowup`, `arrowdown`, `arrowleftright`, and `arrowupdown` in every master as native Glyphs 4 strokes: an open shaft path plus a V-shaped head, no outlines. Stroke weight comes from each master’s stems (horizontal stem for horizontal strokes, vertical stem for vertical ones), falling back to the hyphen’s thickness. Horizontal arrows span the emdash width (or hyphen × factor) at hyphen height; vertical arrows run from baseline to cap height. Sidebearings reference `hyphen`. Glyphs 4 renames these glyphs on creation (for example `arrowright` becomes `rightArrow`); existing ones are found by Unicode. |
| **Build Letters from Diacritic** | One or more selected diacritics (combining, e.g. `acutecomb`, or legacy, e.g. `acute`), plus the base letters in the font | Opens a window to choose the Latin language sets of Add Glyphs (Basic, Western European, Central European, South Eastern European, South American, and more) and adds every letter of those sets that uses the diacritic, as a base + combining mark composite with automatic alignment in all masters. Letters whose base glyph is missing (for example `idotless` for `iacute`) are skipped and listed in the Macro Panel; letters that already have artwork are left alone. Optionally builds the legacy spacing mark (`acutecomb` → `acute`), when it exists in the glyph data, as an auto-aligned component of the comb. |
| **Center Components in Reference Height** | Selected glyphs containing components | Opens controls for vertical positioning relative to cap height, x-height, or layer height, on current or all layers. Disables automatic alignment on moved components. |
| **Set Diacritics Sidebearings** | Every glyph with category Mark | Combining marks (e.g. `acutecomb`) get LSB `=40` and RSB `=|` (equal to the LSB), with all layers synced. Legacy spacing marks (e.g. `acute`) get no keys of their own: each becomes an auto-aligned component of its `…comb` glyph and follows its metrics. Legacy glyphs that already hold that component just have auto alignment turned on; empty ones are built; ones with other artwork are left alone and listed in the Macro Panel (`REPLACE_DRAWN = True` rebuilds them). Layer-level LSB/RSB keys on these glyphs are cleared. |
| **Create Centerline** | Two segments (the 2 on-curve nodes of each, 4 in total, in the same or different contours) or two whole paths | Adds a new open path halfway between the two lines, for example the waist of an 8. Lines and curves can be mixed; direction is matched automatically. With two whole paths they need the same node structure; the start point and direction are matched automatically (it also works on closed paths drawn in opposite directions). The original paths are not changed and coordinates are rounded to whole units. Inspired by Harbor Type’s Create Centerline, rewritten for Glyphs 4. |
| **Flip Components** | Selected components, or selected glyphs that contain components | Opens a window with **Flip Horizontally** and **Flip Vertically**. Flips the selected components (or all components of the selected glyphs when none is selected) in all masters at once, each one around the center of its own bounds, so it stays in place and only its orientation changes. Components are matched across masters by their order in the glyph. Disables automatic alignment on flipped components; running it twice restores the original. Optional checkbox **Include special layers** also flips brace, bracket and backup layers. |
| **Make Segments Parallel** | Two segments in the current layer (select the 2 on-curve nodes of each, 4 in total) | Rotates both segments around their own midpoints to their average angle, so they become parallel without changing length. Handles attached to the moved nodes follow. One undo step. Shortcut: `cmd+opt+shift+p`. |
| **Make Segments Symmetric** | Four segments in the current layer: two left and two right of the glyph center (for example the four diagonal edges of a V) | Pairs each left segment with its right counterpart and makes them exact mirror images across the vertical axis at width ÷ 2, averaging both sides. Handles on moved nodes follow. If extra short segments are selected too, the four longest are used. One undo step. |
| **Fill Font Metadata** | An open font, a client name, an optional font name, and your foundry name, URL and vendor ID | Sets the family name to the font name (defaults to the client name when left empty; the client name is used in the copyright), fills designer and manufacturer (foundry name and URL), vendor ID and copyright, and resets the version to **0.000**. Optional checkbox **Add clean version string** sets the version string to just “Version X.XXX” and adds `--no-info` to existing ttfautohint options. Foundry fields and the checkbox are remembered between runs. |
| **Windows Font Fix** | Exported TTF/OTF fonts, chosen in a file dialog (or passed on the command line) | Fixes exported fonts so Microsoft Office (PowerPoint, Word) applies their OpenType substitutions: adds an empty `fvar` table, adds a `latn` script record copied from `DFLT` in GSUB/GPOS, makes `calt` also run every `rclt` lookup (shared, not copied), and builds a legacy `kern` table from the GPOS kerning (class pairs are expanded to glyph pairs; at most 10,920 pairs, keeping first the pairs between the most common characters (ASCII, then Latin-1 and common punctuation); skipped for variable fonts), which PowerPoint is reported to apply more reliably than the GPOS `kern` feature. Opens a window with a checkbox per fix (including **Kerning for PowerPoint**, so you can leave the kern table out; your choices are remembered) and a file picker; copies go into a “Windows Fix” folder next to each font unless you choose to overwrite. Web fonts (`woff`, `woff2`) are never touched and real variable fonts keep their `fvar`. Also runs from the command line and as a Glyphs Post-Export Command (see below). |
| **Export Release Package** | The font in front (saved), its active instances, and the previous release folder | Exports the font into a dated release folder (`yy.mm.dd`) with the structure of the previous release: `01. Desktop Variable` (variable TTF), `02. Webfont Variable (Recommended)` (variable WOFF2 plus the CSS and HTML sample), `03. Static OTF Files`, and `04. Windows TTF`, where the fonts go through Windows Font Fix and the four RIBBI styles move into `01. Windows RIBBI`. The README, CSS and HTML are copied from the previous release, with the version line of the README updated to the new folder name. Static fonts are autohinted with overlaps removed; the variable font is deliberately not autohinted and gets the post-export fixes of the project’s `fix_vf.py` (`usWeightClass` from the default of the weight axis, smart dropout control at the start of `prep`, the WWS bit), and its WOFF2 is built from the fixed TTF. A checkbox per folder (remembered), and it asks before writing into a non-empty release folder. |

### Basic Math behavior

- Each master uses the width of `figurespace` if that glyph exists; otherwise it uses `zero`. The width must be positive. `zero.tf` is not required.
- Empty master layers are filled. Existing artwork is kept for most symbols, but all symbol master layers receive the chosen width and are centered horizontally without scaling.
- **`less` and `lessequal` are rebuilt on every run**, replacing their master-layer artwork with horizontally mirrored components of `greater` and `greaterequal`.
- Editing the source shapes updates their mirrored counterparts. Rerun the script after changing spacing-source widths to apply the new widths and reflection positions.
- All symbols use **one stroke thickness**, so every part of `plus`, `multiply` and the others is equally thick. It follows the stems of each master (Font Info → Masters → Stems): the horizontal stem by default, the same thickness as `minus`. A master without stems gets them measured on the classic glyphs: `l`, `I` or `H` (vertical, with `n` as a last resort) and the crossbar of `H` or `hyphen` (horizontal). The source of each value is printed in the Macro Panel. At the top of the script, `math_stem` chooses `"horizontal"`, `"vertical"` or `"average"`, and `math_stem_factor` makes the symbols lighter or heavier than that stem.
- `greater` is an open path with a native Glyphs 4 stroke (and `less` mirrors it), so after generation you can move its nodes or change the stroke width instead of editing an outline. The stroke ends are aligned to the axis and the tip has a bevel join (flat tip); `stroke_cap` and `stroke_join` at the top of the script change that.

### Existing glyphs

Dashes and Periodcentered/Bullet replace their target master-layer content. Fill Font Metadata overwrites the fields listed above. In Arrow Maker, the option labeled **“Ask (backup then replace)” currently does not show a confirmation dialog**; it backs up and replaces. Use a saved font copy when trying these tools.

### Windows Font Fix as a Post-Export Command

Windows Font Fix can run automatically after every export with Florian Pircher’s [Post-Export Command](https://github.com/florianpircher/Post-Export-Command) plugin (work in progress; it may need to be installed from his repository instead of the Plugin Manager).

1. Copy `windows-font-fix.sh` and `Windows Font Fix.py` from the `Plau/Post-Production` folder next to your `.glyphs` file.
2. In Font Info, add a custom parameter named `Post-Export Command` to the font (or to the instances you export as TTF/OTF) with the value `./windows-font-fix.sh`.
3. Export. The plugin runs the command from the folder of the `.glyphs` file and passes the exported font’s path as the first argument. Web fonts (`woff`, `woff2`) are ignored, so web exports stay as they are.

The script needs Python with fontTools (`pip3 install fonttools`); `windows-font-fix.sh` looks for it in the usual places, because Glyphs starts commands without your shell environment. From the Terminal: `python3 "Windows Font Fix.py" --help`. To leave the kern table out of Post-Export runs, add `-x kerntable` before `"$@"` in `windows-font-fix.sh`.

## Updating and troubleshooting

To update, use the Plugin Manager and reload the Script menu. Preserve any local customizations first. If a manual copy of the `Plau` folder is still in the Scripts folder alongside the Plugin Manager install, remove one of them so scripts do not appear twice.

- **A script is missing:** check its location, `.py` extension, and first line. Active scripts use `#MenuTitle: …`. Reload the menu after moving or editing files.
- **The menu shows Plau → Plau:** move the inner folder’s contents one level up to match the structure above.
- **A source glyph is missing:** create it in the font, with usable outlines in each master, then rerun the tool.
- **A script fails:** copy the complete traceback from Glyphs’ scripting console and include the script name, Glyphs build, and steps that produced the error when reporting it.

See the [Glyphs scripting guide](https://glyphsapp.com/learn/scripting-glyphs-part-3) for background on script installation and menu headers.

## Contributing

Keep scripts in the appropriate category, use a `#MenuTitle:` header on the first line, and import Glyphs API objects explicitly. Test changes in Glyphs 4 on a copy of a font, including multiple masters and existing target glyphs. Describe which glyphs or metadata a script changes. Avoid adding editor autosave files.

## License

See [the GNU GPL v3 license included in this repository](Plau/LICENSE).
