# SportOut — Product Specification
**Version:** 1.0.0  
**Status:** Draft — Source of Truth  
**Author:** CPO / Lead Architect  
**Date:** 2026-04-15

---

## Table of Contents

1. [Vision & Mission](#1-vision--mission)
2. [User Personas](#2-user-personas)
3. [The 5 Pillars — Functional Requirements](#3-the-5-pillars--functional-requirements)
4. [High-Level Data Model](#4-high-level-data-model)
5. [Technical Stack & Architecture](#5-technical-stack--architecture)
6. [System Design Principles](#6-system-design-principles)
7. [Open Questions & Deferred Decisions](#7-open-questions--deferred-decisions)

---

## 1. Vision & Mission

### Vision
SportOut is the connective tissue between the physical court and the digital world. It transforms every amateur and semi-pro ball game into structured, actionable data — creating a living sports ecosystem rather than a static scorekeeping tool.

### Mission
To give every player — regardless of whether they play at a professional academy or a neighborhood court — a **digital sports identity** that grows with them, connects them to the right competition, and accelerates their development.

### Core Problem Statement
The amateur sports world operates in an information vacuum:
- Players have no credible, portable record of their performance.
- Facility managers have no visibility into demand patterns.
- Scouts cannot efficiently discover talent outside organized leagues.
- Coaches lack longitudinal data to personalize training.

SportOut closes all four gaps with a unified, data-first platform.

### Design Philosophy
> "Measure everything. Expose only what matters."

The platform is built on the principle that raw data is infrastructure, and derived insights are the product. Every module that collects data is architecturally separate from every module that presents it. This allows the rating algorithm, the matchmaking logic, and the coaching recommendations to evolve independently.

---

## 2. User Personas

### 2.1 The Player

| Attribute | Description |
|-----------|-------------|
| **Who** | Amateur or semi-pro athlete, age 16–40, playing ball sports recreationally or in local leagues |
| **Technical Literacy** | Mobile-first. Comfortable with social apps. Not necessarily a data person. |
| **Primary Motivation** | Improve, compete fairly, get recognized |
| **Core Pain Points** | No way to prove skill to strangers; hard to find games at the right level; training advice is generic |
| **Success Metric** | "My rating reflects how I actually play, I found a game tonight, and I know exactly what to work on." |

**Key Jobs-to-be-Done:**
- Find a game or a partner at the right skill level within X km
- Build a credible, shareable sports profile
- Watch personalized highlights from their last game
- Receive a specific drill recommendation based on yesterday's weaknesses

---

### 2.2 The Facility Manager

| Attribute | Description |
|-----------|-------------|
| **Who** | Operator of a sports complex, municipal court, or private gym; may manage 1–30 courts |
| **Technical Literacy** | Varies widely. Needs a simple dashboard, not an API. |
| **Primary Motivation** | Maximize court utilization, reduce no-shows, understand demand |
| **Core Pain Points** | Courts sit empty at off-peak times; no data on who their users actually are; manual booking is error-prone |
| **Success Metric** | "I can see which courts are occupied right now, predict tomorrow's demand, and push a promo to fill the 10am slot." |

**Key Jobs-to-be-Done:**
- View real-time court occupancy
- Manage booking slots and availability windows
- Receive demand forecasts to plan staffing
- Understand the aggregate skill level and demographics of their facility's user base

---

### 2.3 The Scout / Coach

| Attribute | Description |
|-----------|-------------|
| **Who** | Youth academy coach, semi-pro team manager, university recruiter, or independent talent scout |
| **Technical Literacy** | Sports-literate; comfortable with spreadsheets and video tools; wants data but not raw data |
| **Primary Motivation** | Discover undervalued talent efficiently; track prospects over time |
| **Core Pain Points** | Talent discovery is entirely network-dependent; no structured performance record for non-academy players; video is scattered |
| **Success Metric** | "I can filter players by position, rating trend, and location, then watch a 2-minute highlight reel before deciding whether to make contact." |

**Key Jobs-to-be-Done:**
- Search and filter the player database with structured criteria
- View a player's longitudinal performance trajectory (not just current rating)
- Access game highlights linked directly to a player's profile
- Receive alerts when a tracked player's performance crosses a threshold

---

## 3. The 5 Pillars — Functional Requirements

### Pillar 1: Performance Stats & Dynamic Ratings

**Purpose:** Give every player a credible, portable, and continuously updated athletic identity.

**Functional Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| PR-01 | The system shall record per-game statistics for each player (sport-specific, e.g., points, assists, rebounds for basketball) | Must Have |
| PR-02 | The system shall maintain a dynamic rating for each player that updates after each recorded game | Must Have |
| PR-03 | The rating engine shall be implemented as a pluggable module — the algorithm itself (Elo, TrueSkill, custom ML model, etc.) is a runtime-configurable component, not hardcoded | Must Have |
| PR-04 | The system shall support multiple input sources for rating computation: raw stats, peer reviews, AI video analysis, and manual coach assessments | Must Have |
| PR-05 | Each player shall have a rating history (time-series), not just a current value | Must Have |
| PR-06 | The system shall support sport-specific stat schemas (basketball stats differ from futsal stats) | Must Have |
| PR-07 | Peer reviews shall require post-game confirmation from both parties before influencing the rating | Should Have |
| PR-08 | The system shall flag potential rating manipulation (e.g., two accounts consistently reviewing each other) | Should Have |
| PR-09 | Players shall be able to view a breakdown of what is driving their current rating | Should Have |
| PR-10 | The system shall support positional ratings (a player may have different ratings for Point Guard vs. Small Forward) | Could Have |

**Key Design Note — Rating Algorithm Flexibility:**
The `RatingEngine` is defined as an abstract interface. Version 1.0 will ship with a configurable Elo-based implementation. The architecture explicitly reserves space for a future ML model trained on video insights and peer data. No business logic in the application layer should assume a specific algorithm.

---

### Pillar 2: Matchmaking

**Purpose:** Connect the right players to the right game at the right time.

**Functional Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| MM-01 | Players shall be able to search for open games filtered by sport, location radius, skill bracket, and time window | Must Have |
| MM-02 | Players shall be able to create a game listing (time, location, required skill range, number of spots) | Must Have |
| MM-03 | The system shall suggest compatible games proactively based on a player's profile and historical patterns | Must Have |
| MM-04 | The system shall support team matchmaking: finding opponent teams for a scrimmage, not just individual players | Must Have |
| MM-05 | A match shall only be confirmed when the minimum required number of players have accepted | Must Have |
| MM-06 | The system shall send reminders and handle cancellation workflows with configurable grace periods | Should Have |
| MM-07 | Players shall be able to set a weekly availability schedule that the matchmaking engine reads | Should Have |
| MM-08 | The system shall track match outcomes (result, attendance, conduct) to feed back into the rating engine | Must Have |
| MM-09 | The system shall support private games (invite-only) and public games | Should Have |
| MM-10 | Matchmaking score shall be a composite of: skill compatibility, geographic proximity, and historical play-together preference | Should Have |

---

### Pillar 3: Smart Media

**Purpose:** Make professional-grade video analysis accessible to amateur players.

**Functional Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| SM-01 | The system shall integrate with AI filming hardware providers (initial target: Pixellot-compatible API) via an adapter interface | Must Have |
| SM-02 | Recorded game footage shall be automatically linked to the corresponding match record | Must Have |
| SM-03 | The system shall trigger automated highlight generation for each player per game (configurable duration: 30s, 60s, 2min) | Must Have |
| SM-04 | Highlights shall be tagged with event types (e.g., "made 3-pointer", "block", "assist") derived from CV analysis | Should Have |
| SM-05 | Players shall be able to view, download, and share their personal highlight reels | Must Have |
| SM-06 | Video-derived metrics (shot chart, movement heatmap, defensive positioning) shall be exported as structured data and passed to the rating engine | Should Have |
| SM-07 | The system shall support manual video upload as a fallback when AI filming hardware is unavailable | Should Have |
| SM-08 | The media pipeline shall be asynchronous — video processing shall not block any real-time game flow | Must Have |
| SM-09 | The system shall support multiple filming provider adapters — the core platform must not be coupled to a single vendor | Must Have |

**Key Design Note — Adapter Pattern:**
The `FilmingProvider` is an abstract interface. Pixellot is the first concrete implementation. A `ManualUpload` adapter shall exist from day one to ensure the platform works without AI hardware. Future providers (Veo, StatsPerform, etc.) are drop-in additions.

---

### Pillar 4: Growth & Coaching

**Purpose:** Turn collected data into a personalized development roadmap for each player.

**Functional Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| GC-01 | The system shall generate a post-game performance summary for each player, highlighting strengths and areas for improvement | Must Have |
| GC-02 | The system shall recommend specific drills or training resources based on a player's identified weaknesses | Must Have |
| GC-03 | Recommendations shall reference structured data (e.g., "your 3-point % dropped 15% this week") not vague generalities | Must Have |
| GC-04 | The system shall track a player's progress against previously set improvement goals | Should Have |
| GC-05 | A coach or trainer with explicit permission shall be able to view a player's full data profile and annotate it | Should Have |
| GC-06 | The system shall identify peer benchmarks: "Players at your rating level average X assists per game" | Should Have |
| GC-07 | Players shall be able to set public or private improvement goals | Could Have |
| GC-08 | The coaching module shall be able to consume video-derived data from Pillar 3 as an input signal | Must Have |

---

### Pillar 5: Municipal Information

**Purpose:** Create a real-time intelligence layer over city sports infrastructure.

**Functional Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| MU-01 | The system shall maintain a database of sports facilities (courts, gyms, pitches) with location, sport type, and surface data | Must Have |
| MU-02 | Facility availability (open/booked/full) shall be queryable in near-real-time | Must Have |
| MU-03 | Players shall be able to find the nearest available court for a given sport at a given time | Must Have |
| MU-04 | The system shall generate aggregate demand heatmaps per sport, per district, per time-of-day | Should Have |
| MU-05 | Facility Managers shall have a dashboard to update availability, view occupancy history, and manage their facility profile | Must Have |
| MU-06 | The system shall expose a public API endpoint for municipal authorities to query aggregate (anonymized) sports activity data | Could Have |
| MU-07 | The system shall support integration with third-party booking platforms (via webhook or API adapter) | Should Have |
| MU-08 | Facility data shall include amenities, pricing, lighting availability, and accessibility information | Should Have |

---

## 4. High-Level Data Model

> This is a conceptual model, not a schema definition. Field types and normalization are deferred to the engineering phase. The goal here is to define entities, their key attributes, and their relationships.

---

### Entity: `Player`

```
Player
├── id                  : UUID (primary key)
├── display_name        : string
├── email               : string (unique)
├── date_of_birth       : date
├── location            : GeoPoint (lat/lon)
├── sports              : list[SportProfile]  # one per sport they play
├── availability        : WeeklySchedule
├── created_at          : timestamp
└── is_verified         : bool
```

**SportProfile** (embedded within Player, one per sport):
```
SportProfile
├── sport               : Enum (BASKETBALL, FUTSAL, VOLLEYBALL, ...)
├── primary_position    : string
├── secondary_positions : list[string]
├── current_rating      : float
├── rating_history      : list[RatingSnapshot]  # time-series
└── career_stats        : StatAggregate
```

---

### Entity: `Match`

```
Match
├── id                  : UUID
├── sport               : Enum
├── facility_id         : UUID (FK → Facility)
├── scheduled_at        : timestamp
├── status              : Enum (OPEN, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED)
├── format              : Enum (PICKUP, SCRIMMAGE, LEAGUE_GAME, TRAINING)
├── skill_bracket       : RatingRange (min_rating, max_rating)
├── rosters             : list[MatchRoster]   # home/away or just participants
├── result              : MatchResult | null   # null until completed
├── media_session_id    : UUID | null          # FK → MediaSession
└── created_by          : UUID (FK → Player)
```

**MatchResult**:
```
MatchResult
├── score               : dict (team_id → int)
├── mvp_player_id       : UUID | null
├── confirmed_by        : list[UUID]  # player IDs who confirmed the result
└── confirmed_at        : timestamp
```

---

### Entity: `Rating`

> Designed as an **event log**, not a mutable value. The current rating is always the latest entry. This enables full auditability and algorithm replay.

```
RatingEvent
├── id                  : UUID
├── player_id           : UUID (FK → Player)
├── sport               : Enum
├── rating_before       : float
├── rating_after        : float
├── delta               : float  # computed
├── algorithm_version   : string  # e.g., "elo_v1", "truskill_v2"
├── source_type         : Enum (MATCH_RESULT, PEER_REVIEW, VIDEO_ANALYSIS, COACH_ASSESSMENT)
├── source_id           : UUID    # FK to the source record
└── created_at          : timestamp
```

---

### Entity: `Facility`

```
Facility
├── id                  : UUID
├── name                : string
├── manager_id          : UUID (FK → User)
├── location            : GeoPoint
├── address             : Address
├── sports_supported    : list[Enum]
├── courts              : list[Court]
├── operating_hours     : WeeklySchedule
└── amenities           : dict  # { lighting: bool, parking: bool, ... }
```

**Court** (embedded within Facility):
```
Court
├── id                  : UUID
├── sport               : Enum
├── surface             : Enum (HARDWOOD, ASPHALT, SYNTHETIC_GRASS, ...)
├── indoor              : bool
└── availability_slots  : list[AvailabilitySlot]
```

---

### Entity: `MediaSession`

```
MediaSession
├── id                  : UUID
├── match_id            : UUID (FK → Match)
├── provider            : Enum (PIXELLOT, MANUAL_UPLOAD, VEO, ...)
├── raw_footage_url     : string | null
├── processing_status   : Enum (PENDING, PROCESSING, COMPLETE, FAILED)
├── highlights          : list[Highlight]
└── video_metrics       : VideoMetrics | null  # structured CV output
```

**Highlight**:
```
Highlight
├── id                  : UUID
├── player_id           : UUID
├── duration_seconds    : int
├── event_tags          : list[string]  # ["3PT_MADE", "ASSIST"]
├── url                 : string
└── generated_at        : timestamp
```

---

### Entity: `PeerReview`

```
PeerReview
├── id                  : UUID
├── reviewer_id         : UUID (FK → Player)
├── reviewed_player_id  : UUID (FK → Player)
├── match_id            : UUID (FK → Match)
├── ratings             : dict  # { "defense": 4, "communication": 5, ... }
├── is_confirmed        : bool  # must be True to affect rating
└── submitted_at        : timestamp
```

---

### Entity Relationship Summary

```
Player ──< SportProfile
Player ──< MatchRoster >── Match
Match ──── Facility
Match ──── MediaSession ──< Highlight
Match ──< RatingEvent >── Player
Match ──< PeerReview >── Player
```

---

## 5. Technical Stack & Architecture

### 5.1 Stack Overview

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **API Layer** | Python + FastAPI | Async-native, automatic OpenAPI docs, Python-first ecosystem for data work, natural fit for IE/Python background |
| **Data Validation** | Pydantic v2 | First-class integration with FastAPI; enforces data contracts at system boundaries; aligns with the IE mindset of explicit, validated inputs |
| **Primary Database** | PostgreSQL | Relational integrity for Player/Match/Facility; mature geospatial support via PostGIS (critical for Pillars 2 & 5) |
| **Time-Series Data** | PostgreSQL (TimescaleDB extension) or InfluxDB | Rating history and facility occupancy are time-series workloads; TimescaleDB keeps the stack unified |
| **Cache / Session** | Redis | Match lobbies, real-time availability slots, and notification queues; also used for rate limiting |
| **Task Queue** | Celery + Redis | Video processing pipeline (Pillar 3) is async by requirement; all ML inference jobs are background tasks |
| **Object Storage** | S3-compatible (AWS S3 / MinIO for local dev) | Highlight videos, raw footage, player profile media |
| **Search & Matchmaking** | PostgreSQL + PostGIS (phase 1); Elasticsearch optional (phase 2) | Geo-queries and skill bracket filtering are achievable in Postgres initially; Elasticsearch added only when full-text player search is needed |
| **Authentication** | JWT + OAuth2 (via `python-jose` / `authlib`) | Standard, stateless; supports social login (Google, Apple) for consumer app UX |
| **Containerization** | Docker + Docker Compose | Reproducible local dev; production-ready container images for K8s or ECS |
| **Orchestration** | Kubernetes (production) | Horizontal scaling of API and worker nodes independently |
| **CI/CD** | GitHub Actions | Lightweight, sufficient for the scale; test → lint → build → deploy pipeline |
| **API Documentation** | FastAPI auto-generated OpenAPI/Swagger | Zero-cost documentation; essential for Scout API integrations and third-party facility booking adapters |
| **Monitoring** | Prometheus + Grafana | Metrics-first observability; aligned with IE background (track throughput, queue depth, error rate as KPIs) |

---

### 5.2 Service Architecture

SportOut is designed as a **modular monolith first, microservices when justified**. This is a deliberate architectural decision:

> A premature microservices split adds coordination overhead without scaling benefit at early stage. The codebase is organized so that each pillar is an independently deployable service *when* the need arises, but runs as a single process *until* it does.

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                          │
│                  (FastAPI / rate-limited)                    │
└──────────┬──────────┬────────────┬──────────────────────────┘
           │          │            │
    ┌──────▼───┐ ┌────▼────┐ ┌────▼──────────┐
    │  Player  │ │  Match  │ │   Facility    │
    │  Service │ │ Service │ │   Service     │
    └──────┬───┘ └────┬────┘ └────┬──────────┘
           │          │            │
    ┌──────▼──────────▼────────────▼──────────┐
    │            Domain Core                  │
    │  (Rating Engine, Matchmaking Engine,    │
    │   Coaching Engine — pluggable modules)  │
    └──────────────────┬──────────────────────┘
                       │
    ┌──────────────────▼──────────────────────┐
    │            Data Layer                   │
    │  PostgreSQL + TimescaleDB │ Redis        │
    └──────────────────┬──────────────────────┘
                       │
    ┌──────────────────▼──────────────────────┐
    │          Async Worker Layer             │
    │     Celery Workers (video pipeline,     │
    │     rating recalculation, notifications)│
    └─────────────────────────────────────────┘
```

---

### 5.3 Rating Engine — Pluggable Architecture

This is the most architecturally sensitive component, as the algorithm is explicitly TBD.

```python
# Conceptual interface — not final code
class RatingEngine(ABC):
    @abstractmethod
    def compute(self, context: RatingContext) -> RatingDelta:
        """
        context contains: match result, player stats, peer reviews,
        video metrics, opponent ratings, format weight.
        Returns a delta and metadata about what drove it.
        """
        ...

# Concrete implementations registered by name
ENGINES = {
    "elo_v1":        EloRatingEngine,
    "truskill_v1":   TrueSkillEngine,
    "composite_v1":  CompositeWeightedEngine,
}
```

The active engine is set via environment configuration. A migration path exists to recalculate all historical ratings when the algorithm changes (by replaying the `RatingEvent` log).

---

### 5.4 Media Pipeline — Adapter Architecture

```
FilmingProvider (abstract)
    ├── PixellotAdapter       # AI auto-filming
    ├── VeoAdapter            # Veo camera system
    └── ManualUploadAdapter   # Fallback: user uploads phone video
          │
          ▼
    VideoProcessingWorker (Celery)
          │
          ├── HighlightGenerator (calls provider's highlight API)
          ├── MetricsExtractor   (structured CV output → RatingContext)
          └── StorageUploader    (writes to S3, updates MediaSession)
```

---

### 5.5 Geospatial Stack (Pillars 2 & 5)

- All location data stored as `GEOGRAPHY(POINT, 4326)` in PostGIS
- Facility search and matchmaking queries use `ST_DWithin` for radius filtering
- Demand heatmaps generated via `ST_SnapToGrid` aggregation queries
- No external geospatial service required in phase 1

---

## 6. System Design Principles

These are non-negotiable constraints that apply across all pillars.

1. **Events, not mutations.** Ratings, match states, and availability changes are recorded as immutable event logs. Current state is always derivable. This enables auditability, debugging, and algorithm replay.

2. **Pluggable engines.** The Rating Engine, Matchmaking Engine, and Coaching Engine are abstract interfaces. No application code is allowed to depend on a concrete implementation directly.

3. **Async by default for heavy work.** Video processing, rating recalculation after a large tournament, and notification dispatch are always background tasks. The API layer never blocks on these operations.

4. **Explicit data contracts.** Every API boundary uses Pydantic models. No `dict` passing between services. This is the equivalent of engineering tolerances — every input and output has a defined shape.

5. **Geo-awareness is a first-class concern.** Every entity that exists in physical space stores a `GeoPoint`. The schema does not allow this to be optional or added later.

6. **Sport-agnostic core, sport-specific schemas.** The platform core (Player, Match, Rating, Facility) is sport-neutral. Sport-specific stat schemas are registered as plugins, not baked into the core model.

7. **No vendor lock-in for media.** The filming provider is an adapter. The platform must function fully (including rating computation from manual stats and peer reviews) without any AI filming hardware.

---

## 7. Open Questions & Deferred Decisions

These are known unknowns that require further research, user testing, or external input before they can be resolved. They are listed explicitly to prevent premature closure.

| # | Question | Pillar | Blocker? |
|---|----------|--------|----------|
| OQ-01 | What is the final rating algorithm? Options: Elo, TrueSkill, custom ML model, composite weighted score. Requires data from at least one full season of games to tune. | Pillar 1 | No — architecture is designed to be algorithm-agnostic |
| OQ-02 | Which AI filming providers will be integrated at launch? Pixellot is the target, but licensing and API access terms are unknown. | Pillar 3 | No — ManualUpload adapter is the fallback |
| OQ-03 | What is the monetization model? Freemium per player? B2B per facility? Scout subscription? This affects which features are gated. | All | No — spec is written feature-first |
| OQ-04 | What sports are in scope for v1? Basketball is the implied primary sport. Futsal, volleyball are secondary candidates. | All | Yes — stat schemas and position enums cannot be finalized without this |
| OQ-05 | Are municipal partnerships (Pillar 5) B2G contracts or self-service? This affects the facility onboarding flow significantly. | Pillar 5 | No |
| OQ-06 | What is the consent and privacy model for video? Players must opt-in. How is footage handled for minors? | Pillar 3 | Yes — legal review required before any video feature ships |
| OQ-07 | Is the peer review system anonymous or attributed? Anonymous reviews reduce bias but enable abuse. | Pillar 1 | No — can be a feature flag |
| OQ-08 | Real-time vs. near-real-time for court availability? WebSockets vs. polling interval. Depends on facility hardware integration. | Pillar 5 | No |

---

*This document is the single source of truth for SportOut product decisions. All subsequent technical design documents, API contracts, and sprint plans should reference this spec and note any deviations explicitly.*
