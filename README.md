# pshots

スクリーンショットを連続取得し、PNG を PDF に変換する Flask アプリです。

## 必要環境

- Python 3.14
- uv

## セットアップ

```bash
uv sync --dev
```

## 使い方

1. 座標を登録する

```bash
uv run python -m pshots.cli.create_box --name default
```

既定では `auto` モードで次の順に 3 点を取得します。

- まず click 方式（左/右どちらのクリックでも可）
- 失敗時は manual 方式へ自動フォールバック

取得順:

- 左上
- 右下
- 次ページボタン

必要に応じて方式を明示できます。

```bash
# click のみ（タイムアウト時は終了）
uv run python -m pshots.cli.create_box --name default --mode click --timeout 20

# 手入力のみ（OS 非依存）
uv run python -m pshots.cli.create_box --name default --mode manual
```

保存先は `click_coords.json` です。

2. アプリを起動する

```bash
uv run pshots
```

ブラウザで以下を開きます。

- http://127.0.0.1:5000/

3. Web 画面で実行する

- `スクリーンショット保存` で連続キャプチャ
- `PNG -> PDF 変換` で PDF 生成

## 開発コマンド

- フォーマットと自動修正

```bash
just modify
```

- 静的検証

```bash
just verify
```

注: 現在テストケースが未作成のため、`just verify` の `pytest` ステップは `collected 0 items` で終了コード 5 になります。
