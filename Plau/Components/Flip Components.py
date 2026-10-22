#MenuTitle: Flip Components
# -*- coding: utf-8 -*-
# Description: Flips the selected components (or all components of the selected glyphs) horizontally or vertically in all masters, each one around its own center.

__doc__ = """
Flips components horizontally or vertically in all masters at once, each one around the center of its own bounds, so it stays where it is and only its orientation changes.
Selected components are flipped; if no component is selected, all components of the selected glyphs are. Components are matched across masters by their order in the glyph.
Turns off automatic alignment on the flipped components. Running it twice restores the original. Optionally includes special layers (brace, bracket, backups).
"""

import vanilla
from GlyphsApp import Glyphs, GSComponent, Message

TITLE = "Flip Components"


def components_of(layer):
    return [s for s in layer.shapes if isinstance(s, GSComponent)]


def targets():
    """[(glyph, [component indexes or None for all])] from the selection in the current tab."""
    font = Glyphs.font
    if not font or not font.selectedLayers:
        raise RuntimeError("Open a glyph and select components, or select glyphs that contain components.")
    out = []
    for layer in font.selectedLayers:
        comps = components_of(layer)
        picked = [i for i, c in enumerate(comps) if c in layer.selection]
        out.append((layer.parent, picked or None))
    return out


def flip_layer(layer, indexes, horizontal, expected):
    comps = components_of(layer)
    names = [c.componentName for c in comps]
    if expected is not None and names != expected:
        return 0, False
    count = 0
    for i, comp in enumerate(comps):
        if indexes is not None and i not in indexes:
            continue
        b = comp.bounds
        cx = b.origin.x + b.size.width / 2.0
        cy = b.origin.y + b.size.height / 2.0
        comp.automaticAlignment = False
        if horizontal:
            comp.applyTransform((-1, 0, 0, 1, 2 * cx, 0))
        else:
            comp.applyTransform((1, 0, 0, -1, 0, 2 * cy))
        count += 1
    return count, True


def flip(horizontal, include_special):
    font = Glyphs.font
    done = 0
    mismatched = []
    seen = set()
    for glyph, indexes in targets():
        if glyph.name in seen:
            continue
        seen.add(glyph.name)
        reference = None
        for layer in glyph.layers:
            if layer.isMasterLayer and reference is None:
                reference = [c.componentName for c in components_of(layer)]
        glyph.beginUndo()
        try:
            for layer in glyph.layers:
                if not (layer.isMasterLayer or include_special):
                    continue
                n, ok = flip_layer(layer, indexes, horizontal, reference)
                done += n
                if not ok:
                    mismatched.append("%s / %s" % (glyph.name, layer.name or layer.master.name))
        finally:
            glyph.endUndo()
    axis = "horizontally" if horizontal else "vertically"
    print("✅ %s: %d components flipped %s in %d glyph(s)." % (TITLE, done, axis, len(seen)))
    if mismatched:
        print("   Skipped (different components than the first master): " + ", ".join(mismatched))
    if done == 0:
        raise RuntimeError("No components found to flip.")


class FlipWindow(object):
    def __init__(self):
        self.w = vanilla.FloatingWindow((260, 128), TITLE)
        self.w.horizontal = vanilla.Button((15, 14, -15, 24), "Flip Horizontally", callback=self.flipH)
        self.w.horizontal.getNSButton().setToolTip_("Mirrors each component left to right around its own center, in all masters.")
        self.w.vertical = vanilla.Button((15, 46, -15, 24), "Flip Vertically", callback=self.flipV)
        self.w.vertical.getNSButton().setToolTip_("Mirrors each component top to bottom around its own center, in all masters.")
        self.w.special = vanilla.CheckBox((15, 82, -15, 20), "Include special layers", value=False)
        self.w.special.getNSButton().setToolTip_("Also flips brace, bracket and backup layers, not only the masters.")
        self.w.open()
        self.w.makeKey()

    def run(self, horizontal):
        try:
            flip(horizontal, bool(self.w.special.get()))
        except Exception as e:
            Message(str(e), TITLE)
            return
        self.w.close()

    def flipH(self, sender):
        self.run(True)

    def flipV(self, sender):
        self.run(False)


if __name__ == "__main__":
    FlipWindow()
