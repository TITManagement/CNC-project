# 検証ガイド


このプロジェクトの検証手順やテスト方針を記載します。

## シミュレーション動作確認

1. 仮想環境を有効化・依存インストール
   ```bash
   python3 -m venv .venv_CNC
   source .venv_CNC/bin/activate
   pip install --no-build-isolation -e .
   ```
2. GUI ランチャーで実行（推奨）
   ```bash
   xy-runner-gui
   ```
   - ドライバに「SIM」を選択
   - YAML に `examples/example_xy/SIM_svg_sample.yaml` を選択
   - SVG/G-code を任意に指定
   - 実行し、matplotlib で軌跡が表示されることを確認
3. 3D ランナーも確認（CLI）
   ```bash
   python -m xyz_runner.xyz_runner --config examples/example_xyz/grid_spheres.yaml --show
   ```

## 実機動作確認

1. 実機（中央精機XYステージ）をPCに接続
2. 実機用YAML（例: examples/example_xy/REAL_chuo_svg.yaml）を選択（GUI または CLI）
3. ポート・ボーレート等の設定値を確認
4. 実行コマンド例
	```bash
	python -m xy_runner.xy_runner --config examples/example_xy/REAL_chuo_svg.yaml
	```
5. 実機が指定通り動作することを確認

## SVGパス処理検証

1. Inkscape, Illustrator, PowerPoint等でSVGファイルを作成
2. サンプルYAMLでSVGファイルを指定し、シミュレーションまたは実機で実行
3. SVGのパスが正しくCNC動作に変換されることを確認

## その他

- テストコード（pytest）による自動検証も推奨
- 依存パッケージのバージョン違いによる動作差異に注意
