#MenuTitle: Export Release Package
# -*- coding: utf-8 -*-
# Description: Exports the open font into a dated release folder: variable TTF, variable WOFF2 + web sample, static OTFs, and Windows TTFs fixed with Windows Font Fix (RIBBI in its own subfolder).

__doc__ = """
Exports the font in front into a dated release folder, with the same structure as the previous release: 01. Desktop Variable (TTF), 02. Webfont Variable (WOFF2 plus the CSS and HTML sample), 03. Static OTF Files, and 04. Windows TTF, where the fonts go through Windows Font Fix and the four RIBBI styles move to the "01. Windows RIBBI" subfolder.
The README, CSS and HTML are copied from the previous release folder, with the version line of the README updated to the new folder name.
Static fonts are autohinted and have overlaps removed. The variable font is not autohinted and gets the post-export fixes of fix_vf.py (usWeightClass from the default of the weight axis, smart dropout control at the start of prep, WWS bit); its WOFF2 is built from the fixed TTF.
Uses the active instances of the font. Never overwrites a non-empty release folder without asking.
"""

import importlib.util
import os
import re
import shutil
import tempfile
import time

import vanilla
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram
from vanilla.dialogs import askYesNo, getFolder
from GlyphsApp import Glyphs, Message, INSTANCETYPESINGLE, INSTANCETYPEVARIABLE, OTF, TTF

TITLE = "Export Release Package"
DEFAULTS_PREFIX = "com.plau.exportRelease."

# The folder structure of a release (the same names as in the previous releases)
FOLDER_VARIABLE = "01. Desktop Variable"
FOLDER_WEB = "02. Webfont Variable (Recommended)"
FOLDER_OTF = "03. Static OTF Files"
FOLDER_TTF = "04. Windows TTF"
FOLDER_RIBBI = "01. Windows RIBBI"
README_NAME = "README.txt"

RELEASE_NAME = re.compile(r"^[^/\\:*?\"<>|\s.][^/\\:*?\"<>|]*$")   # any valid folder name; the default is yy.mm.dd
VERSION_LINE = re.compile(r"Version \d{2}\.\d{2}\.\d{2}")
RIBBI_STYLES = ("Regular", "Italic", "Bold", "Bold Italic")
WEB_FONT_EXTENSIONS = (".woff", ".woff2")

# Export settings, as in the previous releases (checked against the 26.10.14 files).
STATIC_SETTINGS = dict(autoHint=True, removeOverlap=True, useSubroutines=True, useProductionNames=True)
# The variable font is NOT autohinted on purpose: without autohint Glyphs writes the minimal TrueType instructions,
# cvt/cvar and the gasp table that Windows needs, and fix_variable_font() below finishes the job.
VARIABLE_SETTINGS = dict(autoHint=False, removeOverlap=False, useSubroutines=True, useProductionNames=True)
# Smart dropout control (SCANCTRL / SCANTYPE) for the start of the prep program.
DROPOUT_CONTROL = bytes([0xB8, 0x01, 0xFF, 0x85, 0xB0, 0x04, 0x8D])

GROUPS = ("variable", "web", "otf", "ttf")


# ===== Helpers =====

def load_windows_font_fix():
    """The Windows Font Fix script that sits next to this one."""
    here = os.path.dirname(os.path.abspath(globals().get("__file__", "")))
    path = os.path.join(here, "Windows Font Fix.py")
    if not os.path.exists(path):
        path = os.path.expanduser("~/Library/Application Support/Glyphs 4/Scripts/Plau/Post-Production/Windows Font Fix.py")
    spec = importlib.util.spec_from_file_location("plau_windows_font_fix", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_release_folder(path):
    """A folder that looks like a release: it holds one of the release subfolders or a README."""
    if not os.path.isdir(path):
        return False
    known = (FOLDER_VARIABLE, FOLDER_WEB, FOLDER_OTF, FOLDER_TTF)
    return any(os.path.isdir(os.path.join(path, n)) for n in known) or os.path.exists(os.path.join(path, README_NAME))


def previous_releases(output_dir, exclude=None):
    """Release folders in the output folder (whatever their names), newest first."""
    if not output_dir or not os.path.isdir(output_dir):
        return []
    paths = [os.path.join(output_dir, n) for n in os.listdir(output_dir) if not n.startswith(".") and n != exclude]
    paths = [p for p in paths if is_release_folder(p)]
    paths.sort(key=lambda p: (os.path.basename(p), os.path.getmtime(p)), reverse=True)
    return [os.path.basename(p) for p in paths]


def default_output_dir(font):
    stored = Glyphs.defaults[DEFAULTS_PREFIX + "outputDir"]
    if stored is not None and not isinstance(stored, str):
        try:
            stored = str(stored[0]) if hasattr(stored, "__getitem__") and len(stored) else str(stored)
        except Exception:
            stored = ""
    if stored and os.path.isdir(stored):
        return str(stored)
    if font is not None and font.filepath:
        candidate = os.path.join(os.path.dirname(font.filepath), "Output")
        if os.path.isdir(candidate):
            return candidate
    return ""


def active_instances(font, kind):
    return [i for i in font.instances if i.active and i.type == kind]


def generate_all(instances, fmt, destination, settings, containers=None):
    """Exports each instance into destination. Returns a list of error messages."""
    os.makedirs(destination, exist_ok=True)
    errors = []
    for instance in instances:
        arguments = dict(settings)
        if containers:
            arguments["containers"] = containers
        try:
            result = instance.generate(format=fmt, fontPath=destination, **arguments)
        except Exception as e:
            result = "%s: %s" % (type(e).__name__, e)
        if result and result is not True:
            errors.append("%s: %s" % (instance.name, result))
    return errors


def fix_variable_font(path):
    """Post-export fixes of the variable TTF, in place (the logic of the project's fix_vf.py):
    usWeightClass = default of the wght axis, smart dropout control at the start of prep (and a gasp table if missing),
    and the WWS bit of fsSelection when the font has no WWS family name (nameID 21)."""
    font = TTFont(path, recalcTimestamp=False)
    if "fvar" in font and "OS/2" in font:
        for axis in font["fvar"].axes:
            if axis.axisTag == "wght":
                font["OS/2"].usWeightClass = int(round(axis.defaultValue))
    existing = b""
    if "prep" in font and hasattr(font["prep"], "program"):
        existing = font["prep"].program.getBytecode()
    if DROPOUT_CONTROL not in existing:
        prep = newTable("prep")
        prep.program = ttProgram.Program()
        prep.program.fromBytecode(DROPOUT_CONTROL + existing)
        font["prep"] = prep
    if "gasp" not in font:
        gasp = newTable("gasp")
        gasp.version = 1
        gasp.gaspRange = {0xFFFF: 0x000F}
        font["gasp"] = gasp
    maxp = font["maxp"]
    if hasattr(maxp, "maxStackElements"):
        maxp.maxStackElements = max(maxp.maxStackElements, 2)
    if "OS/2" in font and not font["name"].getName(21, 3, 1, 0x409):
        font["OS/2"].fsSelection |= 1 << 8
    font.save(path)


def write_woff2(ttf_path, woff2_path):
    font = TTFont(ttf_path)
    font.flavor = "woff2"
    font.save(woff2_path)   # needs the brotli module


def font_files(folder, extensions):
    return sorted(n for n in os.listdir(folder) if n.lower().endswith(extensions) and not n.startswith(".")) if os.path.isdir(folder) else []


# ===== The export =====

def export_release(font, release_dir, groups=GROUPS, template_dir=None, label=None, log=print):
    """Exports the groups of fonts into release_dir. Returns a list of problems (empty if all went well)."""
    problems = []
    label = label or os.path.basename(release_dir.rstrip("/"))
    os.makedirs(release_dir, exist_ok=True)
    variable = active_instances(font, INSTANCETYPEVARIABLE)
    static = active_instances(font, INSTANCETYPESINGLE)

    if "variable" in groups or "web" in groups:
        if not variable:
            log("   no active variable instance: skipped the variable and web fonts")
        else:
            temp = tempfile.mkdtemp(prefix="plau-release-")
            try:
                problems += generate_all(variable, TTF, temp, VARIABLE_SETTINGS)
                for name in sorted(n for n in os.listdir(temp) if n.lower().endswith(".ttf")):
                    path = os.path.join(temp, name)
                    try:
                        fix_variable_font(path)
                    except Exception as e:
                        problems.append("%s: the variable font fixes failed (%s: %s)" % (name, type(e).__name__, e))
                    if "variable" in groups:
                        os.makedirs(os.path.join(release_dir, FOLDER_VARIABLE), exist_ok=True)
                        shutil.copy2(path, os.path.join(release_dir, FOLDER_VARIABLE, name))
                        log("   %s/%s (fixed)" % (FOLDER_VARIABLE, name))
                    if "web" in groups:
                        os.makedirs(os.path.join(release_dir, FOLDER_WEB), exist_ok=True)
                        woff2_name = os.path.splitext(name)[0] + ".woff2"
                        try:
                            write_woff2(path, os.path.join(release_dir, FOLDER_WEB, woff2_name))
                            log("   %s/%s (from the fixed TTF)" % (FOLDER_WEB, woff2_name))
                        except Exception as e:
                            problems.append("%s: WOFF2 failed (%s: %s)" % (woff2_name, type(e).__name__, e))
            finally:
                shutil.rmtree(temp, ignore_errors=True)

    if ("otf" in groups or "ttf" in groups) and not static:
        log("   no active static instance: skipped the OTF and TTF folders")
        groups = tuple(g for g in groups if g not in ("otf", "ttf"))

    if "otf" in groups:
        folder = os.path.join(release_dir, FOLDER_OTF)
        problems += generate_all(static, OTF, folder, STATIC_SETTINGS)
        log("   %s: %d fonts" % (FOLDER_OTF, len(font_files(folder, (".otf",)))))

    if "ttf" in groups:
        folder = os.path.join(release_dir, FOLDER_TTF)
        problems += generate_all(static, TTF, folder, STATIC_SETTINGS)
        log("   %s: %d fonts exported" % (FOLDER_TTF, len(font_files(folder, (".ttf",)))))
        problems += fix_windows_fonts(folder, log)

    if template_dir and os.path.isdir(template_dir):
        copy_template_files(template_dir, release_dir, label, groups, log)
    return problems


def fix_windows_fonts(folder, log=print):
    """Windows Font Fix on the TTFs of the folder, then the RIBBI styles move into their own subfolder."""
    problems = []
    try:
        fix = load_windows_font_fix()
    except Exception as e:
        return ["Windows Font Fix could not be loaded: %s" % e]
    steps = [step for step in fix.DEFAULT_STEPS if Glyphs.defaults[fix.DEFAULTS_PREFIX + step] in (None, True, 1)]
    paths = [os.path.join(folder, n) for n in font_files(folder, (".ttf",))]
    errors = fix.process(paths, steps)
    if errors:
        problems.append("Windows Font Fix: %d font(s) failed" % errors)
    ribbi = []
    for path in paths:
        names = fix.TTFont(path)["name"]
        family, typographic, style = names.getDebugName(1), names.getDebugName(16), names.getDebugName(2)
        # RIBBI = a plain Regular/Italic/Bold/Bold Italic that sits in the family named by nameID 1 (no wider or lighter family name)
        if style in RIBBI_STYLES and (not typographic or typographic == family):
            ribbi.append(path)
    if len(ribbi) == len(paths):
        ribbi = []   # a family made only of RIBBI styles needs no subfolder
    if ribbi:
        target = os.path.join(folder, FOLDER_RIBBI)
        os.makedirs(target, exist_ok=True)
        for path in ribbi:
            shutil.move(path, os.path.join(target, os.path.basename(path)))
    log("   Windows Font Fix (%s): %d fonts, %d RIBBI moved to %s" % (", ".join(steps) or "no steps", len(paths), len(ribbi), FOLDER_RIBBI))
    return problems


def copy_template_files(template_dir, release_dir, label, groups, log=print):
    """README (with the version line updated) and the non-font files of the web folder, from the previous release."""
    for name in sorted(os.listdir(template_dir)):
        source = os.path.join(template_dir, name)
        if name.startswith(".") or not os.path.isfile(source):
            continue
        if name.lower().startswith("readme") and name.lower().endswith((".txt", ".md")):
            with open(source, encoding="utf-8") as fh:
                text = fh.read()
            text = VERSION_LINE.sub("Version " + label, text, count=1)
            with open(os.path.join(release_dir, name), "w", encoding="utf-8") as fh:
                fh.write(text)
            log("   %s (version line: %s)" % (name, label))
        else:
            shutil.copy2(source, os.path.join(release_dir, name))
            log("   %s (copied from %s)" % (name, os.path.basename(template_dir)))
    web = os.path.join(template_dir, FOLDER_WEB)
    if "web" in groups and os.path.isdir(web):
        os.makedirs(os.path.join(release_dir, FOLDER_WEB), exist_ok=True)
        for name in sorted(os.listdir(web)):
            if name.startswith(".") or name.lower().endswith(WEB_FONT_EXTENSIONS):
                continue
            shutil.copy2(os.path.join(web, name), os.path.join(release_dir, FOLDER_WEB, name))
            log("   %s/%s (copied from %s)" % (FOLDER_WEB, name, os.path.basename(template_dir)))


def summary(font, release_dir):
    """What the release folder holds, against what the font defines."""
    static = active_instances(font, INSTANCETYPESINGLE)
    ttf_folder = os.path.join(release_dir, FOLDER_TTF)
    ttf_count = len(font_files(ttf_folder, (".ttf",))) + len(font_files(os.path.join(ttf_folder, FOLDER_RIBBI), (".ttf",)))
    return {
        "static instances": len(static),
        FOLDER_VARIABLE: len(font_files(os.path.join(release_dir, FOLDER_VARIABLE), (".ttf",))),
        FOLDER_WEB: len(font_files(os.path.join(release_dir, FOLDER_WEB), WEB_FONT_EXTENSIONS)),
        FOLDER_OTF: len(font_files(os.path.join(release_dir, FOLDER_OTF), (".otf",))),
        FOLDER_TTF + " (incl. RIBBI)": ttf_count,
    }


def run_export(font, output_dir, label, groups, template_name, log=print):
    output_dir, label = str(output_dir), str(label)
    release_dir = os.path.join(output_dir, label)
    if os.path.isdir(release_dir) and os.listdir(release_dir) and any(not n.startswith(".") for n in os.listdir(release_dir)):
        if not askYesNo("The folder %s is not empty. Export into it anyway?" % label, informativeText="Files with the same name are replaced."):
            log("Cancelled: %s is not empty." % label)
            return None
    log("Exporting %s → %s" % (font.familyName, release_dir))
    started = time.time()
    template_dir = os.path.join(output_dir, template_name) if template_name else None
    problems = export_release(font, release_dir, groups, template_dir, label, log)
    log("Done in %.0f s. %s" % (time.time() - started, ", ".join("%s: %s" % kv for kv in summary(font, release_dir).items())))
    for problem in problems:
        log("‼️ " + problem)
    return problems


# ===== Window =====

class ExportReleaseWindow(object):
    def __init__(self, font):
        self.font = font
        self.output_dir = default_output_dir(font)
        self.w = vanilla.FloatingWindow((470, 318), TITLE)
        y = 14
        self.w.intro = vanilla.TextBox((15, y, -15, 30), "Exports %s into a dated release folder, with the structure of the previous release." % font.familyName, sizeStyle="small")
        y += 40
        self.w.labelLabel = vanilla.TextBox((15, y + 3, 110, 18), "Release folder:")
        self.w.label = vanilla.EditText((130, y, -15, 22), time.strftime("%y.%m.%d"))
        self.w.label.getNSTextField().setToolTip_("Name of the new folder inside the output folder: yy.mm.dd. It also becomes the version line of the README.")
        y += 32
        self.w.outLabel = vanilla.TextBox((15, y + 3, 110, 18), "Output folder:")
        self.w.outPath = vanilla.TextBox((130, y + 3, -100, 18), self.output_dir or "Choose a folder…", sizeStyle="small")
        self.w.outChoose = vanilla.Button((-90, y, -15, 22), "Choose…", callback=self.choose_output)
        y += 32
        self.w.templateLabel = vanilla.TextBox((15, y + 3, 150, 18), "README and web sample:")
        self.w.template = vanilla.PopUpButton((170, y, -15, 22), [])
        self.w.template.getNSPopUpButton().setToolTip_("The previous release the README, CSS and HTML are copied from. The version line of the README is updated.")
        self.refresh_templates()
        y += 36
        self.boxes = {}
        labels = (
            ("variable", "%s  (TTF)" % FOLDER_VARIABLE, "The variable font as TTF, without autohint."),
            ("web", "%s  (WOFF2 + CSS + HTML)" % FOLDER_WEB, "The variable font as WOFF2, plus the CSS and HTML sample from the previous release."),
            ("otf", "%s" % FOLDER_OTF, "One OTF per active static instance, autohinted, overlaps removed."),
            ("ttf", "%s  (+ Windows Font Fix, RIBBI subfolder)" % FOLDER_TTF, "One TTF per active static instance, then Windows Font Fix (its menu choices apply) and the four RIBBI styles into their own subfolder."),
        )
        for key, label, tip in labels:
            stored = Glyphs.defaults[DEFAULTS_PREFIX + key]
            box = vanilla.CheckBox((15, y, -15, 20), label, value=True if stored is None else bool(stored), callback=self.remember)
            box.getNSButton().setToolTip_(tip)
            setattr(self.w, "group_" + key, box)
            self.boxes[key] = box
            y += 24
        y += 12
        self.w.cancel = vanilla.Button((-190, y, -105, 22), "Cancel", callback=self.cancel)
        self.w.export = vanilla.Button((-95, y, -15, 22), "Export", callback=self.export)
        self.w.setDefaultButton(self.w.export)
        self.w.open()
        self.w.makeKey()

    def refresh_templates(self):
        label = self.w.label.get().strip()
        names = previous_releases(self.output_dir, exclude=label)
        self.template_names = names
        self.w.template.setItems(names + ["None"])
        self.w.template.set(0)

    def choose_output(self, sender):
        folder = getFolder(messageText="Choose the folder that holds the release folders (the Output folder)", directory=self.output_dir or None)
        if folder:
            # getFolder returns an NSArray (not a list/tuple) of paths
            first = folder if isinstance(folder, str) else folder[0]
            self.output_dir = str(first)
            self.w.outPath.set(self.output_dir)
            Glyphs.defaults[DEFAULTS_PREFIX + "outputDir"] = self.output_dir
            self.refresh_templates()

    def remember(self, sender):
        for key, box in self.boxes.items():
            Glyphs.defaults[DEFAULTS_PREFIX + key] = bool(box.get())

    def chosen_groups(self):
        return tuple(k for k in GROUPS if self.boxes[k].get())

    def export(self, sender):
        label = self.w.label.get().strip()
        if not RELEASE_NAME.match(label):
            Message("Enter a name for the release folder, such as 26.10.26 (yy.mm.dd). It cannot contain / \\ : * ? \" < > |.", TITLE)
            return
        if not self.output_dir:
            Message("Choose the output folder first.", TITLE)
            return
        groups = self.chosen_groups()
        if not groups:
            Message("Choose at least one folder to export.", TITLE)
            return
        index = self.w.template.get()
        template = self.template_names[index] if index < len(self.template_names) else None
        self.w.close()
        Glyphs.clearLog()
        problems = run_export(self.font, self.output_dir, label, groups, template)
        Glyphs.showMacroWindow()
        if problems is not None:
            Glyphs.showNotification(TITLE, "Release %s exported%s." % (label, " with problems, see the Macro Panel" if problems else ""))

    def cancel(self, sender):
        self.w.close()


def main():
    font = Glyphs.font
    if font is None:
        raise RuntimeError("Open a font before running this script.")
    return ExportReleaseWindow(font)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Message(str(e), TITLE)
