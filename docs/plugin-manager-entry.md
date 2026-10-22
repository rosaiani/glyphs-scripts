# Plugin Manager entry (titles and descriptions)

The Plugin Manager reads its list from `packages.plist` in the
[schriftgestalt/glyphs-packages](https://github.com/schriftgestalt/glyphs-packages) repository, not from this one.
These are the localized `titles` and `descriptions` for this package, ready to paste into the existing entry
(keep the other keys of the entry as they are, and match the format of the neighboring entries).

```text
titles = {
	en = "Plau Scripts";
	pt = "Plau Scripts";
	es = "Plau Scripts";
	ja = "Plau Scripts";
	"zh-Hans" = "Plau Scripts";
};
descriptions = {
	en = "Everyday type design tools from Plau for Glyphs 4: build math symbols, dashes, bullets and arrows, set diacritic sidebearings, center components, align segments and fill in font metadata.";
	pt = "Ferramentas de design de tipos do dia a dia da Plau para o Glyphs 4: construa símbolos matemáticos, travessões, bullets e setas, defina sidebearings de diacríticos, centralize componentes, alinhe segmentos e preencha os metadados da fonte.";
	es = "Herramientas de diseño tipográfico del día a día de Plau para Glyphs 4: construye símbolos matemáticos, rayas, bullets y flechas, define sidebearings de diacríticos, centra componentes, alinea segmentos y rellena los metadatos de la fuente.";
	ja = "Plau が日々のタイプデザインで使っている Glyphs 4 用ツール集。数学記号、ダッシュ、ブレット、矢印の作成、ダイアクリティカルマークのサイドベアリング設定、コンポーネントの中央揃え、セグメントの整列、フォントメタデータの入力ができます。";
	"zh-Hans" = "Plau 日常字体设计使用的 Glyphs 4 工具集：构建数学符号、破折号、圆点和箭头，设置变音符号的边距，居中组件，对齐线段，并填写字体元数据。";
};
```

Notes:
- Language codes follow the ones already used in `packages.plist`; check the neighboring entries and adjust
  (for example `zh-Hans` vs `zh`) if the file uses a different code.
- The full documentation in each language is in the READMEs: [English](../README.md),
  [Português](../README.pt.md), [Español](../README.es.md), [日本語](../README.ja.md), [简体中文](../README.zh.md).
