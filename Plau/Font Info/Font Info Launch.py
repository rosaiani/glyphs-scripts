#MenuTitle: Fill Font Metadata
# -*- coding: utf-8 -*-
# Description: Fills the Font Info metadata from a client name, a font name (defaults to the client name) and your foundry details: family name, vendor ID, copyright, designer/manufacturer and their URLs. Resets the version to 0.000 and can add a clean version string ("Version X.XXX" only). Foundry fields are remembered between runs.

__doc__ = """
Fills the Font Info metadata from a client name, a font name (defaults to the client name) and your foundry details: family name, vendor ID, copyright, designer/manufacturer and their URLs.
Resets the version to 0.000 and can add a clean version string. Foundry fields are remembered between runs. Overwrites the existing values.
"""

from GlyphsApp import Glyphs, Message
from string import Template
from datetime import datetime
import vanilla

TITLE = "Fill Font Metadata"
PREFIX = "com.plau.fillMetadata."  # keys for remembered values in Glyphs.defaults

COPYRIGHT_TPL = Template(
    "(c) $client $year. Typeface designed by $foundry exclusively for $client"
)


def remembered(key, default=""):
    value = Glyphs.defaults[PREFIX + key]
    return value if value is not None else default


def remember(key, value):
    Glyphs.defaults[PREFIX + key] = value


def set_clean_version_string(font):
    """Version string reduced to 'Version X.XXX', and ttfautohint info left out of it."""
    if Glyphs.versionNumber >= 3:
        font.setProperty_value_languageTag_("versionString", "Version %d.%03d", None)
    else:
        font.customParameters["versionString"] = "Version %d.%03d"

    parameter = "TTFAutohint options"
    for instance in font.instances:
        value = instance.customParameters[parameter]
        if value is not None and "--no-info" not in value.split():
            instance.customParameters[parameter] = (value.strip() + " --no-info").strip()


class FillMetadataWindow(object):
    def __init__(self):
        self.w = vanilla.FloatingWindow((340, 314), TITLE)

        y = 14
        self.w.clientLabel = vanilla.TextBox((15, y, -15, 17), "Client name:")
        self.w.client = vanilla.EditText((15, y + 20, -15, 22), "")

        y += 52
        self.w.fontLabel = vanilla.TextBox((15, y, -15, 17), "Font name (family name):")
        self.w.fontName = vanilla.EditText((15, y + 20, -15, 22), "", placeholder="Same as client name")

        y += 52
        self.w.foundryLabel = vanilla.TextBox((15, y, -15, 17), "Foundry name:")
        self.w.foundry = vanilla.EditText((15, y + 20, -15, 22), remembered("foundry"))

        y += 52
        self.w.urlLabel = vanilla.TextBox((15, y, 200, 17), "Foundry URL:")
        self.w.url = vanilla.EditText((15, y + 20, 205, 22), remembered("url"), placeholder="https://")
        self.w.vendorLabel = vanilla.TextBox((235, y, -15, 17), "Vendor ID:")
        self.w.vendor = vanilla.EditText((235, y + 20, -15, 22), remembered("vendor"))

        y += 54
        self.w.cleanVersion = vanilla.CheckBox(
            (15, y, -15, 20), "Add clean version string",
            value=bool(remembered("cleanVersion", False)),
        )

        self.w.applyButton = vanilla.Button((15, -36, -15, 20), "OK", callback=self.apply_callback)
        self.w.setDefaultButton(self.w.applyButton)

        self.w.open()
        self.w.makeKey()

    def apply_callback(self, sender):
        client = self.w.client.get().strip()
        family = self.w.fontName.get().strip() or client
        foundry = self.w.foundry.get().strip()
        url = self.w.url.get().strip()
        vendor = self.w.vendor.get().strip()
        clean_version = bool(self.w.cleanVersion.get())
        year = datetime.now().year

        if not client:
            Message("Enter the client name.", TITLE)
            return
        if not foundry:
            Message("Enter the foundry name.", TITLE)
            return
        if not vendor or len(vendor) > 4:
            Message("Vendor ID must be 1 to 4 characters (OpenType uses 4 uppercase letters).", TITLE)
            return

        font = Glyphs.font
        if not font:
            Message("Open a font first.", TITLE)
            return

        remember("foundry", foundry)
        remember("url", url)
        remember("vendor", vendor)
        remember("cleanVersion", clean_version)

        font.familyName = family
        font.customParameters["vendorID"] = vendor
        font.copyright = COPYRIGHT_TPL.substitute(client=client, foundry=foundry, year=year)
        font.designer = foundry
        font.manufacturer = foundry
        font.designerURL = url
        font.manufacturerURL = url

        # Fixed version 0.000
        font.versionMajor = 0
        font.versionMinor = 0

        if clean_version:
            set_clean_version_string(font)

        print("✅ {0}:".format(TITLE))
        print("  Client: {0}".format(client))
        print("  Family: {0}".format(font.familyName))
        print("  vendorID: {0}".format(font.customParameters["vendorID"]))
        print("  copyright: {0}".format(font.copyright))
        print("  designer / manufacturer: {0}".format(foundry))
        print("  URLs: {0}".format(url))
        print("  Version: {0}.{1:03d}{2}".format(
            font.versionMajor, font.versionMinor, " (clean version string)" if clean_version else ""
        ))

        self.w.close()


FillMetadataWindow()
