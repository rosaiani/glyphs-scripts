# Plau Glyphs Scripts

[English](README.md) · **Português** · [Español](README.es.md) · [日本語](README.ja.md) · [简体中文](README.zh.md)

Ferramentas em Python para o trabalho diário de design de tipos na Plau: construir glifos, posicionar componentes e preencher os metadados da fonte. Criado por Rodrigo Saiani com a ajuda do ChatGPT.

## Requisitos

- macOS e Glyphs 4.
- Suporte a scripts Python no Glyphs.
- A biblioteca de interface `vanilla`, para Arrow Maker, Center Components e Fill Font Metadata. Se uma importação falhar, verifique os módulos Python disponíveis no Plugin Manager do Glyphs.

Execute estes scripts **dentro do Glyphs**, não pelo Terminal. O Basic Math usa a API do Glyphs 4; a compatibilidade com o Glyphs 3 não é garantida. A visibilidade nos menus e a sintaxe Python foram verificadas, mas a coleção não foi totalmente testada em diferentes fontes e versões do Glyphs. Alguns diálogos e mensagens estão em português.

## Instalação

Instale os scripts pelo **Plugin Manager** do Glyphs (**Window → Plugin Manager → Scripts**). As atualizações também chegam pelo Plugin Manager; depois, recarregue os scripts (segure **Option** ao abrir o menu Script e escolha **Reload Scripts**, ou reinicie o Glyphs).

Para instalar manualmente, baixe ou clone este repositório, escolha **Script → Open Scripts Folder** no Glyphs 4 e copie a **pasta `Plau`** do repositório para lá, com as subpastas intactas. Depois, recarregue os scripts.

A estrutura instalada deve ficar assim:

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

Depois da instalação, as ferramentas aparecem em **Script → Plau**. Os nomes no menu podem ser diferentes dos nomes dos arquivos.

## Como usar os scripts

Abra uma fonte, salve uma cópia e escolha uma ferramenta no menu. Os construtores de glifos geralmente atuam em todas as masters da fonte atual. Revise as formas geradas, o espaçamento e a interpolação antes de usar em produção.

| Item do menu | Glifos de origem ou seleção | O que faz |
| --- | --- | --- |
| **Build Basic Math G4** | `n`, `hyphen`, `dotaccentcomb` e `figurespace` ou `zero` | Constrói `plus`, `minus`, `equal`, `multiply`, `divide`, `logicalnot`, `greater`, `less`, `greaterequal` e `lessequal`. |
| **Build En and Em Dashes from Hyphen** | `hyphen` | Reconstrói `endash` e `emdash` com componentes de hyphen escalados na horizontal. As larguras padrão são 140% e 180% da largura de avanço do hyphen, com chaves de sidebearing que referenciam o hyphen. |
| **Build Periodcentered and Bullet** | `period` | Reconstrói `periodcentered` e `bullet` a partir de componentes de period. O bullet usa escala 1,4× por padrão; ambos usam chaves de sidebearing baseadas no period. |
| **Build Arrows from Hyphen** | `hyphen`; opcionalmente `emdash`; stems no Font Info | Constrói `arrowleft`, `arrowright`, `arrowup`, `arrowdown`, `arrowleftright` e `arrowupdown` em todas as masters como strokes nativos do Glyphs 4: um path aberto para a haste e uma ponta em V, sem contornos. A espessura do traço vem dos stems de cada master (stem horizontal para traços horizontais, stem vertical para os verticais), com a espessura do hyphen como alternativa. As setas horizontais ocupam a largura do emdash (ou hyphen × fator) na altura do hyphen; as verticais vão da linha de base até a altura das maiúsculas. Os sidebearings referenciam `hyphen`. O Glyphs 4 renomeia esses glifos ao criá-los (por exemplo, `arrowright` vira `rightArrow`); os já existentes são encontrados pelo Unicode. |
| **Build Letters from Diacritic** | Um ou mais diacríticos selecionados (combinantes, por exemplo `acutecomb`, ou legados, por exemplo `acute`), mais as letras base da fonte | Abre uma janela para escolher os conjuntos de idiomas latinos do Add Glyphs (Basic, Western European, Central European, South Eastern European, South American e outros) e adiciona toda letra desses conjuntos que usa o diacrítico, como um composto de base + marca combinante com alinhamento automático em todas as masters. Letras cuja base está ausente (por exemplo `idotless` para `iacute`) são ignoradas e listadas no Macro Panel; letras que já têm desenho são deixadas como estão. Opcionalmente constrói a marca espaçada legada (`acutecomb` → `acute`), quando ela existe nos dados de glifos, como um componente com alinhamento automático do comb. |
| **Center Components in Reference Height** | Glifos selecionados que contêm componentes | Abre controles para posicionamento vertical em relação à altura das maiúsculas, à altura-x ou à altura da layer, na layer atual ou em todas. Desativa o alinhamento automático dos componentes movidos. |
| **Set Diacritics Sidebearings** | Todo glifo da categoria Mark | Marcas combinantes (por exemplo, `acutecomb`) recebem LSB `=40` e RSB `=|` (igual ao LSB), com todas as layers sincronizadas. Marcas espaçadas legadas (por exemplo, `acute`) não recebem chaves próprias: cada uma vira um componente com alinhamento automático do seu glifo `…comb` e segue as métricas dele. Glifos legados que já contêm esse componente apenas têm o alinhamento automático ativado; os vazios são construídos; os que têm outro desenho são deixados como estão e listados no Macro Panel (`REPLACE_DRAWN = True` os reconstrói). As chaves de LSB/RSB no nível da layer desses glifos são apagadas. |
| **Create Centerline** | Dois segmentos (os 2 nós on-curve de cada um, 4 no total, no mesmo contorno ou em contornos diferentes) ou dois caminhos inteiros | Adiciona um novo path aberto no meio das duas linhas, por exemplo o miolo de um 8. Linhas e curvas podem ser misturadas; a direção é ajustada automaticamente. Com dois caminhos inteiros, eles precisam ter a mesma estrutura de nós; o ponto de partida e a direção são ajustados automaticamente (também funciona com contornos fechados desenhados em sentidos opostos). Os caminhos originais não são alterados e as coordenadas são arredondadas para unidades inteiras. Inspirado no Create Centerline da Harbor Type, reescrito para o Glyphs 4. |
| **Flip Components** | Componentes selecionados, ou glifos selecionados que contêm componentes | Abre uma janela com **Flip Horizontally** e **Flip Vertically**. Espelha os componentes selecionados (ou todos os componentes dos glifos selecionados, se nenhum estiver selecionado) em todas as masters de uma vez, cada um em torno do centro dos seus próprios limites, de modo que ele fica no lugar e só muda a orientação. Os componentes são associados entre as masters pela ordem no glifo. Desativa o alinhamento automático dos componentes espelhados; executar duas vezes restaura o original. A caixa opcional **Include special layers** também espelha layers brace, bracket e de backup. |
| **Make Segments Parallel** | Dois segmentos na layer atual (selecione os 2 nós on-curve de cada um, 4 no total) | Gira os dois segmentos em torno do próprio ponto médio até o ângulo médio, tornando-os paralelos sem mudar o comprimento. As alças ligadas aos nós movidos acompanham. Um único passo de desfazer. Atalho: `cmd+opt+shift+p`. |
| **Make Segments Symmetric** | Quatro segmentos na layer atual: dois à esquerda e dois à direita do centro do glifo (por exemplo, as quatro bordas diagonais de um V) | Une cada segmento da esquerda ao seu par da direita e os torna imagens espelhadas exatas em relação ao eixo vertical em largura ÷ 2, tirando a média dos dois lados. As alças dos nós movidos acompanham. Se segmentos curtos extras também estiverem selecionados, usa os quatro mais longos. Um único passo de desfazer. |
| **Fill Font Metadata** | Uma fonte aberta, o nome do cliente, um nome de fonte opcional e o nome, a URL e o vendor ID da sua foundry | Define o nome da família como o nome da fonte (usa o nome do cliente se ficar vazio; o nome do cliente é usado no copyright), preenche designer e manufacturer (nome e URL da foundry), vendor ID e copyright, e redefine a versão para **0.000**. A caixa opcional **Add clean version string** define a version string apenas como “Version X.XXX” e adiciona `--no-info` às opções existentes do ttfautohint. Os campos da foundry e a caixa são lembrados entre as execuções. |
| **Windows Font Fix** | Fontes TTF/OTF exportadas, escolhidas numa janela de arquivos (ou passadas na linha de comando) | Corrige fontes exportadas para que o Microsoft Office (PowerPoint, Word) aplique suas substituições OpenType: adiciona uma tabela `fvar` vazia, adiciona um registro de script `latn` copiado de `DFLT` em GSUB/GPOS e faz o `calt` executar também todos os lookups do `rclt` (compartilhados, não copiados). Abre uma janela para escolher as correções e as fontes; as cópias vão para uma pasta “Windows Fix” ao lado de cada fonte, a menos que você escolha sobrescrever. Fontes web (`woff`, `woff2`) nunca são alteradas e fontes variáveis reais mantêm o seu `fvar`. Também roda pela linha de comando e como Post-Export Command do Glyphs (veja abaixo). |

### Comportamento do Basic Math

- Cada master usa a largura de `figurespace`, se esse glifo existir; caso contrário, usa `zero`. A largura precisa ser positiva. `zero.tf` não é necessário.
- As layers de master vazias são preenchidas. O desenho existente é mantido na maioria dos símbolos, mas todas as layers de master dos símbolos recebem a largura escolhida e são centralizadas na horizontal, sem escala.
- **`less` e `lessequal` são reconstruídos a cada execução**, substituindo o desenho das layers de master por componentes de `greater` e `greaterequal` espelhados na horizontal.
- Editar as formas de origem atualiza os glifos espelhados. Execute o script de novo depois de mudar as larguras de origem do espaçamento, para aplicar as novas larguras e posições de reflexo.
- Todos os símbolos usam **uma única espessura de traço**, então todas as partes de `plus`, `multiply` e dos demais têm a mesma espessura. Ela segue os stems de cada master (Font Info → Masters → Stems): por padrão o stem horizontal, a mesma espessura do `minus`. Uma master sem stems tem esses valores medidos nos glifos clássicos: `l`, `I` ou `H` (vertical, com `n` como último recurso) e o travessão do `H` ou o `hyphen` (horizontal). A origem de cada valor é impressa no Macro Panel. No início do script, `math_stem` escolhe `"horizontal"`, `"vertical"` ou `"average"`, e `math_stem_factor` deixa os símbolos mais leves ou mais pesados que esse stem.
- `greater` é um caminho aberto com stroke nativo do Glyphs 4 (e `less` o espelha), então depois da geração você pode mover os nós ou mudar a espessura do stroke em vez de editar um contorno.

### Glifos existentes

Dashes e Periodcentered/Bullet substituem o conteúdo das layers de master de destino. O Fill Font Metadata sobrescreve os campos listados acima. No Arrow Maker, a opção **“Ask (backup then replace)” atualmente não mostra um diálogo de confirmação**; ela faz o backup e substitui. Use uma cópia salva da fonte ao testar estas ferramentas.

### Windows Font Fix como Post-Export Command

O Windows Font Fix pode rodar automaticamente depois de cada exportação, com o plugin [Post-Export Command](https://github.com/florianpircher/Post-Export-Command) de Florian Pircher (em desenvolvimento; pode ser preciso instalá-lo pelo repositório dele em vez do Plugin Manager).

1. Copie `windows-font-fix.sh` e `Windows Font Fix.py` da pasta `Plau/Post-Production` para ao lado do seu arquivo `.glyphs`.
2. No Font Info, adicione um custom parameter chamado `Post-Export Command` à fonte (ou às instâncias que você exporta como TTF/OTF) com o valor `./windows-font-fix.sh`.
3. Exporte. O plugin executa o comando a partir da pasta do arquivo `.glyphs` e passa o caminho da fonte exportada como primeiro argumento. Fontes web (`woff`, `woff2`) são ignoradas, então as exportações para web ficam como estão.

O script precisa de Python com fontTools (`pip3 install fonttools`); o `windows-font-fix.sh` o procura nos lugares usuais, porque o Glyphs inicia comandos sem o ambiente do seu shell. No Terminal: `python3 "Windows Font Fix.py" --help`.

## Atualização e solução de problemas

Para atualizar, use o Plugin Manager e recarregue o menu Script. Preserve antes qualquer personalização local. Se ainda houver uma cópia manual da pasta `Plau` na pasta Scripts junto com a instalação do Plugin Manager, remova uma das duas para que os scripts não apareçam duplicados.

- **Falta um script:** verifique o local, a extensão `.py` e a primeira linha. Os scripts ativos usam `#MenuTitle: …`. Recarregue o menu depois de mover ou editar arquivos.
- **O menu mostra Plau → Plau:** mova o conteúdo da pasta interna um nível acima, para ficar como na estrutura acima.
- **Falta um glifo de origem:** crie-o na fonte, com contornos utilizáveis em cada master, e execute a ferramenta de novo.
- **Um script falha:** copie o traceback completo do console de scripts do Glyphs e, ao relatar o erro, inclua o nome do script, a versão (build) do Glyphs e os passos que levaram ao erro.

Veja o [guia de scripts do Glyphs](https://glyphsapp.com/learn/scripting-glyphs-part-3) (em inglês) para entender a instalação de scripts e os cabeçalhos de menu.

## Contribuindo

Mantenha os scripts na categoria adequada, use um cabeçalho `#MenuTitle:` na primeira linha e importe explicitamente os objetos da API do Glyphs. Teste as mudanças no Glyphs 4 com uma cópia de uma fonte, incluindo várias masters e glifos de destino já existentes. Descreva quais glifos ou metadados um script altera. Evite adicionar arquivos de autosave do editor.

## Licença

Veja [a licença GNU GPL v3 incluída neste repositório](Plau/LICENSE).
