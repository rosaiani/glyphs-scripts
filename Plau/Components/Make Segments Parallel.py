#MenuTitle: Make Segments Parallel
# -*- coding: utf-8 -*-
# Shortcut: cmd+opt+shift+p
# Description: Select the two nodes of each of two segments (4 on-curve nodes) and run. If other neighboring selected nodes form extra short segments, the two longest are used. Both segments are rotated around their own midpoints to the average angle, so they become parallel without changing their lengths.

import math
from GlyphsApp import Glyphs, Message, GSOFFCURVE

TITLE = "Make Segments Parallel"


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


def segment_length(segment):
    _, a, b = segment
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


def make_parallel():
    font = Glyphs.font
    if not font or not font.selectedLayers:
        raise RuntimeError("Abra um glifo e selecione os nós dos dois segmentos.")
    layer = font.selectedLayers[0]

    segments = selected_segments(layer)
    if len(segments) < 2:
        raise RuntimeError(
            "Selecione dois segmentos (2 nós em cada, 4 no total). "
            "Encontrados: {0}.".format(len(segments))
        )
    # Selected nodes that are neighbors also form short connecting segments
    # (e.g. the base of a stem); keep the two longest.
    segments = sorted(segments, key=segment_length, reverse=True)[:2]

    # Direction of each segment; flip the second if needed so both point the same way.
    vecs = []
    for path, a, b in segments:
        vecs.append((b.position.x - a.position.x, b.position.y - a.position.y))
    lens = [math.hypot(*v) for v in vecs]
    if min(lens) == 0:
        raise RuntimeError("Um dos segmentos tem comprimento zero.")
    u1 = (vecs[0][0] / lens[0], vecs[0][1] / lens[0])
    u2 = (vecs[1][0] / lens[1], vecs[1][1] / lens[1])
    if u1[0] * u2[0] + u1[1] * u2[1] < 0:
        u2 = (-u2[0], -u2[1])
    sx, sy = u1[0] + u2[0], u1[1] + u2[1]
    norm = math.hypot(sx, sy)
    if norm == 0:
        raise RuntimeError("Os segmentos são perpendiculares; ângulo médio indefinido.")
    target = (sx / norm, sy / norm)

    layer.parent.beginUndo()
    try:
        for (path, a, b), v, length in zip(segments, vecs, lens):
            # Keep each segment's own direction sign, just adopt the target axis.
            sign = 1 if v[0] * target[0] + v[1] * target[1] >= 0 else -1
            mx = (a.position.x + b.position.x) / 2.0
            my = (a.position.y + b.position.y) / 2.0
            hx = target[0] * sign * length / 2.0
            hy = target[1] * sign * length / 2.0
            move_with_handles(path, a, (mx - hx, my - hy))
            move_with_handles(path, b, (mx + hx, my + hy))
    finally:
        layer.parent.endUndo()

    angle = math.degrees(math.atan2(target[1], target[0]))
    print("✅ {0}: segmentos paralelos em {1:.2f}°.".format(TITLE, angle))


try:
    make_parallel()
except Exception as e:
    Message(str(e), title=TITLE)
