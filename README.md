# pshots

スクリーンショットを連続取得し、PNG を PDF に変換するアプリです。
実行モードは Web と CLI の 2 種類です。

## 必要環境

- Python 3.14 以上
- uv

## セットアップ

```bash
uv sync --dev
```

## クイックスタート

1. Web モードで起動

```bash
uv run pshots --web
```

2. ブラウザで `http://127.0.0.1:5000/` を開く
3. `座標を登録する` で座標を保存
4. `スクリーンショット保存` を実行
5. `PNG -> PDF 変換` を実行

## 使い方

`pshots` は `--web` か `--cli` のどちらかを必ず指定して実行します。
引数なしでは実行できません。

### 1. Web モード

基本起動:

```bash
uv run pshots --web
```

起動オプション付き:

```bash
uv run pshots --web --host 127.0.0.1 --port 5000 --debug
```

主な画面:

- `/coords` : 座標プロファイル登録
- `/screenshot` : 連続スクリーンショット取得
- `/convert` : PNG から PDF へ変換

### 2. CLI モード（座標登録）

```bash
uv run pshots --cli
```

CLI では以下を対話入力します。

- 座標設定名
- 座標取得方式（`click` / `manual`）
- `click` 選択時の待機秒数

座標の取得順は次の 3 点です。

- 左上
- 右下
- 次ページボタン

### 3. 座標データ

座標プロファイルは `json/click_coords.json` に保存されます。
既存の `click_coords.txt` がある場合は初回読込時に自動移行します。

### 4. 生成物

- スクリーンショット: `pngs/<フォルダ名>/`
- PDF: `pdfs/<フォルダ名>.pdf`
- 変換後の元画像フォルダ: `trash/<フォルダ名>/`

## 開発コマンド

フォーマットと自動修正:

```bash
just modify
```

静的検証 + テスト:

```bash
just verify
```

型チェックのみ:

```bash
uv run mypy src tests
```
