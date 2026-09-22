#MenuTitle: Build Basic Math G4
# -*- coding: utf-8 -*-

__doc__ = """
Builds the following math symbols: plus, minus, equal, multiply, divide, logicalnot, greater, less, greaterequal, lessequal. Empty master layers are filled. Existing less and lessequal master artwork is replaced with mirrored components; other artwork is preserved. Uses figurespace width when present, otherwise zero, per master. Measures n, hyphen, and dotaccentcomb. All symbol master layers receive this width and are centered horizontally without scaling.
"""

from Foundation import NSClassFromString, NSAffineTransform
from GlyphsApp import Glyphs, GSGlyph, GSComponent

font = Glyphs.font
if font is None:
    raise RuntimeError("Open a font before running this script.")

spacing_name = "figurespace" if font.glyphs["figurespace"] is not None else "zero"
required = (spacing_name, "n", "hyphen", "dotaccentcomb")
missing = [name for name in required if font.glyphs[name] is None]
if missing:
    raise RuntimeError("Missing source glyphs: " + ", ".join(missing))

# Glyphs 4 moved the stroke operation from the filter to GlyphsCore.
offsetFilter = NSClassFromString("GSOffsetCurve")
if offsetFilter is None:
    raise RuntimeError("GSOffsetCurve is unavailable. Run this script in Glyphs 4.")


def master_layers(glyph):
    for master in font.masters:
        layer = glyph.layers[master.id]
        if layer is None:
            raise RuntimeError("Missing master layer: %s / %s" % (glyph.name, master.name))
        yield master.id, layer


def empty_master_layers(name):
    glyph = font.glyphs[name]
    if glyph is None:
        glyph = GSGlyph(name)
        font.glyphs.append(glyph)
    for master_id, layer in master_layers(glyph):
        if len(layer.shapes) == 0:
            yield master_id, layer
            print("Built %s / %s (%d shapes)" % (name, layer.master.name, len(layer.shapes)))


def require_intersections(points, glyph_name, layer):
    if len(points) < 4:
        raise RuntimeError(
            "Cannot measure %s in master %s: expected at least two outline intersections."
            % (glyph_name, layer.master.name)
        )


master_contrast = {}
symbol_width = {}
hyphen_lsb = {}
n_distance = {}
hyphen_factor = 1.1
hyphen_thick_factor = 0.9
contrast_factor = 0.95
multiply_factor = 1.01

for i, layer in master_layers(font.glyphs[spacing_name]):
    if layer.isMasterLayer:
        if layer.width <= 0:
            raise RuntimeError("%s must have a positive width in master %s." % (
                spacing_name, layer.master.name))
        symbol_width[i] = layer.width

for i, layer in master_layers(font.glyphs['n']):
    if layer.isMasterLayer:
        measure_y = layer.master.xHeight/3
        start = 0
        stop = layer.width
        intersections = layer.intersectionsBetweenPoints((start, measure_y), (stop, measure_y))
        require_intersections(intersections, "n", layer)
        n_distance[i] = intersections[1].x + (stop-intersections[-2].x)

for i, layer in master_layers(font.glyphs['hyphen']):
    if layer.isMasterLayer:
        hyphen_layer = layer.copyDecomposedLayer()
        hyphen_lsb[i] = layer.LSB * hyphen_factor
        measure_x = hyphen_layer.width / 2
        start = layer.master.capHeight
        stop = layer.master.descender
        intersections = hyphen_layer.intersectionsBetweenPoints((measure_x, start), (measure_x, stop))
        require_intersections(intersections, "hyphen", layer)
        stem_height = abs(intersections[-2].y - intersections[-3].y) * hyphen_thick_factor
        master_contrast[i] = (stem_height, round(stem_height * contrast_factor))



for i, layer in empty_master_layers('minus'):
    h, v = master_contrast[i]
    layer.width = symbol_width[i]
    line_width = layer.width - hyphen_lsb[i]
    y_start = layer.master.capHeight / 2
    y_end = y_start
    x_start = hyphen_lsb[i]
    x_end = line_width
    pen = layer.getPen()
    pen.moveTo((x_start, y_start))
    pen.lineTo((x_end, y_start))
    pen.endPath()
    offsetFilter.offsetLayer_offsetX_offsetY_makeStroke_autoStroke_position_metrics_error_shadow_capStyleStart_capStyleEnd_join_keepCompatibleOutlines_(
        layer,
        h / 2, v / 2, # horizontal and vertical offset
        True,     # if True, creates a stroke
        False,     # if True, distorts resulting shape to vertical metrics
        0.0,       # Glyphs 4: -1 = left, 0 = centered, 1 = right
        None, None, None, 0, 0, 0, False)
    layer.correctPathDirection()

for i, layer in empty_master_layers('plus'):
    h,v = master_contrast[i]
    layer.width = symbol_width[i]
    line_width = layer.width - hyphen_lsb[i]
    y_start = layer.master.capHeight / 2
    y_end = y_start
    x_start = hyphen_lsb[i]
    x_end = line_width
    pen = layer.getPen()
    pen.moveTo((x_start, y_start))
    pen.lineTo((x_end, y_start))
    pen.endPath()

    x_start = layer.width / 2
    x_end = x_start
    y_start = (layer.master.capHeight + hyphen_lsb[i] - line_width) / 2
    y_end = layer.master.capHeight - y_start

    pen.moveTo((x_start, y_start))
    pen.lineTo((x_end, y_end))
    pen.endPath()

    offsetFilter.offsetLayer_offsetX_offsetY_makeStroke_autoStroke_position_metrics_error_shadow_capStyleStart_capStyleEnd_join_keepCompatibleOutlines_(
        layer,
        h / 2, v / 2, # horizontal and vertical offset
        True,     # if True, creates a stroke
        False,     # if True, distorts resulting shape to vertical metrics
        0.0,       # Glyphs 4: -1 = left, 0 = centered, 1 = right
        None, None, None, 0, 0, 0, True)
    layer.correctPathDirection()

for i, layer in empty_master_layers('equal'):
    minusLayerBounds = font.glyphs['minus'].layers[i].bounds
    equal_height = minusLayerBounds.size.height
    layer.width = symbol_width[i]
    y_offset = (equal_height/2) + (n_distance[i]/2)

    top_equal = GSComponent('minus', (0, y_offset))
    top_equal.automaticAlignment = False
    layer.shapes.append(top_equal)

    bottom_equal = GSComponent('minus', (0, -y_offset))
    bottom_equal.automaticAlignment = False
    layer.shapes.append(bottom_equal)

for i, layer in empty_master_layers('multiply'):
    h,v = master_contrast[i]
    layer.width = symbol_width[i]
    line_width = round((layer.width - hyphen_lsb[i]) * multiply_factor)
    y_start = layer.master.capHeight / 2
    y_end = y_start
    x_start = (layer.width - line_width) / 2

    x_end = x_start + line_width
    pen = layer.getPen()
    pen.moveTo((x_start, y_start))
    pen.lineTo((x_end, y_start))
    pen.endPath()

    x_start = layer.width / 2
    x_end = x_start
    y_start = (layer.master.capHeight - line_width) / 2
    y_end = y_start + line_width

    pen.moveTo((x_start, y_start))
    pen.lineTo((x_end, y_end))
    pen.endPath()

    offsetFilter.offsetLayer_offsetX_offsetY_makeStroke_autoStroke_position_metrics_error_shadow_capStyleStart_capStyleEnd_join_keepCompatibleOutlines_(
        layer,
        h / 2, v / 2, # horizontal and vertical offset
        True,     # if True, creates a stroke
        False,     # if True, distorts resulting shape to vertical metrics
        0.0,       # Glyphs 4: -1 = left, 0 = centered, 1 = right
        None, None, None, 0, 0, 0, True)
    layer.correctPathDirection()
    rotate_transform = NSAffineTransform.new()
    cx, cy = layer.width / 2, layer.master.capHeight / 2
    rotate_transform.translateXBy_yBy_(cx, cy)
    rotate_transform.rotateByDegrees_(45)
    rotate_transform.translateXBy_yBy_(-cx, -cy)
    layer.applyTransform(rotate_transform)

for i, layer in empty_master_layers('divide'):
    minusLayerBounds = font.glyphs['minus'].layers[i].bounds
    layer.width = symbol_width[i]
    divide_height = minusLayerBounds.size.height
    divide_bottom = minusLayerBounds.origin.y
    dotaccentBounds = font.glyphs['dotaccentcomb'].layers[i].bounds
    dot_accent_x = dotaccentBounds.origin.x
    dot_accent_width = dotaccentBounds.size.width
    dot_accent_height = dotaccentBounds.size.height
    dot_accent_y = dotaccentBounds.origin.y
    dot_accent_distance = dotaccentBounds.origin.y - layer.master.xHeight

    minus = GSComponent('minus')
    minus.automaticAlignment = False

    x = (layer.width / 2) - (dot_accent_width / 2) - dot_accent_x
    y = (layer.master.capHeight / 2) - dot_accent_y + (divide_height / 2) + dot_accent_distance
    dot_top = GSComponent('dotaccentcomb', (x, y))

    x = (layer.width / 2) - (dot_accent_width / 2) - dot_accent_x
    y = divide_bottom - dot_accent_y - dot_accent_height - dot_accent_distance
    dot_bottom = GSComponent('dotaccentcomb', (x, y))
    dot_top.automaticAlignment = False
    dot_bottom.automaticAlignment = False

    layer.shapes.append(minus)
    layer.shapes.append(dot_top)
    layer.shapes.append(dot_bottom)



# Additional proportions, relative to the length of the minus sign.
comparison_height_factor = 0.70
logicalnot_depth_factor = 0.35


def stroke_polyline(layer, points, master_id):
    pen = layer.getPen()
    pen.moveTo(points[0])
    for point in points[1:]:
        pen.lineTo(point)
    pen.endPath()
    h, v = master_contrast[master_id]
    offsetFilter.offsetLayer_offsetX_offsetY_makeStroke_autoStroke_position_metrics_error_shadow_capStyleStart_capStyleEnd_join_keepCompatibleOutlines_(
        layer, h / 2, v / 2, True, False, 0.0,
        None, None, None, 0, 0, 0, True)
    layer.correctPathDirection()


def positioned_component(name, x, y):
    component = GSComponent(name, (x, y))
    component.automaticAlignment = False
    return component


for i, layer in empty_master_layers('logicalnot'):
    layer.width = symbol_width[i]
    bounds = font.glyphs['minus'].layers[i].bounds
    left = bounds.origin.x
    right = left + bounds.size.width
    center_y = bounds.origin.y + bounds.size.height / 2
    # Inset the corner by half the vertical stem so its outer edge
    # aligns with the right edge of minus after stroking.
    right -= master_contrast[i][0] / 2
    depth = bounds.size.width * logicalnot_depth_factor
    stroke_polyline(layer, [
        (left, center_y), (right, center_y), (right, center_y - depth)
    ], i)


for name, points_right in (('greater', True),):
    for i, layer in empty_master_layers(name):
        layer.width = symbol_width[i]
        bounds = font.glyphs['minus'].layers[i].bounds
        left = bounds.origin.x
        right = left + bounds.size.width
        center_y = bounds.origin.y + bounds.size.height / 2
        half_height = bounds.size.width * comparison_height_factor / 2
        tip_x, ends_x = (right, left) if points_right else (left, right)
        stroke_polyline(layer, [
            (ends_x, center_y + half_height),
            (tip_x, center_y),
            (ends_x, center_y - half_height),
        ], i)


for name, comparison in (('greaterequal', 'greater'),):
    for i, layer in empty_master_layers(name):
        layer.width = symbol_width[i]
        sign_bounds = font.glyphs[comparison].layers[i].bounds
        bar_bounds = font.glyphs['minus'].layers[i].bounds
        # One horizontal bar below the comparison sign. Match the clear
        # gap in equal and center the complete symbol on the math axis.
        gap = max(0, n_distance[i])
        total_height = sign_bounds.size.height + gap + bar_bounds.size.height
        axis_y = bar_bounds.origin.y + bar_bounds.size.height / 2
        bottom_y = axis_y - total_height / 2
        bar_x = (layer.width - bar_bounds.size.width) / 2 - bar_bounds.origin.x
        bar_y = bottom_y - bar_bounds.origin.y
        sign_x = (layer.width - sign_bounds.size.width) / 2 - sign_bounds.origin.x
        sign_y = bottom_y + bar_bounds.size.height + gap - sign_bounds.origin.y
        layer.shapes.append(positioned_component(comparison, sign_x, sign_y))
        layer.shapes.append(positioned_component('minus', bar_x, bar_y))

# Space in dependency order: source components must be positioned before
# the glyphs referencing them. Center artwork without changing its size.
for name in ('minus', 'plus', 'equal', 'multiply', 'divide',
             'logicalnot', 'greater', 'greaterequal'):
    for master_id, layer in master_layers(font.glyphs[name]):
        width = symbol_width[master_id]
        bounds = layer.bounds
        if len(layer.shapes):
            shift_x = (width - bounds.size.width) / 2 - bounds.origin.x
            if abs(shift_x) > 0.000001:
                layer.applyTransform((1, 0, 0, 1, shift_x, 0))
        layer.width = width


# Always update these two glyphs, including versions made by earlier scripts.
# Reflect across the source advance-width midpoint: x becomes width - x.
for target_name, source_name in (('less', 'greater'), ('lessequal', 'greaterequal')):
    target = font.glyphs[target_name]
    if target is None:
        target = GSGlyph(target_name)
        font.glyphs.append(target)
    for master_id, layer in master_layers(target):
        source_layer = font.glyphs[source_name].layers[master_id]
        width = symbol_width[master_id]
        component = GSComponent(source_name)
        component.automaticAlignment = False
        component.transform = (-1, 0, 0, 1, width, 0)
        layer.shapes = [component]
        layer.width = width
        print("Linked %s / %s to mirrored %s" % (
            target_name, layer.master.name, source_name))

print("Finished. All math symbols use %s width in each master; less and lessequal use mirrored components." % spacing_name)
