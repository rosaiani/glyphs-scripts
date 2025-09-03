# -*- coding: utf-8 -*-
# MenuTitle: Plau – Center Components in Reference Height (Y)
# Shortcut: cmd+opt+shift+c
# Description: Centers components along Y based on Cap Height, x-Height, or Total Layer Height. Works on current or all layers of selected glyphs.

import vanilla
from GlyphsApp import Glyphs, Message
from AppKit import NSPoint

font = Glyphs.font

class CenterComponentDialog(object):
    def __init__(self):
        self.w = vanilla.FloatingWindow((260, 140), "Center Components (Y)")

        self.w.reference_height_label = vanilla.TextBox((10, 12, 120, 20), "Reference Height:")
        self.w.reference_height = vanilla.PopUpButton((130, 10, 120, 22), ["Cap Height", "X-Height", "Total Height"])

        self.w.layer_option_label = vanilla.TextBox((10, 44, 120, 20), "Layers:")
        self.w.layer_option = vanilla.PopUpButton((130, 42, 120, 22), ["Current Layer", "All Layers"])

        self.w.center_button = vanilla.Button((10, 100, 110, 24), "Center", callback=self.center_callback)
        self.w.cancel_button = vanilla.Button((140, 100, 110, 24), "Cancel", callback=self.cancel_callback)

        self.w.open()
        self.w.makeKey()

    def center_callback(self, sender):
        ref_type = self.w.reference_height.getItems()[self.w.reference_height.get()]
        layer_opt = self.w.layer_option.getItems()[self.w.layer_option.get()]
        try:
            center_components_in_reference_height_y(ref_type, layer_opt)
        except Exception as e:
            Message(str(e), title="Center Components (Y)")
        self.w.close()

    def cancel_callback(self, sender):
        self.w.close()


def center_components_in_reference_height_y(reference_height_type, layer_option="All Layers"):
    font = Glyphs.font
    if not font:
        raise RuntimeError("Abra uma fonte no Glyphs antes de rodar o script.")

    if not font.selectedLayers:
        raise RuntimeError("Selecione pelo menos um glifo.")

    selected_glyphs = [l.parent for l in font.selectedLayers]

    if layer_option == "Current Layer":
        layers = font.selectedLayers
    elif layer_option == "All Layers":
        layers = [layer for glyph in selected_glyphs for layer in glyph.layers]
    else:
        raise ValueError("Invalid layer option.")

    count_components = 0

    for layer in layers:
        master = layer.master
        if reference_height_type == "Cap Height":
            reference_height = master.capHeight
        elif reference_height_type == "X-Height":
            reference_height = master.xHeight
        elif reference_height_type == "Total Height":
            reference_height = layer.bounds.size.height
        else:
            raise ValueError("Invalid reference height type.")

        for component in layer.components:
            # Ensure we can move it manually
            try:
                if hasattr(component, "automaticAlignment") and component.automaticAlignment:
                    component.automaticAlignment = False
            except Exception:
                pass

            comp_bounds = component.bounds
            comp_h = comp_bounds.size.height
            new_y = (reference_height - comp_h) / 2.0

            # Keep x as-is
            old_pos = component.position
            component.position = NSPoint(old_pos.x, new_y)
            count_components += 1

    print("✅ Center Components (Y): alinhados {0} componentes pelo critério '{1}' em '{2}'.".format(
        count_components, reference_height_type, layer_option
    ))


if __name__ == "__main__":
    CenterComponentDialog()
