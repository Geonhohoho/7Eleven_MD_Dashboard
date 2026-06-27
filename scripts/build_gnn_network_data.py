from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "data" / "gnn-network.json"

DELIVERABLE = Path("/Users/geonhokim/Desktop/gnn_deliverable_참여점포수.csv")
RESERVATION_LINK = Path("/Users/geonhokim/Desktop/gnn_점포상품_예약연결.csv")
EDGE_LINK = Path("/Users/geonhokim/Desktop/gnn_점포상품_연결(엣지).csv")


def to_int(value: str | float | int) -> int:
    try:
        return int(round(float(str(value or "0").replace(",", ""))))
    except Exception:
        return 0


def to_float(value: str | float | int) -> float:
    try:
        return float(str(value or "0").replace(",", ""))
    except Exception:
        return 0.0


def empty_link_summary() -> dict:
    return {
        "rows": 0,
        "reservationQty": 0.0,
        "orderQty": 0.0,
        "reservedOrderStores": 0,
        "reservedDropStores": 0,
        "nonReservedOrderStores": 0,
        "reservedOrderQty": 0.0,
        "nonReservedOrderQty": 0.0,
        "samples": {
            "reservedOrdered": [],
            "reservedDropped": [],
            "nonReservedOrdered": [],
        },
    }


def add_sample(samples: list[str], store_code: str, limit: int = 6) -> None:
    if store_code and len(samples) < limit:
        samples.append(store_code)


def load_reservation_test() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = defaultdict(empty_link_summary)
    if not RESERVATION_LINK.exists():
        return out

    with RESERVATION_LINK.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("split") != "test":
                continue
            key = ((row.get("ITEM_CODE") or "").strip(), (row.get("CENTER_CODE") or "").strip())
            if not key[0] or not key[1]:
                continue
            bucket = out[key]
            bucket["rows"] += 1
            bucket["reservationQty"] += to_float(row.get("예약수량"))
            if row.get("본발주참여") == "1":
                bucket["reservedOrderStores"] += 1
                bucket["reservedOrderQty"] += to_float(row.get("본발주수량"))
                add_sample(bucket["samples"]["reservedOrdered"], row.get("STORE_CODE", ""))
            else:
                bucket["reservedDropStores"] += 1
                add_sample(bucket["samples"]["reservedDropped"], row.get("STORE_CODE", ""))
    return out


def load_edge_test() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = defaultdict(empty_link_summary)
    if not EDGE_LINK.exists():
        return out

    with EDGE_LINK.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("split") != "test":
                continue
            key = ((row.get("ITEM_CODE") or "").strip(), (row.get("CENTER_CODE") or "").strip())
            if not key[0] or not key[1]:
                continue
            bucket = out[key]
            bucket["rows"] += 1
            bucket["reservationQty"] += to_float(row.get("예약수량"))
            bucket["orderQty"] += to_float(row.get("본발주수량"))
            if row.get("예약여부") == "1" and row.get("본발주참여") == "1":
                bucket["reservedOrderStores"] += 1
                bucket["reservedOrderQty"] += to_float(row.get("본발주수량"))
                add_sample(bucket["samples"]["reservedOrdered"], row.get("STORE_CODE", ""))
            elif row.get("예약여부") == "1" and row.get("본발주참여") != "1":
                bucket["reservedDropStores"] += 1
                add_sample(bucket["samples"]["reservedDropped"], row.get("STORE_CODE", ""))
            elif row.get("예약여부") != "1" and row.get("본발주참여") == "1":
                bucket["nonReservedOrderStores"] += 1
                bucket["nonReservedOrderQty"] += to_float(row.get("본발주수량"))
                add_sample(bucket["samples"]["nonReservedOrdered"], row.get("STORE_CODE", ""))
    return out


def main() -> None:
    if not DELIVERABLE.exists():
        raise FileNotFoundError(DELIVERABLE)

    reservation = load_reservation_test()
    edge = load_edge_test()

    items: dict[str, dict] = {}
    totals = {
        "items": 0,
        "centers": 0,
        "reservationStores": 0,
        "actualStores": 0,
        "predictedStores": 0,
        "reservedOrderStores": 0,
        "nonReservedOrderStores": 0,
        "reservedDropStores": 0,
        "orderQty": 0,
    }
    centers_seen: set[str] = set()

    with DELIVERABLE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_code = (row.get("ITEM_CODE") or "").strip()
            center_code = (row.get("CENTER_CODE") or "").strip()
            if not item_code or not center_code:
                continue

            key = (item_code, center_code)
            edge_summary = edge.get(key, empty_link_summary())
            reservation_summary = reservation.get(key, empty_link_summary())

            reservation_stores = to_int(row.get("예약점포수"))
            actual_stores = to_int(row.get("실제참여점포수(정답)"))
            predicted_stores = to_int(row.get("GNN예측(확장마진포함)"))
            raw_pred = to_float(row.get("GNN예측(raw)"))
            expansion_margin = to_int(row.get("확장마진_추가분"))
            reserved_order = int(edge_summary["reservedOrderStores"] or reservation_summary["reservedOrderStores"])
            reserved_drop = int(edge_summary["reservedDropStores"] or reservation_summary["reservedDropStores"])
            non_reserved_order = max(0, int(edge_summary["nonReservedOrderStores"]))
            order_qty = int(round(edge_summary["orderQty"]))

            item = items.setdefault(
                item_code,
                {
                    "itemCode": item_code,
                    "itemName": row.get("상품명") or item_code,
                    "summary": {
                        "reservationStores": 0,
                        "actualStores": 0,
                        "predictedStores": 0,
                        "rawPredictedStores": 0.0,
                        "expansionMargin": 0,
                        "reservedOrderStores": 0,
                        "reservedDropStores": 0,
                        "nonReservedOrderStores": 0,
                        "reservationQty": 0,
                        "orderQty": 0,
                    },
                    "centers": [],
                },
            )

            item["centers"].append(
                {
                    "centerCode": center_code,
                    "centerName": row.get("센터명") or center_code,
                    "reservationStores": reservation_stores,
                    "actualStores": actual_stores,
                    "predictedStores": predicted_stores,
                    "rawPredictedStores": round(raw_pred, 2),
                    "expansionMargin": expansion_margin,
                    "reservedOrderStores": reserved_order,
                    "reservedDropStores": reserved_drop,
                    "nonReservedOrderStores": non_reserved_order,
                    "reservationQty": int(round(edge_summary["reservationQty"] or reservation_summary["reservationQty"])),
                    "reservedOrderQty": int(round(edge_summary["reservedOrderQty"] or reservation_summary["reservedOrderQty"])),
                    "nonReservedOrderQty": int(round(edge_summary["nonReservedOrderQty"])),
                    "orderQty": order_qty,
                    "predictionError": predicted_stores - actual_stores,
                    "predictionRatio": round(predicted_stores / actual_stores, 3) if actual_stores else 0,
                    "reservationToActualMultiplier": round(actual_stores / reservation_stores, 2) if reservation_stores else 0,
                    "samples": edge_summary["samples"],
                }
            )

            summary = item["summary"]
            summary["reservationStores"] += reservation_stores
            summary["actualStores"] += actual_stores
            summary["predictedStores"] += predicted_stores
            summary["rawPredictedStores"] += raw_pred
            summary["expansionMargin"] += expansion_margin
            summary["reservedOrderStores"] += reserved_order
            summary["reservedDropStores"] += reserved_drop
            summary["nonReservedOrderStores"] += non_reserved_order
            summary["reservationQty"] += int(round(edge_summary["reservationQty"] or reservation_summary["reservationQty"]))
            summary["orderQty"] += order_qty
            centers_seen.add(center_code)

    for item in items.values():
        s = item["summary"]
        s["rawPredictedStores"] = round(s["rawPredictedStores"], 1)
        s["predictionError"] = s["predictedStores"] - s["actualStores"]
        s["predictionRatio"] = round(s["predictedStores"] / s["actualStores"], 3) if s["actualStores"] else 0
        s["reservationToActualMultiplier"] = round(s["actualStores"] / s["reservationStores"], 2) if s["reservationStores"] else 0
        s["nonReservedShare"] = round(s["nonReservedOrderStores"] / s["actualStores"] * 100, 1) if s["actualStores"] else 0
        item["centers"].sort(key=lambda x: x["actualStores"], reverse=True)

    item_list = sorted(items.values(), key=lambda x: x["summary"]["actualStores"], reverse=True)
    totals["items"] = len(item_list)
    totals["centers"] = len(centers_seen)
    for item in item_list:
        for key in [
            "reservationStores",
            "actualStores",
            "predictedStores",
            "reservedOrderStores",
            "nonReservedOrderStores",
            "reservedDropStores",
            "orderQty",
        ]:
            totals[key] += int(item["summary"].get(key, 0))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generatedAt": datetime.now().isoformat(timespec="seconds"),
                "sourceFiles": {
                    "deliverable": str(DELIVERABLE),
                    "reservationLink": str(RESERVATION_LINK),
                    "edgeLink": str(EDGE_LINK),
                },
                "totals": totals,
                "items": item_list,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print(f"Wrote {OUT} with {len(item_list)} items")


if __name__ == "__main__":
    main()
