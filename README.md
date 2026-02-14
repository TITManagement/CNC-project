# CNC XY/XYZ Runner（クロスプラットフォーム対応）

<!-- README_LEVEL: L1 -->

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

**SVG・G-code・STEPファイル対応CNCコントローラ：Windows・Mac・Linuxで動作！**

[特徴](#特徴) ・ [インストール](#インストール) ・ [使い方](#使い方) ・ [構成](#構成) ・ [ライセンス](#ライセンス)

</div>

## 概要

汎用ドローソフト（Inkscape, Illustrator, PowerPoint等）で作成したSVG図形、G-codeファイル、STEPファイルをCNC制御で実行するクロスプラットフォーム対応Pythonツールです。

### サポートプラットフォーム
- 🪟 **Windows** (Windows 10/11)
- 🍎 **macOS** (macOS 10.15+)
- 🐧 **Linux** (Ubuntu 24.04, その他ディストリビューション)

### 主な機能

- **2D制御 (xy_runner)**: SVG（Inkscape, Illustrator, PowerPoint等） → CNC制御
- **3D制御 (xyz_runner)**: G-codeファイル・STEPファイル → 3D CNC制御
- GUIによる直感的なファイル選択
- matplotlibによる軌跡シミュレーション（2D/3D）
- 中央精機 QT-BMM2 / OptoSigma GSC-02 ステージ対応（シリアル通信）
- クロスプラットフォーム自動セットアップ

## 特徴

### 2D制御 (xy_runner)
- ✅ SVG図形（Inkscape, Illustrator, PowerPoint等）をそのままCNCで描画
- ✅ SVGファイルの対話的選択
- ✅ 2D軌跡のリアルタイムシミュレーション

### 3D制御 (xyz_runner)
- ✅ G-codeファイル・STEPファイル直接実行
- ✅ 3D軌跡アニメーション表示
- ✅ ファイル選択のみのシンプルUI

### 共通機能
- ✅ クロスプラットフォーム対応（Windows・macOS・Linux）
- ✅ 実機制御（中央精機 QT-BMM2 / OptoSigma GSC-02 ステージ）
- ✅ プラットフォーム別自動セットアップ
- ✅ 安全リミット設定
- ✅ 拡張性の高いドライバ設計

## インストール

### 🛠️ インストール手順（推奨）

```bash
# リポジトリ取得
git clone https://github.com/TITManagement/CNC.git
cd CNC

# 仮想環境作成
python3 -m venv .venv_CNC
source .venv_CNC/bin/activate

# 依存ライブラリインストール（開発モード）
python -m pip install --no-build-isolation -e .
python -m pip check
```

Windows の場合は `.\.venv_CNC\Scripts\activate` を使用してください。
`python -m pip -V` で `.venv_CNC` 配下の pip が使われていることを確認してください。

> **依存更新ルール（再発防止）**  
> `cnc-drivers` を更新した場合は version を上げ、`lab_automation_libs/internal-PyPI/dist/` の wheel を更新してください。同一バージョン差し替えはキャッシュ衝突の原因になります。

## 使い方

### 1. 描画ソフトで図形作成 → SVG保存
Inkscape, Illustrator, PowerPointなど任意のドローソフトで図形（テキスト不可）を作成し、SVG形式で保存してください。
（PowerPointの場合は「ファイル → エクスポート → SVG形式」で保存、「現在のスライド」を選択）

### 2. GUI で実行（推奨）
```bash
xy-runner-gui   # venv を有効化した状態で実行
```
- 1つのウィンドウで「ドライバ（SIM/REAL）」「YAML設定」「SVG/G-code」を指定して実行できます。

### 3. CLI で実行（従来スタイル）
```bash
python -m xy_runner.xy_runner --config drawing_data/xy/SIM_svg_sample.yaml
# 3D ランナー（任意）
python -m xyz_runner.xyz_runner --config drawing_data/xyz/single_sphere_step_sim.yaml
```
サンプルYAML（XYZ）
- `SIM_basic_gcode.yaml`（単純なG-code）
- `cube_gcode_sim_standard.yaml`（立方体G-code）
- `spiral_gcode_sim_standard.yaml`（螺旋G-code）
- `single_sphere_step_sim.yaml`（単一STEP球）
- `multi_spheres_step_sim.yaml`（複数STEP球）
- `visual_demo_sim_fast.yaml`（高速アニメーションデモ）

## 構成

```
CNC_project/
├── src/                    # ソースコード
│   ├── common/             # 共有ロジック
│   ├── xy_runner/          # 2D ランナー
│   │   └── xy_runner.py    # メインスクリプト
│   └── xyz_runner/         # 3D ランナー
│       └── xyz_runner.py   # メインスクリプト
├── drawing_data/           # 設定・サンプル
│   ├── xy/                 # XY 用 YAML / SVG
│   └── xyz/                # XYZ 用 YAML / G-code / STEP
├── docs/                   # ドキュメント
│   ├── user-guide.md       # ユーザーガイド
│   └── developer-guide.md  # 開発者ガイド
├── pyproject.toml          # パッケージ設定
└── README.md               # このファイル
```
driver: sim                 # シミュレーション or 'chuo'で実機
svg_file: select            # GUIでSVGファイル選択

motion_params:
  cut_speed: 100            # 描画速度 (mm/min)
  lift_height: 5            # Z軸リフト高さ

```yaml
# drawing_data/xy/SIM_svg_sample.yaml
driver: sim
svg_file: select            # GUIでSVGファイル選択
visual:
  animate: true
  title: "CNC XY Simulation"

# driver: chuo を用いる場合の例（XY ランナー）
driver: chuo
port: /dev/tty.usbserial-XXXX
baud: 9600
mm_per_pulse: 0.0005        # 1パルスあたりのmm
qt_enable_response: true    # 必要に応じてレスポンスを有効化
driver_settings:
  rapid_speed: 3000         # 早送り速度 (mm/min)
  cut_speed: 1200           # 描画速度 (mm/min)
  accel: 100                # 加減速パラメータ

# driver: chuo を用いる場合の例（XYZ ランナー）
driver: chuo
port: /dev/tty.usbserial-XXXX
baud: 9600
mm_per_pulse: 0.0005
qt_enable_response: true
driver_settings:
  rapid_speed: 5000
  cut_speed: 1500
  accel: 150

# driver: gsc02 を用いる場合の例（XY ランナー）
driver: gsc02
port: /dev/tty.usbserial-GSC02
baud: 9600
timeout: 1.5
write_timeout: 1.5
mm_per_pulse: 0.001
```


## 実機対応

### 中央精機XYステージ
```
- PySerialによるシリアル通信
- COMポート・ボーレート設定可能
- 位置フィードバック
- 安全リミット管理
```

### OptoSigma GSC-02
```
- RS-232C (RTS/CTS) ベースの ASCII プロトコル
- 既定速度テーブルの設定（Dコマンド）
- 原点復帰方向の切り替え
- Busy/Ready 応答による状態監視
```

### シミュレーションモード
- 実機不要
- matplotlibで軌跡表示
- アニメーション・プレビュー

## ドキュメント

- 📖 [ユーザーガイド](docs/user-guide.md)
- 🔧 [開発者ガイド](docs/developer-guide.md)
- 📚 [総合ドキュメント](docs/index.md)
- 🧪 [検証ガイド](VERIFICATION_GUIDE.md)

## コントリビュート

開発・改善への参加歓迎！詳細は[開発者ガイド](docs/developer-guide.md)参照。

### 開発フロー
1. リポジトリをフォーク
2. フィーチャーブランチ作成
3. テスト付きで修正
4. コード品質チェック（black, mypy等）
5. プルリクエスト提出

## 主な用途

- 試作・研究用途のパターン生成
- 教育・CNC原理学習
- 実験自動化
- 製造現場での図形→動作変換

## 技術情報

- Python 3.8以上対応
- 主要依存：PyYAML, matplotlib, PySerial, svgpathtools
- モジュール設計：ドライバ拡張可能
- テスト：pytest
- コード品質：black, mypy

## ライセンス

MITライセンス（詳細は[LICENSE](LICENSE)参照）

## サポート

- 📧 info@titmanagement.com
- 🐛 [GitHub Issues](https://github.com/TITManagement/CNC/issues)
- 📖 [総合ドキュメント](docs/index.md)

---

<div align="center">
<strong>SVG図形（Inkscape, Illustrator, PowerPoint等）をCNCで自在に動かす！教育・研究・製造現場で活用できます。</strong>
</div>
