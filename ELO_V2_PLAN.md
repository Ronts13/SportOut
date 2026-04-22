# ELO_V2_PLAN.md — Pillar-Based Rating System (Hardcore Accuracy)

## Overview

This document defines the complete mathematical and architectural specification for `elo_v2`, SportOut's advanced rating engine. It supersedes `elo_v1` by introducing:

1. **Placement Phase** — dynamic K-factor for faster convergence in first 10 games
2. **AI Combine** — pillar-based physical assessment with community-dynamic benchmarks
3. **Strength-Biased Weighting** — specialists are rewarded for their weapon, not penalized for weaknesses
4. **Hardcore Fusion** — strict 70/30 ELO + Combine blend; no free bonuses

---

## Part 1 — Placement Phase: Dynamic K-Factor

### Problem
A player seeded at 1000 whose true level is 1400 needs ~30 games at K=32 to converge. We want convergence in 10.

### Formula

```
N_PLACEMENT = 10
K_BASE      = 32.0
K_MAX       = 96.0   # 3× base — inspired by FIDE "rapid development" tier

K(n) = K_MAX − (K_MAX − K_BASE) × (n / N_PLACEMENT)   for n < N_PLACEMENT
K(n) = K_BASE                                          for n ≥ N_PLACEMENT

n = games_played BEFORE the current match (0-indexed)
```

| Before game | n   | K     |
|-------------|-----|-------|
| 1st         | 0   | 96.0  |
| 3rd         | 2   | 83.2  |
| 5th         | 4   | 70.4  |
| 7th         | 6   | 57.6  |
| 10th        | 9   | 38.4  |
| 11th+       | 10+ | 32.0  |

### Soft Seeding from Combine

If a player completes the AI Combine before their first ranked game, shift their starting ELO:

```
SEED_RANGE   = 400
initial_elo  = 1000 + (combine_score − 0.5) × SEED_RANGE

combine_score = 0.0  →  start at  800
combine_score = 0.5  →  start at 1000  (no change)
combine_score = 1.0  →  start at 1200
```

This reduces the distance the placement phase must travel for clearly strong or weak athletes.

---

## Part 2 — AI Combine: Pillar-Based Architecture

### Design Philosophy

SportOut is street sports — no fixed positions. The system must highlight individual weapons, not average them away. A tennis player with a 250 km/h serve and poor footwork should be recognized as a Power specialist, not penalized as "mediocre overall".

### Data Structure — `app/sports/registry.py`

Two new dataclasses define the sport metadata:

```python
@dataclass
class CombineMetric:
    key: str            # matches key in raw_metrics dict from extract_video_metrics()
    weight: float       # within-pillar importance weight
    floor: float        # physiological safety-net minimum (prevents div/0 on empty DB)
    ceiling: float      # physiological safety-net maximum
    inverted: bool = False  # True if lower value = better (e.g. sprint time)

@dataclass
class CombinePillar:
    name: str           # display name on Player Card  (e.g. "Pace")
    key: str            # snake_case identifier stored in breakdown dict
    metrics: list[CombineMetric]
```

### Tennis Pillar Definitions

```python
TENNIS_PILLARS: list[CombinePillar] = [
    CombinePillar("Pace", "pace", [
        CombineMetric("sprint_10m_seconds",      weight=1.5, floor=1.5,  ceiling=3.5,  inverted=True),
        CombineMetric("court_coverage_score",    weight=1.2, floor=0.0,  ceiling=1.0),
    ]),
    CombinePillar("Power", "power", [
        CombineMetric("serve_speed_kmh",         weight=1.5, floor=60,   ceiling=250),
        CombineMetric("groundstroke_power_kmh",  weight=1.3, floor=40,   ceiling=180),
    ]),
    CombinePillar("Precision", "precision", [
        CombineMetric("first_serve_pct",         weight=1.5, floor=0.25, ceiling=0.92),
        CombineMetric("target_accuracy_pct",     weight=1.4, floor=0.15, ceiling=0.97),
        CombineMetric("double_fault_rate",       weight=1.0, floor=0.0,  ceiling=0.35, inverted=True),
    ]),
    CombinePillar("Stamina", "stamina", [
        CombineMetric("rally_endurance_score",   weight=1.3, floor=0.0,  ceiling=1.0),
        CombineMetric("recovery_time_seconds",   weight=1.1, floor=5.0,  ceiling=45.0, inverted=True),
    ]),
    CombinePillar("Technique", "technique", [
        CombineMetric("forehand_form_score",     weight=1.3, floor=0.0,  ceiling=1.0),
        CombineMetric("backhand_form_score",     weight=1.2, floor=0.0,  ceiling=1.0),
        CombineMetric("footwork_score",          weight=1.1, floor=0.0,  ceiling=1.0),
    ]),
]

COMBINE_PILLARS: dict[Sport, list[CombinePillar]] = {
    Sport.TENNIS:     TENNIS_PILLARS,
    Sport.BASKETBALL: BASKETBALL_PILLARS,  # to be defined similarly
    Sport.SOCCER:     SOCCER_PILLARS,      # to be defined similarly
}
```

---

## Part 3 — Combine Score: Three-Step Computation

### Step 1: Normalize Each Raw Metric Against Community Benchmark

No static tables. The community's personal best *is* the 1.0 ceiling — the "Community Usain Bolt".

```
community_max, community_min = CombineBenchmarks.get(sport, metric_key)
                                # Redis (TTL=600s) → combine_benchmarks table fallback

For higher-is-better metrics:
  norm = clamp((value − floor) / (community_max − floor), 0.0, 1.0)

For inverted (lower-is-better) metrics:
  norm = clamp((ceiling − value) / (ceiling − community_min), 0.0, 1.0)

Bootstrap rule:
  if sample_count < 10: return 0.5  # neutral — don't punish early adopters
```

### Step 2: Aggregate Metrics into Per-Pillar Score

```
pillar_score_k = Σ(w_i × norm_i) / Σ(w_i)    for all metrics i belonging to pillar k
```

### Step 3: Strength-Biased Combine Score

Sort pillar scores descending. Assign rank weights `[N, N−1, ..., 1]`. The player's best pillar **always** receives the highest weight — regardless of which pillar that happens to be.

```
pillar_scores_sorted = sorted(pillar_scores.values(), reverse=True)
rank_weights         = [N, N−1, N−2, ..., 1]   # e.g. [5,4,3,2,1] for 5 pillars

combine_score = Σ(rank_weight_k × pillar_score_k) / Σ(rank_weights)
```

### Worked Example — Power Hitter in Tennis

| Pillar    | Score | Rank | Weight | Contribution |
|-----------|-------|------|--------|--------------|
| Power     | 0.92  | 1st  | 5      | 4.60         |
| Technique | 0.75  | 2nd  | 4      | 3.00         |
| Precision | 0.60  | 3rd  | 3      | 1.80         |
| Stamina   | 0.50  | 4th  | 2      | 1.00         |
| Pace      | 0.28  | 5th  | 1      | 0.28         |

```
combine_score (strength-biased) = 10.68 / 15 = 0.712
combine_score (flat average)    = 3.05  /  5 = 0.610

Specialist bonus: +0.102
```

A balanced player with 0.70 across all pillars scores exactly **0.70** with both methods — no penalty for versatility, no reward for weakness hiding.

---

## Part 4 — Strict Overall Score Fusion (No Free Bonuses)

### Formulas

```
# 1. Normalize competitive ELO to [0, 1] using the same 400-point spread as Elo itself
elo_norm = 1 / (1 + 10^((1000 − elo) / 400))

# 2. Fusion
if combine_result is None:
    overall_01 = elo_norm                                    # 100% ELO — pure competitive
else:
    overall_01 = 0.70 × elo_norm + 0.30 × combine_score     # strict 70/30 — no bonuses

# 3. Map to display scale 55–99
overall_display = round(55 + overall_01 × 44)
```

### Real Stakes

If `combine_score < elo_norm`, the player's Overall **drops** relative to pure ELO. The Combine is a commitment to transparency, not a path to free points.

### Sanity Check Table

| ELO  | Combine Score | overall_01 | Display |
|------|---------------|------------|---------|
| 1400 | None          | 0.909      | **95**  |
| 1400 | 0.712         | 0.850      | **92**  |
| 1000 | None          | 0.500      | **77**  |
| 1000 | 0.712         | 0.564      | **80**  |
| 1000 | 0.20          | 0.410      | **73**  | ← combine hurts |
| 700  | 0.712         | 0.341      | **70**  |

---

## Part 5 — Community Benchmark Infrastructure

### The Problem

Querying `MAX(value)` across all combine rows on every Overall computation is O(N). The solution is a three-layer architecture.

### Layer 1 — `combine_benchmarks` Table (Source of Truth)

One row per `(sport, metric_key)`. Updated atomically by the Celery combine worker:

```sql
INSERT INTO combine_benchmarks (sport, metric_key, community_max, community_min, sample_count)
VALUES (%(sport)s, %(metric_key)s, %(value)s, %(value)s, 1)
ON CONFLICT (sport, metric_key) DO UPDATE SET
  community_max = GREATEST(combine_benchmarks.community_max, EXCLUDED.community_max),
  community_min = LEAST(combine_benchmarks.community_min, EXCLUDED.community_min),
  sample_count  = combine_benchmarks.sample_count + 1,
  updated_at    = now();
```

Table size: ~N_sports × N_metrics ≈ 30–50 rows. Always accurate, never stale.

### Layer 2 — Redis Cache (Fast Reads)

```
key:    benchmark:{sport}:{metric_key}
value:  {"max": float, "min": float, "sample_count": int}
TTL:    600 seconds (10 minutes)
```

On cache miss → single indexed PK lookup on `combine_benchmarks` → repopulate cache.
A new community record propagates to all computations within 10 minutes.

### Layer 3 — Engine Fallback

If Redis and DB are both unavailable → `combine_result = None` → Overall falls back to 100% ELO. The Combine pipeline never blocks a rating update.

---

## Architectural Changes

| File | Action | What Changes |
|------|--------|--------------|
| `app/engines/rating/base.py` | Modify | Add `CombineResult` dataclass; extend `RatingContext` with `games_played: int` and `combine_result: CombineResult \| None`; extend `RatingDelta` with `overall_score: float \| None` |
| `app/engines/rating/elo_v2.py` | **Create** | `EloV2RatingEngine`: dynamic K, pillar aggregation, strength-biased combine, strict fusion |
| `app/engines/rating/__init__.py` | Modify | Register `"elo_v2": EloV2RatingEngine` |
| `app/sports/registry.py` | Modify | Add `CombineMetric`, `CombinePillar` dataclasses; define `TENNIS_PILLARS`, `BASKETBALL_PILLARS`, `SOCCER_PILLARS`; export `COMBINE_PILLARS` dict |
| `app/models/combine_result.py` | **Create** | `combine_results` (append-only per-attempt) + `combine_benchmarks` (aggregate, upserted) ORM models |
| `app/models/sport_profile.py` | Modify | Add `overall_score: float \| None` and `combine_score: float \| None` columns |
| `app/workers/ratings.py` | Modify | Query `career_games` and latest `combine_results` row; pass to `RatingContext` |
| `app/workers/video.py` | Modify | Add combine processing task: normalize → pillar scores → combine_score → upsert benchmarks → insert `combine_results` row → update `sport_profiles` |
| `alembic/versions/xxx_add_v2_fields.py` | **Create** | Migration: new `combine_results` and `combine_benchmarks` tables; new columns on `sport_profiles` |

---

## Verification Checklist

- [ ] `python test_pulse.py` — existing schema and engine wiring tests pass unchanged
- [ ] Unit: `dynamic_k(0)` → 96.0; `dynamic_k(9)` → 38.4; `dynamic_k(10)` → 32.0
- [ ] Unit: Power Hitter example — `combine_score` → 0.712 (not 0.610)
- [ ] Unit: Balanced player (all pillars = 0.70) → `combine_score` = 0.70 (no distortion)
- [ ] Unit: `combine_result=None`, `elo=1000` → `overall_display` = 77
- [ ] Unit: `combine_score=0.20`, `elo=1000` → `overall_display` = 73 (combine hurts — real stakes confirmed)
- [ ] Unit: benchmark upsert with new record higher than current max → `community_max` updates
- [ ] `docker-compose exec app alembic upgrade head` — migration applies cleanly
- [ ] Set `RATING_ENGINE=elo_v2` in `.env` → API responds at `http://localhost:8000/docs`
