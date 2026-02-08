# runtime サブパッケージ

目的
- ランタイム時に必要なユーティリティや責務分割されたコンポーネント（設定ロード、ジョブディスパッチ、可視化コントローラなど）を収めます。

主要モジュール
- `config.py` — 設定読み込み / バリデーション
- `jobs.py` — ジョブのスケジューリング / ディスパッチ
- `visuals.py` — 可視化（シミュレーション描画）周りのヘルパ

使い方（概念）
```
from common.runtime.config import ConfigLoader
cfg = ConfigLoader.load(path)
dispatcher = JobDispatcher(cfg)
dispatcher.run()
```

注意
- ランナーの `main()` はこれらのコンポーネントを薄く結合し、依存注入でテストしやすくする設計を目指しています。
