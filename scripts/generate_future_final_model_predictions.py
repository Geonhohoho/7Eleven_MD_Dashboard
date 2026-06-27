from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT.parent
MODEL_DIR = DATA_ROOT / "대시보드 작업" / "최종 모델 예정"
PREDICTIONS_CSV = MODEL_DIR / "predictions.csv"
BASELINE_CSV = MODEL_DIR / "baseline_dataset.csv"
FINAL_PREORDER_CSV = DATA_ROOT / "중간발표까지" / "중간발표" / "NEWSeven-main-2" / "final_preorder.csv"
PYDEPS = Path("/tmp/7eleven_pydeps")
ALPHA_RECOMMENDED = 1.15
TARGET_RELEASE = "20251231"

MODEL_FIELDS = [
    "ITEM_CODE",
    "CENTER_CODE",
    "NP_RLSE_YMD",
    "split",
    "ITEM_NM",
    "ITEM_TREAT_DV_CD",
    "issue_type",
    "RES_PREDEC_QTY",
    "actual_outflow_4d",
    "is_seasonal",
    "model_qty",
    "formula_qty",
    "formula_recal_qty",
    "calibrated_qty_auto",
    "calibrated_qty_reco",
]

NUMERIC_FEATURES = [
    "RES_PREDEC_QTY",
    "RES4_REG_QTY",
    "RES_PREDEC_STR",
    "RES4_REG_STR",
    "velocity",
    "frontload",
    "span",
    "hhi",
    "lead",
    "maxday",
    "store_vel",
    "center_store_pool",
    "center_reserve_coverage",
    "reserve_qty_center_share",
    "reserve_qty_per_store",
    "reserve4_qty_ratio",
    "min_order_cost",
    "owner_roi_score",
    "ST_CPM_AMT",
    "PRF_RT",
    "ITEM_CPCT_VAL",
    "ORD_SUPP_EVN_AMT",
    "ORD_SUPP_EVN_CND_QTY",
    "support_per_unit",
    "effective_margin_rate",
    "CENTER_AVG_OUTFLOW_CAT",
    "cf_prior_resv_scale",
    "nb_demand_per_store",
    "nb_mult",
    "over_index_qty",
]

CATEGORICAL_FEATURES = ["CENTER_CODE", "MDDV_X_CENTER_ENC", "issue_type"]
DAILY_COLUMNS = ["D-11", "D-10", "D-9", "D-8", "D-7", "D-6", "D-5"]
INITIAL_RESERVE_COLUMNS = ["D-11", "D-10", "D-9", "D-8"]


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce").fillna(0)


def _weighted_mode(values: pd.Series) -> str:
    values = values.dropna().astype(str)
    if values.empty:
        return "일반"
    return values.mode().iloc[0]


def _baseline_fill_maps(baseline: pd.DataFrame) -> tuple[dict[str, float], dict[str, dict[str, float]], dict[str, str], dict[str, str]]:
    global_median = {
        col: float(pd.to_numeric(baseline[col], errors="coerce").median())
        for col in NUMERIC_FEATURES
        if col in baseline.columns
    }
    center_medians: dict[str, dict[str, float]] = {}
    for center, group in baseline.groupby("CENTER_CODE"):
        center_medians[str(center)] = {
            col: float(pd.to_numeric(group[col], errors="coerce").median())
            for col in NUMERIC_FEATURES
            if col in group.columns
        }
    center_issue = baseline.groupby("CENTER_CODE")["issue_type"].agg(_weighted_mode).astype(str).to_dict()
    center_mddv = baseline.groupby("CENTER_CODE")["MDDV_X_CENTER_ENC"].agg(_weighted_mode).astype(str).to_dict()
    return global_median, center_medians, center_issue, center_mddv


def _prepare_future_features(preorder: pd.DataFrame, baseline: pd.DataFrame, existing_keys: set[tuple[str, str, str]]) -> pd.DataFrame:
    current = preorder[preorder["NP_RLSE_YMD"].astype(str) == TARGET_RELEASE].copy()
    current = current[current["ITEM_MDDV_NM"].fillna("").astype(str).str.len() > 0]
    current["ITEM_CODE"] = current["ITEM_CODE"].astype(str).str.strip()
    current["CENTER_CODE"] = current["CENTER_CODE"].astype(str).str.strip()
    current["NP_RLSE_YMD"] = current["NP_RLSE_YMD"].astype(str).str.strip()
    current = current[
        ~current.apply(lambda r: (r["ITEM_CODE"], r["CENTER_CODE"], r["NP_RLSE_YMD"]) in existing_keys, axis=1)
    ].copy()

    if current.empty:
        return current

    for col in DAILY_COLUMNS + ["INITIAL_ORD_QTY", "ordering_store_cnt", "total_store_cnt", "ST_CPM_AMT", "ST_SLEM_AMT", "MIN_ORD_QTY"]:
        current[col] = _to_numeric(current[col])

    global_median, center_medians, center_issue, center_mddv = _baseline_fill_maps(baseline)

    daily = current[DAILY_COLUMNS].clip(lower=0)
    initial_daily = current[INITIAL_RESERVE_COLUMNS].clip(lower=0)
    current["RES_PREDEC_QTY"] = daily.sum(axis=1)
    current["RES4_REG_QTY"] = initial_daily.sum(axis=1)
    current = current[current["RES_PREDEC_QTY"] > 0].copy()
    if current.empty:
        return current

    daily = current[DAILY_COLUMNS].clip(lower=0)
    initial_daily = current[INITIAL_RESERVE_COLUMNS].clip(lower=0)
    current["RES_PREDEC_STR"] = current["ordering_store_cnt"]
    current["RES4_REG_STR"] = np.where(
        current["RES_PREDEC_QTY"] > 0,
        current["ordering_store_cnt"] * current["RES4_REG_QTY"] / current["RES_PREDEC_QTY"],
        0,
    )
    current["RES4_REG_STR"] = np.minimum(current["RES4_REG_STR"], current["ordering_store_cnt"])
    active_days = (daily > 0).sum(axis=1).clip(lower=1)
    daily_share = daily.div(current["RES_PREDEC_QTY"], axis=0).fillna(0)
    current["velocity"] = np.log1p(current["RES_PREDEC_QTY"] / active_days)
    current["frontload"] = np.where(current["RES_PREDEC_QTY"] > 0, current["RES4_REG_QTY"] / current["RES_PREDEC_QTY"], 0)
    current["span"] = np.log1p(active_days)
    current["hhi"] = (daily_share**2).sum(axis=1)
    current["lead"] = np.log1p(6)
    current["maxday"] = daily_share.max(axis=1)
    current["store_vel"] = np.log1p(current["ordering_store_cnt"] / 7)
    current["center_store_pool"] = current["total_store_cnt"]
    current["center_reserve_coverage"] = np.where(
        current["total_store_cnt"] > 0,
        current["ordering_store_cnt"] / current["total_store_cnt"],
        0,
    )

    item_totals = current.groupby("ITEM_CODE")["RES_PREDEC_QTY"].transform("sum").replace(0, np.nan)
    current["reserve_qty_center_share"] = (current["RES_PREDEC_QTY"] / item_totals).fillna(0)
    current["reserve_qty_per_store"] = np.where(
        current["ordering_store_cnt"] > 0,
        current["RES_PREDEC_QTY"] / current["ordering_store_cnt"],
        0,
    )
    current["reserve4_qty_ratio"] = np.where(
        current["RES_PREDEC_QTY"] > 0,
        current["RES4_REG_QTY"] / current["RES_PREDEC_QTY"],
        0,
    )
    current["min_order_cost"] = current["MIN_ORD_QTY"] * current["ST_CPM_AMT"]

    current["ITEM_TREAT_DV_CD"] = "1"
    current["issue_type"] = current["CENTER_CODE"].map(center_issue).fillna("일반").astype(str)
    current["MDDV_X_CENTER_ENC"] = current["CENTER_CODE"].map(center_mddv).fillna("UNKNOWN").astype(str)

    for col in NUMERIC_FEATURES:
        if col not in current.columns:
            current[col] = np.nan
        center_fill = current["CENTER_CODE"].map(lambda c: center_medians.get(str(c), {}).get(col, np.nan))
        current[col] = pd.to_numeric(current[col], errors="coerce").fillna(center_fill).fillna(global_median.get(col, 0)).fillna(0)

    for col in CATEGORICAL_FEATURES:
        current[col] = current[col].fillna("UNKNOWN").astype(str)

    return current


def main() -> None:
    if PYDEPS.exists():
        sys.path.insert(0, str(PYDEPS))
    sys.path.insert(0, str(MODEL_DIR))

    from initial_order_model import InitialOrderModel

    predictions = pd.read_csv(PREDICTIONS_CSV, dtype=str, encoding="utf-8-sig")
    baseline = pd.read_csv(BASELINE_CSV, dtype=str, encoding="utf-8-sig")
    preorder = pd.read_csv(FINAL_PREORDER_CSV, dtype=str, encoding="utf-8-sig")

    existing_keys = set(
        zip(
            predictions["ITEM_CODE"].astype(str).str.strip(),
            predictions["CENTER_CODE"].astype(str).str.strip(),
            predictions["NP_RLSE_YMD"].astype(str).str.strip(),
        )
    )
    feature_df = _prepare_future_features(preorder, baseline, existing_keys)
    if feature_df.empty:
        print("No future feature rows to append.")
        return

    model = InitialOrderModel.load(MODEL_DIR / "artifact")
    pred = model.predict(feature_df, alpha=ALPHA_RECOMMENDED)
    auto = model.predict(feature_df, alpha=float(model.alpha_auto_))

    out = pd.DataFrame(
        {
            "ITEM_CODE": feature_df["ITEM_CODE"].astype(str),
            "CENTER_CODE": feature_df["CENTER_CODE"].astype(str),
            "NP_RLSE_YMD": feature_df["NP_RLSE_YMD"].astype(str),
            "split": "future",
            "ITEM_NM": feature_df["ITEM_NM"].astype(str),
            "ITEM_TREAT_DV_CD": feature_df["ITEM_TREAT_DV_CD"].astype(str),
            "issue_type": feature_df["issue_type"].astype(str),
            "RES_PREDEC_QTY": np.rint(feature_df["RES_PREDEC_QTY"]).astype(int),
            "actual_outflow_4d": 0,
            "is_seasonal": 0,
            "model_qty": pred["model_qty"].astype(int),
            "formula_qty": pred["formula_qty"].astype(int),
            "formula_recal_qty": pred["formula_recal_qty"].astype(int),
            "calibrated_qty_auto": auto["calibrated_qty"].astype(int),
            "calibrated_qty_reco": pred["calibrated_qty"].astype(int),
        }
    )[MODEL_FIELDS]

    backup = PREDICTIONS_CSV.with_name(f"predictions.backup_before_{TARGET_RELEASE}.csv")
    if not backup.exists():
        shutil.copy2(PREDICTIONS_CSV, backup)

    merged = pd.concat([predictions[MODEL_FIELDS], out], ignore_index=True)
    merged = merged.drop_duplicates(["ITEM_CODE", "CENTER_CODE", "NP_RLSE_YMD"], keep="last")
    merged.to_csv(PREDICTIONS_CSV, index=False, encoding="utf-8-sig")

    item_count = out["ITEM_CODE"].nunique()
    print(f"Appended {len(out)} center predictions for {item_count} items on {TARGET_RELEASE}.")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
