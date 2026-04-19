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

`pshots` は `--web` か `--cli` のどちらかを必ず指定して実行します。
引数なし実行はエラーになります。

1. 座標を登録する（CLI モード）

```bash
uv run pshots --cli
```

`--cli` では追加引数を受け取らず、以下を対話式で決定します。

- 座標設定名
- 座標取得方式（click/manual）
- click 時の待機秒数

取得順:

- 左上
- 右下
- 次ページボタン

保存先は `click_coords.json` です。

2. アプリを起動する（Web モード）

```bash
uv run pshots --web
```

必要なら起動オプションを指定します。

```bash
uv run pshots --web --host 127.0.0.1 --port 5000 --debug
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
