from __future__ import annotations

import csv
import json
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    import pandas as pd
except Exception:
    pd = None


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CANDIDATES = [
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/중간발표까지/중간발표/NEWSeven-main-2/final_preorder.csv"),
    ROOT / "public" / "data" / "final_preorder.csv",
]
OUT = ROOT / "public" / "data" / "dashboard-data.json"
PREDICTIONS_CANDIDATES = [
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/중간발표까지/중간발표/NEWSeven-main-2/predictions.parquet"),
    ROOT / "public" / "data" / "predictions.parquet",
]
PREDICTIONS_CSV = ROOT / "public" / "data" / "ml_predictions_for_dashboard.csv"
FINAL_MODEL_PREDICTION_CANDIDATES = [
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/대시보드 작업/최종 모델 예정/predictions.csv"),
    ROOT.parent / "대시보드 작업" / "최종 모델 예정" / "predictions.csv",
]
FINAL_MODEL_ALPHA_RECOMMENDED = 1.15
SALES_DEPLETION_HORIZON_DAYS = 4
TODAY_DECISION_DATE = "2025-12-26"
STANDARD_CENTER_NAMES = {
    "20006": "성남센터",
    "20007": "대구센터",
    "20010": "양주센터",
    "20017": "울산상온센터(K7)",
    "20033": "제주상온센터",
    "20034": "구성상온센터",
    "20050": "세종상온센터",
    "20065": "원주상온센터(K7)",
    "20075": "인천상온센터",
    "20079": "A광주상온센터",
    "20080": "A의왕상온센터",
    "20081": "A양산상온센터",
    "20083": "김제상온센터",
    "20084": "천안상온센터",
    "20085": "인천B상온센터",
}
FINAL_MODEL_BASELINE_CSV = Path(
    "/Users/geonhokim/Desktop/세븐일레븐 내부데이터/대시보드 작업/최종 모델 예정/baseline_dataset.csv"
)
NEW_ITEM_INFO_CANDIDATES = [
    ROOT.parent / "데이터(원본)" / "신상품정보서_final.csv",
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/신상품정보서_final.csv"),
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/중간발표까지/중간발표/NEWSeven-main-2/데이터/A7_신상품_상품마스터.csv"),
]
ITEM_DV_INFO = Path(
    "/Users/geonhokim/Desktop/세븐일레븐 내부데이터/B조/B4_ITEM_DV_INFO.csv"
)
CENTER_STK_CANDIDATES = [
    ROOT / "public" / "data" / "A4_final_CENTER_STK.csv",
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/중간발표까지/중간발표/NEWSeven-main-2/A4_final_CENTER_STK.csv"),
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/대시보드 작업/public/data/A4_final_CENTER_STK.csv"),
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/A4_CENTER_STK.csv"),
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/A4_CENTER_STK_2024(LR11).csv"),
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/A4_CENTER_STK_(MD1302).csv"),
]
CENTER_FLOW_CANDIDATES = [
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/A4-1_CENT_RCDB(LR11).csv"),
]
STORE_SALE_PATTERNS = [
    "A5_A6_NEW_ITEM_SALE.csv",
    "A3_STORE_SALE(202401_202402_LR11).csv",
    "A3_STORE_SALE(202403_202404_LR11).csv",
    "A3_STORE_SALE(202405_202406_LR11).csv",
    "A3_STORE_SALE(202407_202408_LR11).csv",
    "A3_STORE_SALE(202409_202410_LR11).csv",
    "A3_STORE_SALE(202411_202412_LR11).csv",
]
STORE_SALE_CACHE = ROOT / "public" / "data" / "store_sales_item_center_date_cache.csv"
STORE_SALE_COVERAGE = ROOT / "public" / "data" / "store_sales_item_date_coverage.csv"
STORE_CENTER_CANDIDATES = [
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/A2-1_STR_CENT.csv"),
]
CENTER_WEIGHT_CSV = Path(
    "/Users/geonhokim/Desktop/세븐일레븐 내부데이터/중간발표까지/중간발표/NEWSeven-main-2/asymmetric_recommended_W.csv"
)
FORWARD_PREDICTION_SUMMARY_CANDIDATES = [
    ROOT.parent / "데이터(원본)" / "forward_predictions_9items_summary.csv",
    Path("/Users/geonhokim/Desktop/forward_predictions_9items_summary.csv"),
]
FORWARD_PREDICTION_CENTER_CANDIDATES = [
    ROOT.parent / "데이터(원본)" / "forward_predictions_9items_by_center.csv",
    Path("/Users/geonhokim/Desktop/forward_predictions_9items_by_center.csv"),
]


def to_int(v: str) -> int:
    try:
        return int(float(str(v or 0).replace(",", "")))
    except Exception:
        return 0


def to_float(v: str) -> float:
    try:
        return float(str(v or 0).replace(",", ""))
    except Exception:
        return 0.0


def format_date(ymd: str) -> str:
    try:
        return datetime.strptime(ymd, "%Y%m%d").strftime("%Y-%m-%d")
    except Exception:
        return ymd


def compact_ymd_to_iso(ymd: str) -> str:
    text = normalize_ymd_key(ymd)
    if len(text) == 8:
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text


def parse_date_yyyymmdd(ymd: str) -> datetime | None:
    try:
        return datetime.strptime((ymd or "").strip(), "%Y%m%d")
    except Exception:
        return None


def normalize_ymd_key(value: str) -> str:
    text = (value or "").strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 8:
        return digits[:8]
    return text


def clean_info_text(value: str, limit: int = 220) -> str:
    text = " ".join(str(value or "").replace("\\n", " ").split())
    if text.lower() == "nan":
        return ""
    return text[:limit].rstrip()


def split_info_points(value: str, limit: int = 3) -> list[str]:
    text = clean_info_text(value, 500)
    if not text:
        return []
    chunks: list[str] = []
    normalized = text
    for marker in ["1.", "2.", "3.", "4.", "5."]:
        normalized = normalized.replace(marker, f"\n{marker}")
    for part in normalized.splitlines():
        part = part.strip()
        if not part:
            continue
        if len(part) >= 2 and part[0].isdigit() and part[1] == ".":
            part = part[2:].strip()
        if part:
            chunks.append(part[:110].rstrip())
    return chunks[:limit] or [text[:110].rstrip()]


def capacity_label(value: str, unit_code: str) -> str:
    amount = to_float(value)
    if amount <= 0:
        return ""
    unit_key = str(unit_code or "").strip()
    unit_map = {
        "5": "g",
        "5.0": "g",
        "6": "ml",
        "6.0": "ml",
        "7": "입",
        "7.0": "입",
    }
    unit = unit_map.get(unit_key, "")
    amount_text = f"{int(amount):,}" if amount.is_integer() else f"{amount:,.1f}"
    return f"{amount_text}{unit}" if unit else amount_text


def resolve_original_data_dir() -> Path:
    direct = ROOT.parent / "데이터(원본)"
    if direct.exists():
        return direct
    for child in ROOT.parent.iterdir():
        name = unicodedata.normalize("NFC", child.name)
        if child.is_dir() and "데이터" in name and "원본" in name:
            return child
    return direct


def store_sale_files() -> list[Path]:
    data_dir = resolve_original_data_dir()
    files: list[Path] = []
    if not data_dir.exists():
        return files
    for pattern in STORE_SALE_PATTERNS:
        files.extend(data_dir.glob(pattern))
    return sorted(set(files), key=lambda p: p.name)


def sale_file_date_range(path: Path) -> tuple[str, str]:
    name = path.name
    digits = "".join(ch if ch.isdigit() else " " for ch in name).split()
    candidates = [d for d in digits if len(d) >= 6]
    if "A5_A6" in name:
        return "20250101", "20251231"
    if len(candidates) >= 2:
        start = candidates[0][:6] + "01"
        end_month = candidates[1][:6]
        try:
            end_dt = datetime.strptime(end_month + "01", "%Y%m%d")
            next_month = (end_dt.replace(day=28) + timedelta(days=4)).replace(day=1)
            end = (next_month - timedelta(days=1)).strftime("%Y%m%d")
        except Exception:
            end = end_month + "31"
        return start, end
    return "", "99999999"


def load_store_center_map() -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for path in STORE_CENTER_CANDIDATES:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                store = (row.get("STR_CD") or row.get("STORE_CODE") or "").strip()
                center = (row.get("CENT_CD") or row.get("CENTER_CODE") or "").strip()
                center_name = (row.get("CENT_NM") or row.get("CENTER_NM") or center).strip()
                if store and center:
                    out[store] = (center, center_name or center)
    return out


def risk_from_rate(rate: float) -> str:
    if rate < 100:
        return "결품위험"
    if rate <= 140:
        return "정상"
    return "과발주"


def outflow_horizon_days(category: str, category_mid: str, category_sub: str) -> int:
    text = f"{category} {category_mid} {category_sub}"
    if "용기면" in text:
        return 10
    return 4


def resolve_first_existing(candidates: list[Path]) -> Path:
    for p in candidates:
        if p.exists():
            return p
    return candidates[-1]


def load_center_weight_map() -> dict[str, float]:
    if not CENTER_WEIGHT_CSV.exists():
        return {}
    out: dict[str, float] = {}
    with CENTER_WEIGHT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (row.get("CENTER_CODE") or "").strip()
            if not code:
                continue
            out[code] = to_float(row.get("CENTER_WEIGHT") or "1.0") or 1.0
    return out


def load_forward_prediction_maps() -> tuple[dict[tuple[str, str], dict], dict[tuple[str, str], list[dict]]]:
    summary: dict[tuple[str, str], dict] = {}
    centers: dict[tuple[str, str], list[dict]] = defaultdict(list)

    summary_path = next((p for p in FORWARD_PREDICTION_SUMMARY_CANDIDATES if p.exists()), None)
    if summary_path:
        with summary_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item_code = (row.get("상품코드") or "").strip()
                if not item_code:
                    continue
                summary[(item_code, "20251231")] = {
                    "itemCode": item_code,
                    "itemName": (row.get("상품명") or "").strip(),
                    "centerCount": to_int(row.get("센터수", 0)),
                    "reservationQty": to_int(row.get("예약수량합", 0)),
                    "recommendedQty": to_int(row.get("예측_초도발주합_4일", 0)),
                    "predictedStores": to_int(row.get("예측_참여점포수합", 0)),
                    "lifecycleDemandUpper": to_int(row.get("예측_생애수요상한합", 0)),
                    "source": summary_path.name,
                }

    center_path = next((p for p in FORWARD_PREDICTION_CENTER_CANDIDATES if p.exists()), None)
    if center_path:
        with center_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item_code = (row.get("상품코드") or "").strip()
                ymd = normalize_ymd_key(row.get("출시일", "")) or "20251231"
                center_code = (row.get("센터코드") or "").strip()
                if not (item_code and center_code):
                    continue
                centers[(item_code, ymd)].append({
                    "centerCode": center_code,
                    "issueType": (row.get("이슈성") or "").strip(),
                    "reservationQty": to_int(row.get("예약수량", 0)),
                    "reservationStores": to_int(row.get("예약점포수", 0)),
                    "recommendedQty": to_int(row.get("예측_초도발주_4일출고", 0)),
                    "predictedStores": to_int(row.get("예측_참여점포수", 0)),
                    "lifecycleDemandUpper": to_int(row.get("예측_생애수요상한", 0)),
                    "source": center_path.name,
                })

    return summary, centers


def _empty_prediction_group() -> dict[str, float]:
    return {
        "modelQty": 0.0,
        "formulaFixedQty": 0.0,
        "formulaRecalQty": 0.0,
        "calibratedQtyAuto": 0.0,
        "calibratedQtyReco": 0.0,
        "actualOutflow4dFromModel": 0.0,
        "reservationAnchorQty": 0.0,
    }


def _prediction_payload_from_group(v: dict[str, float]) -> dict:
    recommend = v["calibratedQtyReco"] or v["modelQty"]
    return {
        "mlRecommendQty": int(round(recommend)),
        "modelQty": int(round(v["modelQty"])),
        "formulaFixedQty": int(round(v["formulaFixedQty"])),
        "formulaRecalQty": int(round(v["formulaRecalQty"])),
        "calibratedQtyAuto": int(round(v["calibratedQtyAuto"])),
        "calibratedQtyReco": int(round(v["calibratedQtyReco"])),
        # Legacy field name retained for current UI compatibility. In final v6 it stores 4-day actual outflow label when available.
        "predictedOutflow7d": int(round(v["actualOutflow4dFromModel"])),
        "actualOutflow4dFromModel": int(round(v["actualOutflow4dFromModel"])),
        "formulaQtyFromModelTable": int(round(v["formulaFixedQty"])),
        "reservationAnchorQty": int(round(v["reservationAnchorQty"])),
        "modelSource": "final_v6_calibrated_reco",
        "modelAlphaRecommended": FINAL_MODEL_ALPHA_RECOMMENDED,
    }


def load_final_model_prediction_csv(path: Path) -> dict[tuple[str, str], dict]:
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(_empty_prediction_group)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = (row.get("ITEM_CODE") or "").strip()
            ymd = normalize_ymd_key(row.get("NP_RLSE_YMD", ""))
            if not item or not ymd:
                continue
            key = (item, ymd)
            grouped[key]["modelQty"] += to_float(row.get("model_qty") or row.get("MODEL_QTY") or "0")
            grouped[key]["formulaFixedQty"] += to_float(row.get("formula_qty") or row.get("FORMULA_QTY") or "0")
            grouped[key]["formulaRecalQty"] += to_float(row.get("formula_recal_qty") or row.get("FORMULA_RECAL_QTY") or "0")
            grouped[key]["calibratedQtyAuto"] += to_float(row.get("calibrated_qty_auto") or row.get("CALIBRATED_QTY_AUTO") or "0")
            grouped[key]["calibratedQtyReco"] += to_float(
                row.get("calibrated_qty_reco") or row.get("CALIBRATED_QTY_RECO") or row.get("ML_PRED_QTY") or "0"
            )
            grouped[key]["actualOutflow4dFromModel"] += to_float(
                row.get("actual_outflow_4d") or row.get("ACTUAL_OUTFLOW_4D") or row.get("OUTFLOW_4D") or "0"
            )
            grouped[key]["reservationAnchorQty"] += to_float(row.get("RES_PREDEC_QTY") or row.get("reservation_anchor_qty") or "0")

    return {k: _prediction_payload_from_group(v) for k, v in grouped.items()}


def load_legacy_prediction_csv(path: Path) -> dict[tuple[str, str], dict]:
    grouped_csv: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"ML_PRED_QTY": 0.0, "OUTFLOW_7D": 0.0, "FORMULA_QTY": 0.0}
    )
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = (row.get("ITEM_CODE") or "").strip()
            ymd = normalize_ymd_key(row.get("NP_RLSE_YMD", ""))
            if not item or not ymd:
                continue
            key = (item, ymd)
            grouped_csv[key]["ML_PRED_QTY"] += to_float(row.get("ML_PRED_QTY", "0"))
            grouped_csv[key]["OUTFLOW_7D"] += to_float(row.get("OUTFLOW_7D", "0"))
            grouped_csv[key]["FORMULA_QTY"] += to_float(row.get("FORMULA_QTY", "0"))
    return {
        k: {
            "mlRecommendQty": int(round(v["ML_PRED_QTY"])),
            "modelQty": int(round(v["ML_PRED_QTY"])),
            "formulaFixedQty": int(round(v["FORMULA_QTY"])),
            "formulaRecalQty": 0,
            "calibratedQtyAuto": 0,
            "calibratedQtyReco": int(round(v["ML_PRED_QTY"])),
            "predictedOutflow7d": int(round(v["OUTFLOW_7D"])),
            "actualOutflow4dFromModel": 0,
            "formulaQtyFromModelTable": int(round(v["FORMULA_QTY"])),
            "reservationAnchorQty": 0,
            "modelSource": "legacy_ml_pred_qty",
            "modelAlphaRecommended": 0,
        }
        for k, v in grouped_csv.items()
    }


def load_prediction_csv(path: Path) -> dict[tuple[str, str], dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
    if {"model_qty", "calibrated_qty_reco"}.issubset(fieldnames) or {"MODEL_QTY", "CALIBRATED_QTY_RECO"}.issubset(fieldnames):
        return load_final_model_prediction_csv(path)
    return load_legacy_prediction_csv(path)


def load_ml_prediction_map() -> dict[tuple[str, str], dict]:
    for p in FINAL_MODEL_PREDICTION_CANDIDATES:
        if p.exists():
            return load_final_model_prediction_csv(p)

    if PREDICTIONS_CSV.exists():
        return load_prediction_csv(PREDICTIONS_CSV)

    predictions = resolve_first_existing(PREDICTIONS_CANDIDATES)
    if pd is None or not predictions.exists():
        return {}
    try:
        pred = pd.read_parquet(predictions)
    except Exception:
        return {}

    required = {"ITEM_CODE", "NP_RLSE_YMD", "ML_PRED_QTY", "OUTFLOW_7D", "FORMULA_QTY"}
    if not required.issubset(set(pred.columns)):
        return {}

    scoped = pred[list(required)].copy()
    scoped["ITEM_CODE"] = scoped["ITEM_CODE"].astype(str).str.strip()
    scoped["NP_RLSE_YMD"] = scoped["NP_RLSE_YMD"].astype(str).map(normalize_ymd_key)
    for col in ["ML_PRED_QTY", "OUTFLOW_7D", "FORMULA_QTY"]:
        scoped[col] = pd.to_numeric(scoped[col], errors="coerce").fillna(0)

    grouped = (
        scoped.groupby(["ITEM_CODE", "NP_RLSE_YMD"], as_index=False)[["ML_PRED_QTY", "OUTFLOW_7D", "FORMULA_QTY"]]
        .sum()
    )
    return {
        (str(r["ITEM_CODE"]).strip(), normalize_ymd_key(str(r["NP_RLSE_YMD"]))): {
            "mlRecommendQty": int(round(r["ML_PRED_QTY"])),
            "modelQty": int(round(r["ML_PRED_QTY"])),
            "formulaFixedQty": int(round(r["FORMULA_QTY"])),
            "formulaRecalQty": 0,
            "calibratedQtyAuto": 0,
            "calibratedQtyReco": int(round(r["ML_PRED_QTY"])),
            "predictedOutflow7d": int(round(r["OUTFLOW_7D"])),
            "actualOutflow4dFromModel": 0,
            "formulaQtyFromModelTable": int(round(r["FORMULA_QTY"])),
            "reservationAnchorQty": 0,
            "modelSource": "legacy_parquet_ml_pred_qty",
            "modelAlphaRecommended": 0,
        }
        for _, r in grouped.iterrows()
    }


def write_dashboard_prediction_csv(prediction_map: dict[tuple[str, str], dict]) -> None:
    if not prediction_map:
        return
    PREDICTIONS_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ITEM_CODE",
        "NP_RLSE_YMD",
        "ML_PRED_QTY",
        "MODEL_QTY",
        "FORMULA_QTY",
        "FORMULA_RECAL_QTY",
        "CALIBRATED_QTY_AUTO",
        "CALIBRATED_QTY_RECO",
        "OUTFLOW_4D",
        "RES_PREDEC_QTY",
        "ALPHA_RECOMMENDED",
        "MODEL_SOURCE",
    ]
    with PREDICTIONS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for (item, ymd), v in sorted(prediction_map.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            writer.writerow({
                "ITEM_CODE": item,
                "NP_RLSE_YMD": ymd,
                "ML_PRED_QTY": v.get("mlRecommendQty", 0),
                "MODEL_QTY": v.get("modelQty", 0),
                "FORMULA_QTY": v.get("formulaFixedQty", 0),
                "FORMULA_RECAL_QTY": v.get("formulaRecalQty", 0),
                "CALIBRATED_QTY_AUTO": v.get("calibratedQtyAuto", 0),
                "CALIBRATED_QTY_RECO": v.get("calibratedQtyReco", 0),
                "OUTFLOW_4D": v.get("actualOutflow4dFromModel", 0),
                "RES_PREDEC_QTY": v.get("reservationAnchorQty", 0),
                "ALPHA_RECOMMENDED": v.get("modelAlphaRecommended", 0),
                "MODEL_SOURCE": v.get("modelSource", ""),
            })


def load_item_category_map() -> dict[str, tuple[str, str, str]]:
    if not ITEM_DV_INFO.exists():
        return {}
    out: dict[str, tuple[str, str, str]] = {}
    with ITEM_DV_INFO.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (row.get("ITEM_CD") or "").strip()
            if not code:
                continue
            l = (row.get("ITEM_LRDV_NM") or "").strip() or "기타"
            m = (row.get("ITEM_MDDV_NM") or "").strip() or "기타"
            s = (row.get("ITEM_SMDV_NM") or "").strip() or "기타"
            out[code] = (l, m, s)
    return out


def load_new_item_info_map() -> tuple[dict[tuple[str, str], dict], dict[str, dict]]:
    by_release: dict[tuple[str, str], dict] = {}
    by_item: dict[str, dict] = {}
    for path in NEW_ITEM_INFO_CANDIDATES:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = (row.get("ITEM_CD") or row.get("ITEM_CODE") or "").strip()
                ymd = normalize_ymd_key(row.get("NP_RLSE_YMD") or "")
                if not item:
                    continue
                box_unit_ea = max(
                    to_int(row.get("OB_OBT_QY") or row.get("BOX_QTY") or row.get("MIN_ORD_QTY") or "0"),
                    1,
                )
                payload = {
                    "itemName": clean_info_text(row.get("ITEM_NM") or "", 80),
                    "goalIntroRate": to_float(row.get("GOAL_INTRO_RT") or "0"),
                    "boxUnitEa": box_unit_ea,
                    "lduEa": box_unit_ea,
                    "minOrdQty": max(to_int(row.get("MIN_ORD_QTY") or "0"), 1),
                    "price": to_int(row.get("ST_SLEM_AMT") or "0"),
                    "cost": to_int(row.get("ST_CPM_AMT") or "0"),
                    "profitRate": to_float(row.get("PRF_RT") or "0"),
                    "capacity": capacity_label(row.get("ITEM_CPCT_VAL") or "", row.get("ITEM_CPCT_UNIT_CD") or ""),
                    "displayLocation": clean_info_text(row.get("DISP_LOC_CN") or "", 60),
                    "eventNote": clean_info_text(row.get("ETC_EVN_CN") or "", 80),
                    "orderStartDate": compact_ymd_to_iso(row.get("ORD_PSS_YMD") or ""),
                    "releaseDate": compact_ymd_to_iso(ymd),
                    "orderLimitQty": to_int(row.get("ORD_LMT_QTY") or "0"),
                    "storeOrderUnitQty": to_int(row.get("STR_ORD_UNIT_QTY") or "0"),
                    "countryCode": clean_info_text(row.get("COO_CD") or "", 20),
                    "description": clean_info_text(row.get("ITEM_CRTR_CN") or "", 260),
                    "descriptionPoints": split_info_points(row.get("ITEM_CRTR_CN") or ""),
                    "releaseYmd": ymd,
                    "source": str(path),
                }
                if ymd:
                    by_release[(item, ymd)] = payload
                by_item[item] = payload
    return by_release, by_item


def load_center_stock_map() -> dict[tuple[str, str], dict[str, int]]:
    """
    key: (item_code, center_code) -> {yyyymmdd: book_end_qty}
    """
    out: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    for center_stk in CENTER_STK_CANDIDATES:
        if not center_stk.exists():
            continue
        with center_stk.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ymd = normalize_ymd_key(row.get("BIZ_DATE", ""))
                center = (row.get("CENTER_CODE") or "").strip()
                item = (row.get("ITEM_CODE") or "").strip()
                if not (ymd and center and item):
                    continue
                out[(item, center)][ymd] = to_int(row.get("BOOK_END_QTY", "0"))
    return out


def center_codes_for_item(center_stock_map: dict[tuple[str, str], dict[str, int]], item_code: str) -> set[str]:
    return {center for item, center in center_stock_map.keys() if item == item_code}


def load_center_flow_map() -> dict[tuple[str, str], dict[str, dict[str, int]]]:
    """
    key: (item_code, center_code) -> {yyyymmdd: {inbound, outflow}}
    A4-1_CENT_RCDB is the actual center flow file:
    - CUST_WARH_QTY: supplier-to-center inbound
    - STR_RLE_QTY: center-to-store release quantity
    """
    out: dict[tuple[str, str], dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: {"inbound": 0, "outflow": 0}))
    for flow_path in CENTER_FLOW_CANDIDATES:
        if not flow_path.exists():
            continue
        with flow_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ymd = normalize_ymd_key(row.get("RCDB_YMD", ""))
                center = (row.get("CENT_CD") or "").strip()
                item = (row.get("ITEM_CD") or "").strip()
                if not (ymd and center and item):
                    continue
                key = (item, center)
                out[key][ymd]["inbound"] += to_int(row.get("CUST_WARH_QTY", "0"))
                out[key][ymd]["outflow"] += to_int(row.get("STR_RLE_QTY", "0"))
    return out


def build_needed_sales_pairs(rows: list[dict]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for r in rows:
        item = str(r.get("itemCode", "")).strip()
        rel = parse_date_yyyymmdd(normalize_ymd_key(str(r.get("releaseDate", "")).replace("-", "")))
        if not item or rel is None:
            continue
        horizon_days = max(to_int(r.get("outflowHorizonDays", 4)) or 4, SALES_DEPLETION_HORIZON_DAYS)
        for offset in range(max(horizon_days, 1)):
            pairs.add((item, (rel + timedelta(days=offset)).strftime("%Y%m%d")))
    return pairs


def load_store_sales_map(
    needed_pairs: set[tuple[str, str]] | None = None,
) -> tuple[dict[tuple[str, str], dict[str, int]], dict[tuple[str, str, str], dict[str, int]], list[Path]]:
    """
    key: (item_code, yyyy-mm-dd) -> {qty, amount}
    A3 store sales are store-level rows, so dashboard aggregates them to item-date.
    """
    out: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"qty": 0, "amount": 0})
    by_center: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: {"qty": 0, "amount": 0})
    sources = store_sale_files()
    pair_filter = {(str(item).strip(), str(ymd).strip()) for item, ymd in needed_pairs or set() if str(item).strip() and str(ymd).strip()}
    item_filter = {item for item, _ in pair_filter}
    pair_key_filter = {f"{item}|{ymd}" for item, ymd in pair_filter}
    remaining_pairs = set(pair_filter)
    cache_rows: list[dict] = []
    source_paths_used: set[Path] = set()

    if STORE_SALE_CACHE.exists():
        with STORE_SALE_CACHE.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = (row.get("ITEM_CODE") or "").strip()
                ymd = normalize_ymd_key(row.get("SALE_YMD") or "")
                if pair_filter and (item, ymd) not in pair_filter:
                    continue
                date_key = compact_ymd_to_iso(ymd)
                qty = to_int(row.get("SALE_QTY", "0"))
                amount = to_int(row.get("SALE_AMT_VAT", "0"))
                center = (row.get("CENTER_CODE") or "").strip()
                out[(item, date_key)]["qty"] += qty
                out[(item, date_key)]["amount"] += amount
                if center:
                    by_center[(item, center, date_key)]["qty"] += qty
                    by_center[(item, center, date_key)]["amount"] += amount
                remaining_pairs.discard((item, ymd))
    if STORE_SALE_COVERAGE.exists():
        with STORE_SALE_COVERAGE.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = (row.get("ITEM_CODE") or "").strip()
                ymd = normalize_ymd_key(row.get("SALE_YMD") or "")
                if item and ymd:
                    remaining_pairs.discard((item, ymd))

    if pair_filter and not remaining_pairs:
        return out, by_center, sources

    active_pairs = remaining_pairs if pair_filter else pair_filter
    active_items = {item for item, _ in active_pairs}
    active_pair_keys = {f"{item}|{ymd}" for item, ymd in active_pairs}
    active_dates = {ymd for _, ymd in active_pairs}
    store_center_map = load_store_center_map()

    for sale_path in sources:
        if active_dates:
            start, end = sale_file_date_range(sale_path)
            if start and end and not any(start <= d <= end for d in active_dates):
                continue
        source_paths_used.add(sale_path)
        if pd is not None:
            try:
                usecols = ["ITEM_CODE", "SALE_AMT_VAT", "SALE_QTY"]
                if sale_path.name.startswith("A3_STORE_SALE"):
                    usecols = ["STD_YMD_DT", "STORE_CODE", "ITEM_CODE", "SALE_AMT_VAT", "SALE_QTY"]
                elif sale_path.name.startswith("A5_A6"):
                    usecols = ["BIZ_DATE", "ITEM_CODE", "SALE_AMT_VAT", "SALE_QTY"]
                chunks = pd.read_csv(sale_path, encoding="utf-8-sig", dtype=str, usecols=usecols, chunksize=500_000)
                for chunk in chunks:
                    chunk["ITEM_CODE"] = chunk["ITEM_CODE"].astype(str).str.strip()
                    if active_items:
                        chunk = chunk[chunk["ITEM_CODE"].isin(active_items)]
                    if chunk.empty:
                        continue
                    date_col = "STD_YMD_DT" if "STD_YMD_DT" in chunk.columns else "BIZ_DATE"
                    chunk["_ymd"] = (
                        chunk[date_col]
                        .astype(str)
                        .str.replace(r"\D", "", regex=True)
                        .str.slice(0, 8)
                    )
                    if active_pair_keys:
                        chunk["_pair"] = chunk["ITEM_CODE"] + "|" + chunk["_ymd"]
                        chunk = chunk[chunk["_pair"].isin(active_pair_keys)]
                    if chunk.empty:
                        continue
                    chunk["_qty"] = pd.to_numeric(
                        chunk["SALE_QTY"].astype(str).str.replace(",", "", regex=False),
                        errors="coerce",
                    ).fillna(0)
                    chunk["_amount"] = pd.to_numeric(
                        chunk["SALE_AMT_VAT"].astype(str).str.replace(",", "", regex=False),
                        errors="coerce",
                    ).fillna(0)
                    if "STORE_CODE" in chunk.columns:
                        chunk["_store"] = chunk["STORE_CODE"].astype(str).str.strip()
                        chunk["_center"] = chunk["_store"].map(lambda s: store_center_map.get(s, ("", ""))[0])
                        grouped_center = chunk.groupby(["ITEM_CODE", "_ymd", "_center"], as_index=False)[["_qty", "_amount"]].sum()
                        for _, row in grouped_center.iterrows():
                            item = str(row["ITEM_CODE"]).strip()
                            ymd = normalize_ymd_key(str(row["_ymd"]))
                            center = str(row["_center"]).strip()
                            if not center:
                                continue
                            date_key = compact_ymd_to_iso(ymd)
                            qty = int(round(float(row["_qty"])))
                            amount = int(round(float(row["_amount"])))
                            by_center[(item, center, date_key)]["qty"] += qty
                            by_center[(item, center, date_key)]["amount"] += amount
                            cache_rows.append({
                                "ITEM_CODE": item,
                                "SALE_YMD": ymd,
                                "CENTER_CODE": center,
                                "SALE_QTY": qty,
                                "SALE_AMT_VAT": amount,
                                "SOURCE": sale_path.name,
                            })
                    grouped_sales = chunk.groupby(["ITEM_CODE", "_ymd"], as_index=False)[["_qty", "_amount"]].sum()
                    for _, row in grouped_sales.iterrows():
                        item = str(row["ITEM_CODE"]).strip()
                        ymd = normalize_ymd_key(str(row["_ymd"]))
                        key = (item, compact_ymd_to_iso(ymd))
                        qty = int(round(float(row["_qty"])))
                        amount = int(round(float(row["_amount"])))
                        out[key]["qty"] += qty
                        out[key]["amount"] += amount
                        if "STORE_CODE" not in chunk.columns:
                            cache_rows.append({
                                "ITEM_CODE": item,
                                "SALE_YMD": ymd,
                                "CENTER_CODE": "",
                                "SALE_QTY": qty,
                                "SALE_AMT_VAT": amount,
                                "SOURCE": sale_path.name,
                            })
                continue
            except Exception:
                pass

        with sale_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = (row.get("ITEM_CODE") or row.get("ITEM_CD") or "").strip()
                if not item or (active_items and item not in active_items):
                    continue
                ymd = normalize_ymd_key(row.get("BIZ_DATE") or row.get("STD_YMD_DT") or row.get("SALE_YMD") or row.get("SALE_DT") or "")
                if not ymd or (active_pairs and (item, ymd) not in active_pairs):
                    continue
                date_key = compact_ymd_to_iso(ymd)
                qty = to_int(row.get("SALE_QTY") or row.get("SALE_QTY_SUM") or row.get("QTY") or "0")
                amount = to_int(row.get("SALE_AMT_VAT") or row.get("SALE_AMT") or row.get("AMT") or "0")
                key = (item, date_key)
                out[key]["qty"] += qty
                out[key]["amount"] += amount
                store = (row.get("STORE_CODE") or row.get("STR_CD") or "").strip()
                center = store_center_map.get(store, ("", ""))[0] if store else ""
                if center:
                    by_center[(item, center, date_key)]["qty"] += qty
                    by_center[(item, center, date_key)]["amount"] += amount
                cache_rows.append({
                    "ITEM_CODE": item,
                    "SALE_YMD": ymd,
                    "CENTER_CODE": center,
                    "SALE_QTY": qty,
                    "SALE_AMT_VAT": amount,
                    "SOURCE": sale_path.name,
                })

    if cache_rows:
        STORE_SALE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        exists = STORE_SALE_CACHE.exists()
        with STORE_SALE_CACHE.open("a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["ITEM_CODE", "SALE_YMD", "CENTER_CODE", "SALE_QTY", "SALE_AMT_VAT", "SOURCE"],
                lineterminator="\n",
            )
            if not exists:
                writer.writeheader()
            writer.writerows(cache_rows)
    if active_pairs:
        STORE_SALE_COVERAGE.parent.mkdir(parents=True, exist_ok=True)
        existing_coverage: set[tuple[str, str]] = set()
        if STORE_SALE_COVERAGE.exists():
            with STORE_SALE_COVERAGE.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_coverage.add(((row.get("ITEM_CODE") or "").strip(), normalize_ymd_key(row.get("SALE_YMD") or "")))
        new_coverage = sorted(active_pairs - existing_coverage)
        if new_coverage:
            exists = STORE_SALE_COVERAGE.exists()
            with STORE_SALE_COVERAGE.open("a", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["ITEM_CODE", "SALE_YMD"], lineterminator="\n")
                if not exists:
                    writer.writeheader()
                for item, ymd in new_coverage:
                    writer.writerow({"ITEM_CODE": item, "SALE_YMD": ymd})
    return out, by_center, sorted(source_paths_used or set(sources), key=lambda p: p.name)


def compute_post_release_sales_series(
    sales_by_item_date: dict[tuple[str, str], dict[str, int]],
    item_code: str,
    release_ymd: str,
    horizon_days: int = 4,
) -> list[dict]:
    rel = parse_date_yyyymmdd(release_ymd)
    if rel is None:
        return []
    out = []
    for offset in range(max(horizon_days, 1)):
        cur_dt = rel + timedelta(days=offset)
        date_key = cur_dt.strftime("%Y-%m-%d")
        sale = sales_by_item_date.get((item_code, date_key), {})
        out.append(
            {
                "date": date_key,
                "qty": to_int(sale.get("qty", 0)),
                "amount": to_int(sale.get("amount", 0)),
            }
        )
    return out


def distribute_qty(total: int, slots: int) -> list[int]:
    if slots <= 0:
        return []
    total = max(to_int(str(total)), 0)
    base = total // slots
    rem = total % slots
    return [base + (1 if i < rem else 0) for i in range(slots)]


def normalized_curve(values: list[int]) -> list[float]:
    total = sum(max(to_int(str(v)), 0) for v in values)
    if total <= 0:
        return [0.0 for _ in values]
    return [max(to_int(str(v)), 0) / total for v in values]


def reservation_similarity(a: list[int], b: list[int]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    aa = normalized_curve(a[:n])
    bb = normalized_curve(b[:n])
    distance = sum(abs(x - y) for x, y in zip(aa, bb)) / 2
    return round(max(0.0, 1.0 - distance) * 100, 1)


def compute_initial_and_outflow_from_flow(
    flow_by_day: dict[str, dict[str, int]],
    release_ymd: str,
    horizon_days: int = 4,
) -> tuple[int, int]:
    rel = parse_date_yyyymmdd(release_ymd)
    if rel is None or not flow_by_day:
        return 0, 0
    release_key = rel.strftime("%Y%m%d")
    initial = sum(to_int(v.get("inbound", 0)) for d, v in flow_by_day.items() if d <= release_key)
    outflow = 0
    for offset in range(max(horizon_days, 1)):
        cur_key = (rel + timedelta(days=offset)).strftime("%Y%m%d")
        outflow += to_int(flow_by_day.get(cur_key, {}).get("outflow", 0))
    return initial, outflow


def compute_post_release_flow_series(
    flow_by_day: dict[str, dict[str, int]],
    release_ymd: str,
    horizon_days: int = 4,
) -> list[dict]:
    rel = parse_date_yyyymmdd(release_ymd)
    if rel is None:
        return []
    out = []
    for offset in range(max(horizon_days, 1)):
        cur_dt = rel + timedelta(days=offset)
        cur_key = cur_dt.strftime("%Y%m%d")
        flow = flow_by_day.get(cur_key, {})
        out.append(
            {
                "date": cur_dt.strftime("%Y-%m-%d"),
                "outflow": to_int(flow.get("outflow", 0)),
                "inbound": to_int(flow.get("inbound", 0)),
            }
        )
    return out


def compute_initial_and_outflow_7d(
    stock_by_day: dict[str, int],
    release_ymd: str,
    horizon_days: int = 7,
) -> tuple[int, int]:
    """
    - initial_qty: 출시일까지 일자별 재고 증가분 합
    - outflow: 출시일 재고 - 출시+horizon_days일 재고 (순감소량, 음수면 0)
    """
    rel = parse_date_yyyymmdd(release_ymd)
    if rel is None or not stock_by_day:
        return 0, 0
    release_key = rel.strftime("%Y%m%d")
    end_key = (rel + timedelta(days=horizon_days)).strftime("%Y%m%d")

    dates = sorted(stock_by_day.keys())
    initial = 0
    prev = 0
    for d in dates:
        if d > release_key:
            break
        cur = to_int(stock_by_day.get(d, 0))
        delta = cur - prev
        if delta > 0:
            initial += delta
        prev = cur

    release_stock = to_int(stock_by_day.get(release_key, prev))
    end_stock = to_int(stock_by_day.get(end_key, release_stock))
    outflow = max(release_stock - end_stock, 0)
    return initial, outflow


def compute_post_release_outflow_series_7d(
    stock_by_day: dict[str, int],
    release_ymd: str,
    horizon_days: int = 7,
) -> list[dict]:
    rel = parse_date_yyyymmdd(release_ymd)
    if rel is None:
        return []
    prev_stock = to_int(stock_by_day.get(release_ymd, 0))
    out = []
    for i in range(1, horizon_days + 1):
        cur_dt = rel + timedelta(days=i)
        cur_key = cur_dt.strftime("%Y%m%d")
        cur_stock = to_int(stock_by_day.get(cur_key, prev_stock))
        daily_outflow = max(prev_stock - cur_stock, 0)
        out.append(
            {
                "date": cur_dt.strftime("%Y-%m-%d"),
                "outflow": daily_outflow,
                "stockEnd": cur_stock,
            }
        )
        prev_stock = cur_stock
    return out


def main() -> None:
    source = resolve_first_existing(SOURCE_CANDIDATES)
    ml_prediction_map = load_ml_prediction_map()
    forward_summary_map, forward_center_map = load_forward_prediction_maps()
    write_dashboard_prediction_csv(ml_prediction_map)
    center_weight_map = load_center_weight_map()
    item_category_map = load_item_category_map()
    new_item_info_by_release, new_item_info_by_item = load_new_item_info_map()
    center_flow_map = load_center_flow_map()
    center_stock_map = load_center_stock_map()
    grouped: dict[tuple[str, str], dict] = {}
    row_centers: dict[tuple[str, str], set[str]] = defaultdict(set)
    center_name_by_code: dict[str, str] = dict(STANDARD_CENTER_NAMES)
    categories = set()
    categories_mid = set()
    categories_sub = set()
    latest_ymd = ""

    with source.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ymd = (row.get("NP_RLSE_YMD") or "").strip()

            item_code = (row.get("ITEM_CODE") or "").strip()
            item_name = (row.get("ITEM_NM") or "").strip()
            lms = item_category_map.get(item_code)
            category = (lms[0] if lms else (row.get("ITEM_MDDV_NM") or "").strip()) or "기타"
            category_mid = (lms[1] if lms else (row.get("ITEM_MDDV_NM") or "").strip()) or "기타"
            category_sub = (lms[2] if lms else (row.get("ITEM_SMDV_NM") or "").strip()) or "기타"
            if category != "과자":
                continue
            if ymd > latest_ymd:
                latest_ymd = ymd
            categories.add(category)
            categories_mid.add(category_mid)
            categories_sub.add(category_sub)
            key = (item_code, ymd)

            if key not in grouped:
                release_date = format_date(ymd)
                box_unit_ea = max(
                    to_int(row.get("OB_OBT_QY") or row.get("BOX_QTY") or row.get("MIN_ORD_QTY") or "0"),
                    1,
                )
                try:
                    release_dt = datetime.strptime(release_date, "%Y-%m-%d")
                    deadline = (release_dt - timedelta(days=5)).strftime("%Y-%m-%d")
                except Exception:
                    deadline = release_date
                grouped[key] = {
                    "rowKey": f"{item_code}_{release_date}",
                    "itemCode": item_code,
                    "itemName": item_name,
                    "category": category,
                    "categoryMid": category_mid,
                    "categorySub": category_sub,
                    "boxUnitEa": box_unit_ea,
                    "lduEa": box_unit_ea,
                    "minOrdQty": max(to_int(row.get("MIN_ORD_QTY", "0")), 1),
                    "price": to_int(row.get("ST_SLEM_AMT", "0")),
                    "recommendQty": 0,
                    "mlRecommendQty": 0,
                    "modelQty": 0,
                    "formulaFixedQty": 0,
                    "formulaRecalQty": 0,
                    "calibratedQtyAuto": 0,
                    "calibratedQtyReco": 0,
                    "predictedOutflow7d": 0,
                    "actualOutflow4dFromModel": 0,
                    "formulaQtyFromModelTable": 0,
                    "reservationAnchorQty": 0,
                    "modelSource": "",
                    "modelAlphaRecommended": 0,
                    "goalIntroRtSum": 0.0,
                    "goalIntroRtCnt": 0,
                    "releaseDate": release_date,
                    "deadlineDate": deadline,
                    "decisionDate": deadline,
                    "outflowHorizonDays": outflow_horizon_days(category, category_mid, category_sub),
                }
            center_code = (row.get("CENTER_CODE") or "").strip()
            if center_code:
                row_centers[key].add(center_code)
                center_name = ((row.get("CENTER_NM") or "").strip() or center_code)
                center_name_by_code[center_code] = center_name

            grouped[key]["recommendQty"] += to_int(row.get("INITIAL_ORD_QTY", "0"))
            goal_rt = to_float(row.get("GOAL_INTRO_RT", "0"))
            if goal_rt > 0:
                grouped[key]["goalIntroRtSum"] += goal_rt
                grouped[key]["goalIntroRtCnt"] += 1

            norm_key = (item_code, normalize_ymd_key(ymd))
            if norm_key in ml_prediction_map:
                prediction = ml_prediction_map[norm_key]
                for field in [
                    "mlRecommendQty",
                    "modelQty",
                    "formulaFixedQty",
                    "formulaRecalQty",
                    "calibratedQtyAuto",
                    "calibratedQtyReco",
                    "predictedOutflow7d",
                    "actualOutflow4dFromModel",
                    "formulaQtyFromModelTable",
                    "reservationAnchorQty",
                    "modelAlphaRecommended",
                ]:
                    grouped[key][field] = prediction.get(field, grouped[key].get(field, 0))
                grouped[key]["modelSource"] = prediction.get("modelSource", "")
            if norm_key in forward_summary_map:
                forward_prediction = forward_summary_map[norm_key]
                if to_int(forward_prediction.get("recommendedQty", 0)) > 0:
                    grouped[key]["mlRecommendQty"] = to_int(forward_prediction.get("recommendedQty", 0))
                    grouped[key]["calibratedQtyReco"] = to_int(forward_prediction.get("recommendedQty", 0))
                    grouped[key]["predictedOutflow7d"] = to_int(forward_prediction.get("recommendedQty", 0))
                    grouped[key]["modelSource"] = "forward_predictions_9items"

    if FINAL_MODEL_BASELINE_CSV.exists():
        with FINAL_MODEL_BASELINE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ymd = normalize_ymd_key(row.get("NP_RLSE_YMD", ""))
                if not ymd.startswith("2024"):
                    continue
                item_code = (row.get("ITEM_CODE") or "").strip()
                item_name = (row.get("ITEM_NM") or "").strip()
                center_code = (row.get("CENTER_CODE") or "").strip()
                if not (item_code and ymd and center_code):
                    continue
                lms = item_category_map.get(item_code)
                if lms and lms[0] != "과자":
                    continue
                if not lms and not (row.get("ITEM_MDDV_CD") or "").startswith("11"):
                    continue
                category = (lms[0] if lms else "과자") or "과자"
                category_mid = (lms[1] if lms else (row.get("ITEM_MDDV_CD") or "기타").strip()) or "기타"
                category_sub = (lms[2] if lms else "기타") or "기타"
                categories.add(category)
                categories_mid.add(category_mid)
                categories_sub.add(category_sub)
                key = (item_code, ymd)
                release_date = format_date(ymd)
                if key not in grouped:
                    box_unit_ea = max(
                        to_int(row.get("OB_OBT_QY") or row.get("BOX_QTY") or row.get("MIN_ORD_QTY") or "0"),
                        1,
                    )
                    try:
                        release_dt = datetime.strptime(release_date, "%Y-%m-%d")
                        deadline = (release_dt - timedelta(days=5)).strftime("%Y-%m-%d")
                    except Exception:
                        deadline = release_date
                    grouped[key] = {
                        "rowKey": f"{item_code}_{release_date}",
                        "itemCode": item_code,
                        "itemName": item_name,
                        "category": category,
                        "categoryMid": category_mid,
                        "categorySub": category_sub,
                        "boxUnitEa": box_unit_ea,
                        "lduEa": box_unit_ea,
                        "minOrdQty": max(to_int(row.get("MIN_ORD_QTY", "0")), 1),
                        "price": to_int(row.get("ST_SLEM_AMT", "0")),
                        "recommendQty": 0,
                        "mlRecommendQty": 0,
                        "modelQty": 0,
                        "formulaFixedQty": 0,
                        "formulaRecalQty": 0,
                        "calibratedQtyAuto": 0,
                        "calibratedQtyReco": 0,
                        "predictedOutflow7d": 0,
                        "actualOutflow4dFromModel": 0,
                        "formulaQtyFromModelTable": 0,
                        "reservationAnchorQty": 0,
                        "modelSource": "",
                        "modelAlphaRecommended": 0,
                        "goalIntroRtSum": 0.0,
                        "goalIntroRtCnt": 0,
                        "releaseDate": release_date,
                        "deadlineDate": deadline,
                        "decisionDate": deadline,
                        "outflowHorizonDays": outflow_horizon_days(category, category_mid, category_sub),
                    }
                    norm_key = (item_code, ymd)
                    if norm_key in ml_prediction_map:
                        prediction = ml_prediction_map[norm_key]
                        for field in [
                            "mlRecommendQty",
                            "modelQty",
                            "formulaFixedQty",
                            "formulaRecalQty",
                            "calibratedQtyAuto",
                            "calibratedQtyReco",
                            "predictedOutflow7d",
                            "actualOutflow4dFromModel",
                            "formulaQtyFromModelTable",
                            "reservationAnchorQty",
                            "modelAlphaRecommended",
                        ]:
                            grouped[key][field] = prediction.get(field, grouped[key].get(field, 0))
                        grouped[key]["modelSource"] = prediction.get("modelSource", "")
                    if norm_key in forward_summary_map:
                        forward_prediction = forward_summary_map[norm_key]
                        if to_int(forward_prediction.get("recommendedQty", 0)) > 0:
                            grouped[key]["mlRecommendQty"] = to_int(forward_prediction.get("recommendedQty", 0))
                            grouped[key]["calibratedQtyReco"] = to_int(forward_prediction.get("recommendedQty", 0))
                            grouped[key]["predictedOutflow7d"] = to_int(forward_prediction.get("recommendedQty", 0))
                            grouped[key]["modelSource"] = "forward_predictions_9items"
                grouped[key]["recommendQty"] += to_int(row.get("OPT_D", "0"))
                row_centers[key].add(center_code)
                center_name_by_code.setdefault(center_code, center_code)

    rows = list(grouped.values())
    for r in rows:
        info = new_item_info_by_release.get(
            (r["itemCode"], normalize_ymd_key(str(r.get("releaseDate", "")).replace("-", "")))
        ) or new_item_info_by_item.get(r["itemCode"], {})
        if r["goalIntroRtCnt"] <= 0 and to_float(info.get("goalIntroRate", 0)) > 0:
            r["goalIntroRtSum"] = to_float(info.get("goalIntroRate", 0))
            r["goalIntroRtCnt"] = 1
        if to_int(r.get("boxUnitEa", 0)) <= 1 and to_int(info.get("boxUnitEa", 0)) > 1:
            r["boxUnitEa"] = to_int(info.get("boxUnitEa", 1))
        r["boxUnitEa"] = max(to_int(r.get("boxUnitEa") or r.get("lduEa") or info.get("boxUnitEa") or 1), 1)
        r["lduEa"] = r["boxUnitEa"]
        if to_int(r.get("minOrdQty", 0)) <= 1 and to_int(info.get("minOrdQty", 0)) > 1:
            r["minOrdQty"] = to_int(info.get("minOrdQty", 1))
        if to_int(r.get("price", 0)) <= 0 and to_int(info.get("price", 0)) > 0:
            r["price"] = to_int(info.get("price", 0))
        avg_rate = (r["goalIntroRtSum"] / r["goalIntroRtCnt"]) if r["goalIntroRtCnt"] else 0.0
        goal_intro_rate = round(avg_rate * 100, 1) if avg_rate and avg_rate <= 1 else round(avg_rate, 1)
        model_base_qty = max(r["mlRecommendQty"], 1)
        model_outflow = max(r["predictedOutflow7d"], 0)
        model_rate = (model_outflow / model_base_qty) * 100
        fallback_rate = goal_intro_rate
        sales_rate = round(model_rate, 1) if r["mlRecommendQty"] > 0 else fallback_rate
        r["goalIntroRate"] = goal_intro_rate
        r["salesRate"] = sales_rate
        r["risk"] = risk_from_rate(sales_rate)
        r["inputQty"] = r["mlRecommendQty"] if r["mlRecommendQty"] > 0 else r["recommendQty"]
        r["formulaQty"] = r["formulaFixedQty"] if r["formulaFixedQty"] > 0 else r["formulaQtyFromModelTable"] if r["formulaQtyFromModelTable"] > 0 else r["recommendQty"]
        item_code = r["itemCode"]
        rel_ymd = normalize_ymd_key(r["releaseDate"].replace("-", ""))
        centers = set(row_centers.get((item_code, rel_ymd), set()))
        centers.update(center_codes_for_item(center_stock_map, item_code))
        horizon_days = to_int(r.get("outflowHorizonDays", 4)) or 4
        initial_sum = 0
        outflow_sum = 0
        for c in centers:
            flow_series = center_flow_map.get((item_code, c), {})
            if flow_series:
                init_c, out7_c = compute_initial_and_outflow_from_flow(flow_series, rel_ymd, horizon_days)
            else:
                stock_series = center_stock_map.get((item_code, c), {})
                init_c, out7_c = compute_initial_and_outflow_7d(stock_series, rel_ymd, horizon_days)
            initial_sum += init_c
            outflow_sum += out7_c
        r["actualInitialQty"] = initial_sum
        r["actualOutflow7d"] = outflow_sum
        r["appropriateOutflowQty"] = outflow_sum
        r["actualOutflowRate7d"] = round((outflow_sum / max(initial_sum, 1)) * 100, 1) if initial_sum > 0 else 0.0
        r["salesDepletionRate"] = 0.0
        if outflow_sum > 0:
            r["orderAdequacyRate"] = round((initial_sum / outflow_sum) * 100, 1)
        elif initial_sum > 0:
            r["orderAdequacyRate"] = 999.0
        else:
            r["orderAdequacyRate"] = 0.0
        if initial_sum <= 0:
            if not centers:
                r["actualDataReason"] = "센터 매핑 없음"
            else:
                r["actualDataReason"] = "출시일까지 실입고 미확인"
        else:
            r["actualDataReason"] = ""
        del r["goalIntroRtSum"]
        del r["goalIntroRtCnt"]

    rows.sort(key=lambda x: (x["releaseDate"], x["recommendQty"]), reverse=True)
    row_map = {r["rowKey"]: r for r in rows}
    weekly_rows = [r for r in rows if r.get("decisionDate") == TODAY_DECISION_DATE]
    if not weekly_rows:
        weekly_rows = [r for r in rows if r["releaseDate"] == format_date(latest_ymd)]
    weekly_rows.sort(key=lambda x: x["recommendQty"], reverse=True)
    weekly_rows = weekly_rows[:80]

    detail_map: dict[str, dict] = defaultdict(lambda: {
        "reservation4d": {str(i): 0 for i in range(7)},  # D-11 ~ D-5
        "reservationPre": {str(i): 0 for i in range(7)},  # D-11 ~ D-5
        "centers": defaultdict(int),
        "centerMeta": {},
        "reservationStart": "",
    })

    with source.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_code = (row.get("ITEM_CODE") or "").strip()
            ymd = (row.get("NP_RLSE_YMD") or "").strip()
            if not item_code:
                continue
            release_date = format_date(ymd)
            row_key = f"{item_code}_{release_date}"
            d = detail_map[row_key]
            start_dt = parse_date_yyyymmdd(row.get("PRE_D11", "")) or (
                parse_date_yyyymmdd(ymd) - timedelta(days=11)
                if parse_date_yyyymmdd(ymd) else None
            )
            if start_dt and not d["reservationStart"]:
                d["reservationStart"] = start_dt.strftime("%Y-%m-%d")
            d["reservation4d"]["0"] += to_int(row.get("D-11", "0"))
            d["reservation4d"]["1"] += to_int(row.get("D-10", "0"))
            d["reservation4d"]["2"] += to_int(row.get("D-9", "0"))
            d["reservation4d"]["3"] += to_int(row.get("D-8", "0"))
            d["reservation4d"]["4"] += to_int(row.get("D-7", "0"))
            d["reservation4d"]["5"] += to_int(row.get("D-6", "0"))
            d["reservation4d"]["6"] += to_int(row.get("D-5", "0"))
            for i, label in enumerate(["D-11", "D-10", "D-9", "D-8", "D-7", "D-6", "D-5"]):
                d["reservationPre"][str(i)] += to_int(row.get(label, "0"))
            center = ((row.get("CENTER_NM") or "").strip() or "미지정센터")
            center_code = (row.get("CENTER_CODE") or "").strip()
            d["centers"][center] += to_int(row.get("INITIAL_ORD_QTY", "0"))
            ordering_store_cnt = to_int(row.get("ordering_store_cnt", "0"))
            total_store_cnt = to_int(row.get("total_store_cnt", "0"))
            center_weight = center_weight_map.get(center_code, 1.0)
            d["centerMeta"][center] = {
                "centerCode": center_code,
                "orderingStoreCnt": ordering_store_cnt,
                "totalStoreCnt": total_store_cnt,
                "centerWeight": center_weight,
            }

    if FINAL_MODEL_BASELINE_CSV.exists():
        with FINAL_MODEL_BASELINE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ymd = normalize_ymd_key(row.get("NP_RLSE_YMD", ""))
                if not ymd.startswith("2024"):
                    continue
                item_code = (row.get("ITEM_CODE") or "").strip()
                center_code = (row.get("CENTER_CODE") or "").strip()
                if not (item_code and center_code):
                    continue
                lms = item_category_map.get(item_code)
                if lms and lms[0] != "과자":
                    continue
                if not lms and not (row.get("ITEM_MDDV_CD") or "").startswith("11"):
                    continue
                release_date = format_date(ymd)
                row_key = f"{item_code}_{release_date}"
                if row_key not in row_map:
                    continue
                d = detail_map[row_key]
                rel_dt = parse_date_yyyymmdd(ymd)
                if rel_dt and not d["reservationStart"]:
                    d["reservationStart"] = (rel_dt - timedelta(days=11)).strftime("%Y-%m-%d")
                pre4 = to_int(row.get("RES4_REG_QTY", "0"))
                pre_total = to_int(row.get("RES_PREDEC_QTY", "0"))
                tail = max(pre_total - pre4, 0)
                for idx, qty in enumerate(distribute_qty(pre4, 4)):
                    d["reservation4d"][str(idx)] += qty
                    d["reservationPre"][str(idx)] += qty
                for idx, qty in enumerate(distribute_qty(tail, 3), start=4):
                    d["reservation4d"][str(idx)] += qty
                    d["reservationPre"][str(idx)] += qty
                center = center_name_by_code.get(center_code, center_code)
                d["centers"][center] += to_int(row.get("OPT_D", "0"))
                d["centerMeta"][center] = {
                    "centerCode": center_code,
                    "orderingStoreCnt": 0,
                    "totalStoreCnt": 0,
                    "centerWeight": center_weight_map.get(center_code, 1.0),
                }

    # 예약 시작일(D-11) 수량은 0 이상이어야 함(음수 데이터만 제외)
    valid_row_keys = {
        row_key
        for row_key, detail in detail_map.items()
        if detail["reservation4d"]["0"] >= 0
    }
    rows = [r for r in rows if r["rowKey"] in valid_row_keys]
    weekly_rows = [r for r in rows if r.get("decisionDate") == TODAY_DECISION_DATE]
    if not weekly_rows:
        weekly_rows = [r for r in rows if r["releaseDate"] == format_date(latest_ymd)]
    store_sales_map, center_store_sales_map, store_sales_sources = load_store_sales_map(build_needed_sales_pairs(rows))
    for r in rows:
        sales_timeline = compute_post_release_sales_series(
            store_sales_map,
            r["itemCode"],
            normalize_ymd_key(str(r.get("releaseDate", "")).replace("-", "")),
            SALES_DEPLETION_HORIZON_DAYS,
        )
        r["actualStoreSalesQty"] = sum(to_int(x.get("qty", 0)) for x in sales_timeline)
        r["actualStoreSalesAmount"] = sum(to_int(x.get("amount", 0)) for x in sales_timeline)
        r["salesDepletionRate"] = (
            round((r["actualStoreSalesQty"] / max(to_int(r.get("actualInitialQty", 0)), 1)) * 100, 1)
            if to_int(r.get("actualInitialQty", 0)) > 0
            else 0.0
        )
        r["storeSalesToOutflowRate"] = (
            round((r["actualStoreSalesQty"] / max(to_int(r.get("actualOutflow7d", 0)), 1)) * 100, 1)
            if to_int(r.get("actualOutflow7d", 0)) > 0
            else 0.0
        )

    item_details = {}
    all_row_keys = {r["rowKey"] for r in rows}
    for row_key, detail in detail_map.items():
        if row_key not in all_row_keys:
            continue
        base_date = datetime.strptime(detail["reservationStart"], "%Y-%m-%d") if detail["reservationStart"] else datetime.strptime(format_date(latest_ymd), "%Y-%m-%d")
        reservation4d = []
        reservation_pre = []
        for offset_key, qty in detail["reservation4d"].items():
            offset = int(offset_key)
            date_label = (base_date + timedelta(days=offset)).strftime("%Y-%m-%d")
            reservation4d.append({"date": date_label, "qty": qty})
        for offset_key, qty in detail["reservationPre"].items():
            offset = int(offset_key)
            date_label = (base_date + timedelta(days=offset)).strftime("%Y-%m-%d")
            reservation_pre.append({"date": date_label, "qty": qty})
        item_code = row_key.split("_", 1)[0]
        row_info = row_map.get(row_key, {})
        rel_ymd = normalize_ymd_key(str(row_info.get("releaseDate", "")).replace("-", ""))
        mapped_center_codes = set(center_weight_map.keys())
        if not mapped_center_codes:
            mapped_center_codes.update(row_centers.get((item_code, rel_ymd), set()))
            mapped_center_codes.update(center_codes_for_item(center_stock_map, item_code))
        mapped_center_codes = sorted(mapped_center_codes)
        center_initial_from_stock: list[dict] = []
        for cc in mapped_center_codes:
            flow_series = center_flow_map.get((item_code, cc), {})
            if flow_series:
                init_c, _ = compute_initial_and_outflow_from_flow(
                    flow_series,
                    rel_ymd,
                    to_int(row_info.get("outflowHorizonDays", 4)) or 4,
                )
            else:
                stock_series = center_stock_map.get((item_code, cc), {})
                init_c, _ = compute_initial_and_outflow_7d(
                    stock_series,
                    rel_ymd,
                    to_int(row_info.get("outflowHorizonDays", 4)) or 4,
                )
            center_initial_from_stock.append(
                {
                    "centerCode": cc,
                    "centerName": center_name_by_code.get(cc, cc),
                    "initialQty": init_c,
                }
            )
        centers_sorted = sorted(center_initial_from_stock, key=lambda x: x["initialQty"], reverse=True)[:15]
        centers = []
        per_center_perf = []
        post7_agg: dict[str, int] = defaultdict(int)
        center_total_initial = 0
        center_total_out7 = 0
        horizon_days = to_int(row_info.get("outflowHorizonDays", 4)) or 4
        for cinfo in centers_sorted:
            center_code = (cinfo.get("centerCode") or "").strip()
            n = cinfo.get("centerName") or center_code
            q = to_int(cinfo.get("initialQty", 0))
            meta = detail["centerMeta"].get(n, {})
            ordering_store_cnt = to_int(meta.get("orderingStoreCnt", 0))
            total_store_cnt = to_int(meta.get("totalStoreCnt", 0))
            store_share = (ordering_store_cnt / total_store_cnt) if total_store_cnt > 0 else 0.0
            center_weight = to_float(meta.get("centerWeight", 1.0)) or 1.0
            out7_c = 0
            sales_c = 0
            if center_code and item_code and rel_ymd:
                flow_series = center_flow_map.get((item_code, center_code), {})
                if flow_series:
                    _, out7_c = compute_initial_and_outflow_from_flow(flow_series, rel_ymd, horizon_days)
                    for p in compute_post_release_flow_series(flow_series, rel_ymd, horizon_days):
                        post7_agg[p["date"]] += to_int(p["outflow"])
                else:
                    stock_series = center_stock_map.get((item_code, center_code), {})
                    _, out7_c = compute_initial_and_outflow_7d(stock_series, rel_ymd, horizon_days)
                    for p in compute_post_release_outflow_series_7d(stock_series, rel_ymd, horizon_days):
                        post7_agg[p["date"]] += to_int(p["outflow"])
                rel_dt = parse_date_yyyymmdd(rel_ymd)
                if rel_dt:
                    for offset in range(SALES_DEPLETION_HORIZON_DAYS):
                        date_key = (rel_dt + timedelta(days=offset)).strftime("%Y-%m-%d")
                        sales_c += to_int(center_store_sales_map.get((item_code, center_code, date_key), {}).get("qty", 0))
            perf_rate = round((out7_c / max(to_int(q), 1)) * 100, 1) if to_int(q) > 0 else 0.0
            sales_depletion_c = round((sales_c / max(to_int(q), 1)) * 100, 1) if to_int(q) > 0 else 0.0
            if out7_c > 0:
                order_adequacy_rate = round((to_int(q) / out7_c) * 100, 1)
            elif to_int(q) > 0:
                order_adequacy_rate = 999.0
            else:
                order_adequacy_rate = 0.0
            center_total_initial += to_int(q)
            center_total_out7 += out7_c
            centers.append({
                "centerName": n,
                "qty": q,
                "centerCode": center_code,
                "orderingStoreCnt": ordering_store_cnt,
                "totalStoreCnt": total_store_cnt,
                "storeShare": store_share,
                "centerWeight": center_weight,
                "allocationIndex": store_share * center_weight,
            })
            per_center_perf.append({
                "centerName": n,
                "initialQty": to_int(q),
                "outflow7d": out7_c,
                "storeSalesQty": sales_c,
                "outflowRate7d": perf_rate,
                "salesDepletionRate": sales_depletion_c,
                "orderAdequacyRate": order_adequacy_rate,
            })
        total_qty = center_total_initial
        ml_total_qty = to_int(row_info.get("mlRecommendQty", 0))
        formula_qty = ml_total_qty if ml_total_qty > 0 else total_qty
        post_release_timeline = [
            {"date": d, "qty": to_int(post7_agg[d])}
            for d in sorted(post7_agg.keys())
        ]
        post_release_sales_timeline = compute_post_release_sales_series(
            store_sales_map,
            item_code,
            rel_ymd,
            SALES_DEPLETION_HORIZON_DAYS,
        )
        post_release_sales_total_qty = sum(to_int(x.get("qty", 0)) for x in post_release_sales_timeline)
        post_release_sales_total_amount = sum(to_int(x.get("amount", 0)) for x in post_release_sales_timeline)
        product_info = new_item_info_by_release.get((item_code, rel_ymd)) or new_item_info_by_item.get(item_code, {})
        forward_summary = forward_summary_map.get((item_code, rel_ymd), {})
        forward_centers_raw = forward_center_map.get((item_code, rel_ymd), [])
        forward_centers = []
        for fc in forward_centers_raw:
            center_code = (fc.get("centerCode") or "").strip()
            center_name = center_name_by_code.get(center_code, center_code)
            if not center_name:
                continue
            box_unit_ea = max(to_int(row_info.get("boxUnitEa") or row_info.get("lduEa") or 1), 1)
            recommended_qty = to_int(fc.get("recommendedQty", 0))
            lifecycle_upper = to_int(fc.get("lifecycleDemandUpper", 0))
            forward_centers.append({
                "centerCode": center_code,
                "centerName": center_name,
                "issueType": fc.get("issueType", ""),
                "reservationQty": to_int(fc.get("reservationQty", 0)),
                "reservationStores": to_int(fc.get("reservationStores", 0)),
                "recommendedQty": recommended_qty,
                "recommendedBox": round(recommended_qty / box_unit_ea) if box_unit_ea else recommended_qty,
                "predictedStores": to_int(fc.get("predictedStores", 0)),
                "lifecycleDemandUpper": lifecycle_upper,
                "lifecycleDemandUpperBox": round(lifecycle_upper / box_unit_ea) if box_unit_ea else lifecycle_upper,
            })
        forward_centers.sort(key=lambda x: x["recommendedQty"], reverse=True)
        if (
            post_release_sales_total_qty > 0
            and center_total_initial > 0
            and sum(to_int(x.get("storeSalesQty", 0)) for x in per_center_perf) <= 0
        ):
            allocated = 0
            for idx, perf in enumerate(per_center_perf):
                if idx == len(per_center_perf) - 1:
                    sales_c = max(post_release_sales_total_qty - allocated, 0)
                else:
                    sales_c = int(round(post_release_sales_total_qty * (to_int(perf.get("initialQty", 0)) / center_total_initial)))
                    allocated += sales_c
                perf["storeSalesQty"] = sales_c
                perf["salesDepletionRate"] = round((sales_c / max(to_int(perf.get("initialQty", 0)), 1)) * 100, 1) if to_int(perf.get("initialQty", 0)) > 0 else 0.0
        item_details[row_key] = {
            "reservation4d": reservation4d,
            "reservationPreRelease": reservation_pre,
            "reservationPre4dSum": sum(to_int(x["qty"]) for x in reservation4d),
            "reservationPreTotalSum": sum(to_int(x["qty"]) for x in reservation_pre),
            "centerDistribution": centers,
            "centerPerformance7d": sorted(per_center_perf, key=lambda x: x["outflowRate7d"], reverse=True),
            "postReleaseOutflow7d": post_release_timeline,
            "postReleaseStoreSales": post_release_sales_timeline,
            "postReleaseStoreSalesQty": post_release_sales_total_qty,
            "postReleaseStoreSalesAmount": post_release_sales_total_amount,
            "salesDepletionRate": (
                round((post_release_sales_total_qty / max(center_total_initial, 1)) * 100, 1)
                if center_total_initial > 0
                else 0.0
            ),
            "storeSalesToOutflowRate": (
                round((post_release_sales_total_qty / max(center_total_out7, 1)) * 100, 1)
                if center_total_out7 > 0
                else 0.0
            ),
            "centerInitialQtySum": center_total_initial,
            "centerOutflow7dSum": center_total_out7,
            "outflowHorizonDays": horizon_days,
            "salesDepletionHorizonDays": SALES_DEPLETION_HORIZON_DAYS,
            "formula": {
                "totalRecommendQty": formula_qty,
                "modelQty": to_int(row_info.get("modelQty", 0)),
                "formulaFixedQty": to_int(row_info.get("formulaFixedQty", 0)),
                "formulaRecalQty": to_int(row_info.get("formulaRecalQty", 0)),
                "calibratedQtyAuto": to_int(row_info.get("calibratedQtyAuto", 0)),
                "calibratedQtyReco": to_int(row_info.get("calibratedQtyReco", 0)),
                "actualOutflow4dFromModel": to_int(row_info.get("actualOutflow4dFromModel", 0)),
                "reservationAnchorQty": to_int(row_info.get("reservationAnchorQty", 0)),
                "alphaRecommended": to_float(row_info.get("modelAlphaRecommended", 0)),
                "modelSource": row_info.get("modelSource", ""),
                "rule": "최종 모델 v6 calibrated_qty_reco 합계 (model_qty × 운영 α 1.15, 미존재 시 센터별 INITIAL_ORD_QTY 합계)",
            },
            "productInfo": product_info,
            "forwardPrediction": {
                "itemCode": item_code,
                "itemName": row_info.get("itemName", ""),
                "reservationQty": to_int(forward_summary.get("reservationQty", 0)),
                "recommendedQty": to_int(forward_summary.get("recommendedQty", 0)),
                "recommendedBox": (
                    round(to_int(forward_summary.get("recommendedQty", 0)) / max(to_int(row_info.get("boxUnitEa") or row_info.get("lduEa") or 1), 1))
                    if to_int(forward_summary.get("recommendedQty", 0)) > 0
                    else 0
                ),
                "predictedStores": to_int(forward_summary.get("predictedStores", 0)),
                "lifecycleDemandUpper": to_int(forward_summary.get("lifecycleDemandUpper", 0)),
                "centerCount": to_int(forward_summary.get("centerCount", 0)) or len(forward_centers),
                "centers": forward_centers,
                "source": forward_summary.get("source", ""),
            },
        }

    detail_rows = [r for r in rows if r["rowKey"] in item_details]
    for r in detail_rows:
        detail = item_details[r["rowKey"]]
        reservation_series = [to_int(p.get("qty", 0)) for p in detail.get("reservationPreRelease", [])]
        reservation_total = sum(reservation_series)
        reservation_initial = sum(reservation_series[:4])
        frontload_ratio = round((reservation_initial / reservation_total) * 100, 1) if reservation_total > 0 else 0.0
        candidates = []
        for p in detail_rows:
            if p["rowKey"] == r["rowKey"]:
                continue
            if (p.get("releaseDate") or "") >= (r.get("releaseDate") or ""):
                continue
            same_sub = p.get("categorySub") == r.get("categorySub")
            same_mid = p.get("categoryMid") == r.get("categoryMid")
            same_major = p.get("category") == r.get("category")
            if not (same_sub or same_mid or same_major):
                continue
            p_detail = item_details.get(p["rowKey"], {})
            p_series = [to_int(x.get("qty", 0)) for x in p_detail.get("reservationPreRelease", [])]
            trend_score = reservation_similarity(reservation_series, p_series)
            category_score = 30 if same_sub else 20 if same_mid else 8
            score = round(trend_score * 0.7 + category_score, 1)
            candidates.append(
                {
                    "rowKey": p["rowKey"],
                    "itemCode": p["itemCode"],
                    "itemName": p["itemName"],
                    "releaseDate": p["releaseDate"],
                    "categoryMid": p.get("categoryMid", "기타"),
                    "categorySub": p.get("categorySub", "기타"),
                    "actualOrderQty": to_int(p.get("actualInitialQty", p.get("recommendQty", 0))),
                    "adequacyRate": to_float(p.get("orderAdequacyRate", 0)),
                    "outflowQty": to_int(p.get("actualOutflow7d", 0)),
                    "trendSimilarity": trend_score,
                    "score": score,
                    "reason": "동일 소분류+예약추세" if same_sub else "동일 중분류+예약추세" if same_mid else "동일 대분류+예약추세",
                }
            )
        candidates.sort(key=lambda x: (x["score"], x["releaseDate"]), reverse=True)
        similar = candidates[:6]
        similar_avg_order = round(sum(x["actualOrderQty"] for x in similar) / len(similar)) if similar else 0
        similar_avg_rate = round(sum(x["adequacyRate"] for x in similar) / len(similar), 1) if similar else 0.0
        detail["similarProducts"] = similar
        detail["recommendationEvidence"] = {
            "reservationDecisionSum": reservation_total,
            "reservationInitial4Sum": reservation_initial,
            "frontloadRatio": frontload_ratio,
            "similarAvgOrderQty": similar_avg_order,
            "similarAvgAdequacyRate": similar_avg_rate,
            "modelRule": "예약주문 앵커와 상품/센터/이슈/가격·마진 피처를 사용한 최종 모델 v6 운영 추천량",
            "mdInterpretation": [
                "예약주문 총량은 기본 수요 크기를 설명합니다.",
                "초기 4일 집중도는 출시 전 관심이 빠르게 몰렸는지 판단하는 신호입니다.",
                "동일 분류와 예약추세가 비슷한 과거 상품의 실제 초도/적정 비율을 함께 비교합니다.",
                "과자는 출시일 포함 4일 실출고를 적정 출고량으로 두고 1.0~1.4배를 정상 범위로 봅니다.",
            ],
        }

    weekly_row_keys = {r["rowKey"] for r in weekly_rows}
    past_rows = [r for r in rows if r["rowKey"] not in weekly_row_keys]
    past_rows.sort(key=lambda x: (x["releaseDate"], x["recommendQty"]), reverse=True)
    past_rows = [
        {
            "rowKey": r["rowKey"],
            "releaseDate": r["releaseDate"],
            "itemCode": r["itemCode"],
            "itemName": r["itemName"],
            "category": r["category"],
            "categoryMid": r.get("categoryMid", "기타"),
            "categorySub": r.get("categorySub", "기타"),
            "boxUnitEa": r.get("boxUnitEa", r.get("lduEa", 1)),
            "lduEa": r.get("lduEa", 1),
            "minOrdQty": r.get("minOrdQty", 1),
            "goalIntroRate": r.get("goalIntroRate", 0),
            "actualOrderQty": r.get("actualInitialQty", r["recommendQty"]),
            "salesRate": r.get("orderAdequacyRate", 0),
            "actualOutflowRate": r.get("actualOutflowRate7d", 0),
            "outflowRate": r.get("actualOutflowRate7d", 0),
            "salesDepletionRate": r.get("salesDepletionRate", 0),
            "actualOutflow7d": r.get("actualOutflow7d", 0),
            "appropriateOutflowQty": r.get("appropriateOutflowQty", 0),
            "actualStoreSalesQty": r.get("actualStoreSalesQty", 0),
            "actualStoreSalesAmount": r.get("actualStoreSalesAmount", 0),
            "storeSalesToOutflowRate": r.get("storeSalesToOutflowRate", 0),
            "salesDepletionHorizonDays": SALES_DEPLETION_HORIZON_DAYS,
            "outflowHorizonDays": r.get("outflowHorizonDays", 4),
            "actualDataReason": r.get("actualDataReason", ""),
        }
        for r in past_rows
    ]

    total_recommend = sum(r["recommendQty"] for r in weekly_rows)
    avg_sales_rate = round(sum(r["salesRate"] for r in weekly_rows) / max(len(weekly_rows), 1), 1)
    risk_item_count = sum(1 for r in weekly_rows if r.get("salesRate", 0) < 100 or r.get("salesRate", 0) > 140)

    release_dates = sorted({r["releaseDate"] for r in rows}, reverse=True)

    payload = {
        "generatedAt": datetime.now().isoformat(),
        "latestReleaseDate": format_date(latest_ymd),
        "decisionDate": TODAY_DECISION_DATE,
        "releaseDates": release_dates,
        "kpis": {
            "newItemCount": len({r["itemCode"] for r in weekly_rows}),
            "totalRecommendQty": total_recommend,
            "avgSalesRate": avg_sales_rate,
            "riskItemCount": risk_item_count,
        },
        "categories": ["전체"] + sorted(categories),
        "categoriesMid": ["전체"] + sorted(categories_mid),
        "categoriesSub": ["전체"] + sorted(categories_sub),
        "dataSources": {
            "preorder": str(source),
            "actualCenterFlow": [str(p) for p in CENTER_FLOW_CANDIDATES if p.exists()],
            "actualCenterFlowDefinition": "A4-1_CENT_RCDB(LR11): CUST_WARH_QTY=센터 실입고, STR_RLE_QTY=점포 실출고",
            "stockFallback": [str(p) for p in CENTER_STK_CANDIDATES if p.exists()],
            "newItemInfo": [str(p) for p in NEW_ITEM_INFO_CANDIDATES if p.exists()],
            "newItemInfoDefinition": "신상품정보서 GOAL_INTRO_RT를 목표도입률 보강 소스로 사용",
            "storeSales": [str(p) for p in store_sales_sources if p.exists()],
            "storeSalesCache": str(STORE_SALE_CACHE) if STORE_SALE_CACHE.exists() else "",
            "storeSalesDefinition": "A3_STORE_SALE/A5_A6_NEW_ITEM_SALE: SALE_QTY/SALE_AMT_VAT를 상품코드+일자(+가능 시 센터)로 캐시 집계",
            "modelPrediction": str(resolve_first_existing(FINAL_MODEL_PREDICTION_CANDIDATES)) if any(p.exists() for p in FINAL_MODEL_PREDICTION_CANDIDATES) else str(PREDICTIONS_CSV),
        },
        "allRows": rows,
        "weeklyRows": weekly_rows,
        "pastRows": past_rows,
        "itemDetails": item_details,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"source={source}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
