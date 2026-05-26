from __future__ import annotations

import csv
import json
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
ITEM_DV_INFO = Path(
    "/Users/geonhokim/Desktop/세븐일레븐 내부데이터/B조/B4_ITEM_DV_INFO.csv"
)
CENTER_STK_CANDIDATES = [
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/A4_CENTER_STK.csv"),
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/A4_CENTER_STK_2024(LR11).csv"),
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/데이터(원본)/A4_CENTER_STK_(MD1302).csv"),
    Path("/Users/geonhokim/Desktop/세븐일레븐 내부데이터/중간발표까지/중간발표/NEWSeven-main-2/A4_final_CENTER_STK.csv"),
    ROOT / "public" / "data" / "A4_final_CENTER_STK.csv",
]
CENTER_WEIGHT_CSV = Path(
    "/Users/geonhokim/Desktop/세븐일레븐 내부데이터/중간발표까지/중간발표/NEWSeven-main-2/asymmetric_recommended_W.csv"
)


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


def risk_from_rate(rate: float) -> str:
    if rate < 50:
        return "과발주"
    if rate <= 100:
        return "정상"
    return "결품위험"


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


def load_ml_prediction_map() -> dict[tuple[str, str], dict]:
    predictions = resolve_first_existing(PREDICTIONS_CANDIDATES)
    if pd is None or not predictions.exists():
        grouped_csv: dict[tuple[str, str], dict[str, float]] = defaultdict(
            lambda: {"ML_PRED_QTY": 0.0, "OUTFLOW_7D": 0.0, "FORMULA_QTY": 0.0}
        )
        if not PREDICTIONS_CSV.exists():
            return {}
        with PREDICTIONS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
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
                "predictedOutflow7d": int(round(v["OUTFLOW_7D"])),
                "formulaQtyFromModelTable": int(round(v["FORMULA_QTY"])),
            }
            for k, v in grouped_csv.items()
        }
    try:
        pred = pd.read_parquet(predictions)
    except Exception:
        grouped_csv: dict[tuple[str, str], dict[str, float]] = defaultdict(
            lambda: {"ML_PRED_QTY": 0.0, "OUTFLOW_7D": 0.0, "FORMULA_QTY": 0.0}
        )
        if not PREDICTIONS_CSV.exists():
            return {}
        with PREDICTIONS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
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
                "predictedOutflow7d": int(round(v["OUTFLOW_7D"])),
                "formulaQtyFromModelTable": int(round(v["FORMULA_QTY"])),
            }
            for k, v in grouped_csv.items()
        }

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
            "predictedOutflow7d": int(round(r["OUTFLOW_7D"])),
            "formulaQtyFromModelTable": int(round(r["FORMULA_QTY"])),
        }
        for _, r in grouped.iterrows()
    }


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


def load_center_stock_map() -> dict[tuple[str, str], dict[str, int]]:
    """
    key: (item_code, center_code) -> {yyyymmdd: book_end_qty}
    """
    out: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    center_stk = resolve_first_existing(CENTER_STK_CANDIDATES)
    if not center_stk.exists():
        return out
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


def compute_initial_and_outflow_7d(
    stock_by_day: dict[str, int],
    release_ymd: str,
) -> tuple[int, int]:
    """
    - initial_qty: 출시일까지 일자별 재고 증가분 합
    - outflow_7d: 출시일 재고 - 출시+7일 재고 (순감소량, 음수면 0)
    """
    rel = parse_date_yyyymmdd(release_ymd)
    if rel is None or not stock_by_day:
        return 0, 0
    release_key = rel.strftime("%Y%m%d")
    d7_key = (rel + timedelta(days=7)).strftime("%Y%m%d")

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
    end7_stock = to_int(stock_by_day.get(d7_key, release_stock))
    outflow_7d = max(release_stock - end7_stock, 0)
    return initial, outflow_7d


def compute_post_release_outflow_series_7d(stock_by_day: dict[str, int], release_ymd: str) -> list[dict]:
    rel = parse_date_yyyymmdd(release_ymd)
    if rel is None:
        return []
    prev_stock = to_int(stock_by_day.get(release_ymd, 0))
    out = []
    # release+1 ~ release+7 구간의 일자별 순출고를 누적 7일 합과 동일 기준으로 계산
    for i in range(1, 8):
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
    center_weight_map = load_center_weight_map()
    item_category_map = load_item_category_map()
    center_stock_map = load_center_stock_map()
    grouped: dict[tuple[str, str], dict] = {}
    row_centers: dict[tuple[str, str], set[str]] = defaultdict(set)
    center_name_by_code: dict[str, str] = {}
    categories = set()
    categories_mid = set()
    categories_sub = set()
    latest_ymd = ""

    with source.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ymd = (row.get("NP_RLSE_YMD") or "").strip()
            if ymd > latest_ymd:
                latest_ymd = ymd

            item_code = (row.get("ITEM_CODE") or "").strip()
            item_name = (row.get("ITEM_NM") or "").strip()
            lms = item_category_map.get(item_code)
            category = (lms[0] if lms else (row.get("ITEM_MDDV_NM") or "").strip()) or "기타"
            category_mid = (lms[1] if lms else (row.get("ITEM_MDDV_NM") or "").strip()) or "기타"
            category_sub = (lms[2] if lms else (row.get("ITEM_SMDV_NM") or "").strip()) or "기타"
            categories.add(category)
            categories_mid.add(category_mid)
            categories_sub.add(category_sub)
            key = (item_code, ymd)

            if key not in grouped:
                release_date = format_date(ymd)
                try:
                    start_dt = parse_date_yyyymmdd(row.get("PRE_D11", "")) or (
                        datetime.strptime(release_date, "%Y-%m-%d") - timedelta(days=11)
                    )
                    deadline = (start_dt + timedelta(days=3)).strftime("%Y-%m-%d")
                except Exception:
                    deadline = release_date
                grouped[key] = {
                    "rowKey": f"{item_code}_{release_date}",
                    "itemCode": item_code,
                    "itemName": item_name,
                    "category": category,
                    "categoryMid": category_mid,
                    "categorySub": category_sub,
                    "lduEa": max(to_int(row.get("MIN_ORD_QTY", "0")), 1),
                    "price": to_int(row.get("ST_SLEM_AMT", "0")),
                    "recommendQty": 0,
                    "mlRecommendQty": 0,
                    "predictedOutflow7d": 0,
                    "formulaQtyFromModelTable": 0,
                    "goalIntroRtSum": 0.0,
                    "goalIntroRtCnt": 0,
                    "releaseDate": release_date,
                    "deadlineDate": deadline,
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
                grouped[key]["mlRecommendQty"] = ml_prediction_map[norm_key]["mlRecommendQty"]
                grouped[key]["predictedOutflow7d"] = ml_prediction_map[norm_key]["predictedOutflow7d"]
                grouped[key]["formulaQtyFromModelTable"] = ml_prediction_map[norm_key]["formulaQtyFromModelTable"]

    rows = list(grouped.values())
    for r in rows:
        avg_rate = (r["goalIntroRtSum"] / r["goalIntroRtCnt"]) if r["goalIntroRtCnt"] else 0.0
        model_base_qty = max(r["mlRecommendQty"], 1)
        model_outflow = max(r["predictedOutflow7d"], 0)
        model_rate = (model_outflow / model_base_qty) * 100
        fallback_rate = round(avg_rate * 100, 1) if avg_rate <= 1 else round(avg_rate, 1)
        sales_rate = round(model_rate, 1) if r["mlRecommendQty"] > 0 else fallback_rate
        r["salesRate"] = sales_rate
        r["risk"] = risk_from_rate(sales_rate)
        r["inputQty"] = r["mlRecommendQty"] if r["mlRecommendQty"] > 0 else r["recommendQty"]
        r["formulaQty"] = r["formulaQtyFromModelTable"] if r["formulaQtyFromModelTable"] > 0 else r["recommendQty"]
        item_code = r["itemCode"]
        rel_ymd = normalize_ymd_key(r["releaseDate"].replace("-", ""))
        centers = row_centers.get((item_code, rel_ymd), set())
        initial_sum = 0
        outflow_sum = 0
        for c in centers:
            stock_series = center_stock_map.get((item_code, c), {})
            init_c, out7_c = compute_initial_and_outflow_7d(stock_series, rel_ymd)
            initial_sum += init_c
            outflow_sum += out7_c
        r["actualInitialQty"] = initial_sum
        r["actualOutflow7d"] = outflow_sum
        r["actualOutflowRate7d"] = round((outflow_sum / max(initial_sum, 1)) * 100, 1) if initial_sum > 0 else 0.0
        if initial_sum <= 0:
            if not centers:
                r["actualDataReason"] = "센터 매핑 없음"
            else:
                r["actualDataReason"] = "출시일까지 재고 증가분 미확인"
        else:
            r["actualDataReason"] = ""
        del r["goalIntroRtSum"]
        del r["goalIntroRtCnt"]

    rows.sort(key=lambda x: (x["releaseDate"], x["recommendQty"]), reverse=True)
    row_map = {r["rowKey"]: r for r in rows}
    weekly_rows = [r for r in rows if r["releaseDate"] == format_date(latest_ymd)]
    weekly_rows.sort(key=lambda x: x["recommendQty"], reverse=True)
    weekly_rows = weekly_rows[:80]

    detail_map: dict[str, dict] = defaultdict(lambda: {
        "reservation4d": {"0": 0, "1": 0, "2": 0, "3": 0},
        "reservationPre": {str(i): 0 for i in range(12)},  # D-11 ~ D-0
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
            d["reservationPre"]["0"] += to_int(row.get("D-11", "0"))
            d["reservationPre"]["1"] += to_int(row.get("D-10", "0"))
            d["reservationPre"]["2"] += to_int(row.get("D-9", "0"))
            d["reservationPre"]["3"] += to_int(row.get("D-8", "0"))
            d["reservationPre"]["4"] += to_int(row.get("D-7", "0"))
            d["reservationPre"]["5"] += to_int(row.get("D-6", "0"))
            d["reservationPre"]["6"] += to_int(row.get("D-5", "0"))
            d["reservationPre"]["7"] += to_int(row.get("D-4", "0"))
            d["reservationPre"]["8"] += to_int(row.get("D-3", "0"))
            d["reservationPre"]["9"] += to_int(row.get("D-2", "0"))
            d["reservationPre"]["10"] += to_int(row.get("D-1", "0"))
            d["reservationPre"]["11"] += to_int(row.get("D-0", "0"))
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

    # 예약 시작일(D-11) 수량은 0 이상이어야 함(음수 데이터만 제외)
    valid_row_keys = {
        row_key
        for row_key, detail in detail_map.items()
        if detail["reservation4d"]["0"] >= 0
    }
    rows = [r for r in rows if r["rowKey"] in valid_row_keys]
    weekly_rows = [r for r in rows if r["releaseDate"] == format_date(latest_ymd)]

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
        mapped_center_codes = sorted(row_centers.get((item_code, rel_ymd), set()))
        center_initial_from_stock: list[dict] = []
        for cc in mapped_center_codes:
            stock_series = center_stock_map.get((item_code, cc), {})
            init_c, _ = compute_initial_and_outflow_7d(stock_series, rel_ymd)
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
            if center_code and item_code and rel_ymd:
                stock_series = center_stock_map.get((item_code, center_code), {})
                _, out7_c = compute_initial_and_outflow_7d(stock_series, rel_ymd)
                for p in compute_post_release_outflow_series_7d(stock_series, rel_ymd):
                    post7_agg[p["date"]] += to_int(p["outflow"])
            perf_rate = round((out7_c / max(to_int(q), 1)) * 100, 1) if to_int(q) > 0 else 0.0
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
                "outflowRate7d": perf_rate,
            })
        total_qty = center_total_initial
        ml_total_qty = to_int(row_info.get("mlRecommendQty", 0))
        formula_qty = ml_total_qty if ml_total_qty > 0 else total_qty
        post_release_timeline = [
            {"date": d, "qty": to_int(post7_agg[d])}
            for d in sorted(post7_agg.keys())
        ]
        item_details[row_key] = {
            "reservation4d": reservation4d,
            "reservationPreRelease": reservation_pre,
            "reservationPre4dSum": sum(to_int(x["qty"]) for x in reservation4d),
            "reservationPreTotalSum": sum(to_int(x["qty"]) for x in reservation_pre),
            "centerDistribution": centers,
            "centerPerformance7d": sorted(per_center_perf, key=lambda x: x["outflowRate7d"], reverse=True),
            "postReleaseOutflow7d": post_release_timeline,
            "centerInitialQtySum": center_total_initial,
            "centerOutflow7dSum": center_total_out7,
            "formula": {
                "totalRecommendQty": formula_qty,
                "rule": "ML_PRED_QTY 합계 (미존재 시 센터별 INITIAL_ORD_QTY 합계)",
            },
        }

    past_rows = [r for r in rows if r["releaseDate"] != format_date(latest_ymd)]
    past_rows.sort(key=lambda x: (x["releaseDate"], x["recommendQty"]), reverse=True)
    past_rows = [
        {
            "releaseDate": r["releaseDate"],
            "itemCode": r["itemCode"],
            "itemName": r["itemName"],
            "category": r["category"],
            "categoryMid": r.get("categoryMid", "기타"),
            "categorySub": r.get("categorySub", "기타"),
            "actualOrderQty": r.get("actualInitialQty", r["recommendQty"]),
            "salesRate": r.get("actualOutflowRate7d", r["salesRate"]),
            "actualOutflow7d": r.get("actualOutflow7d", 0),
            "actualDataReason": r.get("actualDataReason", ""),
        }
        for r in past_rows[:120]
    ]

    total_recommend = sum(r["recommendQty"] for r in weekly_rows)
    avg_sales_rate = round(sum(r["salesRate"] for r in weekly_rows) / max(len(weekly_rows), 1), 1)
    risk_item_count = sum(1 for r in weekly_rows if r["salesRate"] < 80)

    release_dates = sorted({r["releaseDate"] for r in rows}, reverse=True)

    payload = {
        "generatedAt": datetime.now().isoformat(),
        "latestReleaseDate": format_date(latest_ymd),
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
