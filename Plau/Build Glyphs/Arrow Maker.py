#MenuTitle: Build Arrows from Hyphen
# -*- coding: utf-8 -*-
# Shortcut: cmd+opt+shift+a
# Description: Builds arrows (← → ↑ ↓ ↔ ↕) in ALL masters with native Glyphs 4 strokes: a shaft and a V-shaped head
# (open paths with strokeWidth/strokeHeight), no outlines. Stroke weight comes from the master's stems (Font Info → Stems);
# if none exist, the hyphen's thickness is used. Horizontal width = emdash (if present) or hyphen × factor.
# If a glyph already exists, you can skip it or replace it (with a backup of its layers).

__doc__ = """
Builds arrows (← → ↑ ↓ ↔ ↕) in every master from native Glyphs 4 strokes: a shaft plus a V-shaped head, no outlines.
Stroke weight follows each master's stems (Font Info → Stems), falling back to the hyphen's thickness.
Opens a window to choose the arrows, proportions and what to do with existing glyphs. Needs hyphen; uses the emdash width if present.
"""

from GlyphsApp import Glyphs, GSGlyph, GSPath, GSNode, GSLayer, Message, LINE
import vanilla
from datetime import datetime

# ===== Defaults =====
DEFAULT_WIDTH_FACTOR = 1.80   # largura base p/ setas horizontais se não houver emdash
DEFAULT_HEAD_PCT     = 0.25   # comprimento da ponta, em % da largura da seta
DEFAULT_HEAD_RATIO   = 1.00   # meia-altura da ponta ÷ comprimento da ponta (1.0 = braços a 45°)

UNICODES = {
    'arrowleft':      '2190',
    'arrowup':        '2191',
    'arrowright':     '2192',
    'arrowdown':      '2193',
    'arrowleftright': '2194',
    'arrowupdown':    '2195',
}

# ===== Helpers =====

def ensure_glyph(font, name):
    g = font.glyphs[name]
    if not g and name in UNICODES:
        # Glyphs 4 renomeia ao definir o unicode (arrowright -> rightArrow); procura pelo unicode
        g = font.glyphs[UNICODES[name]]
    if not g:
        g = GSGlyph(name)
        g.unicode = UNICODES.get(name)
        font.glyphs.append(g)
    return g

def clear_layer(layer):
    layer.shapes = []

def hyphen_or_minus(font):
    return font.glyphs['hyphen'] or font.glyphs['hyphen-minus']

def set_metrics_keys(glyph, baseName='hyphen'):
    glyph.leftMetricsKey = f'={baseName}'
    glyph.rightMetricsKey = f'={baseName}'

def first_number(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, (list, tuple)) and x:
        try:
            return float(x[0])
        except Exception:
            return None
    if isinstance(x, str):
        import re
        m = re.search(r"-?\d+(?:\.\d+)?", x)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return None
    return None

def get_stems(font, master, fallback):
    """(horizontal, vertical) = espessura dos traços horizontais e verticais nesta master.
    Lê font.stems / master.stems (Glyphs 4); se não houver, parâmetros antigos; senão `fallback`."""
    h = v = None
    try:
        for stem in font.stems:
            value = first_number(master.stems[stem.id])
            if not value or value <= 0:
                continue
            if stem.horizontal:
                h = h or value
            else:
                v = v or value
    except Exception:
        pass
    if v is None:
        for key in ("verticalStems", "Vertical Stems", "stems", "Stems"):
            try:
                n = first_number(master.customParameters.get(key))
            except Exception:
                n = None
            if n is not None and n > 0:
                v = n
                break
    h = h or fallback
    v = v or h
    return h, v

def add_stroke(layer, points, h_stem, v_stem):
    """Path aberto com stroke nativo: traços horizontais com h_stem de espessura, verticais com v_stem."""
    path = GSPath()
    for x, y in points:
        path.nodes.append(GSNode((x, y), type=LINE))
    path.closed = False
    path.attributes['strokeHeight'] = h_stem
    path.attributes['strokeWidth'] = v_stem
    path.attributes['strokePos'] = 0      # centrado no path
    path.attributes['lineCapStart'] = 0   # butt
    path.attributes['lineCapEnd'] = 0
    path.attributes['lineJoin'] = 0       # miter
    layer.shapes.append(path)
    return path

def backup_glyph_layers(glyph):
    """Cria layers de backup (special layers) com cópia de cada master layer existente."""
    ts = datetime.now().strftime("backup %Y-%m-%d %H:%M")
    for layer in list(glyph.layers):
        if not layer:
            continue
        newLayer = GSLayer()
        newLayer.name = ts
        try:
            newLayer.associatedMasterId = layer.associatedMasterId or layer.master.id
        except Exception:
            try:
                newLayer.associatedMasterId = layer.master.id
            except Exception:
                pass
        newLayer.width = layer.width
        for sh in layer.shapes:
            newLayer.shapes.append(sh.copy())
        glyph.layers.append(newLayer)

# ===== Geometria =====
# Cada seta é um eixo (tail → tip) mais uma ou duas pontas em V. Tudo em coordenadas (along, across):
# `along` corre ao longo da seta, `across` é perpendicular. Para setas horizontais along = x, across = y;
# para as verticais os eixos trocam.

def arrow_points(start, end, across, head_len, head_half, heads):
    """Retorna a lista de polilinhas (em along/across) de uma seta.
    heads: 'end', 'start' ou 'both'."""
    lines = [[(start, across), (end, across)]]
    if heads in ('end', 'both'):
        lines.append([(end - head_len, across + head_half), (end, across), (end - head_len, across - head_half)])
    if heads in ('start', 'both'):
        lines.append([(start + head_len, across + head_half), (start, across), (start + head_len, across - head_half)])
    return lines

def draw_arrow(layer, start, end, across, head_len, head_half, heads, vertical, h_stem, v_stem):
    """Desenha a seta fazendo com que a extremidade externa (incluindo o bico do miter) caia
    exatamente em start/end. Constrói, mede o excesso do bico e reconstrói com o recuo certo."""
    inset_start = inset_end = 0.0
    for _ in range(2):
        clear_layer(layer)
        lines = arrow_points(start + inset_start, end - inset_end, across, head_len, head_half, heads)
        for pts in lines:
            if vertical:
                pts = [(a, b) for b, a in pts]
            add_stroke(layer, pts, h_stem, v_stem)
        b = layer.bounds
        lo, hi = (b.origin.y, b.origin.y + b.size.height) if vertical else (b.origin.x, b.origin.x + b.size.width)
        if heads in ('end', 'both'):
            inset_end += hi - end
        if heads in ('start', 'both'):
            inset_start += start - lo

# ===== Builders =====

def prepare(font, name, replace_mode):
    g = ensure_glyph(font, name)
    if replace_mode in ("replace_backup", "ask"):
        has_content = any(len(lyr.shapes) for lyr in g.layers)
        if has_content:
            backup_glyph_layers(g)
    return g

def build_horizontal(font, name, factor, head_pct, head_ratio, replace_mode):
    hy = hyphen_or_minus(font)
    if not hy:
        raise RuntimeError('Glifo "hyphen" não encontrado.')
    g = prepare(font, name, replace_mode)
    em = font.glyphs['emdash']
    heads = {'arrowright': 'end', 'arrowleft': 'start', 'arrowleftright': 'both'}[name]

    for m in font.masters:
        mid = m.id
        hL = hy.layers[mid]
        dL = g.layers[mid]
        if replace_mode == "skip" and len(dL.shapes):
            continue

        hb = hL.bounds
        h_stem, v_stem = get_stems(font, m, hb.size.height or 50.0)
        desired_width = em.layers[mid].width if em else hL.width * factor

        start = hL.LSB
        end = desired_width - hL.RSB
        head_len = (end - start) * head_pct
        head_half = head_len * head_ratio
        across = hb.origin.y + hb.size.height * 0.5   # na altura do hyphen

        dL.width = int(round(desired_width))
        draw_arrow(dL, start, end, across, head_len, head_half, heads, False, h_stem, v_stem)

        set_metrics_keys(g, hy.name)
        dL.syncMetrics()

def build_vertical(font, name, factor, head_pct, head_ratio, replace_mode):
    hy = hyphen_or_minus(font)
    if not hy:
        raise RuntimeError('Glifo "hyphen" não encontrado.')
    g = prepare(font, name, replace_mode)
    heads = {'arrowup': 'end', 'arrowdown': 'start', 'arrowupdown': 'both'}[name]

    for m in font.masters:
        mid = m.id
        hL = hy.layers[mid]
        dL = g.layers[mid]
        if replace_mode == "skip" and len(dL.shapes):
            continue

        hb = hL.bounds
        h_stem, v_stem = get_stems(font, m, hb.size.height or 50.0)

        # comprimento da baseline à altura de maiúscula
        start = 0.0
        end = m.capHeight or m.xHeight or 0
        head_len = (end - start) * head_pct
        head_half = head_len * head_ratio
        across = hL.width / 2.0

        dL.width = hL.width
        draw_arrow(dL, start, end, across, head_len, head_half, heads, True, h_stem, v_stem)

        set_metrics_keys(g, hy.name)
        dL.syncMetrics()

# ===== UI =====
class ArrowBuilderUI(object):
    def __init__(self):
        # janela redimensionável com autosave
        self.w = vanilla.FloatingWindow(
            (560, 420), "Build Arrows from Hyphen",
            minSize=(520, 380), autosaveName="com.plau.buildArrowsWindowV3"
        )

        y = 12
        self.w.chkL = vanilla.CheckBox((16, y, 220, 20), "← arrowleft", value=True); y+=22
        self.w.chkR = vanilla.CheckBox((16, y, 220, 20), "→ arrowright", value=True); y+=22
        self.w.chkU = vanilla.CheckBox((16, y, 220, 20), "↑ arrowup", value=False); y+=22
        self.w.chkD = vanilla.CheckBox((16, y, 220, 20), "↓ arrowdown", value=False); y+=22
        self.w.chkLR= vanilla.CheckBox((16, y, 220, 20), "↔ arrowleftright", value=False); y+=22
        self.w.chkUD= vanilla.CheckBox((16, y, 220, 20), "↕ arrowupdown", value=False); y+=28

        self.w.lblW = vanilla.TextBox((16, y, 180, 20), "Width factor (→):")
        self.w.edW  = vanilla.EditText((200, y, -16, 22), f"{DEFAULT_WIDTH_FACTOR}"); y+=26
        self.w.lblHP= vanilla.TextBox((16, y, 180, 20), "Head length %:")
        self.w.edHP = vanilla.EditText((200, y, -16, 22), f"{int(DEFAULT_HEAD_PCT*100)}"); y+=26
        self.w.lblHT= vanilla.TextBox((16, y, 180, 20), "Head half-height ÷ length:")
        self.w.edHT = vanilla.EditText((200, y, -16, 22), f"{DEFAULT_HEAD_RATIO}"); y+=28

        self.w.lblExist = vanilla.TextBox((16, y, 180, 20), "If glyph exists:")
        self.w.existOpt = vanilla.PopUpButton((200, y, 200, 22),
            ["Replace & Backup", "Skip", "Ask (backup then replace)"]); y+=34

        self.w.btn = vanilla.Button((16, -44, -16, 32), "Build", callback=self.build)

        self.w.open()
        self.w.makeKey()

    def build(self, sender):
        font = Glyphs.font
        if not font:
            Message('Abra uma fonte no Glyphs.', 'Build Arrows')
            return
        try:
            width_factor = float(self.w.edW.get())
            head_pct = float(self.w.edHP.get())/100.0
            head_ratio = float(self.w.edHT.get())
        except Exception:
            Message('Parâmetros inválidos.', 'Build Arrows')
            return

        mode_idx = self.w.existOpt.get()
        replace_mode = ('replace_backup', 'skip', 'ask')[mode_idx]

        if not hyphen_or_minus(font):
            Message('Glifo "hyphen" não encontrado.', 'Build Arrows')
            return

        todo = []
        if self.w.chkL.get(): todo.append('arrowleft')
        if self.w.chkR.get(): todo.append('arrowright')
        if self.w.chkU.get(): todo.append('arrowup')
        if self.w.chkD.get(): todo.append('arrowdown')
        if self.w.chkLR.get(): todo.append('arrowleftright')
        if self.w.chkUD.get(): todo.append('arrowupdown')

        font.disableUpdateInterface()  # batch the changes: the sidebar would re-filter after every new glyph
        try:
            for name in todo:
                if name in ('arrowright','arrowleft','arrowleftright'):
                    build_horizontal(font, name, width_factor, head_pct, head_ratio, replace_mode)
                else:
                    build_vertical(font, name, width_factor, head_pct, head_ratio, replace_mode)
        except Exception as e:
            Message(str(e), 'Build Arrows')
            return
        finally:
            font.enableUpdateInterface()

        print('✅ Arrows criadas/atualizadas:', ', '.join(todo))
        self.w.close()

if __name__ == '__main__':
    ArrowBuilderUI()
