"""Method ranking by anchor consistency (cosine sim primary, RMSE tie-break)."""
from __future__ import annotations


def rank_methods(records: dict) -> list:
    """records: {method_name: {cos_mean, rmse_mean, ...}}.
    Returns list of methods sorted from best to worst by (cos_mean ↓, rmse_mean ↑).
    """
    items = list(records.items())
    items.sort(key=lambda kv: (-(kv[1]["cos_mean"]), kv[1]["rmse_mean"]))
    return [{"method": m, "cos_mean": d["cos_mean"], "rmse_mean": d["rmse_mean"], "rank": i + 1}
            for i, (m, d) in enumerate(items)]


def beats_baseline(records: dict, baseline: str = "none") -> list:
    """Return methods whose cosine_mean strictly exceeds baseline's."""
    if baseline not in records:
        raise KeyError(f"baseline {baseline!r} not in records")
    base_cos = records[baseline]["cos_mean"]
    winners = []
    for m, d in records.items():
        if m == baseline:
            continue
        if d["cos_mean"] > base_cos:
            winners.append(m)
    return winners
