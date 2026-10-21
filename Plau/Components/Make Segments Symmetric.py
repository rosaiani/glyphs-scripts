#MenuTitle: Make Segments Symmetric
# -*- coding: utf-8 -*-
# Description: Select 4 segments (2 on the left, 2 on the right of the glyph's center, e.g. the four diagonal edges of a V) and run. Each left segment is mirrored with its right counterpart across the vertical axis at width/2; both end up as exact mirror images (averaged), so left and right bars sit at the same distance from the axis and the same height.

__doc__ = """
Select 4 segments (2 left and 2 right of the glyph's center, e.g. the four diagonal edges of a V) and run.
Each left segment is mirrored with its right counterpart across the vertical axis at width/2 and both end up as exact mirror images (averaged).
"""

import math
from GlyphsApp import Glyphs, Message, GSOFFCURVE

TITLE = "Make Segments Symmetric"


def next_oncurve(path, node):
    """Next on-curve node after `node`, skipping off-curve handles."""
    nodes = path.nodes
    i = nodes.index(node)
    for step in range(1, len(nodes)):
        n = nodes[(i + step) % len(nodes)]
        if n.type != GSOFFCURVE:
            return n
    return None


def selected_segments(layer):
    """Pairs of consecutive selected on-curve nodes (one pair = one segment)."""
    selection = [n for n in layer.selection if hasattr(n, "type") and n.type != GSOFFCURVE]
    segments = []
    for path in layer.paths:
        for node in path.nodes:
            if node not in selection:
                continue
            nxt = next_oncurve(path, node)
            if nxt is not None and nxt is not node and nxt in selection:
                segments.append((path, node, nxt))
    return segments


def seg_length(seg):
    _, a, b = seg
    return math.hypot(b.position.x - a.position.x, b.position.y - a.position.y)


def move_with_handles(path, node, new_pos):
    dx = new_pos[0] - node.position.x
    dy = new_pos[1] - node.position.y
    nodes = path.nodes
    i = nodes.index(node)
    for neighbor in (nodes[(i - 1) % len(nodes)], nodes[(i + 1) % len(nodes)]):
        if neighbor.type == GSOFFCURVE:
            neighbor.position = (neighbor.position.x + dx, neighbor.position.y + dy)
    node.position = new_pos


def mirror(point, axis):
    return (2.0 * axis - point[0], point[1])


def symmetric_targets(left, right, axis):
    """left/right: ((x, y), (x, y)) endpoints. Returns new endpoints for both,
    where the right ones are the exact mirror of the left ones."""
    (a, b), (c, d) = left, right
    mc, md = mirror(c, axis), mirror(d, axis)

    def dist(p, q):
        return math.hypot(p[0] - q[0], p[1] - q[1])

    if dist(a, mc) + dist(b, md) <= dist(a, md) + dist(b, mc):
        pairs = [(a, mc), (b, md)]
        order = (0, 1)
    else:
        pairs = [(a, md), (b, mc)]
        order = (1, 0)
    new_left = [((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0) for p, q in pairs]
    new_right = [mirror(p, axis) for p in new_left]
    # new_right[i] belongs to the right node paired with left node i
    right_by_node = [None, None]
    for i, node_index in enumerate(order):
        right_by_node[node_index] = new_right[i]
    return new_left, right_by_node


def make_symmetric():
    font = Glyphs.font
    if not font or not font.selectedLayers:
        raise RuntimeError("Abra um glifo e selecione os 4 segmentos.")
    layer = font.selectedLayers[0]
    axis = layer.width / 2.0

    segments = selected_segments(layer)
    if len(segments) < 4:
        raise RuntimeError(
            "Selecione 4 segmentos (2 de cada lado). Encontrados: {0}.".format(len(segments))
        )
    # Selecting all nodes also selects short connecting segments (e.g. the flat
    # bottom of a V); keep the four longest.
    segments = sorted(segments, key=seg_length, reverse=True)[:4]

    def center_x(seg):
        return (seg[1].position.x + seg[2].position.x) / 2.0

    left = sorted([s for s in segments if center_x(s) < axis], key=center_x)
    right = sorted([s for s in segments if center_x(s) >= axis], key=center_x, reverse=True)
    if len(left) != 2 or len(right) != 2:
        raise RuntimeError("Preciso de 2 segmentos à esquerda e 2 à direita do centro ({0:g}).".format(axis))

    all_nodes = [n for s in segments for n in (s[1], s[2])]
    if len(set(id(n) for n in all_nodes)) != 8:
        raise RuntimeError("Os segmentos selecionados compartilham nós.")

    layer.parent.beginUndo()
    try:
        for lseg, rseg in zip(left, right):
            lpath, a, b = lseg
            rpath, c, d = rseg
            pts_l = ((a.position.x, a.position.y), (b.position.x, b.position.y))
            pts_r = ((c.position.x, c.position.y), (d.position.x, d.position.y))
            new_l, new_r = symmetric_targets(pts_l, pts_r, axis)
            move_with_handles(lpath, a, new_l[0])
            move_with_handles(lpath, b, new_l[1])
            move_with_handles(rpath, c, new_r[0])
            move_with_handles(rpath, d, new_r[1])
    finally:
        layer.parent.endUndo()

    print("✅ {0}: segmentos espelhados em torno de x = {1:g}.".format(TITLE, axis))


try:
    make_symmetric()
except Exception as e:
    Message(str(e), title=TITLE)
