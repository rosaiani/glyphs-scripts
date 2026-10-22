#MenuTitle: Set Diacritics Sidebearings
# -*- coding: utf-8 -*-
# Description: Combining marks get LSB = 40 and RSB = |. Legacy (spacing) marks become auto-aligned components of their combining mark and follow its metrics.

__doc__ = """
Combining diacritics (category Mark, nonspacing; e.g. acutecomb): sets LSB =40 and RSB =| (equal to the LSB) on the glyph and syncs all layers.
Legacy diacritics (spacing marks; e.g. acute): no keys of their own. Each one is an auto-aligned component of its combining mark (name + "comb"), so it follows the comb's metrics.
Legacy glyphs that already hold that component just get auto alignment turned on and their keys cleared. Empty ones are built from the comb. Legacy glyphs with other artwork are left alone and listed in the Macro Panel.
Overwrites existing LSB/RSB keys on these glyphs. Edit the settings at the top of the script to change the values.
"""

from GlyphsApp import Glyphs, GSComponent, Message

TITLE = "Set Diacritics Sidebearings"
LSB_KEY = "=40"
RSB_KEY = "=|"
COMB_SUFFIX = "comb"        # legacy "acute" follows "acutecomb"
REPLACE_DRAWN = False       # True = also rebuild legacy glyphs that have other artwork as a comb component


def clear_keys(glyph):
    glyph.leftMetricsKey = None
    glyph.rightMetricsKey = None
    for layer in glyph.layers:
        layer.leftMetricsKey = None
        layer.rightMetricsKey = None


def sync(glyph):
    for layer in glyph.layers:
        layer.syncMetrics()


def set_comb(glyph):
    glyph.leftMetricsKey = LSB_KEY
    glyph.rightMetricsKey = RSB_KEY
    for layer in glyph.layers:
        # a layer-level key would override the glyph-level one
        layer.leftMetricsKey = None
        layer.rightMetricsKey = None
    sync(glyph)


def is_drawn(glyph, comb_name):
    """True if a master layer holds artwork other than the comb component."""
    for layer in glyph.layers:
        if layer.isMasterLayer and any(
            not (hasattr(s, "componentName") and s.componentName == comb_name) for s in layer.shapes
        ):
            return True
    return False


def follow_comb(glyph, comb_name):
    """Make the legacy glyph an auto-aligned component of its comb on every master layer."""
    clear_keys(glyph)
    for layer in glyph.layers:
        comps = [c for c in layer.components if c.componentName == comb_name]
        if comps and len(comps) == len(layer.shapes):
            for c in comps:
                c.automaticAlignment = True
        elif layer.isMasterLayer:
            layer.shapes = []
            comp = GSComponent(comb_name)
            layer.shapes.append(comp)
            comp.automaticAlignment = True
    sync(glyph)


def main():
    font = Glyphs.font
    if not font:
        raise RuntimeError("Open a font before running this script.")

    marks = [g for g in font.glyphs if g.category == "Mark"]
    if not marks:
        raise RuntimeError("No diacritics (category Mark) found in this font.")

    combs, legacy, no_comb = [], [], []
    for g in marks:
        if g.subCategory == "Spacing":
            if font.glyphs[g.name + COMB_SUFFIX] is not None:
                legacy.append(g)
            else:
                no_comb.append(g.name)
        else:
            combs.append(g)

    drawn = [g.name for g in legacy if not REPLACE_DRAWN and is_drawn(g, g.name + COMB_SUFFIX)]
    done = [g for g in legacy if g.name not in drawn]
    font.disableUpdateInterface()
    try:
        for g in combs:
            set_comb(g)
        # combs first, so the legacy glyphs read their final metrics
        for g in done:
            follow_comb(g, g.name + COMB_SUFFIX)
    finally:
        font.enableUpdateInterface()

    print("✅ %s: %d combining marks → LSB %s, RSB %s." % (TITLE, len(combs), LSB_KEY, RSB_KEY))
    print("   %d legacy marks follow their comb (auto-aligned components)." % len(done))
    if drawn:
        print("   Left alone (other artwork; set REPLACE_DRAWN = True to rebuild): %s" % ", ".join(sorted(drawn)))
    if no_comb:
        print("   Legacy marks without a '%s' glyph, untouched: %s" % (COMB_SUFFIX, ", ".join(no_comb)))
    Glyphs.showNotification(TITLE, "%d combining, %d legacy marks updated." % (len(combs), len(done)))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Message(str(e), TITLE)
