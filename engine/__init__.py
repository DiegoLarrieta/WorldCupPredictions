"""WorldCup prediction engine — the single, validated source of truth.

Public API:
    from engine import predict_match, save_match

Every match folder calls this so all predictions use identical, validated logic
(no per-match drift). The validated model is the Elo + Dixon-Coles ensemble; new
models plug in behind models/base.PredictiveModel, new signals only go live after
passing the validation harness.
"""

from engine.predict import predict_match, save_match  # noqa: F401

__all__ = ["predict_match", "save_match"]
