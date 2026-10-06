"""集計ロジックの検証。

検証すること：
- ネット・前週比・建玉比が定義どおりに計算されること
- COT指数が過去レンジ内の位置（0～100）になること、レンジ幅0なら50になること
- 52週未満の期間ではCOT指数が空欄になること
- 履歴の重ね合わせで、同じキーは新しい取得分で上書きされること
- 銘柄・区分が異なる系列どうしが混ざらないこと
"""

import pandas as pd

from cot.aggregate import add_metrics, cot_index, merge_history
from cot.fetch import normalize


def make_frame(nets, code="000001", category="lev_money", open_interest=1000):
    dates = pd.date_range("2024-01-02", periods=len(nets), freq="7D").strftime("%Y-%m-%d")
    return pd.DataFrame({
        "report": "TFF", "variant": "fo", "date": dates, "code": code, "cftc_name": "TEST",
        "category": category, "long": [max(n, 0) + 100 for n in nets],
        "short": [max(-n, 0) + 100 for n in nets], "open_interest": open_interest,
    })


def test_net_change_and_oi_ratio_follow_definitions():
    result = add_metrics(make_frame([10, 30, -20]))
    assert result["net"].tolist() == [10, 30, -20]
    assert pd.isna(result["net_change"].iloc[0])
    assert result["net_change"].tolist()[1:] == [20, -50]
    assert result["net_oi_pct"].tolist() == [1.0, 3.0, -2.0]


def test_cot_index_is_position_within_range():
    series = pd.Series([0.0] * 51 + [100.0, 50.0])
    index = cot_index(series)
    assert index.iloc[51] == 100.0  # 期間中の最大値
    assert index.iloc[52] == 50.0   # 最小0～最大100のちょうど中間


def test_cot_index_is_neutral_when_range_is_flat():
    index = cot_index(pd.Series([5.0] * 60))
    assert index.iloc[-1] == 50.0


def test_cot_index_is_blank_before_52_weeks():
    index = cot_index(pd.Series(range(60), dtype=float))
    assert index.iloc[:51].isna().all()
    assert not pd.isna(index.iloc[51])


def test_cot_index_only_looks_back_156_weeks():
    # 古い極端値（-1000）が156週より前に外れると、レンジから除外されること
    values = [-1000.0] + [0.0] * 155 + [10.0, 5.0]
    index = cot_index(pd.Series(values))
    assert index.iloc[-1] == 50.0


def test_merge_history_overwrites_same_key_with_new_fetch():
    old = make_frame([10, 20])
    new = make_frame([10, 25])  # 2週目がCFTCにより訂正された想定
    merged = merge_history(old, new)
    assert len(merged) == 2
    assert (merged["long"] - merged["short"]).tolist() == [10, 25]


def test_merge_history_keeps_weeks_outside_new_window():
    old = make_frame([1, 2, 3])
    new = make_frame([1, 2, 3]).iloc[1:]
    merged = merge_history(old, new)
    assert len(merged) == 3


def test_series_of_different_markets_are_not_mixed():
    frame = pd.concat([make_frame([10, 20], code="A"), make_frame([500, 400], code="B")])
    result = add_metrics(frame)
    change_a = result.loc[result["code"] == "A", "net_change"].iloc[1]
    change_b = result.loc[result["code"] == "B", "net_change"].iloc[1]
    assert change_a == 10
    assert change_b == -100


def test_normalize_expands_each_category_and_keeps_missing_as_nan():
    rows = [{
        "report_date_as_yyyy_mm_dd": "2026-09-29T00:00:00.000",
        "cftc_contract_market_code": "097741",
        "market_and_exchange_names": "JAPANESE YEN",
        "open_interest_all": "360720",
        "lev_money_positions_long": "77429",
        "lev_money_positions_short": "91590",
    }]
    categories = {
        "lev_money": ("lev_money_positions_long", "lev_money_positions_short"),
        "dealer": ("dealer_positions_long_all", "dealer_positions_short_all"),
    }
    frame = normalize(rows, "TFF", "fo", categories)
    assert len(frame) == 2
    lev = frame[frame["category"] == "lev_money"].iloc[0]
    assert lev["date"] == "2026-09-29"
    assert lev["long"] - lev["short"] == -14161
    assert frame[frame["category"] == "dealer"]["long"].isna().all()
