"""COTデータの保存（履歴への上書き追記）と指標計算。

指標：
- net          : ロング - ショート
- net_change   : 前週からのネット変化
- net_oi_pct   : ネット ÷ 総建玉 × 100
- cot_index    : 過去156週（約3年）のネットの最小～最大レンジ内での現在位置（0～100）
"""

import os

import pandas as pd

KEY_COLUMNS = ["report", "variant", "date", "code", "category"]
SERIES_COLUMNS = ["report", "variant", "code", "category"]
COT_INDEX_WINDOW = 156
# 上場から日が浅い銘柄でも指数を出すため、最低52週あれば計算する
# （156週そろうまで空欄にする案は、新しい銘柄が長期間表示されなくなるため不採用）
COT_INDEX_MIN_WEEKS = 52


def merge_history(existing, fetched):
    """既存の履歴に今回取得分を重ね、同じキーは今回取得分で上書きする。

    CFTCは過去週を訂正することがあるため、取得期間分は毎回取り直して置き換える。
    （差分の最新週だけを追記する方式は、訂正を取り込めないため不採用）
    """
    if existing is None or existing.empty:
        merged = fetched.copy()
    else:
        merged = pd.concat([existing, fetched], ignore_index=True)
        merged = merged.drop_duplicates(subset=KEY_COLUMNS, keep="last")
    merged = merged.sort_values(KEY_COLUMNS).reset_index(drop=True)
    return merged


def load_history(path):
    """保存済みの履歴CSVを読む。無ければNoneを返す。"""
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, dtype={"code": str})


def save_history(frame, path):
    """履歴CSVを保存する。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    frame.to_csv(path, index=False)


def cot_index(net_series):
    """ネットの時系列から、各週のCOTインデックス（0～100）を計算する。"""
    rolling_min = net_series.rolling(COT_INDEX_WINDOW, min_periods=COT_INDEX_MIN_WEEKS).min()
    rolling_max = net_series.rolling(COT_INDEX_WINDOW, min_periods=COT_INDEX_MIN_WEEKS).max()
    width = rolling_max - rolling_min
    index = (net_series - rolling_min) / width * 100
    # レンジ幅0（期間中ずっと同じ値）のときは中立の50とする
    index = index.where(width != 0, 50.0)
    return index.round(1)


def add_metrics(frame):
    """銘柄×区分ごとの時系列に、ネット・前週比・建玉比・COTインデックスを付ける。"""
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"])
    result = result.sort_values(SERIES_COLUMNS + ["date"]).reset_index(drop=True)

    result["net"] = result["long"] - result["short"]
    grouped = result.groupby(SERIES_COLUMNS, sort=False)["net"]
    result["net_change"] = grouped.diff()
    result["net_oi_pct"] = (result["net"] / result["open_interest"] * 100).round(2)
    result["cot_index"] = grouped.transform(cot_index)

    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    return result


def latest_rows(metrics):
    """データ種類×レポートごとに、最新日付の行だけを取り出す。"""
    latest_date = metrics.groupby(["report", "variant"])["date"].transform("max")
    return metrics[metrics["date"] == latest_date].reset_index(drop=True)
