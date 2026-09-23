# Plau Glyphs Scripts

Python tools for everyday type design work at Plau: building glyphs, positioning components, and setting up font metadata. Created by Rodrigo Saiani with assistance from ChatGPT.

## Requirements

- macOS and Glyphs 4.
- Python scripting support in Glyphs.
- The `vanilla` UI library for Arrow Maker, Center Components, and the metadata preset. If an import fails, check the Python modules available through Glyphs’ Plugin Manager.

Run these scripts **inside Glyphs**, not from Terminal. Basic Math uses the Glyphs 4 API; compatibility with Glyphs 3 is not guaranteed. Menu visibility and Python syntax have been checked, but the collection has not been fully tested across fonts and Glyphs builds. Some dialogs and messages are in Portuguese.

## Installation

1. Download or clone this repository.
2. In Glyphs 4, choose **Script → Open Scripts Folder**.
3. Copy the repository’s **`Plau` folder** into that folder. Keep its subfolders intact. Do not copy the entire repository into another folder named Plau.
4. Omit files ending in **`(autosave).py`**: these are saved copies, not additional tools.
5. Hold **Option** while opening the Script menu and choose **Reload Scripts**. If necessary, restart Glyphs.

The installed structure should look like this:

```text
Scripts/
└── Plau/
    ├── Build Glyphs/
    │   ├── Arrow Maker.py
    │   ├── Build Basic Math G4.py
    │   ├── Build Period Glyphs.py
    │   └── Dashes From Hyphen.py
    ├── Components/
    │   └── Vertically Center Component.py
    └── Font Info/
        └── Font Info Launch.py
```

The usual scripts location is `~/Library/Application Support/Glyphs 4/Scripts/`. Using **Open Scripts Folder** ensures you install into the folder your app uses.

After installation, the tools appear under **Script → Plau**. Menu labels may differ from filenames.

## Using the scripts

Open a font, save a copy, and choose a tool from the menu. Glyph builders generally operate on every master of the current font. Review the generated shapes, spacing, and interpolation before using them in production.

| Menu item | Source glyphs or selection | What it does |
| --- | --- | --- |
| **Build Basic Math G4** | `n`, `hyphen`, `dotaccentcomb`, and `figurespace` or `zero` | Builds `plus`, `minus`, `equal`, `multiply`, `divide`, `logicalnot`, `greater`, `less`, `greaterequal`, and `lessequal`. |
| **Build En and Em Dashes from Hyphen** | `hyphen` | Rebuilds `endash` and `emdash` with horizontally scaled hyphen components. Default widths are 140% and 180% of the hyphen advance width, with sidebearing keys referencing hyphen. |
| **Build Periodcentered and Bullet** | `period` | Rebuilds `periodcentered` and `bullet` from period components. Bullet defaults to 1.4× scale; both use period-based sidebearing keys. |
| **Build Arrows from Hyphen** | `hyphen`; optionally `emdash` | Opens controls for arrow selection, proportions, and handling existing glyphs. This builder is experimental; inspect direction and geometry carefully. |
| **Center Components in Reference Height** | Selected glyphs containing components | Opens controls for vertical positioning relative to cap height, x-height, or layer height, on current or all layers. Disables automatic alignment on moved components. |
| **Preset Plau - Fill Metadata** | An open font and a client name | Sets the family name to the client name, fills Plau credits, URLs, vendor ID and copyright, and resets the version to **0.000**. |

### Basic Math behavior

- Each master uses the width of `figurespace` if that glyph exists; otherwise it uses `zero`. The width must be positive. `zero.tf` is not required.
- Empty master layers are filled. Existing artwork is kept for most symbols, but all symbol master layers receive the chosen width and are centered horizontally without scaling.
- **`less` and `lessequal` are rebuilt on every run**, replacing their master-layer artwork with horizontally mirrored components of `greater` and `greaterequal`.
- Editing the source shapes updates their mirrored counterparts. Rerun the script after changing spacing-source widths to apply the new widths and reflection positions.

### Existing glyphs

Dashes and Periodcentered/Bullet replace their target master-layer content. The metadata preset overwrites the fields listed above. In Arrow Maker, the option labeled **“Ask (backup then replace)” currently does not show a confirmation dialog**; it backs up and replaces. Use a saved font copy when trying these tools.

## Updating and troubleshooting

To update, replace the installed scripts with their newer versions and reload the Script menu. Preserve any local customizations first.

- **A script is missing:** check its location, `.py` extension, and first line. Active scripts use `#MenuTitle: …`. Reload the menu after moving or editing files.
- **The menu shows Plau → Plau:** move the inner folder’s contents one level up to match the structure above.
- **A source glyph is missing:** create it in the font, with usable outlines in each master, then rerun the tool.
- **A script fails:** copy the complete traceback from Glyphs’ scripting console and include the script name, Glyphs build, and steps that produced the error when reporting it.

See the [Glyphs scripting guide](https://glyphsapp.com/learn/scripting-glyphs-part-3) for background on script installation and menu headers.

## Contributing

Keep scripts in the appropriate category, use a `#MenuTitle:` header on the first line, and import Glyphs API objects explicitly. Test changes in Glyphs 4 on a copy of a font, including multiple masters and existing target glyphs. Describe which glyphs or metadata a script changes. Avoid adding editor autosave files.

## License

See [the GNU GPL v3 license included in this repository](Plau/LICENSE).
