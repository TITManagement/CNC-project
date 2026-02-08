# ユーザーガイド

## インストール

### 手動セットアップ
1. 仮想環境の作成:
   ```bash
   python3 -m venv .venv_CNC
   source .venv_CNC/bin/activate
   ```

2. 依存ライブラリのインストール:
   ```bash
   pip install --no-build-isolation -e .
   ```

## 基本的な使い方

### SVGジョブの実行（GUI 推奨）
1. SVG/G-code を準備する（PowerPoint からの SVG でも可）
2. GUI ランチャーを起動する:
   ```bash
   xy-runner-gui   # venv 有効化後に実行
   ```
3. ウィンドウ上で
   - ドライバ（SIM/REAL）を選択
   - YAML 設定を選択
   - 必要に応じて SVG/G-code を選択
   - 「実行」でスタート

### CLI での実行例
```bash
python -m xy_runner.xy_runner --config examples/example_xy/SIM_svg_sample.yaml
# 3D ランナーの例
python -m xyz_runner.xyz_runner --config examples/example_xyz/SIM_step_sphere.yaml
```

### 設定ファイル
- `examples/example_xy/SIM_svg_sample.yaml` - SVGファイル選択ダイアログ付きの設定
- `examples/example_xy/SIM_svg_select.yaml` - 実行時にSVGを選択する設定
- `examples/example_xy/SIM_svg_grid_circles.yaml` - グリッドパターン生成
- `examples/example_xy/REAL_chuo_svg.yaml` - 実機（QT-BMM2）制御用設定
- `examples/example_xy/REAL_gsc02_svg.yaml` - 実機（GSC-02）制御用設定
- XYZ用サンプル: `SIM_basic_gcode.yaml` / `SIM_gcode_cube.yaml` / `SIM_gcode_spiral.yaml` / `SIM_step_sphere.yaml` / `SIM_step_multi_spheres.yaml` / `SIM_visual_fast.yaml`
- `driver_settings` セクションで `rapid_speed` / `cut_speed` / `accel` を設定すると、中央精機ステージの速度・加速度が適用されます。

`driver: chuo` を使用する場合は、以下のパラメータを必ず指定してください:

```yaml
driver: chuo
port: /dev/tty.usbserial-XXXX
baud: 9600
mm_per_pulse: 0.0005        # 1 パルスあたりの mm
qt_enable_response: true    # コントローラのレスポンスを有効化
driver_settings:
  rapid_speed: 3000
  cut_speed: 1200
  accel: 100

# XYZ Runner で実機を使う場合の例
driver: chuo
port: /dev/tty.usbserial-XXXX
baud: 9600
mm_per_pulse: 0.0005
qt_enable_response: true
driver_settings:
  rapid_speed: 5000
  cut_speed: 1500
  accel: 150

# GSC-02 を使う場合の例
driver: gsc02
port: /dev/tty.usbserial-GSC02
baud: 9600
mm_per_pulse: 0.001
gsc_enable_response: true    # レスポンス読み取りを有効化
driver_settings:
  rapid_speed: 3000
  cut_speed: 1200
  accel: 100

```

## PowerPoint → SVG ワークフロー

1. **PowerPointでスライド作成**
   - 図形ツールのみ使用（テキスト不可）
   - シンプルなデザイン推奨
   - コントラストの高い色を使う

2. **SVGとしてエクスポート**
   - ファイル → エクスポート → ファイル形式変更 → SVG
   - 「現在のスライド」を選択

3. **CNC XY Runnerで処理**
   - SVG設定ファイルを使う
   - 実行時にSVGファイルを選択

## モーションパラメータ

YAML設定で以下を調整できます:

```yaml
motion_params:
  rapid_speed: 1000    # 高速移動速度
  cut_speed: 100       # 描画速度
  lift_height: 5       # Z軸リフト高さ
```

## 安全設定

機械保護のためのリミット設定:

```yaml
safety:
  max_x: 100
  max_y: 100
  max_speed: 2000
  enable_limits: true
```

## トラブルシューティング

### よくある問題

1. **「No tracks」エラー**
   - SVGにパス要素が含まれているか確認
   - PowerPointで図形のみを使い再エクスポート

2. **ファイル選択ダイアログが表示されない**
   - tkinterがインストールされているか確認
   - デスクトップ環境がGUI対応か確認

3. **シリアル通信が失敗する**
   - COMポート設定を確認
   - ハードウェア接続を確認
   - まずはシミュレーションモードでテスト

### デバッグモード

デバッグ出力を有効化:
```yaml
debug: true
```

表示される内容:
- SVG要素の解析結果
- 生成された動作コマンド
- シリアル通信の詳細
