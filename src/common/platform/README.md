# platform サブパッケージ

目的
- OS や環境依存の処理を抽象化して提供するレイヤーです。ファイルダイアログ、パス操作、環境依存ユーティリティなどをここに集約します。

主要モジュール
- `adapter.py` — `EnvironmentAdapter` の実装。プラットフォーム固有の差分を注入するために使用されます。

使い方
```
from common.platform.adapter import EnvironmentAdapter
adapter = EnvironmentAdapter()
adapter.open_file_dialog(...)
```

注意
- GUI やファイルダイアログなどはテスト実行環境で利用できない場合が多いため、ユニットテスト時はモックを使って差し替えてください。
