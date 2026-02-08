# 開発者ガイド

## このガイドの目的

開発者がコードを読む・変更する際に迷わないよう、ディレクトリ構成や処理フローをまとめたガイドです。実機ドライバの拡張ポイントと設定の考え方を中心に解説しています。

## プロジェクト構成の全体像

```
CNC/
├── src/
│   ├── common/            # 共通ロジック・ドライバ
│   │   ├── drivers/
│   │   │   ├── actual_machine_control.py  # 実機ドライバを生成するファクトリ
│   │   │   ├── chuo_stage_driver.py       # QT-BMM2 用ステージドライバ
│   │   │   ├── gsc02_stage_driver.py      # GSC-02 用ステージドライバ
│   │   │   └── *_controller.py            # シリアルプロトコルごとの低レベルラッパ
│   │   └── ...                            # gcode, jobs, runtime などの共通モジュール
│   ├── xy_runner/         # 2D ランナー（CLI エントリ）
│   └── xyz_runner/        # 3D ランナー（CLI エントリ）
├── examples/              # YAML 設定とサンプルデータ
├── docs/                  # ドキュメント
└── pyproject.toml         # パッケージ設定
```

## ランナーの実行フロー

1. `python -m xy_runner.xy_runner` を実行すると `XYRunnerApp.run()` が YAML を読み込みます。
2. `_create_driver(cfg)` が設定ファイルの `driver` を確認します。
   - `driver == "sim"` なら `SimDriver` を生成。
   - それ以外は `common.drivers.create_actual_driver(driver_name, cfg)` を呼びます。
3. `create_actual_driver` は `actual_machine_control.py` 内で以下を実施します
   （直接 `create_chuo_driver()` や `create_gsc02_driver()` を呼び出すことも可能です）。
   - `_parse_mm_per_pulse()` で `mm_per_pulse` を整理。
   - ドライバ名に応じて `_init_chuo_driver()` または `_init_gsc02_driver()` を実行。
   - 各 `_init_*` で `_build_*_kwargs()` を呼び、シリアル設定をまとめた辞書を作成。
   - `ChuoDriver` / `GSC02Driver` を初期化し、ポートオープンに失敗した場合は例外をラップして通知。
4. 生成された `CncDriver` と `GCodeWrapper` を使い、`JobDispatcher` が YAML に記載されたジョブを順番に実行します。

`xyz_runner` でも同じ考え方で、`XYZRunnerApp` から `create_actual_driver()` を呼ぶ構造になっています。

## YAML 設定の使い分け

共通項目は以下のとおりです。

```yaml
# 共通設定例
driver: sim
motion_params:
  rapid_speed: 1000
  cut_speed: 100
svg_file: examples/drawing.svg
```

### 中央精機（QT-BMM2）を利用する場合

```yaml
driver: chuo
port: /dev/tty.usbserial-XXXX
baud: 9600
mm_per_pulse: 0.0005
qt_enable_response: true
# 任意: 送りや加速度のデフォルト
driver_settings:
  rapid_speed: 3000
  cut_speed: 1200
  accel: 100
# 任意: タイムアウトなど
timeout: 1.5
write_timeout: 1.5
```

XYZ ランナーで使用する場合も同じ設定を流用できます。必要であれば `driver_settings` を XYZ 用に調整してください（例: rapid_speed を 5000 にするなど）。

### OptoSigma GSC-02 を利用する場合

```yaml
driver: gsc02
port: /dev/tty.usbserial-GSC02
baud: 9600
mm_per_pulse: 0.001
gsc_enable_response: true
driver_settings:
  rapid_speed: 3000
  cut_speed: 1200
  accel: 100
# 任意: タイムアウトなど
timeout: 1.5
write_timeout: 1.5
# 任意: home_dirs や encoding など
# gsc_home_dirs: '+-'
# encoding: ascii
```

## 開発環境のセットアップ

1. リポジトリを取得し、仮想環境を作成します。
   ```bash
   git clone https://github.com/TITManagement/CNC.git
   cd CNC
   python3 -m venv .venv_CNC
   source .venv_CNC/bin/activate
   pip install --no-build-isolation -e .
   ```
2. コミット前に自動でコード整形や静的チェックを走らせたい場合は `pre-commit` を設定します。
   ```bash
   pre-commit install
   ```
   ※ 開発チームで共通の lint ルールを使う場合に便利です。

## コードスタイルとテスト

- フォーマッタ: `black src/ --line-length 100`  # Python コード整形（簡単な lint エラーなら自動修正可能）
- 型チェック: `mypy src/`
- 単体テスト: `pytest tests/`

これらは CI と同じルールでコードを検証したいときに利用します。

## 新しい実機ドライバを追加するには

1. 必要に応じてシリアルプロトコル用のラッパ（`*_controller.py`）を実装する。
2. ステージ制御クラス（`*_stage_driver.py`）で `CncDriver` を継承し、`move_abs` などのインターフェースを実装する。
3. `actual_machine_control.py` に `_init_*` / `_build_*_kwargs` を追加し、`create_actual_driver` に分岐を増やす。
4. YAML サンプルを `examples/` に追加し、ユーザー／開発者ガイドへ説明を追記する。

この流れに従うことで、新しい実機ドライバを追加しても CLI 側のコード変更は最小限で済みます。
