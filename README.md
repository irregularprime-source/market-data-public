# market-data-public

再公開が認められている公的データを自動で取得・集計し、GitHub Pages でダッシュボードとして公開するリポジトリです。

- 公開ページ：https://irregularprime-source.github.io/market-data-public/
- CFTC COT ダッシュボード：https://irregularprime-source.github.io/market-data-public/cot/

## 収録データ

### CFTC Commitments of Traders（COT）

- 出典：U.S. Commodity Futures Trading Commission (CFTC), Commitments of Traders
  — [CFTC Public Reporting](https://publicreporting.cftc.gov/stories/s/r4w3-av2u)
- CFTCサイト上の政府情報はパブリックドメインです（[CFTC Web Policy](https://www.cftc.gov/webpolicy/index.htm)）。本リポジトリはCFTCの公表データを独自に集計したもので、CFTCが作成・承認したものではありません。
- 対象：Legacy / Disaggregated / TFF（各「先物のみ」「先物+オプション」）、Supplemental CIT（先物+オプションのみ）
- 銘柄：`cot/config/markets.csv`（行を追加・削除すれば対象が変わります。列の意味は [運用手順](docs/運用手順.md#4-銘柄の追加削除)）
- 更新：CFTC の公表（通常は毎週金曜 15:30 米東部時間＝土曜早朝 JST、火曜時点の建玉）を、公表翌朝に反映します

## 仕組み

| 項目 | 内容 |
|---|---|
| 実行 | GitHub Actions（`.github/workflows/cot-weekly.yml`）毎日 6:47・7:47 JST ＋ 手動実行（CFTC公表は通常 土曜早朝 JST） |
| 取得 | 直近約3年分を毎回取り直し、`data/cot/*.csv` の履歴に上書き追記（CFTCの過去週訂正を反映するため） |
| 集計 | ネット、前週比、建玉比、COT指数（過去156週レンジ内の位置） |
| 出力 | `site/cot/index.html`（ダッシュボード）、`site/cot/YYYYMMDD_COT週次集計.xlsx`（履歴は投機筋区分のみ）、`site/cot/YYYYMMDD_COT全履歴.csv`（全区分） → GitHub Pages |

## ローカル実行（任意）

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python -m cot.run              # 取得から出力まで
python -m cot.run --no-fetch   # 保存済みデータから出力だけ作り直す
```

## 運用

日々の確認方法、銘柄の追加、手動実行、トラブル時の対処、初期設定は [docs/運用手順.md](docs/運用手順.md) にまとめています。

## 免責

本リポジトリおよびダッシュボードの集計・表示は情報提供のみを目的としたもので、投資助言や特定の売買の推奨ではありません。内容の正確性・完全性は保証しません。データの最新・正式な値は CFTC の公表資料を確認してください。

## ライセンス

- コード・集計処理：[0BSD](LICENSE)（Zero-Clause BSD。著作権表示なしで、誰でも自由に利用・改変・再配布できます）
- データ：CFTC の公表データ（パブリックドメイン）
