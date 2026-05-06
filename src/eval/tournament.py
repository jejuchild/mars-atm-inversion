"""Method ranking by anchor consistency (cosine sim primary, RMSE tie-break)."""
from __future__ import annotations


def rank_methods(records: dict) -> list:
    """records: {method_name: {cos_mean, rmse_mean, ...}}.

    Returns list of methods sorted from best to worst by (rmse_mean ↑, cos_mean ↓).
    RMSE primary because cosine similarity is invariant to multiplicative scaling
    (= atmospheric attenuation in Beer-Lambert), so cosine alone fails to detect
    a missing correction.
    """
    items = list(records.items())
    items.sort(key=lambda kv: (kv[1]["rmse_mean"], -(kv[1]["cos_mean"])))
    return [{"method": m, "cos_mean": d["cos_mean"], "rmse_mean": d["rmse_mean"], "rank": i + 1}
            for i, (m, d) in enumerate(items)]


def beats_baseline(records: dict, baseline: str = "none") -> list:
    """Return methods whose RMSE is strictly lower than baseline's."""
    if baseline not in records:
        raise KeyError(f"baseline {baseline!r} not in records")
    base_rmse = records[baseline]["rmse_mean"]
    winners = []
    for m, d in records.items():
        if m == baseline:
            continue
        if d["rmse_mean"] < base_rmse:
            winners.append(m)
    return winners
