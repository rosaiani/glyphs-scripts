#MenuTitle: Open Tab with G2 Nodes
# -*- coding: utf-8 -*-
# Description: Opens a new tab with every glyph that contains a G2 (star) node in any master or special layer.

__doc__ = """
Finds every glyph that has at least one G2 node (the "star" node of Glyphs 4, a curvature-continuous smooth connection) in any of its layers, and opens them all in a new Edit tab.
Only the glyph's own paths are checked, not paths inside components. Prints how many G2 nodes each glyph has.
"""

from GlyphsApp import Glyphs, GSSUPERSMOOTH, Message

TITLE = "Open Tab with G2 Nodes"


def g2_count(glyph):
    """Number of G2 nodes in the glyph, across all of its layers."""
    return sum(
        1
        for layer in glyph.layers
        for path in layer.paths
        for node in path.nodes
        if node.connection == GSSUPERSMOOTH
    )


def run():
    font = Glyphs.font
    if not font:
        Message("Open a font first.", TITLE)
        return

    found = [(g, n) for g in font.glyphs for n in [g2_count(g)] if n]
    if not found:
        Message("No glyph in this font contains a G2 node.", TITLE)
        return

    font.newTab("".join("/%s " % g.name for g, _ in found))
    print("✅ %s: %d glyph(s) with G2 nodes." % (TITLE, len(found)))
    for g, n in found:
        print("   %s: %d" % (g.name, n))


run()
