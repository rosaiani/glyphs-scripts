#MenuTitle: Build Arrows from Hyphen
# -*- coding: utf-8 -*-
# Shortcut: cmd+opt+shift+a
# Description: Cria setas (← → ↑ ↓ ↔ ↕) a partir do hyphen como componente, em TODAS as masters.
# Usa largura base do emdash (se existir) ou hyphen×fator. Espessura (haste/cabeça) baseada no
# “stem” vertical da master (ou espessura do hyphen, como fallback). UI redimensionável.
# Se o glifo já existir, pode perguntar/ignorar/substituir (com backup das layers).

from GlyphsApp import Glyphs, GSComponent, GSGlyph, GSPath, GSNode, GSLayer, Message, LINE
import vanilla
from datetime import datetime

# ===== Defaults =====
DEFAULT_WIDTH_FACTOR = 1.80   # largura base p/ setas horizontais se não houver emdash
DEFAULT_HEAD_PCT     = 0.25   # % da largura destinada a cada cabeça (por ponta)
DEFAULT_HEAD_THICK   = 1.00   # multiplicador sobre o STEM para a altura da cabeça

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
    if not g:
        g = GSGlyph(name)
        g.unicode = UNICODES.get(name)
        font.glyphs.append(g)
    return g

def clear_layer(layer):
    layer.shapes = []

def hyphen_or_minus(font):
    return font.glyphs['hyphen'] or font.glyphs['hyphen-minus']

def add_component(layer, baseName, sx=1.0, sy=1.0, dx=0.0, dy=0.0):
    c = GSComponent(baseName)
    c.automaticAlignment = False
    layer.shapes.append(c)
    c.applyTransform((sx, 0.0, 0.0, sy, dx, dy))
    return c

def add_triangle(layer, baseX, centerY, height, length, direction='right'):
    halfH = height * 0.5
    if direction == 'right':
        pts = [(baseX, centerY + halfH), (baseX, centerY - halfH), (baseX + length, centerY)]
    elif direction == 'left':
        pts = [(baseX, centerY + halfH), (baseX, centerY - halfH), (baseX - length, centerY)]
    elif direction == 'up':
        pts = [(centerY + halfH, baseX), (centerY - halfH, baseX), (centerY, baseX + length)]
    elif direction == 'down':
        pts = [(centerY + halfH, baseX), (centerY - halfH, baseX), (centerY, baseX - length)]
    else:
        return
    path = GSPath()
    for x, y in pts:
        path.nodes.append(GSNode((x, y), type=LINE))
    path.closed = True
    layer.shapes.append(path)

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

def get_vertical_stem(master, fallback):
    # tenta parâmetros conhecidos nas masters
    for key in ("verticalStems", "Vertical Stems", "stems", "Stems"):
        try:
            v = master.customParameters.get(key)
        except Exception:
            v = None
        n = first_number(v)
        if n is not None and n > 0:
            return n
    return fallback

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

# ===== Builders =====

def build_horizontal(font, name, factor, head_pct, head_thick, stem_per_master, replace_mode):
    hy = hyphen_or_minus(font)
    if not hy:
        raise RuntimeError('Glifo "hyphen" não encontrado.')
    g = ensure_glyph(font, name)

    # substituição/backup
    if replace_mode in ("replace_backup", "ask"):
        has_content = any(len(lyr.shapes) for lyr in g.layers)
        if has_content and replace_mode == "replace_backup":
            backup_glyph_layers(g)

    em = font.glyphs['emdash']

    for m in font.masters:
        mid = m.id
        hL = hy.layers[mid]
        dL = g.layers[mid]
        eL = em.layers[mid] if em else None

        if replace_mode == "skip" and len(dL.shapes):
            continue
        if replace_mode == "ask" and len(dL.shapes):
            backup_glyph_layers(g)

        clear_layer(dL)

        # medidas base
        h_LSB, h_RSB, hW = hL.LSB, hL.RSB, hL.width
        hb = hL.bounds
        base_shape_w = hW - h_LSB - h_RSB
        base_thickness = hb.size.height if hb.size.height else 1.0

        # STEM por master
        stem = stem_per_master.get(mid) or base_thickness

        # largura alvo
        desired_width = (eL.width if eL else hW * factor)

        # cabeça
        head_len = desired_width * head_pct
        head_h = stem * head_thick

        # haste (desenho sem SBs e sem cabeça)
        shaft_shape_w = max(0.0, desired_width - head_len - h_LSB - h_RSB)

        # escalas
        sx_len = (shaft_shape_w / base_shape_w) if base_shape_w else 1.0
        sy_thick = (stem / base_thickness) if base_thickness else 1.0

        # manter LSB e centroY
        centerY = hb.origin.y + hb.size.height * 0.5
        dx = h_LSB * (1.0 - sx_len)
        dy = centerY * (1.0 - sy_thick)

        comp = add_component(dL, hy.name)
        comp.applyTransform((1.0, 0.0, 0.0, sy_thick, 0.0, dy))      # espessura
        comp.applyTransform((sx_len, 0.0, 0.0, 1.0, dx, 0.0))        # comprimento

        # cabeça direita
        comp_bounds = comp.bounds
        baseX = comp_bounds.origin.x + comp_bounds.size.width
        add_triangle(dL, baseX, centerY, head_h, head_len, direction='right')

        dL.width = int(round(desired_width))
        set_metrics_keys(g, hy.name)
        try:
            dL.syncMetrics()
        except Exception:
            pass

    if name == 'arrowleftright':
        for m in font.masters:
            dL = g.layers[m.id]
            hL = hy.layers[m.id]
            hb = hL.bounds
            centerY = hb.origin.y + hb.size.height * 0.5
            stem = stem_per_master.get(m.id) or hb.size.height
            head_h = stem * head_thick
            head_len = dL.width * head_pct
            baseX_left = hL.LSB
            add_triangle(dL, baseX_left, centerY, head_h, head_len, direction='left')

def build_vertical(font, name, factor, head_pct, head_thick, stem_per_master, replace_mode):
    hy = hyphen_or_minus(font)
    if not hy:
        raise RuntimeError('Glifo "hyphen" não encontrado.')
    g = ensure_glyph(font, name)

    if replace_mode in ("replace_backup", "ask"):
        has_content = any(len(lyr.shapes) for lyr in g.layers)
        if has_content and replace_mode == "replace_backup":
            backup_glyph_layers(g)

    for m in font.masters:
        mid = m.id
        hL = hy.layers[mid]
        dL = g.layers[mid]

        if replace_mode == "skip" and len(dL.shapes):
            continue
        if replace_mode == "ask" and len(dL.shapes):
            backup_glyph_layers(g)

        clear_layer(dL)

        # base do hyphen
        h_LSB, h_RSB, hW = hL.LSB, hL.RSB, hL.width
        hb = hL.bounds
        base_thickness = hb.size.height if hb.size.height else 1.0

        # parâmetros por master
        stem = stem_per_master.get(mid) or base_thickness
        H = m.capHeight or m.xHeight or 0
        desired_extent = H  # comprimento total da seta (topo a base)

        # avanço horizontal igual ao hyphen
        dL.width = hW

        # cabeças
        head_len = desired_extent * head_pct
        head_h = stem * head_thick

        # haste: comprimento livre
        shaft_len = max(0.0, desired_extent - 2.0 * head_len)

        # escalas no componente (antes da rotação):
        # X → espessura (stem), Y → comprimento (shaft_len), depois rotaciona 90°
        sx_thick = (stem / base_thickness) if base_thickness else 1.0
        sy_len   = (shaft_len / hb.size.height) if hb.size.height else 1.0

        comp = GSComponent(hy.name)
        comp.automaticAlignment = False
        dL.shapes.append(comp)

        comp.applyTransform((sx_thick, 0.0, 0.0, sy_len, 0.0, 0.0))
        comp.applyTransform((0.0, 1.0, -1.0, 0.0, 0.0, 0.0))  # rot 90°
        comp_bounds = comp.bounds
        dx = (dL.width - comp_bounds.size.width) * 0.5 - comp_bounds.origin.x
        dy = (head_len) - comp_bounds.origin.y
        comp.applyTransform((1.0, 0.0, 0.0, 1.0, dx, dy))

        # cabeças
        comp_bounds = comp.bounds
        baseTop = comp_bounds.origin.y + comp_bounds.size.height
        baseBottom = comp_bounds.origin.y
        centerX = comp_bounds.origin.x + comp_bounds.size.width * 0.5
        add_triangle(dL, baseTop, centerX, head_h, head_len, direction='up')
        add_triangle(dL, baseBottom, centerX, head_h, head_len, direction='down')

        set_metrics_keys(g, hy.name)
        try:
            dL.syncMetrics()
        except Exception:
            pass

# ===== UI =====
class ArrowBuilderUI(object):
    def __init__(self):
        # janela redimensionável com autosave
        self.w = vanilla.FloatingWindow(
            (560, 420), "Build Arrows from Hyphen",
            minSize=(520, 380), autosaveName="com.plau.buildArrowsWindowV2"
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
        self.w.lblHT= vanilla.TextBox((16, y, 180, 20), "Head height × STEM:")
        self.w.edHT = vanilla.EditText((200, y, -16, 22), f"{DEFAULT_HEAD_THICK}"); y+=28

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
            head_thick = float(self.w.edHT.get())
        except Exception:
            Message('Parâmetros inválidos.', 'Build Arrows')
            return

        mode_idx = self.w.existOpt.get()
        replace_mode = ('replace_backup', 'skip', 'ask')[mode_idx]

        hy = hyphen_or_minus(font)
        if not hy:
            Message('Glifo "hyphen" não encontrado.', 'Build Arrows')
            return

        # STEM por master (com fallback na espessura do hyphen)
        stem_per_master = {}
        for m in font.masters:
            hb = hy.layers[m.id].bounds
            fallback = hb.size.height if hb.size.height else 50.0
            stem_per_master[m.id] = get_vertical_stem(m, fallback)

        todo = []
        if self.w.chkL.get(): todo.append('arrowleft')
        if self.w.chkR.get(): todo.append('arrowright')
        if self.w.chkU.get(): todo.append('arrowup')
        if self.w.chkD.get(): todo.append('arrowdown')
        if self.w.chkLR.get(): todo.append('arrowleftright')
        if self.w.chkUD.get(): todo.append('arrowupdown')

        try:
            for name in todo:
                if name in ('arrowright','arrowleft','arrowleftright'):
                    build_horizontal(font, name, width_factor, head_pct, head_thick, stem_per_master, replace_mode)
                else:
                    build_vertical(font, name, width_factor, head_pct, head_thick, stem_per_master, replace_mode)
        except Exception as e:
            Message(str(e), 'Build Arrows')
            return

        print('✅ Arrows criadas/atualizadas:', ', '.join(todo))
        self.w.close()

if __name__ == '__main__':
    ArrowBuilderUI()
