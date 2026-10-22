#MenuTitle: Build Letters from Diacritic
# -*- coding: utf-8 -*-
# Description: From the selected diacritics, adds the Latin letters that use them (by language set) and, if it exists, the legacy spacing mark.

__doc__ = """
Select one or more diacritics (combining, e.g. acutecomb, or legacy, e.g. acute) and run. In the window, choose the Latin language sets (the same groups as Add Glyphs: Basic, Western European, Central European…).
Adds every letter of those sets that uses the diacritic (Aacute, aacute, Eacute…) as a composite of base + combining mark with automatic alignment, in all masters. Letters whose base glyph is missing are skipped and listed in the Macro Panel; letters that already have artwork are left alone.
Also, if the combining mark has a legacy spacing mark in the glyph data (acutecomb → acute), builds it as an auto-aligned component of the comb so it follows its metrics.
"""

import os
import plistlib

from Foundation import NSBundle
from GlyphsApp import Glyphs, GSGlyph, GSGlyphsInfo, GSComponent, Message
import vanilla

TITLE = "Build Letters from Diacritic"
SCRIPT_GROUP = "Latin"
DEFAULT_SETS = ("Basic", "Western European", "Central European", "South Eastern European", "South American")
COMB_SUFFIX = "comb"


# ===== Glyph data =====

def load_latin_sets():
    """{set name: [glyph names]} for the Latin language sets of Add Glyphs, in display order."""
    path = NSBundle.bundleForClass_(GSGlyphsInfo).pathForResource_ofType_("defaultLanguages", "plist")
    if not path or not os.path.exists(path):
        path = "/Applications/Glyphs 4.app/Contents/Frameworks/GlyphsCore.framework/Versions/A/Resources/defaultLanguages.plist"
    with open(path, "rb") as fh:
        groups = plistlib.load(fh)
    latin = next(g for g in groups if g.get("name") == SCRIPT_GROUP)
    return {sg["name"]: list(sg["list"]) for sg in latin["subGroup"] if sg.get("list") and not sg.get("hidden")}


def info_of(name):
    return Glyphs.glyphInfoForName(name)


def comb_name(name):
    """Combining mark for a diacritic name (acutecomb → acutecomb, acute → acutecomb), or None."""
    info = info_of(name)
    if info is None or info.category != "Mark":
        return None
    if info.subCategory == "Nonspacing":
        return name
    candidate = name + COMB_SUFFIX
    return candidate if info_of(candidate) is not None else None


def legacy_name(comb):
    """Legacy spacing mark of a combining mark in the glyph data (acutecomb → acute), or None."""
    if not comb.endswith(COMB_SUFFIX):
        return None
    base = comb[:-len(COMB_SUFFIX)]
    info = info_of(base)
    if info is not None and info.category == "Mark" and info.subCategory == "Spacing":
        return base
    return None


def parts(info):
    return [c for c in (info.components or [])]


def uses_mark(info, comb, depth=0):
    """True if the glyph decomposes into `comb`, directly or through a nested composite."""
    if info is None or depth > 4:
        return False
    for c in parts(info):
        if c.name == comb or uses_mark(c, comb, depth + 1):
            return True
    return False


def letters_using(comb, glyph_names):
    out = []
    for name in glyph_names:
        info = info_of(name)
        if info is not None and info.category == "Letter" and uses_mark(info, comb):
            out.append(name)
    return out


# ===== Building =====

def is_empty(glyph):
    return all(len(layer.shapes) == 0 for layer in glyph.layers if layer.isMasterLayer)


def build_letter(font, name):
    """Returns 'built', 'exists' or 'missing: a, b'."""
    existing = font.glyphs[name]
    if existing is not None and not is_empty(existing):
        return "exists"
    required = [c.name for c in parts(info_of(name))]
    missing = [r for r in required if font.glyphs[r] is None]
    if missing:
        return "missing: " + ", ".join(missing)
    glyph = existing
    if glyph is None:
        glyph = GSGlyph(name)
        font.glyphs.append(glyph)
    for layer in glyph.layers:
        if layer.isMasterLayer:
            layer.makeComponents()
    return "built"


def build_legacy(font, comb, legacy):
    """Make `legacy` an auto-aligned component of `comb`. Returns 'built', 'updated' or 'drawn'."""
    glyph = font.glyphs[legacy]
    created = glyph is None
    if created:
        glyph = GSGlyph(legacy)
        font.glyphs.append(glyph)
    for layer in glyph.layers:
        if not layer.isMasterLayer:
            continue
        comps = [s for s in layer.shapes if hasattr(s, "componentName") and s.componentName == comb]
        if layer.shapes and len(comps) != len(layer.shapes):
            return "drawn"
    glyph.leftMetricsKey = None
    glyph.rightMetricsKey = None
    for layer in glyph.layers:
        layer.leftMetricsKey = None
        layer.rightMetricsKey = None
        if not layer.isMasterLayer:
            continue
        if not layer.shapes:
            comp = GSComponent(comb)
            layer.shapes.append(comp)
            comp.automaticAlignment = True
        else:
            for s in layer.shapes:
                s.automaticAlignment = True
        layer.syncMetrics()
    return "built" if created else "updated"


def run(font, combs, set_names, latin_sets, with_letters=True, with_legacy=True):
    report = []
    missing_comb = [c for c in combs if font.glyphs[c] is None]
    combs = [c for c in combs if c not in missing_comb]
    for c in missing_comb:
        report.append("!! %s is not in the font: add it first." % c)

    font.disableUpdateInterface()
    try:
        for comb in combs:
            if with_letters:
                names = []
                for s in set_names:
                    for n in letters_using(comb, latin_sets[s]):
                        if n not in names:
                            names.append(n)
                counts = {"built": 0, "exists": 0, "missing": 0}
                skipped = []
                for n in names:
                    result = build_letter(font, n)
                    if result.startswith("missing"):
                        counts["missing"] += 1
                        skipped.append("%s (%s)" % (n, result))
                    else:
                        counts[result] += 1
                report.append("%s: %d letters built, %d already existed, %d skipped for a missing base." % (
                    comb, counts["built"], counts["exists"], counts["missing"]))
                for line in skipped:
                    report.append("     skipped %s" % line)
            if with_legacy:
                legacy = legacy_name(comb)
                if legacy is None:
                    report.append("%s: no legacy spacing mark in the glyph data." % comb)
                else:
                    result = build_legacy(font, comb, legacy)
                    if result == "drawn":
                        report.append("%s: %s already has other artwork, left alone." % (comb, legacy))
                    else:
                        report.append("%s: legacy %s %s as an auto-aligned component." % (comb, legacy, result))
    finally:
        font.enableUpdateInterface()
    return report


def selected_combs(font):
    combs, ignored = [], []
    for layer in font.selectedLayers:
        name = layer.parent.name
        comb = comb_name(name)
        if comb is None:
            ignored.append(name)
        elif comb not in combs:
            combs.append(comb)
    return combs, ignored


# ===== UI =====

class BuildLettersWindow(object):
    def __init__(self, font, combs, latin_sets):
        self.font = font
        self.combs = combs
        self.latin_sets = latin_sets
        self.names = list(latin_sets.keys())

        legacies = [legacy_name(c) for c in combs]
        legacies = [l for l in legacies if l]
        row = 22
        height = 96 + row * len(self.names) + 36 + 44
        self.w = vanilla.FloatingWindow((380, height), TITLE)

        y = 12
        self.w.marks = vanilla.TextBox((15, y, -15, 34), "Diacritics: " + ", ".join(combs), sizeStyle="small")
        y += 40
        self.w.setsLabel = vanilla.TextBox((15, y, -15, 18), "Language sets (letters that use the diacritic):")
        y += 24
        self.checks = []
        for name in self.names:
            letters = []
            for c in combs:
                for n in letters_using(c, latin_sets[name]):
                    if n not in letters:
                        letters.append(n)
            new = [n for n in letters if self.font.glyphs[n] is None]
            box = vanilla.CheckBox((20, y, -15, 20), "%s  (%d letters, %d new)" % (name, len(letters), len(new)),
                                   value=name in DEFAULT_SETS)
            box.getNSButton().setToolTip_("Adds the letters of the “%s” set that use the selected diacritic." % name)
            setattr(self.w, "set_%d" % len(self.checks), box)
            self.checks.append(box)
            y += row
        y += 8
        label = "Also build the legacy mark (%s)" % ", ".join(legacies) if legacies else "Legacy mark: none in the glyph data"
        self.w.legacy = vanilla.CheckBox((15, y, -15, 20), label, value=bool(legacies))
        self.w.legacy.enable(bool(legacies))
        self.w.legacy.getNSButton().setToolTip_("Builds the spacing version (e.g. acute) as an auto-aligned component of the combining mark.")
        y += 34
        self.w.build = vanilla.Button((-110, -34, -15, 22), "Build", callback=self.build)
        self.w.cancel = vanilla.Button((-200, -34, -120, 22), "Cancel", callback=self.cancel)
        self.w.setDefaultButton(self.w.build)
        self.w.open()
        self.w.makeKey()

    def chosen_sets(self):
        return [n for n, box in zip(self.names, self.checks) if box.get()]

    def build(self, sender):
        sets = self.chosen_sets()
        with_legacy = bool(self.w.legacy.get()) and bool(self.w.legacy.getNSButton().isEnabled())
        if not sets and not with_legacy:
            Message("Choose at least one language set or the legacy mark.", TITLE)
            return
        try:
            Glyphs.clearLog()
            report = run(self.font, self.combs, sets, self.latin_sets, with_letters=bool(sets), with_legacy=with_legacy)
        except Exception as e:
            Message(str(e), TITLE)
            return
        print("✅ " + TITLE)
        for line in report:
            print("   " + line)
        Glyphs.showNotification(TITLE, "Done. See the Macro Panel for the details.")
        Glyphs.showMacroWindow()
        self.w.close()

    def cancel(self, sender):
        self.w.close()


def main():
    font = Glyphs.font
    if not font:
        raise RuntimeError("Open a font before running this script.")
    combs, ignored = selected_combs(font)
    if not combs:
        raise RuntimeError("Select one or more diacritics (e.g. acutecomb or acute) in the font first.")
    if ignored:
        print("Ignored (not diacritics): " + ", ".join(ignored))
    BuildLettersWindow(font, combs, load_latin_sets())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Message(str(e), TITLE)
