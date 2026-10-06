"""CFTC Public Reporting API（Socrata）からCOTデータを取得する。

1データセットにつき、対象銘柄コードと開始日で絞り込んだ行をページングしながら取得し、
「1行 = 日付×銘柄×投機筋区分」の縦持ちDataFrameに変換して返す。
"""

import time

import pandas as pd
import requests

API_BASE = "https://publicreporting.cftc.gov/resource"
PAGE_SIZE = 50000
TIMEOUT_SEC = 60
MAX_RETRY = 3


def request_page(dataset_id, where, offset):
    """1ページ分をJSONで取得する。失敗時は待ち時間を伸ばしながら再試行する。"""
    url = f"{API_BASE}/{dataset_id}.json"
    params = {
        "$where": where,
        "$order": "report_date_as_yyyy_mm_dd, cftc_contract_market_code",
        "$limit": PAGE_SIZE,
        "$offset": offset,
    }
    last_error = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT_SEC)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            last_error = error
            time.sleep(5 * attempt)
    raise RuntimeError(f"{dataset_id} の取得に失敗しました: {last_error}")


def fetch_raw(dataset_id, codes, start_date):
    """対象銘柄・開始日以降の全行を取得してリストで返す。"""
    code_list = ",".join(f"'{code}'" for code in codes)
    where = (
        f"cftc_contract_market_code in ({code_list}) "
        f"AND report_date_as_yyyy_mm_dd >= '{start_date}'"
    )
    rows = []
    offset = 0
    while True:
        page = request_page(dataset_id, where, offset)
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def to_number(value):
    """API値（文字列）を数値に変換する。欠損はNoneのまま。"""
    if value is None or value == "":
        return None
    return float(value)


def normalize(rows, report_key, variant, categories):
    """APIの横持ち行を、投機筋区分ごとの縦持ち行に展開する。"""
    records = []
    for row in rows:
        report_date = row["report_date_as_yyyy_mm_dd"][:10]
        code = row["cftc_contract_market_code"]
        market_name = row.get("market_and_exchange_names", "")
        open_interest = to_number(row.get("open_interest_all"))
        for category, (long_field, short_field) in categories.items():
            records.append({
                "report": report_key,
                "variant": variant,
                "date": report_date,
                "code": code,
                "cftc_name": market_name,
                "category": category,
                "long": to_number(row.get(long_field)),
                "short": to_number(row.get(short_field)),
                "open_interest": open_interest,
            })
    return pd.DataFrame.from_records(records)


def fetch_report(report_key, variant, report_def, codes, start_date):
    """1レポート×1データ種類分を取得し、縦持ちDataFrameで返す。"""
    dataset_id = report_def["datasets"][variant]
    rows = fetch_raw(dataset_id, codes, start_date)
    frame = normalize(rows, report_key, variant, report_def["categories"])
    return frame
