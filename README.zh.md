# Plau Glyphs Scripts

[English](README.md) · [Português](README.pt.md) · [Español](README.es.md) · [日本語](README.ja.md) · **简体中文**

Plau 日常字体设计工作使用的 Python 工具：构建字形、定位组件、设置字体元数据。作者为 Rodrigo Saiani，在 ChatGPT 的协助下完成。

## 系统要求

- macOS 和 Glyphs 4。
- Glyphs 的 Python 脚本支持。
- Arrow Maker、Center Components 和 Fill Font Metadata 需要界面库 `vanilla`。如果导入失败，请在 Glyphs 的 Plugin Manager 中检查可用的 Python 模块。

请在 **Glyphs 内部**运行这些脚本，不要在终端（Terminal）中运行。Basic Math 使用 Glyphs 4 的 API，不保证与 Glyphs 3 兼容。菜单显示和 Python 语法已经检查过，但这套脚本尚未在各种字体和 Glyphs 版本上经过充分测试。部分对话框和提示信息为葡萄牙语。

## 安装

通过 Glyphs 的 **Plugin Manager**（**Window → Plugin Manager → Scripts**）安装脚本。更新也通过 Plugin Manager 进行；更新后请重新加载脚本（打开 Script 菜单时按住 **Option** 键并选择 **Reload Scripts**，或重启 Glyphs）。

如需手动安装，请下载或克隆本仓库，在 Glyphs 4 中选择 **Script → Open Scripts Folder**，然后把仓库中的 **`Plau` 文件夹**连同子文件夹原样复制进去。之后重新加载脚本。

安装后的结构应如下所示：

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

安装后，这些工具会出现在 **Script → Plau** 下。菜单名称可能与文件名不同。

## 使用脚本

打开一个字体，先保存一份副本，然后从菜单中选择工具。字形构建脚本通常会作用于当前字体的所有主板（master）。在投入正式制作之前，请检查生成的形状、间距和插值效果。

| 菜单项 | 源字形或选择 | 功能 |
| --- | --- | --- |
| **Build Basic Math G4** | `n`、`hyphen`、`dotaccentcomb`，以及 `figurespace` 或 `zero` | 构建 `plus`、`minus`、`equal`、`multiply`、`divide`、`logicalnot`、`greater`、`less`、`greaterequal` 和 `lessequal`。 |
| **Build En and Em Dashes from Hyphen** | `hyphen` | 用水平缩放的 hyphen 组件重新构建 `endash` 和 `emdash`。默认宽度为 hyphen 推进宽度的 140% 和 180%，边距键（sidebearing key）引用 hyphen。 |
| **Build Periodcentered and Bullet** | `period` | 用 period 组件重新构建 `periodcentered` 和 `bullet`。bullet 默认缩放为 1.4 倍；两者都使用基于 period 的边距键。 |
| **Build Arrows from Hyphen** | `hyphen`；可选 `emdash`；Font Info 中的笔画粗细（stems） | 在每个主板中，以 Glyphs 4 原生描边（stroke）的方式构建 `arrowleft`、`arrowright`、`arrowup`、`arrowdown`、`arrowleftright` 和 `arrowupdown`：一条开放路径作为箭杆，加上 V 形箭头，不使用轮廓。描边粗细取自每个主板的笔画粗细（水平线条用水平 stem，垂直线条用垂直 stem），没有时退回到 hyphen 的粗细。水平箭头在 hyphen 的高度上，宽度取 emdash 的宽度（或 hyphen × 系数）；垂直箭头从基线延伸到大写字母高度。边距引用 `hyphen`。Glyphs 4 在创建这些字形时会重命名（例如 `arrowright` 会变成 `rightArrow`）；已有的字形通过 Unicode 查找。 |
| **Build Letters from Diacritic** | 选中的一个或多个变音符号（组合标记，例如 `acutecomb`，或旧式标记，例如 `acute`），以及字体中的基础字母 | 打开一个窗口，用于选择 Add Glyphs 中的拉丁语言字符集（Basic、Western European、Central European、South Eastern European、South American 等），并把这些字符集中所有使用该变音符号的字母添加为“基础字母 + 组合标记”的复合字形，在所有主板中使用自动对齐。缺少基础字形的字母（例如 `iacute` 所需的 `idotless`）会被跳过并列在 Macro Panel 中；已有图形的字母保持不变。还可以选择构建旧式间隔标记（`acutecomb` → `acute`，前提是字形数据中存在），作为 comb 的自动对齐组件。 |
| **Center Components in Reference Height** | 所选的包含组件的字形 | 打开控件，可相对于大写字母高度、x 高度或图层高度进行垂直定位，作用于当前图层或所有图层。会关闭被移动组件的自动对齐。 |
| **Set Diacritics Sidebearings** | 所有类别为 Mark 的字形 | 组合标记（例如 `acutecomb`）的 LSB 设为 `=40`，RSB 设为 `=|`（与 LSB 相同），并同步所有图层。旧式的间隔标记（例如 `acute`）本身不设键：每个都会变成其 `…comb` 字形的自动对齐组件，并沿用其度量。已经包含该组件的旧式字形只会打开自动对齐；空的会被构建；含有其他图形的则保持不变，并在 Macro Panel 中列出（设置 `REPLACE_DRAWN = True` 可将其重建）。这些字形上图层级别的 LSB/RSB 键会被清除。 |
| **Create Centerline** | 两个线段（每个线段选中 2 个曲线上的节点，共 4 个，可以在同一轮廓或不同轮廓中），或两个完整的路径 | 在两条线的正中间添加一条新的开放路径，例如 8 的中间腰部。直线和曲线可以混合使用，方向会自动匹配。选择两个完整路径时，它们必须具有相同的节点结构；起点和方向会自动匹配（也适用于方向相反的闭合轮廓）。原始路径不会被修改，坐标会四舍五入为整数。灵感来自 Harbor Type 的 Create Centerline，并针对 Glyphs 4 重写。 |
| **Flip Components** | 选中的组件，或包含组件的选中字形 | 打开一个带有 **Flip Horizontally** 和 **Flip Vertically** 按钮的窗口。在所有主板中同时翻转选中的组件（未选中任何组件时，翻转所选字形的全部组件），每个组件都围绕自身边界的中心翻转，因此位置不变，只改变朝向。主板之间按组件在字形中的顺序进行匹配。会关闭被翻转组件的自动对齐；运行两次即可还原。可选复选框 **Include special layers** 还会翻转 brace、bracket 和备份图层。 |
| **Make Segments Parallel** | 当前图层中的两个线段（每个线段选中 2 个曲线上的节点，共 4 个） | 让两个线段各自绕自己的中点旋转到平均角度，使它们在长度不变的情况下变得平行。与被移动节点相连的手柄会跟随移动。只需一次撤销。快捷键：`cmd+opt+shift+p`。 |
| **Make Segments Symmetric** | 当前图层中的四个线段：字形中心左侧两个、右侧两个（例如 V 的四条斜边） | 将左侧每个线段与右侧对应的线段配对，并取两侧的平均值，使它们关于宽度 ÷ 2 处的垂直轴成为精确的镜像。被移动节点上的手柄会跟随移动。如果还选中了多余的短线段，则使用最长的四个。只需一次撤销。 |
| **Fill Font Metadata** | 一个已打开的字体、客户名称、可选的字体名称，以及你的字体厂牌（foundry）名称、URL 和 vendor ID | 将字体家族名设为字体名称（留空时使用客户名称；版权信息中使用客户名称），填写设计师和制造商（厂牌名称和 URL）、vendor ID 和版权信息，并将版本重置为 **0.000**。可选复选框 **Add clean version string** 会把版本字符串设为仅“Version X.XXX”，并在已有的 ttfautohint 选项中加入 `--no-info`。厂牌字段和复选框的状态会在多次运行之间保留。 |
| **Windows Font Fix** | 导出的 TTF/OTF 字体（在文件对话框中选择，或通过命令行传入） | 修复导出的字体，使 Microsoft Office（PowerPoint、Word）能够应用其 OpenType 替换：添加空的 `fvar` 表，在 GSUB/GPOS 中添加从 `DFLT` 复制的 `latn` 脚本记录，并让 `calt` 同时运行所有 `rclt` 查找（共享，而非复制）。会打开一个窗口来选择要应用的修复和字体；除非选择覆盖，否则副本会保存在每个字体旁边的“Windows Fix”文件夹中。网页字体（`woff`、`woff2`）绝不会被改动，真正的可变字体会保留其 `fvar`。也可以通过命令行运行，或作为 Glyphs 的 Post-Export Command 运行（见下文）。 |

### Basic Math 的行为

- 每个主板使用 `figurespace` 的宽度（如果存在该字形）；否则使用 `zero` 的宽度。宽度必须为正数。不需要 `zero.tf`。
- 空的主板图层会被填充。大多数符号会保留已有的图形，但所有符号的主板图层都会被设为所选宽度，并在水平方向居中，不进行缩放。
- **`less` 和 `lessequal` 每次运行都会重建**，其主板图层中的图形会被替换为 `greater` 和 `greaterequal` 水平镜像后的组件。
- 编辑源形状会同时更新其镜像对应的字形。更改间距来源的宽度后，请重新运行脚本，以应用新的宽度和镜像位置。

### 已有的字形

Dashes 和 Periodcentered/Bullet 会替换目标主板图层的内容。Fill Font Metadata 会覆盖上面列出的字段。在 Arrow Maker 中，标为 **“Ask (backup then replace)” 的选项目前不会显示确认对话框**；它会先备份再替换。试用这些工具时，请使用已保存的字体副本。

### 将 Windows Font Fix 用作 Post-Export Command

借助 Florian Pircher 的 [Post-Export Command](https://github.com/florianpircher/Post-Export-Command) 插件，Windows Font Fix 可以在每次导出后自动运行（该插件仍在开发中，可能需要从作者的仓库安装，而不是通过 Plugin Manager）。

1. 把 `Plau/Post-Production` 文件夹中的 `windows-font-fix.sh` 和 `Windows Font Fix.py` 复制到你的 `.glyphs` 文件旁边。
2. 在 Font Info 中，为字体（或你导出为 TTF/OTF 的实例）添加一个名为 `Post-Export Command` 的自定义参数，值为 `./windows-font-fix.sh`。
3. 导出。插件会从 `.glyphs` 文件所在的文件夹运行该命令，并把导出字体的路径作为第一个参数传入。网页字体（`woff`、`woff2`）会被忽略，因此网页导出保持不变。

脚本需要带有 fontTools 的 Python（`pip3 install fonttools`）；由于 Glyphs 启动命令时没有你的 shell 环境，`windows-font-fix.sh` 会在常见位置查找它。在终端中可运行 `python3 "Windows Font Fix.py" --help`。

## 更新与故障排除

要更新，请使用 Plugin Manager，然后重新加载 Script 菜单。请先保留好本地的自定义修改。如果 Scripts 文件夹中除了 Plugin Manager 的安装之外，还有手动复制的 `Plau` 文件夹，请删除其中一个，以免脚本重复出现。

- **找不到某个脚本：** 检查它的位置、`.py` 扩展名和第一行。有效的脚本以 `#MenuTitle: …` 开头。移动或编辑文件后，请重新加载菜单。
- **菜单显示 Plau → Plau：** 把内层文件夹的内容向上移动一级，使其与上面的结构一致。
- **缺少源字形：** 在字体中创建该字形，并在每个主板中提供可用的轮廓，然后重新运行工具。
- **脚本运行失败：** 从 Glyphs 的脚本控制台复制完整的 traceback，并在报告问题时附上脚本名称、Glyphs 版本（build）以及导致错误的操作步骤。

有关脚本安装和菜单头部的背景知识，请参阅 [Glyphs 脚本编写指南](https://glyphsapp.com/learn/scripting-glyphs-part-3)（英文）。

## 参与贡献

请把脚本放在合适的分类下，第一行使用 `#MenuTitle:` 头部，并显式导入 Glyphs API 对象。请在 Glyphs 4 中使用字体副本测试更改，包括多个主板和已有的目标字形。请说明脚本会修改哪些字形或元数据。请不要添加编辑器的自动保存文件。

## 许可证

请参阅[本仓库中包含的 GNU GPL v3 许可证](Plau/LICENSE)。
