# Center Components in Reference Height (Y-axis only) with Dialog Box and Layer Option

import vanilla
from GlyphsApp import *
font = Glyphs.font

class CenterComponentDialog(object):
    def __init__(self):
        self.w = vanilla.FloatingWindow((240, 130), "Center Components")

        self.w.reference_height_label = vanilla.TextBox((10, 10, 120, 20), "Reference Height:")
        self.w.reference_height = vanilla.PopUpButton((120, 10, 100, 20), ["Cap Height", "X-Height", "Total Height"])

        self.w.layer_option_label = vanilla.TextBox((10, 40, 120, 20), "Layers:")
        self.w.layer_option = vanilla.PopUpButton((120, 40, 100, 20), ["Current Layer", "All Layers"])

        self.w.center_button = vanilla.Button((10, 80, 100, 20), "Center", callback=self.center_callback)
        self.w.cancel_button = vanilla.Button((130, 80, 100, 20), "Cancel", callback=self.cancel_callback)

        self.w.open()

    def center_callback(self, sender):
        reference_height_type = self.w.reference_height.getItems()[self.w.reference_height.get()]
        layer_option = self.w.layer_option.getItems()[self.w.layer_option.get()]
        center_components_in_reference_height_y(reference_height_type, layer_option)
        self.w.close()

    def cancel_callback(self, sender):
        self.w.close()

def center_components_in_reference_height_y(reference_height_type, layer_option="All Layers"):
    if layer_option == "Current Layer":
        layers = font.selectedLayers
    elif layer_option == "All Layers":
        layers = [layer for glyph in font.glyphs for layer in glyph.layers]
    else:
        raise ValueError("Invalid layer option.")
    
    for layer in layers:
        if reference_height_type == "Cap Height":
            reference_height = layer.master.capHeight
        elif reference_height_type == "X-Height":
            reference_height = layer.master.xHeight
        elif reference_height_type == "Total Height":
            reference_height = layer.bounds.size.height
        else:
            raise ValueError("Invalid reference height type.")
        
        for component in layer.components:
            # Calculate the center Y coordinate
            centered_y = (reference_height - component.bounds.size.height) / 2

            # Apply the new Y coordinate
            component.y = centered_y

CenterComponentDialog()
