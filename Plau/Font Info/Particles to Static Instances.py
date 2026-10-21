#MenuTitle: Particles to Static Instances
# -*- coding: utf-8 -*-
__doc__ = """
Turns the name particles of the variable export (Glyphs 4) into static instances, one per
weight x slant, with Windows (RIBBI) style linking:

  Upright family:    Regular + Bold, with Slant -> Italic and Bold Slant -> Bold Italic
  Other weights:     "Light" + "Light Slant" (linked as its italic), and so on
  Backslant:         its own group: "Backslant" + "Bold Backslant" (linked as bold);
                     other weights' Backslant stand alone

Run it with the font open. Nothing is deleted unless you change the settings.
"""

from GlyphsApp import Glyphs, GSInstance, INSTANCETYPESINGLE, INSTANCETYPEVARIABLE

# ---------- settings ----------
DRY_RUN = False             # True = only print what would be created
SKIP_EXISTING = True        # skip a combination if a static instance already sits at those coordinates
REMOVE_PARTICLES = False    # True = clear the name particles of the variable export afterwards (avoids duplicate named instances in the VF)
MAX_NAME = 32               # warn when "Family Style" is longer than this (Word on Windows)
# ------------------------------

WEIGHT_TAGS = ("wght",)
SLOPE_TAGS = ("slnt", "ital")


def style_name(weight_name, slope_name):
	parts = [p for p in (weight_name, slope_name) if p and p != "Regular"]
	return " ".join(parts) or "Regular"


def plan(weights, slopes):
	"""
	weights: list of dicts {name, internal, external}
	slopes:  list of dicts {name, internal, role}  role in ("upright", "italic", "backslant")
	returns a list of dicts describing each instance (pure Python, no Glyphs objects)
	"""
	backslant_base = style_name("Regular", next((s["name"] for s in slopes if s["role"] == "backslant"), None))
	out = []
	for w in weights:
		for s in slopes:
			name = style_name(w["name"], s["name"])
			is_bold = is_italic = False
			link = ""
			if s["role"] == "upright":
				if w["name"] == "Bold":
					is_bold, link = True, "Regular"
			elif s["role"] == "italic":
				is_italic = True
				if w["name"] == "Bold":
					is_bold, link = True, "Regular"
				else:
					link = style_name(w["name"], None)
			elif s["role"] == "backslant":
				if w["name"] == "Bold":
					is_bold, link = True, backslant_base
			out.append(dict(
				name=name, weight=w, slope=s,
				weightClass=int(w.get("external") or w["internal"]),
				isBold=is_bold, isItalic=is_italic, linkStyle=link,
			))
	return out


def read_particles(font):
	"""The instance holding the name particles (Glyphs 4 keeps them per axis on the variable export)."""
	holders = [i for i in font.instances if any(len(v) for v in i.nameParticles.values())]
	holders.sort(key=lambda i: i.type != INSTANCETYPEVARIABLE)
	if not holders:
		return None, None
	return holders[0], holders[0].nameParticles


def particle_list(particles, axis):
	"""Active particles of an axis as plain dicts, sorted by their design-space position."""
	out = []
	for p in particles.get(axis.axisId, []):
		if p.active:
			out.append(dict(name=p.name, internal=p.internal, external=p.external))
	return sorted(out, key=lambda p: p["internal"])


def axis_index(font, tags):
	for i, ax in enumerate(font.axes):
		if ax.axisTag in tags:
			return i
	return None


def slope_role(font, slope_index, value):
	"""upright / italic / backslant, read from the italic angle of a master at that slant."""
	if value == 0:
		return "upright"
	for m in font.masters:
		if abs(m.axes[slope_index] - value) < 0.01:
			angle = m.italicAngle or 0
			if angle > 0:
				return "italic"
			if angle < 0:
				return "backslant"
	# OpenType slnt: negative = leaning right (italic), positive = leaning left
	return "italic" if value < 0 else "backslant"


def instance_axes(inst):
	return list(inst.internalAxesValues)


def set_instance_axes(inst, values):
	inst.internalAxesValues = values


def run():
	font = Glyphs.font
	Glyphs.clearLog()
	if not font:
		print("Open a font first.")
		return
	pinst, particles = read_particles(font)
	if not particles:
		print("No particles export found in this font.")
		return

	wi = axis_index(font, WEIGHT_TAGS)
	si = axis_index(font, SLOPE_TAGS)
	if wi is None:
		print("No weight axis (wght) found.")
		return

	weights = particle_list(particles, font.axes[wi])
	if not weights:
		print("The weight axis has no active name particles.")
		return
	slopes = particle_list(particles, font.axes[si]) if si is not None else []
	if not slopes:
		si = None
		slopes = [dict(name="Regular", internal=0, external=None)]
	for s in slopes:
		s["role"] = slope_role(font, si, s["internal"]) if si is not None else "upright"
	order = {"upright": 0, "italic": 1, "backslant": 2}
	slopes.sort(key=lambda s: order[s["role"]])

	family = font.familyName
	existing = []
	for inst in font.instances:
		if inst.type == INSTANCETYPESINGLE:
			existing.append(tuple(round(v, 2) for v in instance_axes(inst)))

	created = skipped = 0
	for p in plan(weights, slopes):
		coords = [0] * len(font.axes)
		coords[wi] = p["weight"]["internal"]
		if si is not None:
			coords[si] = p["slope"]["internal"]
		tag = "  "
		if SKIP_EXISTING and tuple(round(float(v), 2) for v in coords) in existing:
			skipped += 1
			tag = "= "
		elif not DRY_RUN:
			inst = GSInstance()
			inst.name = p["name"]
			font.instances.append(inst)
			set_instance_axes(inst, coords)
			inst.weightClass = p["weightClass"]
			inst.isBold = p["isBold"]
			inst.isItalic = p["isItalic"]
			inst.linkStyle = p["linkStyle"]
			created += 1
		link = ""
		if p["isBold"] or p["isItalic"] or p["linkStyle"]:
			link = "-> %s%s%s" % (p["linkStyle"] or "(none)", " bold" if p["isBold"] else "", " italic" if p["isItalic"] else "")
		full = "%s %s" % (family, p["name"])
		warn = "  !! %d chars" % len(full) if len(full) > MAX_NAME else ""
		print("%s%-22s %-6s %s%s" % (tag, p["name"], p["weightClass"], link, warn))

	if REMOVE_PARTICLES and not DRY_RUN and pinst is not None:
		pinst.nameParticles = {}
		print("Cleared the name particles of '%s'." % pinst.name)

	print("\n%s %d instances, skipped %d that already existed (=)." % (
		"Would create" if DRY_RUN else "Created", created if not DRY_RUN else len(weights) * len(slopes) - skipped, skipped))
	Glyphs.showMacroWindow()


if __name__ == "__main__":
	run()
