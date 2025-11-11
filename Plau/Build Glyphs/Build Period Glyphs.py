# -*- coding: utf-8 -*-
# MenuTitle: Build periodcentered & bullet from period (Glyphs 3.4; L/R keys only, no leading '=')
"""
Glyphs 3.4 (3425)

Cria/atualiza a partir do componente "period":
- periodcentered (U+00B7): y = (xHeight/2) + 5; LSB/RSB = "period"; escala 1.0
- bullet        (U+2022): y = (xHeight/2) + 5; LSB/RSB = "period*1.25"; escala 1.4

Obs. importante:
- NÃO inclua o sinal '=' nas metric keys salvas. O Glyphs exibe o '=' na UI automaticamente.
- Keys são aplicadas só no LAYER (glyph-level é limpo) para não virar “==”.
"""

from GlyphsApp import Glyphs, GSGlyph, GSLayer, GSComponent

FONT = Glyphs.font
if not FONT:
    raise Exception("Abra uma fonte antes de rodar o script.")

Y_OFFSET_ABOVE_MID = 5.0
BULLET_SCALE = 1.4
SOURCE_GLYPH_NAME = "period"

# targets: (name, unicode, componentScale, sidebearingKeyStringWithoutEquals)
TARGETS = (
    ("periodcentered", "00B7", 1.0,  "period"),
    ("bullet",         "2022", BULLET_SCALE, "period*1.25"),
)

def get_glyph(name):
    try:
        return FONT.glyphs[name]
    except Exception:
        return None

def ensure_glyph(name, uni_hex=None):
    g = get_glyph(name)
    if not g:
        g = GSGlyph(name)
        if uni_hex:
            g.unicode = uni_hex
        FONT.glyphs.append(g)
    elif uni_hex and not g.unicode:
        g.unicode = uni_hex
    return g

def ensure_master_layer(glyph, master):
    layer = glyph.layers[master.id]
    if layer is None:
        layer = GSLayer()
        layer.layerId = master.id
        layer.associatedMasterId = master.id
        glyph.layers[master.id] = layer
    return layer

def clear_layer(layer):
    for shp in list(layer.shapes)[::-1]:
        try: layer.removeShape_(shp)
        except Exception:
            try: shp.removeFromParent()
            except Exception: pass
    for anc in list(layer.anchors)[::-1]:
        try: layer.removeAnchor_(anc)
        except Exception:
            try: anc.removeFromParent()
            except Exception: pass

def period_layer_for_master(master):
    src_g = get_glyph(SOURCE_GLYPH_NAME)
    if not src_g:
        return None
    return src_g.layers[master.id]

def advance_width_or(src_layer, fallback=600):
    try: w = src_layer.width if src_layer else None
    except Exception: w = None
    return w if (w and w > 0) else fallback

# ===== métricas: definir só no LAYER e SEM '=' =====
def set_lr_keys_layer_only(layer, glyph_obj, key_string_without_equals):
    # limpa keys no glyph (evita '==')
    try:
        glyph_obj.leftMetricsKey = None
        glyph_obj.rightMetricsKey = None
        glyph_obj.widthMetricsKey = None
    except Exception:
        pass
    # define no layer (sem '=')
    try:
        layer.leftMetricsKey  = key_string_without_equals
        layer.rightMetricsKey = key_string_without_equals
        # garantir que não há width key no layer
        layer.widthMetricsKey = None
    except Exception:
        pass
# ================================================

def build_target(target_name, unicode_hex, comp_scale, lr_key_no_eq):
    g = ensure_glyph(target_name, unicode_hex)

    for m in FONT.masters:
        src_layer = period_layer_for_master(m)
        if src_layer is None:
            print(u"⚠️ Master ‘{}’ ignorada: não há ‘period’ nessa master.".format(m.name))
            continue

        xh = m.xHeight
        tgt_layer = ensure_master_layer(g, m)
        clear_layer(tgt_layer)

        src_adv = advance_width_or(src_layer, 600)
        tgt_layer.width = src_adv  # valor numérico apenas para posicionamento

        comp_y = (xh * 0.5) + Y_OFFSET_ABOVE_MID
        # posicionamento simples; L/R serão dirigidos pelas keys
        comp_x = 0.0

        comp = GSComponent(SOURCE_GLYPH_NAME)
        comp.alignment = 0
        comp.scale = (comp_scale, comp_scale)
        comp.position = (comp_x, comp_y)
        tgt_layer.shapes.append(comp)

        # aplica LSB/RSB keys (sem '=' e só no layer)
        set_lr_keys_layer_only(tgt_layer, g, lr_key_no_eq)

        print(u"✓ {} @ {}: y={:.2f}, scale={}, L/R key='{}'".format(
            target_name, m.name, comp_y, comp_scale, lr_key_no_eq
        ))

def main():
    if not get_glyph(SOURCE_GLYPH_NAME):
        Glyphs.showNotification("Script abortado", u"Crie o glifo ‘{}’ primeiro.".format(SOURCE_GLYPH_NAME))
        return

    ui_disabled = False
    try:
        FONT.disableUpdateInterface()
        ui_disabled = True
    except Exception:
        pass

    try:
        for args in TARGETS:
            build_target(*args)
    finally:
        if ui_disabled:
            try: FONT.enableUpdateInterface()
            except Exception: pass

    Glyphs.showNotification(
        "periodcentered & bullet",
        u"Concluído: LSB/RSB com '=' único (pc: period; bullet: period*1.25)."
    )
    print("✅ Concluído.")

main()
