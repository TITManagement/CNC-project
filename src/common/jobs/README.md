# jobs サブパッケージ

目的
- ジョブ（描画や移動パターンなど）を表すクラス群と、YAML 定義 → 実行可能オブジェクトへの変換ロジックを提供します。

主要機能
- `Job` 抽象クラス（ジョブの共通インターフェース）
- `JobFactory`（YAML/CLI 定義を受け取り実行可能なジョブオブジェクトを返す）
- サンプル: `grid_circles` や `svg_to_moves` などの具体的ジョブ実装

使い方（例）
```
from common.jobs import JobFactory
job = JobFactory.from_config(cfg)
job.execute(driver)
```

注意
- ジョブはドライバ（`CncDriver`）に依存します。テスト時はシミュレーション用ドライバを使ってください。
- ジョブ定義のスキーマを変更する場合はドキュメントと CLI ヘルプを更新してください。
