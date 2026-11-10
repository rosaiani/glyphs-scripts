#MenuTitle: Propagate G2 Nodes to All Masters
# -*- coding: utf-8 -*-
# Description: Turns the nodes that are G2 (star) nodes in the layer you are looking at into G2 nodes in all the other masters.

__doc__ = """
Copies the G2 nodes (the "star" nodes of Glyphs 4, connection type GSSUPERSMOOTH) of the selected layer of each selected glyph to the same nodes in every other master.
Nodes are matched by their position in the glyph (path number and node number), so a layer is only changed when it has the same paths, nodes and node types as the source layer; the others are skipped and listed.
Only turns nodes into G2 nodes; it never changes a G2 node back to smooth or sharp. Optionally includes special layers (brace, bracket, backups).
"""

import vanilla
from GlyphsApp import Glyphs, GSSUPERSMOOTH, Message

TITLE = "Propagate G2 Nodes to All Masters"


def signature(layer):
    """Structure of the layer's own paths: node types and open/closed state, in order."""
    return [(p.closed, [n.type for n in p.nodes]) for p in layer.paths]


def g2_indexes(layer):
    """[(path index, node index)] of the G2 nodes in the layer."""
    return [
        (pi, ni)
        for pi, path in enumerate(layer.paths)
        for ni, node in enumerate(path.nodes)
        if node.connection == GSSUPERSMOOTH
    ]


def targets():
    font = Glyphs.font
    if not font or not font.selectedLayers:
        raise RuntimeError("Open a glyph, or select glyphs, that have G2 nodes.")
    seen, out = set(), []
    for layer in font.selectedLayers:
        glyph = layer.parent
        if glyph.name not in seen:
            seen.add(glyph.name)
            out.append(layer)
    return out


def propagate(source, include_special):
    """Apply the source layer's G2 nodes to the glyph's other layers. Returns (nodes set, layers changed, skipped)."""
    indexes = g2_indexes(source)
    if not indexes:
        return 0, 0, []
    reference = signature(source)
    glyph = source.parent
    nodes_set, layers_changed, skipped = 0, 0, []
    glyph.beginUndo()
    try:
        for layer in glyph.layers:
            if layer is source or layer.layerId == source.layerId:
                continue
            if not (layer.isMasterLayer or (include_special and layer.isSpecialLayer)):
                continue
            if signature(layer) != reference:
                skipped.append(layer.name or layer.master.name)
                continue
            changed = 0
            for pi, ni in indexes:
                node = layer.paths[pi].nodes[ni]
                if node.connection != GSSUPERSMOOTH:
                    node.connection = GSSUPERSMOOTH
                    changed += 1
            if changed:
                nodes_set += changed
                layers_changed += 1
    finally:
        glyph.endUndo()
    return nodes_set, layers_changed, skipped


def run(include_special):
    total_nodes, total_glyphs = 0, 0
    skipped_report, without = [], []
    sources = targets()
    for source in sources:
        name = source.parent.name
        if not g2_indexes(source):
            without.append(name)
            continue
        nodes_set, layers_changed, skipped = propagate(source, include_special)
        total_nodes += nodes_set
        if layers_changed:
            total_glyphs += 1
        for layer_name in skipped:
            skipped_report.append("%s / %s" % (name, layer_name))
    print("✅ %s: %d node(s) made G2 in %d glyph(s)." % (TITLE, total_nodes, total_glyphs))
    if without:
        print("   No G2 nodes in the selected layer: " + ", ".join(without))
    if skipped_report:
        print("   Skipped (different paths or nodes than the source layer): " + ", ".join(skipped_report))
    if len(without) == len(sources):
        raise RuntimeError("The selected layer has no G2 nodes to propagate.")


class PropagateWindow(object):
    def __init__(self):
        self.w = vanilla.FloatingWindow((280, 96), TITLE)
        self.w.go = vanilla.Button((15, 14, -15, 24), "Propagate G2 Nodes", callback=self.go)
        self.w.go.getNSButton().setToolTip_("Makes the nodes that are G2 in the layer you are looking at G2 in all other masters.")
        self.w.special = vanilla.CheckBox((15, 50, -15, 20), "Include special layers", value=False)
        self.w.special.getNSButton().setToolTip_("Also updates brace, bracket and backup layers, not only the masters.")
        self.w.open()
        self.w.makeKey()

    def go(self, sender):
        try:
            run(bool(self.w.special.get()))
        except Exception as e:
            Message(str(e), TITLE)
            return
        self.w.close()


if __name__ == "__main__":
    PropagateWindow()
