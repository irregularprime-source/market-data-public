# market-data-public

再公開が認められている公的データを週次で取得・集計し、GitHub Pages でダッシュボードとして公開するリポジトリです。

## 収録データ

### CFTC Commitments of Traders（COT）

- 出典：U.S. Commodity Futures Trading Commission (CFTC), Commitments of Traders
  — [CFTC Public Reporting](https://publicreporting.cftc.gov/stories/s/r4w3-av2u)
- CFTCサイト上の政府情報はパブリックドメインです（[CFTC Web Policy](https://www.cftc.gov/webpolicy/index.htm)）。本リポジトリはCFTCの公表データを独自に集計したもので、CFTCが作成・承認したものではありません。
- 対象：Legacy / Disaggregated / TFF（各「先物のみ」「先物+オプション」）、Supplemental CIT（先物+オプションのみ）
- 銘柄：`cot/config/markets.csv`（行を追加・削除すれば対象が変わります）

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
