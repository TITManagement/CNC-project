
# Project Template

このリポジトリはテンプレートプロジェクトです。`advanced-image-editor` の構造を参考にしています。

---

## フォルダ構成

- `docs/` : ドキュメント
- `scripts/` : スクリプト
- `src/` : ソースコード

---

## クイックスタート

```sh
git clone <your-repo-url>
cd project_template
python scripts/setup_dev_environment.py
.venv/bin/python src/main_plugin.py
```

---

## テンプレートの使い方

### 新規リポジトリとして使う場合
1. GitHub上で「テンプレートとして使用」ボタンをクリックし、新しいリポジトリを作成します。
2. 作成したリポジトリをローカルにクローンします。
3. `scripts/setup_dev_environment.py` を実行して開発環境をセットアップします。

### 既存リポジトリに適用する場合
1. テンプレートリポジトリを一時的にクローンし、必要なファイルやフォルダ（`docs/`, `scripts/`, `src/`, 各種設定ファイルなど）を既存リポジトリにコピーします。
2. `.gitignore` や `pyproject.toml` など、既存のものと競合しないように調整します。
3. 必要に応じて `setup_dev_environment.py` で環境構築を行います。

---

## OSごとのパッケージインストール例

Windows:
```sh
pip install -r requirements-windows.txt
```

macOS:
```sh
pip install -r requirements-macos.txt
```

Linux:
```sh
pip install -r requirements-linux.txt
```

共通パッケージのみ:
```sh
pip install -r requirements.txt
```

---

## 注意点

- 既存リポジトリに適用する場合は、上書きや競合に注意してください。
- テンプレートの内容はプロジェクトに合わせてカスタマイズ可能です。

---

## ライセンス

MIT
