# -*- coding: utf-8 -*-
# MenuTitle: Plau – Build En/Em Dashes from Hyphen (component + width %)
# Shortcut: cmd+opt+shift+d
# Description: Cria endash (–) e emdash (—) a partir do hyphen, usando o hyphen como componente. endash = 140% da largura do hyphen; emdash = 180%. LSB/RSB paramétricos: =hyphen.

from GlyphsApp import Glyphs, GSComponent, GSGlyph, Message

EN_FACTOR = 1.40  # 140%
EM_FACTOR = 1.80  # 180%

DASHES = (
    ("endash", EN_FACTOR),  # U+2013
    ("emdash", EM_FACTOR),  # U+2014
)


def ensure_glyph(font, name):
    """Garante a existência do glifo pelo nome, criando com GSGlyph(name) se necessário."""
    g = font.glyphs[name]
    if not g:
        g = GSGlyph(name)
        font.glyphs.append(g)
    return g


def clear_and_make_component(layer, baseName):
    # limpa outlines/componentes existentes e cria um novo componente
    layer.shapes = []
    c = GSComponent(baseName)
    c.automaticAlignment = False
    layer.shapes.append(c)
    return c


def build_dash_from_hyphen(font, dashName, factor):
    # tenta hyphen padrão; se faltar, tenta hyphen-minus (fallback raro)
    hyphen = font.glyphs['hyphen'] or font.glyphs.get('hyphen-minus')
    if not hyphen:
        raise RuntimeError('Glifo "hyphen" não encontrado.')

    dash = ensure_glyph(font, dashName)

    for master in font.masters:
        mID = master.id
        hLayer = hyphen.layers[mID]
        dLayer = dash.layers[mID]

        # garante um componente novo do hyphen
        comp = clear_and_make_component(dLayer, hyphen.name)

        # coleta medidas base do hyphen
        h_LSB = hLayer.LSB
        h_RSB = hLayer.RSB
        h_width = hLayer.width
        base_shape_w = h_width - h_LSB - h_RSB

        # largura desejada do dash e largura do desenho (sem SBearings)
        desired_width = h_width * factor
        desired_shape_w = desired_width - h_LSB - h_RSB

        # fator de escala horizontal do componente (ancorado à borda esquerda = LSB)
        if abs(base_shape_w) > 0.0001:
            sx = desired_shape_w / base_shape_w
        else:
            sx = factor  # fallback improvável

        # manter x = LSB fixo: dx = LSB*(1 - sx)
        dx = h_LSB * (1.0 - sx)
        comp.applyTransform((sx, 0.0, 0.0, 1.0, dx, 0.0))

        # define width do layer para fechar a conta (LSB/RSB iguais ao hyphen)
        dLayer.width = int(round(desired_width))

        # keys paramétricas de SBearings
        dash.leftMetricsKey = f"={hyphen.name}"
        dash.rightMetricsKey = f"={hyphen.name}"

        # sincroniza para aplicar as chaves
        try:
            dLayer.syncMetrics()
        except Exception:
            pass

    print(f"✅ {dashName}: construído a partir de '{hyphen.name}' com largura {int(round(100*factor))}% por master. SBearings = ={hyphen.name}.")


def main():
    font = Glyphs.font
    if not font:
        raise RuntimeError('Abra uma fonte no Glyphs.')

    # cria/atualiza endash e emdash
    for name, f in DASHES:
        build_dash_from_hyphen(font, name, f)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        Message(str(e), 'Plau – Build En/Em Dashes from Hyphen')
