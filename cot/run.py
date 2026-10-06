"""COT週次処理のエントリポイント。

手順：
  1. 銘柄設定（cot/config/markets.csv）を読む
  2. 7データセットを順に取得し、data/cot/ の履歴CSVに上書き追記する
  3. 全履歴から指標（ネット・前週比・建玉比・COT指数）を計算する
  4. Excel と ダッシュボードHTML を site/ に出力する（GitHub Pages の公開物）
  5. 最新週にデータが無い銘柄があれば警告を出す

実行: python -m cot.run
      python -m cot.run --no-fetch   （取得せず、保存済みの履歴CSVから出力だけ作り直す）
"""

import datetime as dt
import os
import sys

import pandas as pd

from cot.aggregate import add_metrics, load_history, merge_history, save_history
from cot.build_html import write_html
from cot.export_excel import write_excel, write_history_csv
from cot.fetch import fetch_report
from cot.reports import REPORTS, VARIANT_COMBINED, VARIANT_FUTURES_ONLY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKETS_PATH = os.path.join(ROOT, "cot", "config", "markets.csv")
DATA_DIR = os.path.join(ROOT, "data", "cot")
SITE_DIR = os.path.join(ROOT, "site")
# 156週のCOT指数を直近8週分そろえて出すため、3年に約12週の余裕を足して取得する
FETCH_DAYS = 3 * 365 + 84
JST = dt.timezone(dt.timedelta(hours=9))


def load_markets():
    """銘柄設定を読み、設定ファイル上の並び順を付ける。"""
    markets = pd.read_csv(MARKETS_PATH, dtype={"code": str})
    markets["market_order"] = range(len(markets))
    return markets


def target_codes(markets, report_key):
    """レポートごとの対象銘柄コードを返す（Legacyは全銘柄）。"""
    flag = REPORTS[report_key]["market_flag"]
    if flag is None:
        return markets["code"].tolist()
    return markets.loc[markets[flag] == 1, "code"].tolist()


def update_one(report_key, variant, markets, start_date):
    """1データセット分を取得し、履歴CSVへ反映して、反映後の履歴を返す。"""
    codes = target_codes(markets, report_key)
    path = os.path.join(DATA_DIR, f"{report_key}_{variant}.csv")
    print(f"取得中: {report_key} / {variant}（{len(codes)}銘柄, {start_date}～）", flush=True)
    fetched = fetch_report(report_key, variant, REPORTS[report_key], codes, start_date)
    history = merge_history(load_history(path), fetched)
    save_history(history, path)
    print(f"  取得 {len(fetched)} 行 / 履歴 {len(history)} 行", flush=True)
    return history


def load_one(report_key, variant):
    """取得せずに、保存済みの履歴CSVを読む（--no-fetch 用）。"""
    path = os.path.join(DATA_DIR, f"{report_key}_{variant}.csv")
    history = load_history(path)
    if history is None:
        raise FileNotFoundError(f"{path} がありません。先に取得ありで実行してください")
    return history


def check_coverage(metrics, markets):
    """最新週にデータが無い（銘柄コード変更・上場廃止の可能性がある）銘柄を列挙する。"""
    warnings = []
    for report_key in REPORTS:
        for variant in REPORTS[report_key]["datasets"]:
            part = metrics[(metrics["report"] == report_key) & (metrics["variant"] == variant)]
            if part.empty:
                warnings.append(f"{report_key}/{variant}: データがありません")
                continue
            latest = part["date"].max()
            present = set(part.loc[part["date"] == latest, "code"])
            for code in target_codes(markets, report_key):
                if code not in present:
                    name = markets.loc[markets["code"] == code, "name_ja"].iloc[0]
                    warnings.append(f"{report_key}/{variant}: {name}（{code}）が最新週 {latest} にありません")
    return warnings


def write_top_page(latest_date):
    """site/index.html（データ一覧の入口ページ）を書き出す。"""
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>market-data-public</title>
<style>body{{font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;max-width:720px;margin:40px auto;padding:0 16px;line-height:1.7;color:#1f2328;background:#fff}}
@media (prefers-color-scheme:dark){{body{{color:#e6e6e6;background:#16181b}}a{{color:#7aa2ff}}}}</style></head><body>
<h1>market-data-public</h1>
<p>公開データを週次で取得・集計したダッシュボードです。</p>
<ul><li><a href="cot/">CFTC COT（建玉明細）ダッシュボード</a> — 基準日 {latest_date}</li></ul>
<p style="font-size:13px;color:#6b7280">データ出典は各ページに記載しています。</p>
</body></html>"""
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as top_file:
        top_file.write(html)


def main():
    markets = load_markets()
    today = dt.datetime.now(JST).date()
    start_date = (today - dt.timedelta(days=FETCH_DAYS)).isoformat()

    if "--no-fetch" in sys.argv:
        tff_fo = load_one("TFF", VARIANT_FUTURES_ONLY)
        tff_combined = load_one("TFF", VARIANT_COMBINED)
        disagg_fo = load_one("Disagg", VARIANT_FUTURES_ONLY)
        disagg_combined = load_one("Disagg", VARIANT_COMBINED)
        legacy_fo = load_one("Legacy", VARIANT_FUTURES_ONLY)
        legacy_combined = load_one("Legacy", VARIANT_COMBINED)
        cit_combined = load_one("CIT", VARIANT_COMBINED)
    else:
        # データセットごとに順番に取得する（7本）
        tff_fo = update_one("TFF", VARIANT_FUTURES_ONLY, markets, start_date)
        tff_combined = update_one("TFF", VARIANT_COMBINED, markets, start_date)
        disagg_fo = update_one("Disagg", VARIANT_FUTURES_ONLY, markets, start_date)
        disagg_combined = update_one("Disagg", VARIANT_COMBINED, markets, start_date)
        legacy_fo = update_one("Legacy", VARIANT_FUTURES_ONLY, markets, start_date)
        legacy_combined = update_one("Legacy", VARIANT_COMBINED, markets, start_date)
        cit_combined = update_one("CIT", VARIANT_COMBINED, markets, start_date)

    all_history = pd.concat(
        [tff_fo, tff_combined, disagg_fo, disagg_combined, legacy_fo, legacy_combined, cit_combined],
        ignore_index=True,
    )
    metrics = add_metrics(all_history)

    generated_at = dt.datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    latest_date = metrics["date"].max()
    excel_name = f"{latest_date.replace('-', '')}_COT週次集計.xlsx"
    csv_name = f"{latest_date.replace('-', '')}_COT全履歴.csv"
    cot_site_dir = os.path.join(SITE_DIR, "cot")
    os.makedirs(cot_site_dir, exist_ok=True)

    write_excel(metrics, markets, os.path.join(cot_site_dir, excel_name), generated_at)
    write_history_csv(metrics, markets, os.path.join(cot_site_dir, csv_name))
    write_html(metrics, markets, os.path.join(cot_site_dir, "index.html"), generated_at, excel_name, csv_name)
    write_top_page(latest_date)
    print(f"出力: site/cot/index.html, site/cot/{excel_name}, site/cot/{csv_name}")

    warnings = check_coverage(metrics, markets)
    for message in warnings:
        print(f"警告: {message}")
    if any("データがありません" in message for message in warnings):
        sys.exit(1)


if __name__ == "__main__":
    main()
