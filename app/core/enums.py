from enum import Enum


class Sport(str, Enum):
    SOCCER = "soccer"
    BASKETBALL = "basketball"
    PADEL = "padel"
    TENNIS = "tennis"


class MatchStatus(str, Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchFormat(str, Enum):
    PICKUP = "pickup"
    SCRIMMAGE = "scrimmage"
    LEAGUE_GAME = "league_game"
    TRAINING = "training"


class RatingSourceType(str, Enum):
    MATCH_RESULT = "match_result"
    PEER_REVIEW = "peer_review"
    VIDEO_ANALYSIS = "video_analysis"
    COACH_ASSESSMENT = "coach_assessment"


class CourtSurface(str, Enum):
    HARDWOOD = "hardwood"
    ASPHALT = "asphalt"
    SYNTHETIC_GRASS = "synthetic_grass"
    CONCRETE = "concrete"


class CourtCondition(str, Enum):
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CLOSED = "closed"


class FilmingProvider(str, Enum):
    PIXELLOT = "pixellot"
    MANUAL_UPLOAD = "manual_upload"
    VEO = "veo"


class MediaProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class UserRole(str, Enum):
    PLAYER = "player"
    FACILITY_MANAGER = "facility_manager"
    COACH = "coach"
    ADMIN = "admin"
