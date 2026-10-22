#MenuTitle: Create Centerline
# -*- coding: utf-8 -*-
# Description: Creates the centerline between two segments (select the two nodes of each) or between two whole paths. Works in Glyphs 4.

__doc__ = """
Creates a new open path halfway between two lines.
Two segments: select the two on-curve nodes of each segment (4 nodes in total, they can belong to different contours, e.g. the waist of an 8) and run. Lines and curves can be mixed.
Two whole paths: select all nodes of both paths. They need the same node structure; direction and start point are matched automatically.
The original paths are not changed. Coordinates are rounded to whole units.
Inspired by Harbor Type's Create Centerline (Apache-2.0), rewritten for Glyphs 4.
"""

import math
from GlyphsApp import Glyphs, GSPath, GSNode, Message, GSLINE, GSCURVE, GSOFFCURVE

TITLE = "Create Centerline"


# ===== Geometry =====

def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def xy(node):
    return (node.position.x, node.position.y)


def to_cubic(seg):
    if len(seg) == 4:
        return seg
    return [seg[0], lerp(seg[0], seg[1], 1 / 3.0), lerp(seg[0], seg[1], 2 / 3.0), seg[1]]


def mid_segment(s1, s2):
    """Point-by-point average of two segments (2 points = line, 4 = cubic), second one flipped if needed."""
    if len(s1) == 2 and len(s2) == 2:
        a, b = s1, s2
    else:
        a, b = to_cubic(s1), to_cubic(s2)
    forward = dist(a[0], b[0]) + dist(a[-1], b[-1])
    backward = dist(a[0], b[-1]) + dist(a[-1], b[0])
    if backward < forward:
        b = b[::-1]
    return [lerp(p, q, 0.5) for p, q in zip(a, b)]


def rounded(p):
    return (round(p[0]), round(p[1]))


# ===== Segments =====

def next_oncurve_index(path, i):
    """Index of the next on-curve node after node i (wrapping only on closed paths), or None."""
    nodes = path.nodes
    count = len(nodes)
    for step in range(1, count):
        j = i + step
        if j >= count:
            if not path.closed:
                return None
            j %= count
        if nodes[j].type != GSOFFCURVE:
            return j
    return None


def segment_points(path, i, j):
    """Points of the segment from node i to node j: [p0, p3] for a line, [p0, c1, c2, p3] for a cubic."""
    nodes = path.nodes
    count = len(nodes)
    between = []
    k = (i + 1) % count
    while k != j:
        between.append(nodes[k])
        k = (k + 1) % count
    if len(between) not in (0, 2):
        raise RuntimeError("Only lines and cubic curves are supported (found a segment with %d off-curve points)." % len(between))
    return [xy(nodes[i])] + [xy(n) for n in between] + [xy(nodes[j])]


def selected_segments(layer, selection):
    segments = []
    for path in layer.paths:
        for i, node in enumerate(path.nodes):
            if node.type == GSOFFCURVE or node not in selection:
                continue
            j = next_oncurve_index(path, i)
            if j is not None and j != i and path.nodes[j] in selection:
                segments.append(segment_points(path, i, j))
    return segments


def seg_length(seg):
    return sum(dist(seg[k], seg[k + 1]) for k in range(len(seg) - 1))


def centerline_of_segments(segments):
    # neighboring selected nodes also form short connecting segments; keep the two longest
    two = sorted(segments, key=seg_length, reverse=True)[:2]
    pts = [rounded(p) for p in mid_segment(two[0], two[1])]
    if len(pts) == 2:
        return [(pts[0], GSLINE), (pts[1], GSLINE)], False
    return [(pts[0], GSLINE), (pts[1], GSOFFCURVE), (pts[2], GSOFFCURVE), (pts[3], GSCURVE)], False


# ===== Whole paths =====

def node_list(path):
    return [(xy(n), n.type) for n in path.nodes]


def reversed_list(nodes, closed):
    """The same path in the opposite direction, with on-curve node types recomputed for the new direction."""
    seq = nodes[::-1]
    out = []
    for k, (pos, typ) in enumerate(seq):
        if typ == GSOFFCURVE:
            out.append((pos, typ))
            continue
        prev = seq[k - 1] if (k > 0 or closed) else None
        out.append((pos, GSCURVE if prev is not None and prev[1] == GSOFFCURVE else GSLINE))
    return out


def best_match(p1, p2):
    """Best (reversal, start shift) of path 2 against path 1: the one with matching node types and the shortest total distance."""
    a = node_list(p1)
    b = node_list(p2)
    closed = p1.closed
    count = len(a)
    best = None
    for flip in (False, True):
        seq = reversed_list(b, closed) if flip else b
        for shift in (range(count) if closed else [0]):
            rolled = seq[shift:] + seq[:shift]
            if [t for _, t in rolled] != [t for _, t in a]:
                continue
            total = sum(dist(x[0], y[0]) for x, y in zip(a, rolled))
            if best is None or total < best[0]:
                best = (total, rolled)
    return a, best[1] if best else None


def centerline_of_paths(p1, p2):
    if len(p1.nodes) != len(p2.nodes):
        raise RuntimeError("The two paths don't have the same number of nodes (%d and %d)." % (len(p1.nodes), len(p2.nodes)))
    if p1.closed != p2.closed:
        raise RuntimeError("One path is open and the other is closed.")
    a, b = best_match(p1, p2)
    if b is None:
        raise RuntimeError("The two paths don't have the same structure of lines and curves.")
    nodes = [(rounded(lerp(x[0], y[0], 0.5)), x[1]) for x, y in zip(a, b)]
    return nodes, p1.closed


# ===== Main =====

def whole_paths(layer, selection):
    """Paths whose on-curve nodes are all selected."""
    return [p for p in layer.paths if p.nodes and all(n in selection for n in p.nodes if n.type != GSOFFCURVE)]


def main():
    font = Glyphs.font
    if not font or not font.selectedLayers:
        raise RuntimeError("Open a glyph and select two segments or two paths.")
    layer = font.selectedLayers[0]
    selection = [n for n in layer.selection if isinstance(n, GSNode)]
    if not selection:
        raise RuntimeError("Select the two nodes of each of two segments, or all nodes of two paths.")

    paths = whole_paths(layer, selection)
    others = [n for n in selection if not any(n in p.nodes for p in paths)]
    if len(paths) == 2 and not others:
        nodes, closed = centerline_of_paths(paths[0], paths[1])
        mode = "paths"
    else:
        segments = selected_segments(layer, selection)
        if len(segments) < 2:
            raise RuntimeError("Select two segments (2 on-curve nodes in each, 4 in total) or two whole paths. Segments found: %d." % len(segments))
        nodes, closed = centerline_of_segments(segments)
        mode = "segments"

    path = GSPath()
    for pos, typ in nodes:
        path.nodes.append(GSNode(pos, type=typ))
    path.closed = closed
    layer.parent.beginUndo()
    try:
        layer.shapes.append(path)
    finally:
        layer.parent.endUndo()
    try:
        layer.selection = list(path.nodes)
    except Exception:
        pass
    print("✅ %s: centerline of two %s added (%d nodes)." % (TITLE, mode, len(nodes)))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Message(str(e), TITLE)
