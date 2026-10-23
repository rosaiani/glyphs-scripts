# Plau Glyphs Scripts

[English](README.md) · [Português](README.pt.md) · **Español** · [日本語](README.ja.md) · [简体中文](README.zh.md)

Herramientas en Python para el trabajo diario de diseño tipográfico en Plau: construir glifos, posicionar componentes y rellenar los metadatos de la fuente. Creado por Rodrigo Saiani con la ayuda de ChatGPT.

## Requisitos

- macOS y Glyphs 4.
- Compatibilidad con scripts de Python en Glyphs.
- La biblioteca de interfaz `vanilla`, para Arrow Maker, Center Components y Fill Font Metadata. Si falla una importación, revisa los módulos de Python disponibles en el Plugin Manager de Glyphs.

Ejecuta estos scripts **dentro de Glyphs**, no desde la Terminal. Basic Math usa la API de Glyphs 4; no se garantiza la compatibilidad con Glyphs 3. Se ha comprobado la visibilidad en los menús y la sintaxis de Python, pero la colección no se ha probado por completo con distintas fuentes y versiones de Glyphs. Algunos diálogos y mensajes están en portugués.

## Instalación

Instala los scripts desde el **Plugin Manager** de Glyphs (**Window → Plugin Manager → Scripts**). Las actualizaciones también llegan a través del Plugin Manager; después, recarga los scripts (mantén pulsada **Option** al abrir el menú Script y elige **Reload Scripts**, o reinicia Glyphs).

Para instalar a mano, descarga o clona este repositorio, elige **Script → Open Scripts Folder** en Glyphs 4 y copia allí la **carpeta `Plau`** del repositorio, con sus subcarpetas intactas. Después, recarga los scripts.

La estructura instalada debería verse así:

```text
Scripts/
└── Plau/
    ├── Build Glyphs/
    │   ├── Arrow Maker.py
    │   ├── Build Basic Math G4.py
    │   ├── Build Letters from Diacritic.py
    │   ├── Build Period Glyphs.py
    │   └── Dashes From Hyphen.py
    ├── Components/
    │   ├── Flip Components.py
    │   ├── Make Segments Parallel.py
    │   ├── Make Segments Symmetric.py
    │   └── Vertically Center Component.py
    ├── Font Info/
    │   └── Font Info Launch.py
    ├── Paths/
    │   └── Create Centerline.py
    ├── Post-Production/
    │   ├── Windows Font Fix.py
    │   └── windows-font-fix.sh
    └── Spacing/
        └── Set Diacritics Sidebearings.py
```

Tras la instalación, las herramientas aparecen en **Script → Plau**. Los nombres del menú pueden diferir de los nombres de archivo.

## Uso de los scripts

Abre una fuente, guarda una copia y elige una herramienta en el menú. Los constructores de glifos suelen actuar sobre todos los másteres de la fuente actual. Revisa las formas generadas, el espaciado y la interpolación antes de usarlos en producción.

| Elemento del menú | Glifos de origen o selección | Qué hace |
| --- | --- | --- |
| **Build Basic Math G4** | `n`, `hyphen`, `dotaccentcomb` y `figurespace` o `zero` | Construye `plus`, `minus`, `equal`, `multiply`, `divide`, `logicalnot`, `greater`, `less`, `greaterequal` y `lessequal`. |
| **Build En and Em Dashes from Hyphen** | `hyphen` | Reconstruye `endash` y `emdash` con componentes de hyphen escalados horizontalmente. Los anchos por defecto son el 140 % y el 180 % del ancho de avance del hyphen, con claves de sidebearing que hacen referencia al hyphen. |
| **Build Periodcentered and Bullet** | `period` | Reconstruye `periodcentered` y `bullet` a partir de componentes de period. El bullet usa por defecto una escala de 1,4×; ambos usan claves de sidebearing basadas en period. |
| **Build Arrows from Hyphen** | `hyphen`; opcionalmente `emdash`; stems en Font Info | Construye `arrowleft`, `arrowright`, `arrowup`, `arrowdown`, `arrowleftright` y `arrowupdown` en todos los másteres como strokes nativos de Glyphs 4: un path abierto para el asta y una punta en V, sin contornos. El grosor del trazo viene de los stems de cada máster (stem horizontal para los trazos horizontales, stem vertical para los verticales), con el grosor del hyphen como alternativa. Las flechas horizontales abarcan el ancho del emdash (o hyphen × factor) a la altura del hyphen; las verticales van de la línea de base a la altura de las mayúsculas. Los sidebearings hacen referencia a `hyphen`. Glyphs 4 renombra estos glifos al crearlos (por ejemplo, `arrowright` pasa a ser `rightArrow`); los que ya existen se encuentran por Unicode. |
| **Build Letters from Diacritic** | Uno o varios diacríticos seleccionados (combinantes, por ejemplo `acutecomb`, o heredados, por ejemplo `acute`), más las letras base de la fuente | Abre una ventana para elegir los conjuntos de idiomas latinos de Add Glyphs (Basic, Western European, Central European, South Eastern European, South American y otros) y añade cada letra de esos conjuntos que usa el diacrítico, como un compuesto de base + marca combinante con alineación automática en todos los másteres. Las letras cuya base falta (por ejemplo `idotless` para `iacute`) se omiten y se listan en el Macro Panel; las letras que ya tienen dibujo se dejan como están. Opcionalmente construye la marca espaciada heredada (`acutecomb` → `acute`), cuando existe en los datos de glifos, como un componente con alineación automática del comb. |
| **Center Components in Reference Height** | Glifos seleccionados que contienen componentes | Abre controles para el posicionamiento vertical respecto a la altura de mayúsculas, la altura de x o la altura de la capa, en la capa actual o en todas. Desactiva la alineación automática de los componentes movidos. |
| **Set Diacritics Sidebearings** | Todo glifo de categoría Mark | Las marcas combinantes (por ejemplo, `acutecomb`) reciben LSB `=40` y RSB `=|` (igual al LSB), con todas las capas sincronizadas. Las marcas espaciadas heredadas (por ejemplo, `acute`) no reciben claves propias: cada una pasa a ser un componente con alineación automática de su glifo `…comb` y sigue sus métricas. Los glifos heredados que ya contienen ese componente solo tienen la alineación automática activada; los vacíos se construyen; los que tienen otro dibujo se dejan como están y se listan en el Macro Panel (`REPLACE_DRAWN = True` los reconstruye). Se borran las claves de LSB/RSB a nivel de capa en estos glifos. |
| **Create Centerline** | Dos segmentos (los 2 nodos on-curve de cada uno, 4 en total, en el mismo contorno o en contornos distintos) o dos paths completos | Añade un nuevo path abierto a medio camino entre las dos líneas, por ejemplo el centro de un 8. Se pueden mezclar líneas y curvas; la dirección se ajusta automáticamente. Con dos paths completos, deben tener la misma estructura de nodos; el punto de inicio y la dirección se ajustan automáticamente (también funciona con contornos cerrados dibujados en sentidos opuestos). Los paths originales no se modifican y las coordenadas se redondean a unidades enteras. Inspirado en el Create Centerline de Harbor Type, reescrito para Glyphs 4. |
| **Flip Components** | Componentes seleccionados, o glifos seleccionados que contienen componentes | Abre una ventana con **Flip Horizontally** y **Flip Vertically**. Refleja los componentes seleccionados (o todos los componentes de los glifos seleccionados si no hay ninguno seleccionado) en todos los másteres a la vez, cada uno alrededor del centro de sus propios límites, de modo que se queda en su sitio y solo cambia su orientación. Los componentes se asocian entre másteres por su orden en el glifo. Desactiva la alineación automática de los componentes reflejados; ejecutarlo dos veces restaura el original. La casilla opcional **Include special layers** también refleja las capas brace, bracket y de copia de seguridad. |
| **Make Segments Parallel** | Dos segmentos en la capa actual (selecciona los 2 nodos on-curve de cada uno, 4 en total) | Gira ambos segmentos alrededor de su propio punto medio hasta el ángulo medio, de modo que quedan paralelos sin cambiar su longitud. Los tiradores unidos a los nodos movidos los acompañan. Un solo paso de deshacer. Atajo: `cmd+opt+shift+p`. |
| **Make Segments Symmetric** | Cuatro segmentos en la capa actual: dos a la izquierda y dos a la derecha del centro del glifo (por ejemplo, los cuatro bordes diagonales de una V) | Empareja cada segmento de la izquierda con su homólogo de la derecha y los convierte en imágenes especulares exactas respecto al eje vertical en ancho ÷ 2, promediando ambos lados. Los tiradores de los nodos movidos los acompañan. Si también hay segmentos cortos adicionales seleccionados, se usan los cuatro más largos. Un solo paso de deshacer. |
| **Fill Font Metadata** | Una fuente abierta, el nombre del cliente, un nombre de fuente opcional y el nombre, la URL y el vendor ID de tu foundry | Establece el nombre de la familia como el nombre de la fuente (usa el nombre del cliente si se deja vacío; el nombre del cliente se usa en el copyright), rellena designer y manufacturer (nombre y URL de la foundry), vendor ID y copyright, y restablece la versión a **0.000**. La casilla opcional **Add clean version string** deja la version string solo como “Version X.XXX” y añade `--no-info` a las opciones existentes de ttfautohint. Los campos de la foundry y la casilla se recuerdan entre ejecuciones. |
| **Windows Font Fix** | Fuentes TTF/OTF exportadas, elegidas en un diálogo de archivos (o pasadas por la línea de comandos) | Corrige las fuentes exportadas para que Microsoft Office (PowerPoint, Word) aplique sus sustituciones OpenType: añade una tabla `fvar` vacía, añade un registro de script `latn` copiado de `DFLT` en GSUB/GPOS y hace que `calt` ejecute también todos los lookups de `rclt` (compartidos, no copiados). Abre una ventana para elegir las correcciones y las fuentes; las copias van a una carpeta «Windows Fix» junto a cada fuente, salvo que elijas sobrescribir. Las fuentes web (`woff`, `woff2`) nunca se tocan y las fuentes variables reales conservan su `fvar`. También se ejecuta desde la línea de comandos y como Post-Export Command de Glyphs (véase abajo). |

### Comportamiento de Basic Math

- Cada máster usa el ancho de `figurespace` si ese glifo existe; si no, usa `zero`. El ancho debe ser positivo. `zero.tf` no es necesario.
- Las capas de máster vacías se rellenan. El dibujo existente se conserva en la mayoría de los símbolos, pero todas las capas de máster de los símbolos reciben el ancho elegido y se centran horizontalmente sin escalar.
- **`less` y `lessequal` se reconstruyen en cada ejecución**, sustituyendo el dibujo de sus capas de máster por componentes de `greater` y `greaterequal` reflejados horizontalmente.
- Al editar las formas de origen se actualizan sus homólogas reflejadas. Vuelve a ejecutar el script después de cambiar los anchos de origen del espaciado para aplicar los nuevos anchos y posiciones de reflejo.

### Glifos existentes

Dashes y Periodcentered/Bullet sustituyen el contenido de las capas de máster de destino. Fill Font Metadata sobrescribe los campos indicados arriba. En Arrow Maker, la opción **«Ask (backup then replace)» actualmente no muestra un diálogo de confirmación**; hace la copia de seguridad y sustituye. Usa una copia guardada de la fuente al probar estas herramientas.

### Windows Font Fix como Post-Export Command

Windows Font Fix puede ejecutarse automáticamente después de cada exportación con el plugin [Post-Export Command](https://github.com/florianpircher/Post-Export-Command) de Florian Pircher (en desarrollo; puede que haya que instalarlo desde su repositorio en lugar del Plugin Manager).

1. Copia `windows-font-fix.sh` y `Windows Font Fix.py` de la carpeta `Plau/Post-Production` junto a tu archivo `.glyphs`.
2. En Font Info, añade un custom parameter llamado `Post-Export Command` a la fuente (o a las instancias que exportas como TTF/OTF) con el valor `./windows-font-fix.sh`.
3. Exporta. El plugin ejecuta el comando desde la carpeta del archivo `.glyphs` y pasa la ruta de la fuente exportada como primer argumento. Las fuentes web (`woff`, `woff2`) se ignoran, así que las exportaciones para web quedan como están.

El script necesita Python con fontTools (`pip3 install fonttools`); `windows-font-fix.sh` lo busca en los lugares habituales, porque Glyphs inicia los comandos sin el entorno de tu shell. Desde la Terminal: `python3 "Windows Font Fix.py" --help`.

## Actualización y solución de problemas

Para actualizar, usa el Plugin Manager y recarga el menú Script. Conserva antes cualquier personalización local. Si sigue habiendo una copia manual de la carpeta `Plau` en la carpeta Scripts junto a la instalación del Plugin Manager, elimina una de las dos para que los scripts no aparezcan duplicados.

- **Falta un script:** revisa su ubicación, la extensión `.py` y la primera línea. Los scripts activos usan `#MenuTitle: …`. Recarga el menú después de mover o editar archivos.
- **El menú muestra Plau → Plau:** sube el contenido de la carpeta interior un nivel para que coincida con la estructura anterior.
- **Falta un glifo de origen:** créalo en la fuente, con contornos utilizables en cada máster, y vuelve a ejecutar la herramienta.
- **Un script falla:** copia el traceback completo de la consola de scripts de Glyphs e incluye, al informar del error, el nombre del script, la versión (build) de Glyphs y los pasos que lo provocaron.

Consulta la [guía de scripting de Glyphs](https://glyphsapp.com/learn/scripting-glyphs-part-3) (en inglés) para entender la instalación de scripts y los encabezados de menú.

## Contribuir

Mantén los scripts en la categoría adecuada, usa un encabezado `#MenuTitle:` en la primera línea e importa explícitamente los objetos de la API de Glyphs. Prueba los cambios en Glyphs 4 con una copia de una fuente, incluyendo varios másteres y glifos de destino ya existentes. Describe qué glifos o metadatos modifica un script. Evita añadir archivos de autoguardado del editor.

## Licencia

Consulta [la licencia GNU GPL v3 incluida en este repositorio](Plau/LICENSE).
