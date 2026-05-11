from pydantic import BaseModel

from app.core.enums import Sport
from app.sports.basketball import BasketballGameStats
from app.sports.padel import PadelGameStats
from app.sports.soccer import SoccerGameStats
from app.sports.tennis import TennisGameStats

# New sports are added by registering a schema here — no DB migration needed
STAT_SCHEMAS: dict[Sport, type[BaseModel]] = {
    Sport.SOCCER: SoccerGameStats,
    Sport.BASKETBALL: BasketballGameStats,
    Sport.PADEL: PadelGameStats,
    Sport.TENNIS: TennisGameStats,
}


def validate_game_stats(sport: Sport, raw: dict) -> BaseModel:
    """Parse and validate a raw stats dict against the registered schema for the given sport.

    Raises ValueError if sport has no registered schema.
    Raises pydantic.ValidationError if the stats dict fails schema validation.
    """
    schema = STAT_SCHEMAS.get(sport)
    if schema is None:
        raise ValueError(f"No stat schema registered for sport '{sport}'. Available: {list(STAT_SCHEMAS)}")
    return schema.model_validate(raw)
