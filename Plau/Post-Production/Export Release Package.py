#MenuTitle: Export Release Package
# -*- coding: utf-8 -*-
# Description: Exports the open font into a dated release folder: variable TTF, variable WOFF2 + web sample, static OTFs, and Windows TTFs fixed with Windows Font Fix (RIBBI in its own subfolder), plus a trilingual README, a CSS file and a test HTML page, all made on the fly.

__doc__ = """
Exports the font in front into a dated release folder, with the same structure as the previous release: 01. Desktop Variable (TTF), 02. Webfont Variable (WOFF2 plus the CSS and HTML sample), 03. Static OTF Files, and 04. Windows TTF, where the fonts go through Windows Font Fix and the four RIBBI styles move to the "01. Windows RIBBI" subfolder.
The README (English, Portuguese, Spanish) is written from scratch from the files that are in the release folder: file names, style counts, variable axes and how the Windows styles are linked. It does not depend on any previous release.
The web sample is made on the fly too: a CSS file (font-face, axis ranges, one class per named instance) and a test HTML page built with the functions of mekkablue's Variable Font Test HTML script (it has to be installed).
After the Windows fixes the style linking is checked (nameID 1/2 against fsSelection, duplicated family + style pairs, Bold without Regular) and problems are reported in the Macro Panel.
Static fonts are autohinted and have overlaps removed. The variable font is not autohinted and gets the post-export fixes of fix_vf.py (usWeightClass from the default of the weight axis, smart dropout control at the start of prep, WWS bit); its WOFF2 is built from the fixed TTF.
Uses the active instances of the font. Never overwrites a non-empty release folder without asking.
"""

import contextlib
import importlib.util
import os
import re
import shutil
import tempfile
import textwrap
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
# Glyphs preferences that reveal the exported files in the Finder after an export (it would open the temp folder of the variable font)
SHOW_IN_FINDER_KEYS = ("GSVariableExportShowInFinder", "OTFExportShowInFinder", "TTFExportShowInFinder")


# ===== Helpers =====

@contextlib.contextmanager
def no_reveal_in_finder():
    """Turns off "Show in Finder" after export while the script exports, then puts the preferences back."""
    saved = {key: Glyphs.defaults[key] for key in SHOW_IN_FINDER_KEYS if Glyphs.defaults[key] is not None}
    try:
        for key in saved:
            Glyphs.defaults[key] = 0
        yield
    finally:
        for key, value in saved.items():
            Glyphs.defaults[key] = value


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


# ===== README (written from scratch from what the release folder holds) =====

README_WIDTH = 64
LANGUAGES = (("en", "English", "ENGLISH"), ("pt", "Português (BR)", "PORTUGUÊS (BRASIL)"), ("es", "Español", "ESPAÑOL"))
AND_WORD = {"en": "and", "pt": "e", "es": "y"}
AXIS_NAMES = {
    "en": {"wght": "weight", "wdth": "width", "slnt": "slant", "ital": "italic", "opsz": "optical size"},
    "pt": {"wght": "peso", "wdth": "largura", "slnt": "inclinação", "ital": "itálico", "opsz": "tamanho óptico"},
    "es": {"wght": "peso", "wdth": "ancho", "slnt": "inclinación", "ital": "cursiva", "opsz": "tamaño óptico"},
}
MAX_FAMILY_NAMES = 6   # family names listed per group of the RIBBI section; the rest is "and N more"

TEXT = {
    "en": dict(
        sub_client="A custom typeface for {client}, made by Plau", sub_plain="A typeface made by Plau", hi="Hi! :)",
        intro_client="This is {family}, the typeface we drew for {client}.", intro_plain="This is {family}, a typeface by Plau.",
        styles_both="It has {n} styles, or one variable font that holds all of them.", styles_static="It has {n} styles.",
        styles_vf="It is one variable font that holds all of its styles.",
        exclusive="It was made exclusively for {client}. Please don't share the files outside the team and the projects they're meant for.",
        contents="WHAT'S IN THIS FOLDER",
        var_desc_many="Our pick for design work. One file, every style, and {axes} become sliders in apps that support variable fonts (Adobe CC, Figma, Sketch, recent macOS apps).",
        var_desc_one="Our pick for design work. One file, every style, and {axes} becomes a slider in apps that support variable fonts (Adobe CC, Figma, Sketch, recent macOS apps).",
        web_desc="For websites. One small file does the whole family.", web_sample="The CSS and HTML files are a ready-made sample of how to use it.",
        otf_desc="{n} separate fonts, for software that doesn't support variable fonts yet, or whenever a static file is needed.",
        ttf_desc="{n} separate fonts tuned for Windows and Microsoft Office.",
        ttf_ribbi='The "{ribbi}" subfolder holds the core styles: {styles}.',
        use_title="Which one should I use?", use_design="Design work, Mac or Windows: folder {var}, the variable font.",
        use_static_both="Apps without variable font support: folder {otf} (Mac) or {ttf} (Windows).",
        use_static_otf="Apps without variable font support: folder {otf}.", use_static_ttf="Apps without variable font support: folder {ttf} (Windows).",
        use_office="Office, PowerPoint, Word: folder {ttf}.", use_web="Websites: folder {web}.",
        use_dont_mix="Don't install the OTF and TTF statics together, they confuse apps.",
        use_vf_with_static="The variable font can live next to one set of statics, but if menus start acting weird, see Troubleshooting.",
        mac_title="INSTALLING ON MAC", mac_1_var="Open the folder you want ({var} for design work).", mac_1_otf="Open the folder with the OTF files ({otf}).",
        mac_2="Select all the font files, then double-click.", mac_3='Font Book opens. Click "Install".',
        mac_4="Restart any app that was already open.", mac_tip="Tip: you can also drag the files straight into the Font Book window.",
        win_title="INSTALLING ON WINDOWS", win_sub=' and its "{ribbi}" subfolder',
        win_1_both="For design work, install the variable font from folder {var}. For Office, open folder {ttf}{sub}.",
        win_1_var="Install the variable font from folder {var}.", win_1_ttf="Open folder {ttf}{sub}.",
        win_2="Select the .ttf files{both}.", win_2_both=" (in folder {ttf}, from both places)",
        win_3='Right-click > "Install for all users". (Windows 11: right-click > "Show more options" first.)',
        win_4="Restart Office and any other app that was open.",
        win_alt='Another way: Settings > Personalization > Fonts, then drag the files into the "Add fonts" area.',
        win_why='"Install for all users" matters: some apps, and anything run as administrator, don\'t see fonts installed for one user only.',
        ribbi_title="HOW THE STYLES ARE ORGANIZED (RIBBI)",
        ribbi_why_bi="Windows and Office have an old rule: a font family can have at most four members. Regular, Italic, Bold and Bold Italic. That's RIBBI. It's what makes the B and I buttons (Ctrl+B, Ctrl+I) work.",
        ribbi_why_b="Windows and Office have an old rule: a font family can have at most four members: Regular, Italic, Bold and Bold Italic. That's RIBBI. {family} has no italic, so here it's just Regular and Bold, tied to the B button (Ctrl+B).",
        ribbi_split="{family} has {n} styles, so we split them up for Windows:", ribbi_more="and {k} more", ribbi_only="{s} only",
        ribbi_mac='On Mac, in Adobe apps and in Figma none of this applies: everything shows up together under "{family}", with all {n} style names in the style menu.',
        trouble_title="TROUBLESHOOTING",
        t_missing_q="The font doesn't show up in the menu",
        t_missing_a='Close the app completely and open it again. Office in particular only reads fonts at startup. On Windows, check you used "Install for all users".',
        t_fake_q='Bold or italic look smudgy or "fake"',
        t_fake_a='The app is faking the style because it can\'t find the real file. On Windows, make sure the files in "{ribbi}" are installed.',
        t_dup_q="Duplicates, wrong weights, or old versions showing up",
        t_dup_a=("An older version is still installed.",
                 'Mac: open Font Book, search "{family}", remove all of it, then install again. Font Book > File > "Resolve Duplicates" also helps.',
                 'Windows: Settings > Personalization > Fonts, search "{short}", uninstall every entry, restart the computer, install again.',
                 "Still stuck on Mac? Clear the font cache: open Terminal, run   sudo atsutil databases -remove   and restart."),
        t_mix_q="Weird mix of styles in an Adobe document",
        t_mix_a="Having the variable font and the statics installed at the same time can make apps mix them up. Keep the variable font and remove the statics, unless you really need them.",
        t_office_q="The variable font misbehaves in Office",
        t_office_a="Office support for variable fonts is still patchy. Use the static TTFs from folder {ttf} there.",
        t_web_q="Using it on the web",
        css_wght="Weight works with plain font-weight ({min} to {max}).", css_wdth="Width works with font-stretch ({min}% to {max}%).",
        css_other="The other axes work through font-variation-settings, within these ranges: {ranges}.",
        closing="Something else? Talk to us at plau.design. We like hearing how the letters are doing out there.",
    ),
    "pt": dict(
        sub_client="Uma fonte sob medida para {client}, feita pela Plau", sub_plain="Uma fonte da Plau", hi="Oi! :)",
        intro_client="Esta é a {family}, a fonte que desenhamos para {client}.", intro_plain="Esta é a {family}, uma fonte da Plau.",
        styles_both="Ela tem {n} estilos, ou uma fonte variável que guarda todos eles.", styles_static="Ela tem {n} estilos.",
        styles_vf="Ela é uma fonte variável que guarda todos os seus estilos.",
        exclusive="Ela foi feita exclusivamente para {client}. Por favor, não compartilhe os arquivos fora da equipe e dos projetos a que se destinam.",
        contents="O QUE TEM NESTA PASTA",
        var_desc_many="Nossa escolha para trabalho de design. Um arquivo, todos os estilos, e {axes} viram controles deslizantes nos programas que aceitam fontes variáveis (Adobe CC, Figma, Sketch, apps recentes do macOS).",
        var_desc_one="Nossa escolha para trabalho de design. Um arquivo, todos os estilos, e {axes} vira um controle deslizante nos programas que aceitam fontes variáveis (Adobe CC, Figma, Sketch, apps recentes do macOS).",
        web_desc="Para sites. Um arquivo pequeno resolve a família inteira.", web_sample="Os arquivos CSS e HTML são um exemplo pronto de como usar.",
        otf_desc="{n} fontes separadas, para programas que ainda não aceitam fontes variáveis, ou quando um arquivo estático for necessário.",
        ttf_desc="{n} fontes separadas, ajustadas para Windows e Microsoft Office.",
        ttf_ribbi='A subpasta "{ribbi}" tem os estilos principais: {styles}.',
        use_title="Qual eu uso?", use_design="Trabalho de design, Mac ou Windows: pasta {var}, a fonte variável.",
        use_static_both="Programas sem suporte a fontes variáveis: pasta {otf} (Mac) ou {ttf} (Windows).",
        use_static_otf="Programas sem suporte a fontes variáveis: pasta {otf}.", use_static_ttf="Programas sem suporte a fontes variáveis: pasta {ttf} (Windows).",
        use_office="Office, PowerPoint, Word: pasta {ttf}.", use_web="Sites: pasta {web}.",
        use_dont_mix="Não instale as estáticas OTF e TTF juntas, isso confunde os programas.",
        use_vf_with_static="A fonte variável pode conviver com um conjunto de estáticas, mas se os menus ficarem estranhos, veja Problemas comuns.",
        mac_title="INSTALANDO NO MAC", mac_1_var="Abra a pasta que você vai usar ({var} para design).", mac_1_otf="Abra a pasta com os arquivos OTF ({otf}).",
        mac_2="Selecione todos os arquivos de fonte e dê dois cliques.", mac_3='O Catálogo de Fontes (Font Book) abre. Clique em "Instalar".',
        mac_4="Reinicie os programas que já estavam abertos.", mac_tip="Dica: dá para arrastar os arquivos direto para a janela do Catálogo de Fontes.",
        win_title="INSTALANDO NO WINDOWS", win_sub=' e a subpasta "{ribbi}"',
        win_1_both="Para design, instale a fonte variável da pasta {var}. Para o Office, abra a pasta {ttf}{sub}.",
        win_1_var="Instale a fonte variável da pasta {var}.", win_1_ttf="Abra a pasta {ttf}{sub}.",
        win_2="Selecione os arquivos .ttf{both}.", win_2_both=" (na pasta {ttf}, dos dois lugares)",
        win_3='Clique com o botão direito > "Instalar para todos os usuários". (No Windows 11: botão direito > "Mostrar mais opções" antes.)',
        win_4="Reinicie o Office e qualquer outro programa que estava aberto.",
        win_alt='Outro caminho: Configurações > Personalização > Fontes, e arraste os arquivos para a área "Adicionar fontes".',
        win_why='"Instalar para todos os usuários" faz diferença: alguns programas, e tudo que roda como administrador, não enxergam fontes instaladas só para um usuário.',
        ribbi_title="COMO OS ESTILOS ESTÃO ORGANIZADOS (RIBBI)",
        ribbi_why_bi="O Windows e o Office têm uma regra antiga: uma família de fontes pode ter no máximo quatro membros. Regular, Italic, Bold e Bold Italic. Isso é o RIBBI. É o que faz os botões N e I (Ctrl+N, Ctrl+I no Office em português) funcionarem.",
        ribbi_why_b="O Windows e o Office têm uma regra antiga: uma família de fontes pode ter no máximo quatro membros: Regular, Italic, Bold e Bold Italic. Isso é o RIBBI. A {family} não tem itálico, então aqui são só Regular e Bold, ligados ao botão N (Ctrl+N no Office em português).",
        ribbi_split="A {family} tem {n} estilos, então dividimos tudo para o Windows:", ribbi_more="e mais {k}", ribbi_only="Só {s}",
        ribbi_mac='No Mac, nos programas da Adobe e no Figma nada disso se aplica: tudo aparece junto em "{family}", com os {n} estilos no menu.',
        trouble_title="PROBLEMAS COMUNS",
        t_missing_q="A fonte não aparece no menu",
        t_missing_a='Feche o programa de vez e abra de novo. O Office, em especial, só lê as fontes quando abre. No Windows, confira se você usou "Instalar para todos os usuários".',
        t_fake_q='Negrito ou itálico com cara de "falso", meio borrado',
        t_fake_a='O programa está simulando o estilo porque não achou o arquivo certo. No Windows, confira se os arquivos de "{ribbi}" estão instalados.',
        t_dup_q="Duplicatas, pesos trocados ou versão antiga aparecendo",
        t_dup_a=("Ainda tem uma versão antiga instalada.",
                 'Mac: abra o Catálogo de Fontes, busque "{family}", remova tudo e instale de novo. Arquivo > "Resolver Duplicatas" também ajuda.',
                 'Windows: Configurações > Personalização > Fontes, busque "{short}", desinstale todas as entradas, reinicie o computador e instale de novo.',
                 "Ainda travado no Mac? Limpe o cache de fontes: abra o Terminal, rode   sudo atsutil databases -remove   e reinicie."),
        t_mix_q="Mistura estranha de estilos num documento da Adobe",
        t_mix_a="Ter a fonte variável e as estáticas instaladas ao mesmo tempo pode fazer os programas misturarem as duas. Fique com a variável e remova as estáticas, a não ser que precise delas.",
        t_office_q="A fonte variável se comporta mal no Office",
        t_office_a="O suporte do Office a fontes variáveis ainda é irregular. Use as TTF estáticas da pasta {ttf} lá.",
        t_web_q="Usando na web",
        css_wght="O peso funciona com font-weight normal ({min} a {max}).", css_wdth="A largura funciona com font-stretch ({min}% a {max}%).",
        css_other="Os outros eixos funcionam com font-variation-settings, dentro destas faixas: {ranges}.",
        closing="Alguma outra coisa? Fala com a gente em plau.design. A gente adora saber como as letras estão se saindo por aí.",
    ),
    "es": dict(
        sub_client="Una tipografía a medida para {client}, hecha por Plau", sub_plain="Una tipografía de Plau", hi="¡Hola! :)",
        intro_client="Esta es {family}, la tipografía que dibujamos para {client}.", intro_plain="Esta es {family}, una tipografía de Plau.",
        styles_both="Tiene {n} estilos, o una fuente variable que los contiene a todos.", styles_static="Tiene {n} estilos.",
        styles_vf="Es una fuente variable que contiene todos sus estilos.",
        exclusive="Fue hecha en exclusiva para {client}. Por favor, no compartas los archivos fuera del equipo y de los proyectos a los que están destinados.",
        contents="QUÉ HAY EN ESTA CARPETA",
        var_desc_many="Nuestra recomendación para trabajo de diseño. Un archivo, todos los estilos, y {axes} se vuelven controles deslizantes en las apps que soportan fuentes variables (Adobe CC, Figma, Sketch, apps recientes de macOS).",
        var_desc_one="Nuestra recomendación para trabajo de diseño. Un archivo, todos los estilos, y {axes} se vuelve un control deslizante en las apps que soportan fuentes variables (Adobe CC, Figma, Sketch, apps recientes de macOS).",
        web_desc="Para sitios web. Un archivo liviano resuelve toda la familia.", web_sample="Los archivos CSS y HTML son un ejemplo listo de cómo usarla.",
        otf_desc="{n} fuentes separadas, para software que todavía no soporta fuentes variables, o cuando se necesite un archivo estático.",
        ttf_desc="{n} fuentes separadas, ajustadas para Windows y Microsoft Office.",
        ttf_ribbi='La subcarpeta "{ribbi}" tiene los estilos principales: {styles}.',
        use_title="¿Cuál uso?", use_design="Trabajo de diseño, Mac o Windows: carpeta {var}, la fuente variable.",
        use_static_both="Apps sin soporte para fuentes variables: carpeta {otf} (Mac) o {ttf} (Windows).",
        use_static_otf="Apps sin soporte para fuentes variables: carpeta {otf}.", use_static_ttf="Apps sin soporte para fuentes variables: carpeta {ttf} (Windows).",
        use_office="Office, PowerPoint, Word: carpeta {ttf}.", use_web="Sitios web: carpeta {web}.",
        use_dont_mix="No instales las estáticas OTF y TTF juntas, confunden a las apps.",
        use_vf_with_static="La fuente variable puede convivir con un conjunto de estáticas, pero si los menús se ponen raros, mira Solución de problemas.",
        mac_title="INSTALAR EN MAC", mac_1_var="Abre la carpeta que vas a usar ({var} para diseño).", mac_1_otf="Abre la carpeta con los archivos OTF ({otf}).",
        mac_2="Selecciona todos los archivos de fuente y haz doble clic.", mac_3='Se abre Catálogo Tipográfico (Font Book). Haz clic en "Instalar".',
        mac_4="Reinicia las apps que ya estaban abiertas.", mac_tip="Tip: también puedes arrastrar los archivos directo a la ventana de Catálogo Tipográfico.",
        win_title="INSTALAR EN WINDOWS", win_sub=' y la subcarpeta "{ribbi}"',
        win_1_both="Para diseño, instala la fuente variable de la carpeta {var}. Para Office, abre la carpeta {ttf}{sub}.",
        win_1_var="Instala la fuente variable de la carpeta {var}.", win_1_ttf="Abre la carpeta {ttf}{sub}.",
        win_2="Selecciona los archivos .ttf{both}.", win_2_both=" (en la carpeta {ttf}, de los dos lugares)",
        win_3='Clic derecho > "Instalar para todos los usuarios". (En Windows 11: clic derecho > "Mostrar más opciones" primero.)',
        win_4="Reinicia Office y cualquier otra app que estuviera abierta.",
        win_alt='Otra forma: Configuración > Personalización > Fuentes, y arrastra los archivos al área "Agregar fuentes".',
        win_why='"Instalar para todos los usuarios" importa: algunas apps, y todo lo que se ejecuta como administrador, no ven las fuentes instaladas solo para un usuario.',
        ribbi_title="CÓMO ESTÁN ORGANIZADOS LOS ESTILOS (RIBBI)",
        ribbi_why_bi="Windows y Office tienen una regla antigua: una familia tipográfica puede tener como máximo cuatro miembros. Regular, Italic, Bold y Bold Italic. Eso es RIBBI. Es lo que hace funcionar los botones de negrita y cursiva (Ctrl+N, Ctrl+K en Office en español).",
        ribbi_why_b="Windows y Office tienen una regla antigua: una familia tipográfica puede tener como máximo cuatro miembros: Regular, Italic, Bold y Bold Italic. Eso es RIBBI. {family} no tiene cursiva, así que aquí son solo Regular y Bold, ligados al botón de negrita (Ctrl+N en Office en español).",
        ribbi_split="{family} tiene {n} estilos, así que los repartimos para Windows:", ribbi_more="y {k} más", ribbi_only="Solo {s}",
        ribbi_mac='En Mac, en las apps de Adobe y en Figma nada de esto aplica: todo aparece junto bajo "{family}", con los {n} estilos en el menú.',
        trouble_title="SOLUCIÓN DE PROBLEMAS",
        t_missing_q="La fuente no aparece en el menú",
        t_missing_a='Cierra la app por completo y ábrela de nuevo. Office, en especial, solo lee las fuentes al abrirse. En Windows, revisa que hayas usado "Instalar para todos los usuarios".',
        t_fake_q='La negrita o la cursiva se ven "falsas" o borrosas',
        t_fake_a='La app está simulando el estilo porque no encontró el archivo real. En Windows, revisa que los archivos de "{ribbi}" estén instalados.',
        t_dup_q="Duplicados, pesos cambiados o una versión vieja",
        t_dup_a=("Todavía hay una versión anterior instalada.",
                 'Mac: abre Catálogo Tipográfico, busca "{family}", elimina todo e instala de nuevo. Archivo > "Resolver duplicados" también ayuda.',
                 'Windows: Configuración > Personalización > Fuentes, busca "{short}", desinstala todas las entradas, reinicia la computadora e instala de nuevo.',
                 "¿Sigue igual en Mac? Limpia la caché de fuentes: abre Terminal, ejecuta   sudo atsutil databases -remove   y reinicia."),
        t_mix_q="Mezcla rara de estilos en un documento de Adobe",
        t_mix_a="Tener la fuente variable y las estáticas instaladas al mismo tiempo puede hacer que las apps las mezclen. Quédate con la variable y elimina las estáticas, salvo que las necesites.",
        t_office_q="La fuente variable se porta mal en Office",
        t_office_a="El soporte de Office para fuentes variables todavía es irregular. Usa las TTF estáticas de la carpeta {ttf} ahí.",
        t_web_q="Usarla en la web",
        css_wght="El peso funciona con font-weight normal ({min} a {max}).", css_wdth="El ancho funciona con font-stretch ({min}% a {max}%).",
        css_other="Los demás ejes funcionan con font-variation-settings, dentro de estos rangos: {ranges}.",
        closing="¿Algo más? Escríbenos en plau.design. Nos encanta saber cómo les va a las letras por ahí.",
    ),
}


def para(text, indent=0, hang=None):
    hang = indent if hang is None else hang
    return textwrap.fill(text, README_WIDTH, initial_indent=" " * indent, subsequent_indent=" " * hang,
                         break_long_words=False, break_on_hyphens=False)


def number(value):
    value = float(value)
    return str(int(value)) if value.is_integer() else "%g" % value


def join_words(items, and_word):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " " + and_word + " " + items[-1]


def read_axes(path):
    try:
        font = TTFont(path, lazy=True)
        return [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in font["fvar"].axes]
    except Exception:
        return []


def read_style_names(path):
    """(nameID 1, nameID 2, nameID 16) of a font file."""
    names = TTFont(path, lazy=True)["name"]
    return names.getDebugName(1), names.getDebugName(2), names.getDebugName(16)


def scan_release(release_dir):
    """What the release folder holds on disk (the source of truth for the README)."""
    def listing(folder, extensions):
        return font_files(os.path.join(release_dir, folder), extensions)
    web_dir = os.path.join(release_dir, FOLDER_WEB)
    ttf_dir = os.path.join(release_dir, FOLDER_TTF)
    scan = {
        "variable": listing(FOLDER_VARIABLE, (".ttf",)),
        "web": [n for n in listing(FOLDER_WEB, WEB_FONT_EXTENSIONS) if n.lower().endswith(".woff2")] or listing(FOLDER_WEB, WEB_FONT_EXTENSIONS),
        "sample": sorted(n for n in os.listdir(web_dir) if n.lower().endswith((".css", ".html")) and not n.startswith(".")) if os.path.isdir(web_dir) else [],
        "otf": listing(FOLDER_OTF, (".otf",)),
        "ttf": listing(FOLDER_TTF, (".ttf",)),
        "ribbi": font_files(os.path.join(ttf_dir, FOLDER_RIBBI), (".ttf",)),
    }
    scan["axes"] = []
    if scan["variable"]:
        scan["axes"] = read_axes(os.path.join(release_dir, FOLDER_VARIABLE, scan["variable"][0]))
    if not scan["axes"] and scan["web"]:
        scan["axes"] = read_axes(os.path.join(web_dir, scan["web"][0]))
    # Windows families: nameID 1 -> set of nameID 2 (the styles linked inside each Windows family)
    families, ribbi_family = {}, None
    for sub, names in ((FOLDER_TTF, scan["ttf"]), (os.path.join(FOLDER_TTF, FOLDER_RIBBI), scan["ribbi"])):
        for name in names:
            try:
                family, style, _ = read_style_names(os.path.join(release_dir, sub, name))
            except Exception:
                continue
            families.setdefault(family, set()).add(style)
            if sub != FOLDER_TTF:
                ribbi_family = family
    scan["families"], scan["ribbi_family"] = families, ribbi_family
    return scan


def style_list(styles, text):
    ordered = [s for s in RIBBI_STYLES if s in styles] + sorted(s for s in styles if s not in RIBBI_STYLES)
    if len(ordered) == 1:
        return text["ribbi_only"].format(s=ordered[0])
    return (", " if len(ordered) >= 4 else " + ").join(ordered)


def windows_groups(scan):
    """[(family names, styles)]: the base family first, then the other families grouped by the styles they hold."""
    families, base = scan["families"], scan["ribbi_family"]
    groups = []
    if base and base in families:
        groups.append(([base], families[base]))
    by_signature = {}
    for family, styles in families.items():
        if family != base:
            by_signature.setdefault(frozenset(styles), []).append(family)
    for signature in sorted(by_signature, key=lambda sig: (-len(sig), sorted(sig))):
        groups.append((sorted(by_signature[signature], key=lambda f: (len(f), f)), signature))
    return groups


def css_block(family, filename, axes):
    ranges = {tag: (lo, hi) for tag, lo, _, hi in axes}
    lines = ['@font-face {', '  font-family: "%s";' % family, '  src: url("%s") format("woff2");' % filename]
    if "wght" in ranges:
        lines.append("  font-weight: %s %s;" % tuple(number(v) for v in ranges["wght"]))
    if "wdth" in ranges:
        lines.append("  font-stretch: %s%% %s%%;" % tuple(number(v) for v in ranges["wdth"]))
    lines += ["  font-display: swap;", "}"]
    others = [a for a in axes if a[0] not in ("wght", "wdth")]
    if others:
        tag, lo, default, hi = others[0]
        lines += [".example {", '  font-variation-settings: "%s" %s;' % (tag, number(default)), "}"]
    return ["    " + line for line in lines]


def build_readme_language(lang, ctx):
    t = TEXT[lang]
    scan, family, n_static = ctx["scan"], ctx["family"], ctx["n_static"]
    has_var, has_web = bool(scan["variable"]), bool(scan["web"])
    has_otf, has_ttf, has_ribbi = bool(scan["otf"]), bool(scan["ttf"] or scan["ribbi"]), bool(scan["ribbi"])
    num = lambda folder: folder.split(".")[0]
    var_n, web_n, otf_n, ttf_n = num(FOLDER_VARIABLE), num(FOLDER_WEB), num(FOLDER_OTF), num(FOLDER_TTF)
    out = []

    # intro
    out.append(t["hi"])
    out.append("")
    if ctx["client"]:
        intro = t["intro_client"].format(family=family, client=ctx["client"])
    else:
        intro = t["intro_plain"].format(family=family)
    if has_var and n_static:
        intro += " " + t["styles_both"].format(n=n_static)
    elif n_static:
        intro += " " + t["styles_static"].format(n=n_static)
    elif has_var:
        intro += " " + t["styles_vf"]
    out.append(para(intro))
    if ctx["client"]:
        out += ["", para(t["exclusive"].format(client=ctx["client"]))]

    # contents
    def title(text):
        return ["", "", text, "-" * len(text), ""]
    out += title(t["contents"])
    if has_var:
        axes = [AXIS_NAMES[lang].get(tag, tag) for tag, _, _, _ in scan["axes"]]
        key = "var_desc_many" if len(axes) != 1 else "var_desc_one"
        desc = t[key].format(axes=join_words(axes, AND_WORD[lang]) if axes else "")
        if not axes:
            desc = desc.replace(" and  ", " ")
        out += ["  " + FOLDER_VARIABLE] + ["      " + n for n in scan["variable"]] + [para(desc, 6), ""]
    if has_web:
        out += ["  " + FOLDER_WEB] + ["      " + n for n in scan["web"]] + [para(t["web_desc"], 6)]
        if scan["sample"]:
            out += ["      " + ", ".join(scan["sample"]), para(t["web_sample"], 6)]
        out.append("")
    if has_otf:
        out += ["  " + FOLDER_OTF, para(t["otf_desc"].format(n=len(scan["otf"])), 6), ""]
    if has_ttf:
        text = t["ttf_desc"].format(n=len(scan["ttf"]) + len(scan["ribbi"]))
        if has_ribbi:
            ribbi_styles = join_words([s for s in RIBBI_STYLES if s in scan["families"].get(scan["ribbi_family"], ())], AND_WORD[lang])
            text += " " + t["ttf_ribbi"].format(ribbi=FOLDER_RIBBI, styles=ribbi_styles)
        out += ["  " + FOLDER_TTF, para(text, 6), ""]
    out.append(t["use_title"])
    bullets = []
    if has_var:
        bullets.append(t["use_design"].format(var=var_n))
    if has_otf and has_ttf:
        bullets.append(t["use_static_both"].format(otf=otf_n, ttf=ttf_n))
    elif has_otf:
        bullets.append(t["use_static_otf"].format(otf=otf_n))
    elif has_ttf:
        bullets.append(t["use_static_ttf"].format(ttf=ttf_n))
    if has_ttf:
        bullets.append(t["use_office"].format(ttf=ttf_n))
    if has_web:
        bullets.append(t["use_web"].format(web=web_n))
    if has_otf and has_ttf:
        bullets.append(t["use_dont_mix"])
    if has_var and (has_otf or has_ttf):
        bullets.append(t["use_vf_with_static"])
    out += [para("- " + b, 2, 4) for b in bullets]

    # installing
    if has_var or has_otf or has_ttf:
        out += title(t["mac_title"])
        steps = [t["mac_1_var"].format(var=var_n) if has_var else t["mac_1_otf"].format(otf=otf_n), t["mac_2"], t["mac_3"], t["mac_4"]]
        out += [para("%d. %s" % (i + 1, s), 2, 5) for i, s in enumerate(steps)]
        out += ["", para(t["mac_tip"], 2)]
    if has_var or has_ttf:
        out += title(t["win_title"])
        sub = t["win_sub"].format(ribbi=FOLDER_RIBBI) if has_ribbi else ""
        if has_var and has_ttf:
            first = t["win_1_both"].format(var=var_n, ttf=ttf_n, sub=sub)
        elif has_var:
            first = t["win_1_var"].format(var=var_n)
        else:
            first = t["win_1_ttf"].format(ttf=ttf_n, sub=sub)
        both = t["win_2_both"].format(ttf=ttf_n) if has_ttf and has_ribbi else ""
        steps = [first, t["win_2"].format(both=both), t["win_3"], t["win_4"]]
        out += [para("%d. %s" % (i + 1, s), 2, 5) for i, s in enumerate(steps)]
        out += ["", para(t["win_alt"], 2), "", para(t["win_why"], 2)]

    # RIBBI
    groups = windows_groups(scan) if has_ttf else []
    if groups:
        out += title(t["ribbi_title"])
        has_italic = any("Italic" in s for _, styles in groups for s in styles)
        out.append(para(t["ribbi_why_bi"] if has_italic else t["ribbi_why_b"].format(family=family)))
        out += ["", para(t["ribbi_split"].format(family=family, n=len(scan["ttf"]) + len(scan["ribbi"])))]
        for names, styles in groups:
            limit = len(names) if len(names) <= MAX_FAMILY_NAMES + 2 else MAX_FAMILY_NAMES
            shown = ", ".join(names[:limit])
            if limit < len(names):
                shown += " (%s)" % t["ribbi_more"].format(k=len(names) - limit)
            out += ["", para(shown, 2, 4), "      " + style_list(styles, t)]
        out += ["", para(t["ribbi_mac"].format(family=family, n=len(scan["ttf"]) + len(scan["ribbi"])))]

    # troubleshooting
    out += title(t["trouble_title"])
    def trouble(question, *answers):
        out.append("  " + question)
        out.append("\n\n".join(para(a, 4) for a in answers))
        out.append("")
    trouble(t["t_missing_q"], t["t_missing_a"])
    if has_ribbi:
        trouble(t["t_fake_q"], t["t_fake_a"].format(ribbi=FOLDER_RIBBI))
    trouble(t["t_dup_q"], *[a.format(family=family, short=ctx["short"]) for a in t["t_dup_a"]])
    if has_var and (has_otf or has_ttf):
        trouble(t["t_mix_q"], t["t_mix_a"])
    if has_var and has_ttf:
        trouble(t["t_office_q"], t["t_office_a"].format(ttf=ttf_n))
    if has_web and scan["axes"]:
        out.append("  " + t["t_web_q"])
        out += css_block(family, scan["web"][0], scan["axes"])
        ranges = {tag: (lo, hi) for tag, lo, _, hi in scan["axes"]}
        notes = []
        if "wght" in ranges:
            notes.append(t["css_wght"].format(min=number(ranges["wght"][0]), max=number(ranges["wght"][1])))
        if "wdth" in ranges:
            notes.append(t["css_wdth"].format(min=number(ranges["wdth"][0]), max=number(ranges["wdth"][1])))
        others = [(tag, lo, hi) for tag, lo, _, hi in scan["axes"] if tag not in ("wght", "wdth")]
        if others:
            notes.append(t["css_other"].format(ranges=", ".join("%s %s to %s" % (tag, number(lo), number(hi)) for tag, lo, hi in others)))
        if notes:
            out += ["", para(" ".join(notes), 4)]
        out.append("")
    out.append(para(t["closing"]))
    out += ["", ("Plau ✶ " + ctx["year"]).rjust(README_WIDTH)]
    return "\n".join(out)


def build_readme(family, label, release_dir, client=""):
    """The whole README text for the release folder (English, Portuguese, Spanish), or None if the folder holds no fonts."""
    scan = scan_release(release_dir)
    n_static = max(len(scan["otf"]), len(scan["ttf"]) + len(scan["ribbi"]))
    if not (scan["variable"] or scan["web"] or n_static):
        return None
    ctx = dict(scan=scan, family=family, short=family.split()[0], label=label, client=(client or "").strip(), n_static=n_static, year=time.strftime("%Y"))
    bar = "=" * README_WIDTH
    t = TEXT["en"]
    sub = (t["sub_client"].format(client=ctx["client"]) if ctx["client"] else t["sub_plain"])
    parts = [bar, "  " + family.upper(), "  " + sub, "  Version " + label, bar, ""]
    parts += ["  %s %s %d" % (name, "." * (20 - len(name) - 1), i + 1) for i, (_, name, _) in enumerate(LANGUAGES)]
    for i, (lang, _, heading) in enumerate(LANGUAGES):
        parts += ["", "", bar, "  %d · %s" % (i + 1, heading), bar, "", build_readme_language(lang, ctx)]
    return "\n".join(parts).replace("\n\n\n\n", "\n\n\n") + "\n"


def write_readme(font_family, release_dir, label, client="", log=print):
    text = build_readme(font_family, label, release_dir, client)
    if text is None:
        log("   README: no fonts in the release folder, not written")
        return
    with open(os.path.join(release_dir, README_NAME), "w", encoding="utf-8") as fh:
        fh.write(text)
    log("   %s (written from scratch from the folder contents)" % README_NAME)


# ===== Web sample (CSS + test HTML), made on the fly =====

TESTER_SCRIPT = "Variable Font Test HTML.py"
TESTER_MARKER = "# clears macro window log:"   # in mekkablue's script, everything after this line runs the script itself


def find_tester_script():
    support = os.path.expanduser("~/Library/Application Support")
    for app in ("Glyphs 4", "Glyphs 3"):
        for base in ("Scripts", "Repositories"):
            path = os.path.join(support, app, base, "mekkablue", "Test", TESTER_SCRIPT)
            if os.path.exists(path):
                return path
    return None


def load_tester():
    """The functions of mekkablue's Variable Font Test HTML script, without running the script (it runs when loaded, so only the part before its main code is executed)."""
    path = find_tester_script()
    if not path:
        raise RuntimeError("mekkablue's \"%s\" is not installed (Window > Plugin Manager > Scripts > mekkablue)" % TESTER_SCRIPT)
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    if TESTER_MARKER not in source:
        raise RuntimeError("the layout of mekkablue's \"%s\" changed, the test HTML cannot be built" % TESTER_SCRIPT)
    namespace = {"__name__": "mekkablue_variable_font_test_html", "__file__": path}
    exec(compile(source.split(TESTER_MARKER)[0], path, "exec"), namespace)
    return namespace


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def read_named_instances(path):
    """[(style name, {axis tag: value})] from the fvar table."""
    try:
        font = TTFont(path, lazy=True)
        names = font["name"]
        return [(names.getDebugName(i.subfamilyNameID), dict(i.coordinates)) for i in font["fvar"].instances]
    except Exception:
        return []


def build_css(family, filename, axes, instances):
    """The CSS of the web sample: @font-face with the axis ranges, a family class and one class per named instance."""
    ranges = {tag: (lo, hi) for tag, lo, _, hi in axes}
    css = ["/* %s: webfont. Put the .woff2 next to this file, or fix the url() below. */" % family, "@font-face {",
           '  font-family: "%s";' % family, '  src: url("%s") format("woff2");' % filename]
    if "wght" in ranges:
        css.append("  font-weight: %s %s;" % tuple(number(v) for v in ranges["wght"]))
    if "wdth" in ranges:
        css.append("  font-stretch: %s%% %s%%;" % tuple(number(v) for v in ranges["wdth"]))
    css += ["  font-display: swap;", "}", "", ".%s {" % slug(family), '  font-family: "%s", sans-serif;' % family, "}"]
    if instances:
        css += ["", "/* Named styles */"]
    for name, coordinates in instances:
        rules = []
        if "wght" in coordinates:
            rules.append("font-weight: %s;" % number(coordinates["wght"]))
        if "wdth" in coordinates:
            rules.append("font-stretch: %s%%;" % number(coordinates["wdth"]))
        others = ", ".join('"%s" %s' % (tag, number(v)) for tag, v in coordinates.items() if tag not in ("wght", "wdth"))
        if others:
            rules.append("font-variation-settings: %s;" % others)
        css += [".%s-%s {" % (slug(family), slug(name))] + ["  " + r for r in rules] + ["}"]
    return "\n".join(css) + "\n"


def write_web_sample(font, release_dir, variable_instances, log=print):
    """CSS file + test HTML page (built with mekkablue's functions) next to the WOFF2 of the web folder."""
    problems = []
    web_dir = os.path.join(release_dir, FOLDER_WEB)
    woff2 = [n for n in font_files(web_dir, (".woff2",))]
    if not woff2:
        return ["Web sample: no WOFF2 in %s, CSS and HTML skipped" % FOLDER_WEB]
    try:
        tester = load_tester()
    except Exception as e:
        problems.append("Web sample: %s. The CSS was written, the test HTML was not." % e)
        tester = None
    for instance in variable_instances:
        # the WOFF2 of this instance: by the name Glyphs gives it, or the only one in the folder
        expected = None
        if tester:
            try:
                expected = os.path.splitext(tester["otVarFileName"](font, instance))[0] + ".woff2"
            except Exception:
                expected = None
        name = expected if expected in woff2 else (woff2[0] if len(woff2) == 1 else None)
        if not name:
            problems.append("Web sample: could not tell which WOFF2 belongs to %s" % instance.name)
            continue
        base = os.path.splitext(name)[0]
        axes = read_axes(os.path.join(web_dir, name))
        css_name = slug(font.familyName) + ".css" if len(variable_instances) == 1 else slug(base) + ".css"
        with open(os.path.join(web_dir, css_name), "w", encoding="utf-8") as fh:
            fh.write(build_css(font.familyName, name, axes, read_named_instances(os.path.join(web_dir, name))))
        log("   %s/%s" % (FOLDER_WEB, css_name))
        if not tester:
            continue
        try:
            info = tester["otVarInfoForInstance"](instance)
            full_name, _, escapes, sliders, variation_css, features, styles, languages, _, glyph_infos, _ = info
            html = tester["buildHTML"](tester["resolveFamilyNamesPlaceholder"](full_name, font), name, escapes, sliders, variation_css, features, styles, languages,
                                       False, glyphInfos=glyph_infos, plainSuffix="woff2")
            html = tester["resolveFamilyNamesPlaceholder"](html, font)
            html_name = "index.html" if len(variable_instances) == 1 else base + " fonttest.html"
            with open(os.path.join(web_dir, html_name), "w", encoding="utf-8") as fh:
                fh.write(html)
            log("   %s/%s (mekkablue's Variable Font Test HTML)" % (FOLDER_WEB, html_name))
        except Exception as e:
            problems.append("Web sample: the test HTML of %s failed (%s: %s)" % (instance.name, type(e).__name__, e))
    return problems


# ===== The export =====

def export_release(font, release_dir, groups=GROUPS, label=None, log=print, client=""):
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
        problems += check_style_linking(release_dir, log)

    if "web" in groups and variable:
        problems += write_web_sample(font, release_dir, variable, log)
    try:
        write_readme(font.familyName, release_dir, label, client, log)
    except Exception as e:
        problems.append("README could not be written (%s: %s)" % (type(e).__name__, e))
    return problems


def check_style_linking(release_dir, log=print):
    """Style linking of the Windows TTFs: nameID 2 must be one of the RIBBI styles and agree with fsSelection / macStyle,
    no (family, style) pair may repeat, and a Windows family with a Bold needs a Regular to link to."""
    problems, seen, by_family = [], {}, {}
    folder = os.path.join(release_dir, FOLDER_TTF)
    paths = [os.path.join(folder, n) for n in font_files(folder, (".ttf",))]
    paths += [os.path.join(folder, FOLDER_RIBBI, n) for n in font_files(os.path.join(folder, FOLDER_RIBBI), (".ttf",))]
    for path in paths:
        name = os.path.basename(path)
        try:
            font = TTFont(path, lazy=True)
            family, style = font["name"].getDebugName(1), font["name"].getDebugName(2)
            selection, mac = font["OS/2"].fsSelection, font["head"].macStyle
        except Exception as e:
            problems.append("%s: could not read for the style linking check (%s)" % (name, e))
            continue
        if style not in RIBBI_STYLES:
            problems.append("%s: style name \"%s\" is not Regular, Italic, Bold or Bold Italic (nameID 2)" % (name, style))
            continue
        wants_bold, wants_italic = "Bold" in style, "Italic" in style
        has_bold, has_italic, has_regular = bool(selection & 0x20), bool(selection & 0x01), bool(selection & 0x40)
        if (has_bold, has_italic) != (wants_bold, wants_italic) or has_regular != (not wants_bold and not wants_italic):
            problems.append("%s: \"%s\" but fsSelection says bold=%s italic=%s regular=%s" % (name, style, has_bold, has_italic, has_regular))
        if bool(mac & 1) != wants_bold or bool(mac & 2) != wants_italic:
            problems.append("%s: \"%s\" but head.macStyle says bold=%s italic=%s" % (name, style, bool(mac & 1), bool(mac & 2)))
        if (family, style) in seen:
            problems.append("%s: same family and style as %s (\"%s\" / %s)" % (name, seen[(family, style)], family, style))
        seen[(family, style)] = name
        by_family.setdefault(family, set()).add(style)
    for family, styles in sorted(by_family.items()):
        if "Bold" in styles and "Regular" not in styles:
            problems.append("\"%s\" has a Bold but no Regular to link it to" % family)
        if "Bold Italic" in styles and not ({"Bold", "Italic"} <= styles):
            problems.append("\"%s\" has a Bold Italic without both Bold and Italic" % family)
    log("   Style linking: %d fonts in %d Windows families, %s" % (len(paths), len(by_family), "%d problem(s)" % len(problems) if problems else "all consistent"))
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


def run_export(font, output_dir, label, groups, log=print, client=""):
    output_dir, label = str(output_dir), str(label)
    release_dir = os.path.join(output_dir, label)
    if os.path.isdir(release_dir) and os.listdir(release_dir) and any(not n.startswith(".") for n in os.listdir(release_dir)):
        if not askYesNo("The folder %s is not empty. Export into it anyway?" % label, informativeText="Files with the same name are replaced."):
            log("Cancelled: %s is not empty." % label)
            return None
    log("Exporting %s → %s" % (font.familyName, release_dir))
    started = time.time()
    with no_reveal_in_finder():
        problems = export_release(font, release_dir, groups, label, log, client)
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
        self.w.clientLabel = vanilla.TextBox((15, y + 3, 110, 18), "Made for:")
        self.w.client = vanilla.EditText((130, y, -15, 22), self.stored_client(), placeholder="Client name (optional)")
        self.w.client.getNSTextField().setToolTip_("Goes into the README (\"the typeface we drew for …\" and the don't-share note). Leave empty for a typeface that is not exclusive.")
        y += 36
        self.boxes = {}
        labels = (
            ("variable", "%s  (TTF)" % FOLDER_VARIABLE, "The variable font as TTF, without autohint."),
            ("web", "%s  (WOFF2 + CSS + HTML)" % FOLDER_WEB, "The variable font as WOFF2, plus a CSS file and a test HTML page (mekkablue's Variable Font Test HTML) made on the fly."),
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

    def stored_client(self):
        stored = Glyphs.defaults[DEFAULTS_PREFIX + "client." + str(self.font.familyName)]
        return str(stored) if stored else ""

    def choose_output(self, sender):
        folder = getFolder(messageText="Choose the folder that holds the release folders (the Output folder)", directory=self.output_dir or None)
        if folder:
            # getFolder returns an NSArray (not a list/tuple) of paths
            first = folder if isinstance(folder, str) else folder[0]
            self.output_dir = str(first)
            self.w.outPath.set(self.output_dir)
            Glyphs.defaults[DEFAULTS_PREFIX + "outputDir"] = self.output_dir

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
        self.w.close()
        Glyphs.clearLog()
        client = self.w.client.get().strip()
        Glyphs.defaults[DEFAULTS_PREFIX + "client." + str(self.font.familyName)] = client
        problems = run_export(self.font, self.output_dir, label, groups, client=client)
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
