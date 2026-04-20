from app.core.enums import MatchFormat
from app.engines.rating.base import RatingContext, RatingDelta, RatingEngine

# Competitive games affect ratings more than casual ones
_FORMAT_WEIGHTS: dict[str, float] = {
    MatchFormat.LEAGUE_GAME: 1.2,
    MatchFormat.SCRIMMAGE: 1.0,
    MatchFormat.PICKUP: 0.8,
    MatchFormat.TRAINING: 0.4,
}

_BASE_K = 32.0
_PEER_REVIEW_WEIGHT = 0.15  # max ± contribution from peer review aggregate
_PEER_REVIEW_NEUTRAL = 3.0  # midpoint on 1–5 scale


class EloRatingEngine(RatingEngine):
    @property
    def version(self) -> str:
        return "elo_v1"

    def compute(self, context: RatingContext) -> RatingDelta:
        expected = self._expected_score(context.current_rating, context.opponent_avg_rating)
        actual = self._actual_score(context.match_result)
        format_weight = _FORMAT_WEIGHTS.get(context.match_format, 1.0)

        match_delta = _BASE_K * format_weight * (actual - expected)

        peer_delta = 0.0
        if context.peer_review_score is not None:
            peer_delta = _PEER_REVIEW_WEIGHT * (context.peer_review_score - _PEER_REVIEW_NEUTRAL)

        total_delta = round(match_delta + peer_delta, 4)
        new_rating = max(0.0, round(context.current_rating + total_delta, 4))

        return RatingDelta(
            delta=total_delta,
            new_rating=new_rating,
            algorithm_version=self.version,
            breakdown={
                "match_delta": round(match_delta, 4),
                "peer_delta": round(peer_delta, 4),
                "format_weight": format_weight,
                "expected_score": round(expected, 4),
                "actual_score": actual,
            },
        )

    @staticmethod
    def _expected_score(rating: float, opponent_rating: float) -> float:
        return 1 / (1 + 10 ** ((opponent_rating - rating) / 400))

    @staticmethod
    def _actual_score(result: str) -> float:
        return {"win": 1.0, "draw": 0.5, "loss": 0.0}.get(result, 0.5)
