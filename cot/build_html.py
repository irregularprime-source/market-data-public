"""ダッシュボードHTMLを生成する。

集計結果をJSONにしてテンプレート（cot/templates/dashboard.html）へ埋め込み、
外部ファイルなしで開ける1枚のHTMLを作る。

JSONの形：
  dates   : 全期間の基準日（昇順）
  markets : {code: {name, asset}}
  reports : {report: {label, categories: [[key, label]], default, variants: [...]}}
  series  : {"variant|report|code": {oi: [...], long: {cat: 値}, short: {cat: 値},
                                     net: {cat: [...]}, idx: {cat: [...]}}}
  配列は dates と同じ長さで、データの無い週は null。
"""

import json
import math
import os

from cot.reports import REPORTS, VARIANT_LABELS

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
PLACEHOLDER = "/*__COT_DATA__*/null"


def clean(value, digits=None):
    """NaNをnullに、必要なら丸めてJSON用の値にする。"""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if digits is None:
        return int(round(value))
    return round(float(value), digits)


def build_payload(metrics, markets, generated_at, excel_file_name, csv_file_name):
    """テンプレートに埋め込むデータ（dict）を作る。"""
    dates = sorted(metrics["date"].unique().tolist())
    date_position = {date: position for position, date in enumerate(dates)}

    market_info = {}
    for row in markets.itertuples():
        market_info[row.code] = {"name": row.name_ja, "asset": row.asset_class, "order": row.market_order}

    report_info = {}
    for report_key, report_def in REPORTS.items():
        report_info[report_key] = {
            "label": report_def["label"],
            "categories": [[key, label] for key, label in report_def["category_labels"].items()],
            "default": report_def["default_category"],
            "variants": list(report_def["datasets"].keys()),
        }

    series = {}
    for (variant, report_key, code, category), group in metrics.groupby(["variant", "report", "code", "category"]):
        series_key = f"{variant}|{report_key}|{code}"
        if series_key not in series:
            series[series_key] = {
                "oi": [None] * len(dates),
                "long": {}, "short": {}, "net": {}, "idx": {},
            }
        entry = series[series_key]
        net_values = [None] * len(dates)
        index_values = [None] * len(dates)
        for row in group.itertuples():
            position = date_position[row.date]
            net_values[position] = clean(row.net)
            index_values[position] = clean(row.cot_index, 1)
            entry["oi"][position] = clean(row.open_interest)
        last_row = group.sort_values("date").iloc[-1]
        entry["long"][category] = clean(last_row["long"])
        entry["short"][category] = clean(last_row["short"])
        entry["net"][category] = net_values
        entry["idx"][category] = index_values

    payload = {
        "generated_at": generated_at,
        "latest": dates[-1],
        "excel": excel_file_name,
        "csv": csv_file_name,
        "variant_labels": VARIANT_LABELS,
        "dates": dates,
        "markets": market_info,
        "reports": report_info,
        "series": series,
    }
    return payload


def write_html(metrics, markets, path, generated_at, excel_file_name, csv_file_name):
    """HTMLファイルを書き出す。"""
    payload = build_payload(metrics, markets, generated_at, excel_file_name, csv_file_name)
    with open(TEMPLATE_PATH, encoding="utf-8") as template_file:
        template = template_file.read()
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # JSON内の "</" がscriptタグを閉じないようにエスケープする
    data_json = data_json.replace("</", "<\\/")
    html = template.replace(PLACEHOLDER, data_json)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as html_file:
        html_file.write(html)
