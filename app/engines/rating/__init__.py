from app.engines.rating.base import RatingContext, RatingDelta, RatingEngine
from app.engines.rating.elo_v1 import EloRatingEngine

ENGINES: dict[str, type[RatingEngine]] = {
    "elo_v1": EloRatingEngine,
}


def get_active_engine() -> RatingEngine:
    from app.core.config import settings

    engine_class = ENGINES.get(settings.RATING_ENGINE)
    if engine_class is None:
        raise RuntimeError(
            f"Unknown rating engine: '{settings.RATING_ENGINE}'. Available: {list(ENGINES)}"
        )
    return engine_class()


__all__ = ["RatingContext", "RatingDelta", "RatingEngine", "EloRatingEngine", "ENGINES", "get_active_engine"]
