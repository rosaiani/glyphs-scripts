#MenuTitle: Set Diacritics Sidebearings
# -*- coding: utf-8 -*-
# Description: Sets the metrics keys of every diacritic (category Mark) in the font: LSB = 40, RSB = | (same as the LSB).

__doc__ = """
Sets the sidebearing keys of every diacritic in the font (all glyphs with category Mark, spacing and combining): LSB =40 and RSB =| (equal to the LSB).
Keys are set on the glyph and synced on all its layers. Layer-level LSB/RSB keys are cleared so the glyph keys apply.
Edit LSB_KEY and RSB_KEY at the top of the script to use other values. Overwrites existing keys on those glyphs.
"""

from GlyphsApp import Glyphs, Message

TITLE = "Set Diacritics Sidebearings"
LSB_KEY = "=40"
RSB_KEY = "=|"


def main():
    font = Glyphs.font
    if not font:
        raise RuntimeError("Open a font before running this script.")

    marks = [g for g in font.glyphs if g.category == "Mark"]
    if not marks:
        raise RuntimeError("No diacritics (category Mark) found in this font.")

    font.disableUpdateInterface()
    try:
        for glyph in marks:
            glyph.leftMetricsKey = LSB_KEY
            glyph.rightMetricsKey = RSB_KEY
            for layer in glyph.layers:
                # a layer-level key would override the glyph-level one
                if layer.leftMetricsKey:
                    layer.leftMetricsKey = None
                if layer.rightMetricsKey:
                    layer.rightMetricsKey = None
                layer.syncMetrics()
    finally:
        font.enableUpdateInterface()

    print("✅ %s: LSB %s, RSB %s on %d diacritics." % (TITLE, LSB_KEY, RSB_KEY, len(marks)))
    Glyphs.showNotification(TITLE, "%d diacritics updated (LSB %s, RSB %s)." % (len(marks), LSB_KEY, RSB_KEY))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Message(str(e), TITLE)
