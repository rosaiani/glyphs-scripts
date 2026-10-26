#MenuTitle: Windows Font Fix
# -*- coding: utf-8 -*-
# Description: Fixes exported TTF/OTF files so Microsoft Office (PowerPoint, Word) applies their OpenType substitutions: empty fvar, latn script record, and calt that also runs the rclt lookups. Also runs from the command line as a Glyphs Post-Export Command.

__doc__ = """
Fixes exported TTF/OTF files so Microsoft Office (PowerPoint, Word) shapes them with its full OpenType engine and applies their substitutions.
Four fixes: an empty fvar table (winfix), a latn script record copied from DFLT in GSUB/GPOS, calt that also runs every rclt lookup (shared, not copied), and a legacy kern table built from the GPOS kerning (PowerPoint applies the legacy table more reliably than the GPOS kern feature).
From the menu: choose the fixes, then the exported fonts. Copies go into a "Windows Fix" folder next to each font unless you choose to overwrite.
Web fonts (woff, woff2) are never touched, and real variable fonts keep their fvar.
Also runs from the command line, as a Post-Export Command: python3 "Windows Font Fix.py" font.ttf
"""

import copy
import os
import sys

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import _f_v_a_r
from fontTools.ttLib.tables import _k_e_r_n
from fontTools.ttLib.tables import otTables as ot

TITLE = "Windows Font Fix"
FONT_EXTENSIONS = (".ttf", ".otf")
WEB_EXTENSIONS = (".woff", ".woff2")
COPY_FOLDER = "Windows Fix"
DEFAULTS_PREFIX = "com.plau.windowsFontFix."  # where the menu window remembers its choices (Glyphs.defaults)
NO_REQUIRED_FEATURE = 0xFFFF
KERN_MAX_PAIRS = 10920  # a kern subtable stores its length in 16 bits: 6 bytes per pair
# Characters outside Latin-1 that are common in running text: quotes, dashes, bullet, ellipsis, euro.
COMMON_PUNCTUATION = {0x2013, 0x2014, 0x2018, 0x2019, 0x201A, 0x201C, 0x201D, 0x201E, 0x2022, 0x2026, 0x2039, 0x203A, 0x20AC}

# Steps run when none are chosen (this is also what a Post-Export Command runs).
DEFAULT_STEPS = ["winfix", "latn", "rclt2calt", "kerntable"]

USAGE = """
Windows Font Fix: fixes for exported TTF/OTF fonts, in place (or into --out).
Runs from the command line or as a Glyphs "Post-Export Command"
(the exported font's path is passed as the first argument).

Usage:
    python3 "Windows Font Fix.py" [options] font1.ttf font2.otf folder/ ...

Steps (all on by default):
    winfix      Add an empty fvar table, so Microsoft Office (PowerPoint, Word)
                shapes the font with its full OpenType engine and applies GSUB.
    latn        Add a 'latn' script record to GSUB/GPOS (a copy of DFLT) if missing.
    rclt2calt   Make 'calt' also reference every 'rclt' lookup (shared, not copied),
                for apps that apply calt but not rclt. rclt stays as it is.
    kerntable   Build a legacy 'kern' table from the GPOS 'kern' feature (class pairs are
                expanded to glyph pairs; at most 10920 pairs: pairs between the most common
                characters are kept first, ASCII, then Latin-1 and common punctuation).
                PowerPoint applies this table more reliably than GPOS kerning.
                Skipped for variable fonts and fonts that already have a kern table.
                The GPOS table is not touched.

Options:
    -s, --steps a,b,c   Run only these steps (e.g. -s latn,rclt2calt)
    -x, --skip a,b      Skip these steps
    -o, --out DIR       Save fixed fonts into DIR instead of overwriting
    -n, --dry-run       Report what would change, save nothing
    -r, --report        Print scripts, features and lookups of each font, change nothing
    -f, --force         winfix / kerntable: replace an existing fvar / kern table (careful with variable fonts)
    -h, --help          Show this help and exit

Web fonts (.woff, .woff2) are never touched. Needs fontTools: pip3 install fonttools
"""


# ===== Steps =====

def step_winfix(font, force=False):
    """Empty fvar: Office then routes the font through its full shaping path."""
    if "fvar" in font and not force:
        if font["fvar"].axes:
            return "skipped: real variable font (fvar has axes)"
        return "skipped: fvar already present"
    fvar = _f_v_a_r.table__f_v_a_r()
    fvar.axes = []
    fvar.instances = []
    font["fvar"] = fvar
    return "added empty fvar"


def _add_latn(table):
    script_list = table.ScriptList
    if script_list is None or not script_list.ScriptRecord:
        return False
    tags = [sr.ScriptTag for sr in script_list.ScriptRecord]
    if "latn" in tags or "DFLT" not in tags:
        return False
    dflt = script_list.ScriptRecord[tags.index("DFLT")]
    record = ot.ScriptRecord()
    record.ScriptTag = "latn"
    record.Script = copy.deepcopy(dflt.Script)
    script_list.ScriptRecord.append(record)
    script_list.ScriptRecord.sort(key=lambda r: r.ScriptTag)
    script_list.ScriptCount = len(script_list.ScriptRecord)
    return True


def step_latn(font, force=False):
    done = [tag for tag in ("GSUB", "GPOS") if tag in font and _add_latn(font[tag].table)]
    return "added latn to %s" % ", ".join(done) if done else "skipped: latn present (or no DFLT)"


def _lang_systems(script):
    systems = [script.DefaultLangSys] if script.DefaultLangSys else []
    return systems + [lr.LangSys for lr in script.LangSysRecord]


def step_rclt2calt(font, force=False):
    if "GSUB" not in font:
        return "skipped: no GSUB"
    gsub = font["GSUB"].table
    if not gsub.FeatureList:
        return "skipped: no features"
    records = gsub.FeatureList.FeatureRecord
    rclt_lookups = sorted({i for fr in records if fr.FeatureTag == "rclt" for i in fr.Feature.LookupListIndex})
    if not rclt_lookups:
        return "skipped: no rclt"
    calt_records = [fr for fr in records if fr.FeatureTag == "calt"]
    if calt_records:
        changed = False
        for fr in calt_records:
            merged = sorted(set(fr.Feature.LookupListIndex) | set(rclt_lookups))
            if merged != sorted(fr.Feature.LookupListIndex):
                fr.Feature.LookupListIndex = merged
                fr.Feature.LookupCount = len(merged)
                changed = True
        return ("calt now also runs rclt lookups %s" % rclt_lookups) if changed else "skipped: calt already has rclt lookups"
    # no calt yet: create one and register it wherever rclt is registered
    feature = ot.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = rclt_lookups
    feature.LookupCount = len(rclt_lookups)
    record = ot.FeatureRecord()
    record.FeatureTag = "calt"
    record.Feature = feature
    rclt_indices = {i for i, fr in enumerate(records) if fr.FeatureTag == "rclt"}
    records.append(record)
    new_index = len(records) - 1
    for sr in gsub.ScriptList.ScriptRecord:
        for ls in _lang_systems(sr.Script):
            if rclt_indices & set(ls.FeatureIndex):
                ls.FeatureIndex.append(new_index)
                ls.FeatureCount = len(ls.FeatureIndex)
    # OpenType wants FeatureRecords sorted by tag: re-sort and remap every index that points at them
    order = sorted(range(len(records)), key=lambda i: records[i].FeatureTag)
    remap = {old: new for new, old in enumerate(order)}
    gsub.FeatureList.FeatureRecord = [records[i] for i in order]
    gsub.FeatureList.FeatureCount = len(order)
    for sr in gsub.ScriptList.ScriptRecord:
        for ls in _lang_systems(sr.Script):
            ls.FeatureIndex = sorted(remap[i] for i in ls.FeatureIndex)
            if getattr(ls, "ReqFeatureIndex", NO_REQUIRED_FEATURE) != NO_REQUIRED_FEATURE:
                ls.ReqFeatureIndex = remap[ls.ReqFeatureIndex]
    return "created calt with rclt lookups %s" % rclt_lookups


def _pair_subtables(lookup):
    """PairPos subtables of a GPOS lookup, unwrapping extension lookups."""
    for subtable in lookup.SubTable:
        real = getattr(subtable, "ExtSubTable", subtable)
        if getattr(real, "LookupType", None) == 2:
            yield real


def _x_advance(value):
    return int(getattr(value, "XAdvance", 0) or 0) if value is not None else 0


def gpos_kern_pairs(font):
    """{(left glyph, right glyph): value} from the lookups of the GPOS 'kern' feature.
    Class pairs are expanded to glyph pairs; inside a lookup the first matching subtable wins and
    several lookups add up, as in shaping. Pairs with 'any other glyph' (class 0) cannot be expanded and are ignored."""
    gpos = font["GPOS"].table
    if not gpos.FeatureList or not gpos.LookupList:
        return {}
    lookup_indices = sorted({i for fr in gpos.FeatureList.FeatureRecord if fr.FeatureTag == "kern" for i in fr.Feature.LookupListIndex})
    totals = {}
    for index in lookup_indices:
        seen = set()
        for subtable in _pair_subtables(gpos.LookupList.Lookup[index]):
            if subtable.Format == 1:
                for left, pair_set in zip(subtable.Coverage.glyphs, subtable.PairSet):
                    for record in pair_set.PairValueRecord:
                        key = (left, record.SecondGlyph)
                        if key not in seen:
                            seen.add(key)
                            totals[key] = totals.get(key, 0) + _x_advance(record.Value1)
            elif subtable.Format == 2:
                left_classes = subtable.ClassDef1.classDefs if subtable.ClassDef1 else {}
                members = {}
                for glyph, cls in (subtable.ClassDef2.classDefs if subtable.ClassDef2 else {}).items():
                    members.setdefault(cls, []).append(glyph)
                for left in subtable.Coverage.glyphs:
                    row = subtable.Class1Record[left_classes.get(left, 0)]
                    for cls, record in enumerate(row.Class2Record):
                        if cls == 0:
                            continue
                        value = _x_advance(record.Value1)
                        for right in members.get(cls, ()):
                            key = (left, right)
                            if key not in seen:
                                seen.add(key)
                                totals[key] = totals.get(key, 0) + value
    return totals


def _character_tier(codepoint):
    """How common a character is in running text: 0 ASCII, 1 Latin-1 and common punctuation, 2 other Latin and punctuation, 3 the rest."""
    if codepoint is None:
        return 3
    if 0x20 <= codepoint <= 0x7E:
        return 0
    if 0xA0 <= codepoint <= 0xFF or codepoint in COMMON_PUNCTUATION:
        return 1
    if 0x100 <= codepoint <= 0x24F or 0x2010 <= codepoint <= 0x206F or 0x20A0 <= codepoint <= 0x20CF:
        return 2
    return 3


def _best_cmap(font):
    """The font's best cmap. When the cmap is still untouched, it is read through a temporary table, so the font
    does not recompile (and rewrite) its cmap when saved."""
    reader = getattr(font, "reader", None)
    if reader is not None and "cmap" in reader.tables and "cmap" not in font.tables:
        table = newTable("cmap")
        table.decompile(reader["cmap"], font)
        return table.getBestCmap()
    return font.getBestCmap()


def rank_kern_pairs(font, pairs):
    """Pairs sorted by how likely they are to occur in text (most useful first), then by strength.
    A class kerning font easily expands to 50,000+ glyph pairs, far more than a kern table holds: keeping
    the strongest pairs would favor rare accented capitals, so the pairs between common characters go first."""
    first_codepoint = {}
    for codepoint, glyph in sorted(_best_cmap(font).items()):
        first_codepoint.setdefault(glyph, codepoint)
    tier = lambda glyph: _character_tier(first_codepoint.get(glyph))
    return sorted(pairs.items(), key=lambda item: (
        max(tier(item[0][0]), tier(item[0][1])), tier(item[0][0]) + tier(item[0][1]), -abs(item[1]), item[0]))


def step_kerntable(font, force=False):
    if "fvar" in font and font["fvar"].axes:
        return "skipped: variable font (a kern table cannot vary)"
    if "kern" in font and not force:
        return "skipped: kern table already present"
    if "GPOS" not in font:
        return "skipped: no GPOS"
    pairs = {k: max(-32768, min(32767, v)) for k, v in gpos_kern_pairs(font).items() if v}
    if not pairs:
        return "skipped: no kerning in GPOS"
    dropped = 0
    if len(pairs) > KERN_MAX_PAIRS:
        dropped = len(pairs) - KERN_MAX_PAIRS
        pairs = dict(rank_kern_pairs(font, pairs)[:KERN_MAX_PAIRS])
    subtable = _k_e_r_n.KernTable_format_0()
    subtable.coverage = 1  # horizontal
    subtable.tupleIndex = None
    subtable.kernTable = pairs
    table = newTable("kern")
    table.version = 0
    table.kernTables = [subtable]
    font["kern"] = table
    note = ", dropped %d rarer pairs (the table holds %d)" % (dropped, KERN_MAX_PAIRS) if dropped else ""
    return "added kern table with %d pairs%s" % (len(pairs), note)


STEPS = {
    "winfix": step_winfix,
    "latn": step_latn,
    "rclt2calt": step_rclt2calt,
    "kerntable": step_kerntable,
}


# ===== Report =====

def report(font, path):
    print("\n📄 %s" % os.path.basename(path))
    names = font["name"]
    print("   %s · %s" % (names.getDebugName(4), names.getDebugName(5)))
    print("   fvar: %s" % ("yes (%d axes)" % len(font["fvar"].axes) if "fvar" in font else "no"))
    for tag in ("GSUB", "GPOS"):
        if tag not in font or not font[tag].table.FeatureList:
            continue
        table = font[tag].table
        records = table.FeatureList.FeatureRecord
        for sr in table.ScriptList.ScriptRecord:
            ls = sr.Script.DefaultLangSys
            feats = [records[i].FeatureTag for i in ls.FeatureIndex] if ls else []
            print("   %s %s: %s" % (tag, sr.ScriptTag, " ".join(feats)))
        for fr in records:
            print("      %s: lookups %s" % (fr.FeatureTag, list(fr.Feature.LookupListIndex)))


# ===== Running =====

def collect_fonts(args):
    """(fonts to fix, web fonts left alone, other ignored arguments)."""
    fonts, web, ignored = [], [], []
    for arg in args:
        if os.path.isdir(arg):
            for name in sorted(os.listdir(arg)):
                full = os.path.join(arg, name)
                if name.lower().endswith(FONT_EXTENSIONS):
                    fonts.append(full)
                elif name.lower().endswith(WEB_EXTENSIONS):
                    web.append(full)
        elif arg.lower().endswith(FONT_EXTENSIONS):
            fonts.append(arg)
        elif arg.lower().endswith(WEB_EXTENSIONS):
            web.append(arg)
        else:
            ignored.append(arg)
    return fonts, web, ignored


def process(paths, steps, out_dir=None, dry_run=False, report_only=False, force=False):
    """Fix (or report on) the given TTF/OTF paths. Returns the number of errors."""
    errors = 0
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    for path in paths:
        try:
            font = TTFont(path, recalcTimestamp=False)  # leave head.modified as exported
            if report_only:
                report(font, path)
                continue
            print("\n🔧 %s" % os.path.basename(path))
            for name in steps:
                print("   %s: %s" % (name, STEPS[name](font, force=force)))
            if dry_run:
                print("   (dry run, not saved)")
                continue
            target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
            font.save(target)
            print("✅ saved %s" % target)
        except Exception as e:
            errors += 1
            print("‼️ error processing %s: %s" % (path, e))
    return errors


def parse_list(value):
    return [s.strip() for s in value.split(",") if s.strip()]


def main_cli(args):
    if not args or "-h" in args or "--help" in args:
        print(USAGE)
        return 0
    steps, skip, out_dir = list(DEFAULT_STEPS), [], None
    dry_run = report_only = force = False
    files = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-s", "--steps"):
            i += 1
            steps = parse_list(args[i])
        elif a in ("-x", "--skip"):
            i += 1
            skip = parse_list(args[i])
        elif a in ("-o", "--out"):
            i += 1
            out_dir = args[i]
        elif a in ("-n", "--dry-run"):
            dry_run = True
        elif a in ("-r", "--report"):
            report_only = True
        elif a in ("-f", "--force"):
            force = True
        else:
            files.append(a)
        i += 1

    unknown = [s for s in steps + skip if s not in STEPS]
    if unknown:
        print("‼️ unknown step(s): %s. Available: %s" % (", ".join(unknown), ", ".join(STEPS)))
        return 1
    steps = [s for s in steps if s not in skip]

    fonts, web, ignored = collect_fonts(files)
    for path in web:
        print("🌐 web font, left untouched: %s" % os.path.basename(path))
    for arg in ignored:
        print("⚠️  not a font or folder, ignored: %s" % arg)
    if not fonts:
        # only web fonts: nothing to do, and that is not an error for a Post-Export Command
        if web:
            return 0
        print("‼️ no fonts given")
        return 1
    return 1 if process(fonts, steps, out_dir, dry_run, report_only, force) else 0


# ===== Glyphs menu =====

def main_glyphs():
    import vanilla
    from vanilla.dialogs import getFile
    from GlyphsApp import Glyphs

    class WindowsFontFixWindow(object):
        def __init__(self):
            self.w = vanilla.FloatingWindow((380, 294), TITLE)
            self.w.intro = vanilla.TextBox(
                (15, 12, -15, 34),
                "Fixes exported TTF/OTF files so PowerPoint and Word apply their OpenType substitutions.",
                sizeStyle="small")
            y = 54
            self.boxes = {}
            labels = (
                ("winfix", "Empty fvar (Office full shaping)", "Adds an empty fvar table so Microsoft Office shapes the font with its full OpenType engine. Skipped for real variable fonts."),
                ("latn", "Add latn script record", "Copies the DFLT script of GSUB/GPOS into a latn record when there is none."),
                ("rclt2calt", "calt also runs the rclt lookups", "Makes calt reference every rclt lookup (shared, not copied), for apps that apply calt but not rclt."),
                ("kerntable", "Kerning for PowerPoint (legacy kern table)", "Builds a legacy kern table from the GPOS kerning: PowerPoint ignores GPOS kerning but applies this table. It holds at most 10,920 pairs, so the pairs between the most common characters go first. Skipped for variable fonts. GPOS is not touched. Untick it if you do not want a kern table."),
            )
            for key, label, tip in labels:
                box = vanilla.CheckBox((15, y, -15, 20), label, value=self.stored(key, True), callback=self.remember)
                box.getNSButton().setToolTip_(tip)
                setattr(self.w, "step_" + key, box)
                self.boxes[key] = box
                y += 24
            y += 8
            self.w.saveLabel = vanilla.TextBox((15, y, -15, 18), "Save:")
            y += 22
            self.w.mode = vanilla.RadioGroup(
                (15, y, -15, 40), ["Copies in a “%s” folder next to each font" % COPY_FOLDER, "Overwrite the originals"], callback=self.remember)
            self.w.mode.set(1 if self.stored("overwrite", False) else 0)
            y += 52
            self.w.report = vanilla.Button((15, y, 110, 22), "Report…", callback=self.report)
            self.w.report.getNSButton().setToolTip_("Prints scripts, features and lookups of the fonts you choose. Changes nothing.")
            self.w.fix = vanilla.Button((-125, y, -15, 22), "Fix Fonts…", callback=self.fix)
            self.w.fix.getNSButton().setToolTip_("Choose exported TTF/OTF files and apply the checked fixes. Web fonts are never touched.")
            self.w.setDefaultButton(self.w.fix)
            self.w.open()
            self.w.makeKey()

        @staticmethod
        def stored(key, default):
            value = Glyphs.defaults[DEFAULTS_PREFIX + key]
            return default if value is None else bool(value)

        def remember(self, sender):
            """Keep the choices for the next time the window opens."""
            for key, box in self.boxes.items():
                Glyphs.defaults[DEFAULTS_PREFIX + key] = bool(box.get())
            Glyphs.defaults[DEFAULTS_PREFIX + "overwrite"] = self.w.mode.get() == 1

        def chosen_steps(self):
            return [k for k in DEFAULT_STEPS if self.boxes[k].get()]

        def choose(self, message):
            paths = getFile(messageText=message, allowsMultipleSelection=True,
                            fileTypes=[e.lstrip(".") for e in FONT_EXTENSIONS])
            return list(paths or [])

        def report(self, sender):
            paths = self.choose("Choose the fonts to report on")
            if paths:
                Glyphs.clearLog()
                process(paths, [], report_only=True)
                Glyphs.showMacroWindow()

        def fix(self, sender):
            steps = self.chosen_steps()
            if not steps:
                from GlyphsApp import Message
                Message("Choose at least one fix.", TITLE)
                return
            paths = self.choose("Choose the exported fonts to fix")
            if not paths:
                return
            Glyphs.clearLog()
            overwrite = self.w.mode.get() == 1
            errors = 0
            by_folder = {}
            for p in paths:
                by_folder.setdefault(os.path.dirname(p), []).append(p)
            for folder, group in by_folder.items():
                errors += process(group, steps, None if overwrite else os.path.join(folder, COPY_FOLDER))
            Glyphs.showMacroWindow()
            Glyphs.showNotification(TITLE, "Done%s. See the Macro Panel." % (" with errors" if errors else ""))

    return WindowsFontFixWindow()


if __name__ == "__main__":
    try:
        from GlyphsApp import Glyphs  # only importable inside Glyphs
        in_glyphs = True
    except ImportError:
        in_glyphs = False
    if in_glyphs:
        main_glyphs()
    else:
        sys.exit(main_cli(sys.argv[1:]))
