"""Initial schema — all SportOut V1 tables

Revision ID: 3f8a1c9b27e4
Revises:
Create Date: 2026-04-16

Table creation order respects FK dependencies:
  users → facilities → courts
       → players → player_follows
                 → sport_profiles
  facilities/courts/players → matches → match_rosters → player_game_stats
                                      → match_result_confirmations
                                      → availability_slots
                             → rating_events
                             → peer_reviews
                             → media_sessions → highlights
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision: str = "3f8a1c9b27e4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS is required for Geometry columns
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="player"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── facilities ───────────────────────────────────────────────────────────
    op.create_table(
        "facilities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("manager_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("location", Geometry("POINT", srid=4326), nullable=False),
        sa.Column("address_street", sa.String(200), nullable=False),
        sa.Column("address_city", sa.String(100), nullable=False),
        sa.Column("address_country", sa.String(3), nullable=False, server_default="IL"),
        sa.Column("sports_supported", ARRAY(sa.String(32)), server_default="{}"),
        sa.Column("opens_at", sa.Time(timezone=False), nullable=True),
        sa.Column("closes_at", sa.Time(timezone=False), nullable=True),
        sa.Column("operating_days", ARRAY(sa.Integer()), server_default="{}"),
        sa.Column("amenities", JSONB(), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_facilities_name", "facilities", ["name"])
    op.create_index("ix_facilities_location", "facilities", ["location"], postgresql_using="gist")

    # ── courts ───────────────────────────────────────────────────────────────
    op.create_table(
        "courts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("facility_id", UUID(as_uuid=True), sa.ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("surface", sa.String(32), nullable=False, server_default="asphalt"),
        sa.Column("indoor", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("lighting_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("lighting_on", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_occupancy", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_capacity", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("condition", sa.String(32), nullable=False, server_default="good"),
        sa.Column("condition_note", sa.String(300), nullable=True),
        sa.Column("is_bookable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_courts_facility_id", "courts", ["facility_id"])

    # ── players ──────────────────────────────────────────────────────────────
    op.create_table(
        "players",
        sa.Column("id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("banner_url", sa.String(512), nullable=True),
        sa.Column("bio", sa.String(500), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("location", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("card_is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("follower_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("following_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_players_display_name", "players", ["display_name"])
    op.create_index("ix_players_username", "players", ["username"], unique=True)

    # ── player_follows ────────────────────────────────────────────────────────
    op.create_table(
        "player_follows",
        sa.Column("follower_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("followed_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("follower_id", "followed_id", name="uq_follow_pair"),
    )

    # ── sport_profiles ────────────────────────────────────────────────────────
    op.create_table(
        "sport_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("player_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("primary_position", sa.String(32), nullable=True),
        sa.Column("secondary_positions", ARRAY(sa.String(32)), server_default="{}"),
        sa.Column("current_rating", sa.Float(), nullable=False, server_default="1000.0"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("career_games", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("career_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("player_id", "sport", name="uq_sport_profiles_player_sport"),
    )
    op.create_index("ix_sport_profiles_player_id", "sport_profiles", ["player_id"])
    op.create_index("ix_sport_profiles_current_rating", "sport_profiles", ["current_rating"])
    op.create_index("ix_sport_profiles_sport_rating", "sport_profiles", ["sport", "current_rating"])

    # ── matches ───────────────────────────────────────────────────────────────
    op.create_table(
        "matches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("facility_id", UUID(as_uuid=True), sa.ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("court_id", UUID(as_uuid=True), sa.ForeignKey("courts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("format", sa.String(32), nullable=False, server_default="pickup"),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("min_rating", sa.Float(), nullable=True),
        sa.Column("max_rating", sa.Float(), nullable=True),
        sa.Column("max_players", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("mvp_player_id", UUID(as_uuid=True), nullable=True),
        sa.Column("result_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_matches_sport", "matches", ["sport"])
    op.create_index("ix_matches_status", "matches", ["status"])
    op.create_index("ix_matches_scheduled_at", "matches", ["scheduled_at"])
    op.create_index("ix_matches_sport_status_scheduled", "matches", ["sport", "status", "scheduled_at"])

    # ── match_rosters ─────────────────────────────────────────────────────────
    op.create_table(
        "match_rosters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("player_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team", sa.String(10), nullable=False, server_default="none"),
        sa.Column("confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attended", sa.Boolean(), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("match_id", "player_id", name="uq_match_rosters_match_player"),
    )
    op.create_index("ix_match_rosters_match_id", "match_rosters", ["match_id"])
    op.create_index("ix_match_rosters_player_id", "match_rosters", ["player_id"])

    # ── match_result_confirmations ────────────────────────────────────────────
    op.create_table(
        "match_result_confirmations",
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("player_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("match_id", "player_id", name="uq_result_confirmation_match_player"),
    )

    # ── player_game_stats ─────────────────────────────────────────────────────
    op.create_table(
        "player_game_stats",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("match_roster_id", UUID(as_uuid=True), sa.ForeignKey("match_rosters.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("stats", JSONB(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── availability_slots ────────────────────────────────────────────────────
    op.create_table(
        "availability_slots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("court_id", UUID(as_uuid=True), sa.ForeignKey("courts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_booked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("booked_by_match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_availability_slots_court_id", "availability_slots", ["court_id"])
    op.create_index("ix_availability_slots_starts_at", "availability_slots", ["starts_at"])
    op.create_index("ix_availability_slots_court_start", "availability_slots", ["court_id", "starts_at"])

    # ── rating_events ─────────────────────────────────────────────────────────
    op.create_table(
        "rating_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("player_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rating_before", sa.Float(), nullable=False),
        sa.Column("rating_after", sa.Float(), nullable=False),
        sa.Column("delta", sa.Float(), nullable=False),
        sa.Column("algorithm_version", sa.String(32), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=False),
        sa.Column("breakdown", JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rating_events_player_id", "rating_events", ["player_id"])
    op.create_index("ix_rating_events_sport", "rating_events", ["sport"])
    op.create_index("ix_rating_events_created_at", "rating_events", ["created_at"])
    op.create_index("ix_rating_events_player_sport_created", "rating_events", ["player_id", "sport", "created_at"])

    # ── peer_reviews ──────────────────────────────────────────────────────────
    op.create_table(
        "peer_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("reviewer_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewed_player_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ratings", JSONB(), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("reviewer_id", "reviewed_player_id", "match_id", name="uq_peer_review_per_match"),
    )
    op.create_index("ix_peer_reviews_reviewer_id", "peer_reviews", ["reviewer_id"])
    op.create_index("ix_peer_reviews_reviewed_player_id", "peer_reviews", ["reviewed_player_id"])
    op.create_index("ix_peer_reviews_match_id", "peer_reviews", ["match_id"])

    # ── media_sessions ────────────────────────────────────────────────────────
    op.create_table(
        "media_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("raw_footage_url", sa.String(512), nullable=True),
        sa.Column("processing_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("video_metrics", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── highlights ────────────────────────────────────────────────────────────
    op.create_table(
        "highlights",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("media_session_id", UUID(as_uuid=True), sa.ForeignKey("media_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("player_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("event_tags", ARRAY(sa.String(50)), server_default="{}"),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_highlights_player_id", "highlights", ["player_id"])
    op.create_index("ix_highlights_match_id", "highlights", ["match_id"])
    op.create_index("ix_highlights_generated_at", "highlights", ["generated_at"])


def downgrade() -> None:
    op.drop_table("highlights")
    op.drop_table("media_sessions")
    op.drop_table("peer_reviews")
    op.drop_table("rating_events")
    op.drop_table("availability_slots")
    op.drop_table("player_game_stats")
    op.drop_table("match_result_confirmations")
    op.drop_table("match_rosters")
    op.drop_table("matches")
    op.drop_table("sport_profiles")
    op.drop_table("player_follows")
    op.drop_table("players")
    op.drop_table("courts")
    op.drop_table("facilities")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS postgis")
