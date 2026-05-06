import pytest

from src.eval.tournament import rank_methods, beats_baseline


def test_rank_orders_by_cos_desc():
    records = {
        "none":           {"cos_mean": 0.50, "rmse_mean": 0.10},
        "volcano_scan":   {"cos_mean": 0.65, "rmse_mean": 0.08},
        "beer_lambert":   {"cos_mean": 0.85, "rmse_mean": 0.05},
        "lambert_albedo": {"cos_mean": 0.75, "rmse_mean": 0.06},
    }
    ranked = rank_methods(records)
    methods = [r["method"] for r in ranked]
    assert methods == ["beer_lambert", "lambert_albedo", "volcano_scan", "none"]
    assert ranked[0]["rank"] == 1
    assert ranked[-1]["rank"] == 4


def test_rank_tie_break_by_rmse():
    records = {
        "a": {"cos_mean": 0.7, "rmse_mean": 0.05},
        "b": {"cos_mean": 0.7, "rmse_mean": 0.10},
    }
    ranked = rank_methods(records)
    assert ranked[0]["method"] == "a"


def test_beats_baseline_returns_winners():
    records = {
        "none":         {"cos_mean": 0.50, "rmse_mean": 0.10},
        "beer_lambert": {"cos_mean": 0.80, "rmse_mean": 0.05},
        "volcano_scan": {"cos_mean": 0.40, "rmse_mean": 0.12},
    }
    winners = beats_baseline(records, baseline="none")
    assert "beer_lambert" in winners
    assert "volcano_scan" not in winners


def test_beats_baseline_unknown_raises():
    records = {"a": {"cos_mean": 0.5, "rmse_mean": 0.1}}
    with pytest.raises(KeyError):
        beats_baseline(records, baseline="missing")
