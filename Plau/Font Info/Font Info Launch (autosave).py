# -*- coding: utf-8 -*-
# MenuTitle: Preset Plau – Fill metadata (com campo de cliente)
# -*- coding: utf-8 -*-

from GlyphsApp import Glyphs, Message
from string import Template
from datetime import datetime
import vanilla

# ==========
# CONFIG
# ==========
VENDOR_IDENTIFICATION = "Plau"  # ou "PLAU" (padrão OT é 4 letras maiúsculas)
PLAU_NAME = "Plau"
PLAU_URL = "https://plau.design"

copyright_tpl = Template(
    "(c) $cliente $ano. Typeface designed by Plau exclusively for $cliente"
)

# ==========
# UI
# ==========
class PresetPlauWindow(object):
    def __init__(self):
        self.w = vanilla.FloatingWindow(
            (320, 120),
            "Preset Plau",
        )

        self.w.text = vanilla.TextBox((15, 20, -15, 20), "Nome do cliente:")
        self.w.clienteEdit = vanilla.EditText((15, 45, -15, 22), "")

        self.w.applyButton = vanilla.Button((15, 80, -15, 20), "Aplicar", callback=self.applyCallback)

        self.w.open()
        self.w.makeKey()

    def applyCallback(self, sender):
        cliente = self.w.clienteEdit.get().strip()
        ano = datetime.now().year

        if not cliente:
            Message("Por favor, digite o nome do cliente.", "Preset Plau")
            return

        font = Glyphs.font
        if not font:
            Message("Abra uma fonte antes de rodar.", "Preset Plau")
            return

        # Family Name = cliente
        font.familyName = cliente

        # Vendor ID
        font.customParameters["vendorID"] = VENDOR_IDENTIFICATION

        # Copyright
        font.copyright = copyright_tpl.substitute(cliente=cliente, ano=ano)

        # Designer / Manufacturer
        font.designer = PLAU_NAME
        font.manufacturer = PLAU_NAME

        # URLs
        font.designerURL = PLAU_URL
        font.manufacturerURL = PLAU_URL

        # Versão fixa 0.000
        font.versionMajor = 0
        font.versionMinor = 0

        print("✅ Preset Plau aplicado:")
        print(f"  Cliente / Family: {font.familyName}")
        print(f"  vendorID: {font.customParameters['vendorID']}")
        print(f"  copyright: {font.copyright}")
        print(f"  designer: {font.designer}")
        print(f"  manufacturer: {font.manufacturer}")
        print(f"  URLs: designer={font.designerURL} | manufacturer={font.manufacturerURL}")
        print(f"  Version: {font.versionMajor}.{font.versionMinor:03d}")

        self.w.close()

# ==========
# RUN
# ==========
PresetPlauWindow()
