"""COTレポートの定義（データセットID・投機筋区分とAPI項目名の対応）。

CFTC Public Reporting（Socrata）のデータセットごとに、
区分キー -> (ロング項目名, ショート項目名) を持つ。
項目名はデータセットごとに表記ゆれ（_all の有無、大文字小文字、誤字）があるため、
APIの実際の項目名をそのまま書いている。
"""

# データ種類（先物のみ / 先物+オプション）
VARIANT_FUTURES_ONLY = "fo"
VARIANT_COMBINED = "combined"

VARIANT_LABELS = {
    VARIANT_FUTURES_ONLY: "先物のみ",
    VARIANT_COMBINED: "先物+オプション",
}

# ---- TFF（金融先物） ----
TFF_CATEGORIES = {
    "lev_money": ("lev_money_positions_long", "lev_money_positions_short"),
    "asset_mgr": ("asset_mgr_positions_long", "asset_mgr_positions_short"),
    "dealer": ("dealer_positions_long_all", "dealer_positions_short_all"),
    "other_rept": ("other_rept_positions_long", "other_rept_positions_short"),
    "nonrept": ("nonrept_positions_long_all", "nonrept_positions_short_all"),
}
TFF_LABELS = {
    "lev_money": "レバレッジドファンド",
    "asset_mgr": "アセットマネージャー",
    "dealer": "ディーラー",
    "other_rept": "その他報告者",
    "nonrept": "非報告者（小口）",
}

# ---- Disaggregated（商品） ----
DISAGG_CATEGORIES = {
    "m_money": ("m_money_positions_long_all", "m_money_positions_short_all"),
    "prod_merc": ("prod_merc_positions_long", "prod_merc_positions_short"),
    # ショート側はAPI上 "swap__positions_short_all"（アンダースコア2つ）が正
    "swap": ("swap_positions_long_all", "swap__positions_short_all"),
    "other_rept": ("other_rept_positions_long", "other_rept_positions_short"),
    "nonrept": ("nonrept_positions_long_all", "nonrept_positions_short_all"),
}
DISAGG_LABELS = {
    "m_money": "マネージドマネー",
    "prod_merc": "生産者・実需",
    "swap": "スワップディーラー",
    "other_rept": "その他報告者",
    "nonrept": "非報告者（小口）",
}

# ---- Legacy ----
LEGACY_CATEGORIES = {
    "noncomm": ("noncomm_positions_long_all", "noncomm_positions_short_all"),
    "comm": ("comm_positions_long_all", "comm_positions_short_all"),
    "nonrept": ("nonrept_positions_long_all", "nonrept_positions_short_all"),
}
LEGACY_LABELS = {
    "noncomm": "非商業（投機筋）",
    "comm": "商業（当業者）",
    "nonrept": "非報告者（小口）",
}

# ---- Supplemental CIT（先物+オプションのみ公表） ----
CIT_CATEGORIES = {
    "cit": ("cit_positions_long_all", "cit_positions_short_all"),
    # CIT系はAPI上で大文字混じり・"Postions" の誤字がそのまま項目名になっている
    "noncomm": ("NComm_Postions_Long_All_NoCIT", "NComm_Postions_Short_All_NoCIT"),
    "comm": ("comm_positions_long_all_nocit", "Comm_Positions_Short_All_NoCIT"),
    "nonrept": ("nonrept_positions_long_all", "nonrept_positions_short_all"),
}
CIT_LABELS = {
    "cit": "指数トレーダー（CIT）",
    "noncomm": "非商業（CIT除く）",
    "comm": "商業（CIT除く）",
    "nonrept": "非報告者（小口）",
}

# レポート一覧：表示順もこの順
REPORTS = {
    "TFF": {
        "label": "TFF（金融先物）",
        "datasets": {VARIANT_FUTURES_ONLY: "gpe5-46if", VARIANT_COMBINED: "yw9f-hn96"},
        "categories": TFF_CATEGORIES,
        "category_labels": TFF_LABELS,
        "default_category": "lev_money",
        "market_flag": "tff",
    },
    "Disagg": {
        "label": "Disaggregated（商品）",
        "datasets": {VARIANT_FUTURES_ONLY: "72hh-3qpy", VARIANT_COMBINED: "kh3c-gbw2"},
        "categories": DISAGG_CATEGORIES,
        "category_labels": DISAGG_LABELS,
        "default_category": "m_money",
        "market_flag": "disagg",
    },
    "Legacy": {
        "label": "Legacy（全銘柄）",
        "datasets": {VARIANT_FUTURES_ONLY: "6dca-aqww", VARIANT_COMBINED: "jun7-fc8e"},
        "categories": LEGACY_CATEGORIES,
        "category_labels": LEGACY_LABELS,
        "default_category": "noncomm",
        "market_flag": None,  # 全銘柄が対象
    },
    "CIT": {
        "label": "Supplemental CIT（農産物）",
        "datasets": {VARIANT_COMBINED: "4zgm-a668"},
        "categories": CIT_CATEGORIES,
        "category_labels": CIT_LABELS,
        "default_category": "cit",
        "market_flag": "cit",
    },
}

# Excelの履歴シート・CSVに載せる「投機筋」区分（全区分の履歴はCSVで別途出力）
SPECULATOR_CATEGORIES = {
    "TFF": ["lev_money", "asset_mgr"],
    "Disagg": ["m_money"],
    "Legacy": ["noncomm"],
    "CIT": ["cit"],
}
