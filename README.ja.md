# Plau Glyphs Scripts

[English](README.md) · [Português](README.pt.md) · [Español](README.es.md) · **日本語** · [简体中文](README.zh.md)

Plau での日々のタイプデザイン作業のための Python ツール集です。グリフの作成、コンポーネントの配置、フォントのメタデータ設定ができます。作者は Rodrigo Saiani で、ChatGPT の支援を受けて作成しました。

## 動作環境

- macOS と Glyphs 4。
- Glyphs の Python スクリプト機能。
- Arrow Maker、Center Components、Fill Font Metadata には UI ライブラリ `vanilla` が必要です。インポートに失敗する場合は、Glyphs の Plugin Manager で利用可能な Python モジュールを確認してください。

これらのスクリプトは Terminal ではなく、**Glyphs の中で**実行してください。Basic Math は Glyphs 4 の API を使用しており、Glyphs 3 との互換性は保証されません。メニューへの表示と Python の構文は確認済みですが、さまざまなフォントや Glyphs のビルドでの動作は十分にテストされていません。一部のダイアログとメッセージはポルトガル語です。

## インストール

Glyphs の **Plugin Manager**（**Window → Plugin Manager → Scripts**）からスクリプトをインストールします。アップデートも Plugin Manager から行えます。更新後はスクリプトを再読み込みしてください（Script メニューを開くときに **Option** キーを押しながら **Reload Scripts** を選ぶか、Glyphs を再起動します）。

手動でインストールする場合は、このリポジトリをダウンロードまたはクローンし、Glyphs 4 で **Script → Open Scripts Folder** を選び、リポジトリの **`Plau` フォルダ**をサブフォルダごとそのままコピーします。その後、スクリプトを再読み込みしてください。

インストール後の構成は次のようになります。

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

インストール後、ツールは **Script → Plau** に表示されます。メニューの名前はファイル名と異なる場合があります。

## スクリプトの使い方

フォントを開き、コピーを保存してから、メニューでツールを選びます。グリフビルダーは通常、現在のフォントのすべてのマスターに対して動作します。生成されたシェイプ、スペーシング、補間を確認してから、制作に使用してください。

| メニュー項目 | 元になるグリフまたは選択 | 内容 |
| --- | --- | --- |
| **Build Basic Math G4** | `n`、`hyphen`、`dotaccentcomb`、および `figurespace` または `zero` | `plus`、`minus`、`equal`、`multiply`、`divide`、`logicalnot`、`greater`、`less`、`greaterequal`、`lessequal` を作成します。 |
| **Build En and Em Dashes from Hyphen** | `hyphen` | 水平方向に拡大した hyphen のコンポーネントで `endash` と `emdash` を作り直します。既定の幅は hyphen のアドバンス幅の 140% と 180% で、サイドベアリングのキーは hyphen を参照します。 |
| **Build Periodcentered and Bullet** | `period` | period のコンポーネントから `periodcentered` と `bullet` を作り直します。bullet の既定の拡大率は 1.4 倍で、どちらも period に基づくサイドベアリングのキーを使います。 |
| **Build Arrows from Hyphen** | `hyphen`、任意で `emdash`、Font Info のステム | `arrowleft`、`arrowright`、`arrowup`、`arrowdown`、`arrowleftright`、`arrowupdown` を、すべてのマスターで Glyphs 4 のネイティブなストロークとして作成します。軸となる開いたパスと V 字の矢じりで構成され、アウトラインは使いません。線の太さは各マスターのステムから決まり（水平の線は水平ステム、垂直の線は垂直ステム）、ステムがない場合は hyphen の太さを使います。水平の矢印は hyphen の高さで emdash の幅（または hyphen × 係数）に広がり、垂直の矢印はベースラインからキャップハイトまで伸びます。サイドベアリングは `hyphen` を参照します。Glyphs 4 は作成時にこれらのグリフ名を変更します（たとえば `arrowright` は `rightArrow` になります）。既存のグリフは Unicode で見つけます。 |
| **Build Letters from Diacritic** | 選択した 1 つ以上のダイアクリティカルマーク（結合マーク。例: `acutecomb`、または従来のマーク。例: `acute`）と、フォント内のベース文字 | Add Glyphs のラテン文字の言語セット（Basic、Western European、Central European、South Eastern European、South American など）を選ぶウィンドウを開き、そのダイアクリティカルマークを使うセット内のすべての文字を、すべてのマスターで自動整列のベース + 結合マークのコンポジットとして追加します。ベースグリフがない文字（たとえば `iacute` に対する `idotless`）はスキップされて Macro Panel に一覧表示され、すでにアートワークがある文字はそのまま残ります。オプションで、グリフデータに存在する場合に、従来のスペーシングマーク（`acutecomb` → `acute`）を comb の自動整列コンポーネントとして作成します。 |
| **Center Components in Reference Height** | コンポーネントを含む選択したグリフ | キャップハイト、x ハイト、またはレイヤーの高さを基準に、現在のレイヤーまたはすべてのレイヤーで垂直方向の位置を調整するコントロールを開きます。移動したコンポーネントの自動整列はオフになります。 |
| **Set Diacritics Sidebearings** | カテゴリが Mark のすべてのグリフ | 結合マーク（例: `acutecomb`）には LSB `=40` と RSB `=|`（LSB と同じ値）を設定し、すべてのレイヤーを同期します。従来のスペーシングマーク（例: `acute`）には独自のキーを設定せず、それぞれ対応する `…comb` グリフの自動整列コンポーネントにして、そのメトリクスに従わせます。すでにそのコンポーネントを持つ従来のグリフは自動整列をオンにするだけで、空のグリフは新しく作成され、別のアートワークがあるグリフはそのままにして Macro Panel に一覧表示します（`REPLACE_DRAWN = True` にすると作り直します）。これらのグリフでは、レイヤー単位の LSB/RSB キーは削除されます。 |
| **Create Centerline** | 2 つのセグメント（それぞれの 2 つのオンカーブノード、合計 4 つ。同じ輪郭でも別の輪郭でも可）、または 2 つのパス全体 | 2 本の線のちょうど中間に、新しい開いたパスを追加します（たとえば 8 の中央のくびれ部分）。直線と曲線を混在させることができ、方向は自動的に合わせられます。パス全体を 2 つ選ぶ場合は、ノード構成が同じである必要があります。開始点と方向は自動的に合わせられます（反対向きに描かれた閉じた輪郭でも動作します）。元のパスは変更されず、座標は整数に丸められます。Harbor Type の Create Centerline にヒントを得て、Glyphs 4 向けに書き直したものです。 |
| **Flip Components** | 選択したコンポーネント、またはコンポーネントを含む選択したグリフ | **Flip Horizontally** と **Flip Vertically** のボタンがあるウィンドウを開きます。選択したコンポーネント（何も選択していない場合は、選択したグリフのすべてのコンポーネント）を、すべてのマスターで一度に反転します。各コンポーネントは自身のバウンディングボックスの中心を軸に反転するため、位置は変わらず向きだけが変わります。マスター間では、グリフ内での順序でコンポーネントを対応づけます。反転したコンポーネントの自動整列はオフになります。2 回実行すると元に戻ります。オプションのチェックボックス **Include special layers** をオンにすると、brace、bracket、バックアップのレイヤーも反転します。 |
| **Make Segments Parallel** | 現在のレイヤーの 2 つのセグメント（それぞれの 2 つのオンカーブノードを選択、合計 4 つ） | 2 つのセグメントをそれぞれの中点を中心に平均の角度へ回転させ、長さを変えずに平行にします。移動したノードにつながるハンドルも一緒に動きます。取り消しは 1 回で戻せます。ショートカット: `cmd+opt+shift+p`。 |
| **Make Segments Symmetric** | 現在のレイヤーの 4 つのセグメント（グリフの中心の左右に 2 つずつ。たとえば V の 4 本の斜めの辺） | 左のセグメントと右の対応するセグメントを組にして、幅 ÷ 2 の縦軸に対して正確に鏡像になるように、両側の平均をとって整えます。移動したノードのハンドルも一緒に動きます。短いセグメントも余分に選択されている場合は、長い方の 4 つを使います。取り消しは 1 回で戻せます。 |
| **Fill Font Metadata** | 開いているフォント、クライアント名、任意のフォント名、およびファウンドリーの名前・URL・ベンダー ID | ファミリー名をフォント名に設定し（空の場合はクライアント名を使います。クライアント名はコピーライトに使われます）、デザイナーとメーカー（ファウンドリーの名前と URL）、ベンダー ID、コピーライトを入力して、バージョンを **0.000** にリセットします。任意のチェックボックス **Add clean version string** をオンにすると、バージョン文字列が「Version X.XXX」だけになり、既存の ttfautohint のオプションに `--no-info` が追加されます。ファウンドリーの項目とチェックボックスは次回以降も記憶されます。 |
| **Windows Font Fix** | 書き出した TTF/OTF フォント（ファイルダイアログで選択、またはコマンドラインで指定） | 書き出したフォントを修正し、Microsoft Office（PowerPoint、Word）が OpenType の置換を適用するようにします。空の `fvar` テーブルの追加、GSUB/GPOS の `DFLT` から複製した `latn` スクリプトレコードの追加、`calt` が `rclt` のすべてのルックアップも実行するようにする設定（コピーではなく共有）を行います。修正内容とフォントを選ぶウィンドウを開き、上書きを選ばない限り、各フォントの隣の「Windows Fix」フォルダにコピーを保存します。Web フォント（`woff`、`woff2`）には一切触れず、本物のバリアブルフォントは `fvar` を保持します。コマンドラインや Glyphs の Post-Export Command としても実行できます（下記参照）。 |

### Basic Math の動作

- 各マスターは、`figurespace` があればその幅を、なければ `zero` の幅を使います。幅は正の値である必要があります。`zero.tf` は不要です。
- 空のマスターレイヤーは埋められます。多くの記号では既存のアートワークが残りますが、すべての記号のマスターレイヤーに選ばれた幅が設定され、拡大縮小なしで水平方向の中央に配置されます。
- **`less` と `lessequal` は実行のたびに作り直され**、マスターレイヤーのアートワークは、`greater` と `greaterequal` を水平方向に反転したコンポーネントに置き換えられます。
- 元のシェイプを編集すると、反転した側も更新されます。スペーシングの元になる幅を変更したら、スクリプトを再実行して新しい幅と反転位置を反映させてください。

### 既存のグリフ

Dashes と Periodcentered/Bullet は、対象のマスターレイヤーの内容を置き換えます。Fill Font Metadata は上記の項目を上書きします。Arrow Maker の **「Ask (backup then replace)」オプションは、現在、確認ダイアログを表示しません**。バックアップを作成して置き換えます。これらのツールを試すときは、保存済みのフォントのコピーを使ってください。

### Post-Export Command としての Windows Font Fix

Florian Pircher 氏の [Post-Export Command](https://github.com/florianpircher/Post-Export-Command) プラグインを使うと、書き出しのたびに Windows Font Fix を自動実行できます（開発中のため、Plugin Manager ではなく作者のリポジトリからインストールする必要がある場合があります）。

1. `Plau/Post-Production` フォルダの `windows-font-fix.sh` と `Windows Font Fix.py` を、`.glyphs` ファイルと同じ場所にコピーします。
2. Font Info で、フォント（または TTF/OTF として書き出すインスタンス）に `Post-Export Command` という名前のカスタムパラメータを追加し、値を `./windows-font-fix.sh` にします。
3. 書き出します。プラグインは `.glyphs` ファイルのあるフォルダからコマンドを実行し、書き出したフォントのパスを最初の引数として渡します。Web フォント（`woff`、`woff2`）は無視されるため、Web 用の書き出しはそのままです。

スクリプトには fontTools が使える Python が必要です（`pip3 install fonttools`）。Glyphs はシェルの環境なしでコマンドを起動するため、`windows-font-fix.sh` が一般的な場所から Python を探します。ターミナルでは `python3 "Windows Font Fix.py" --help` を実行します。

## アップデートとトラブルシューティング

アップデートするには、Plugin Manager を使い、Script メニューを再読み込みします。事前にローカルでのカスタマイズを保存しておいてください。Scripts フォルダに `Plau` フォルダの手動コピーが Plugin Manager のインストールと並んで残っている場合は、スクリプトが二重に表示されないように、どちらか一方を削除してください。

- **スクリプトが表示されない:** 場所、`.py` 拡張子、1 行目を確認してください。有効なスクリプトは `#MenuTitle: …` で始まります。ファイルを移動または編集した後は、メニューを再読み込みしてください。
- **メニューに Plau → Plau と表示される:** 上記の構成になるよう、内側のフォルダの中身を 1 階層上に移動してください。
- **元になるグリフがない:** フォントにそのグリフを作成し、各マスターに使えるアウトラインを用意してから、ツールを再実行してください。
- **スクリプトが失敗する:** Glyphs のスクリプトコンソールから完全なトレースバックをコピーし、報告するときにスクリプト名、Glyphs のビルド、エラーが起きた手順を添えてください。

スクリプトのインストールとメニューヘッダーの背景については、[Glyphs のスクリプティングガイド](https://glyphsapp.com/learn/scripting-glyphs-part-3)（英語）を参照してください。

## コントリビューション

スクリプトは適切なカテゴリに置き、1 行目に `#MenuTitle:` ヘッダーを付け、Glyphs API のオブジェクトは明示的にインポートしてください。変更は Glyphs 4 でフォントのコピーを使ってテストし、複数のマスターと既存の対象グリフも確認してください。スクリプトが変更するグリフやメタデータを説明してください。エディタの自動保存ファイルは追加しないでください。

## ライセンス

[このリポジトリに含まれる GNU GPL v3 ライセンス](Plau/LICENSE)を参照してください。
