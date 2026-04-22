# MVP_DRILLS_PLAN.md — Football AI Combine: 4 Hardcore Drills

<design_principles>
**CV Golden Rule:** Every drill is built around relative and binary measurements, not absolute ones. Fixed known distances (10m gap between cones) act as an in-frame ruler, enabling real-world speed calculation without any depth sensor.

**Wizard of Oz Rule:** Every manual admin annotation (times, counts, tallies) is direct ground truth training data for future CV models. No admin work is wasted — it is the labeling phase of a supervised learning pipeline.
</design_principles>

---

## Drill 1: The 10M Laser

**Pillar:** `pace`
**Raw Metric:** `sprint_10m_seconds` (inverted — lower is better)

### User Setup
Place 2 cones exactly 10 big steps apart (~10m). Lay the phone on the ground to the side so both cones are fully in frame. Stand with the ball touching the foot behind the start cone.

### Task
Dribble from cone A to cone B as fast as possible. Best of 3 attempts.

### Admin Scoring (Oz Mode)
Frame-scrub to the first visible ball movement = START. Frame where ball (or foot) crosses cone B = STOP.
Record `sprint_10m_seconds`. Scoring time: ~60 seconds per video.

### Future CV Pipeline
```text
YOLOv8 (ball + cone detection)

Calibration:
  pixel_distance = |cone_A_x − cone_B_x| in image
  meters_per_pixel = 10.0 / pixel_distance
  → outputs real km/h without depth hardware

Start event: ball displacement > 20px from initial position
End event:   ball_centroid_x crosses cone_B_x coordinate
Speed:       10m / (frames / fps) × 3.6 = km/h
```
**CV Difficulty:** ⭐⭐☆☆☆ — the only drill that yields real-world km/h without a depth sensor.

---

## Drill 2: The Wall Sniper

**Pillar:** `shooting`
**Raw Metric:** `wall_hits_out_of_7`

### User Setup
Draw a circle (~35cm diameter, center at knee height) on any wall using chalk or tape.
Mark a shooting spot 8 big steps back (~7m). Place the phone to the side so the shooter AND the wall circle are both in the same frame.

### Task
Shoot 7 balls at the circle. Max 3-step run-up per shot.

### Admin Scoring (Oz Mode)
A hit = ball makes visible contact with the circle or its outline. Edge contact = 0.5 points.
Record `wall_hits_out_of_7`. Scoring time: ~75 seconds (slow-mo on impact frames).

### Future CV Pipeline
```text
Step 1 — Target detection (one-time per video):
  Hough Circle Transform on static wall region
  → extract circle_center (cx, cy), circle_radius (r)

Step 2 — Ball tracking:
  YOLOv8 + DeepSORT on approaching ball
  Track trajectory for last 15 frames before wall contact

Step 3 — Impact prediction (handles occlusion at impact):
  Fit parabolic curve to last 10 visible frames
  → extrapolate predicted impact point (px, py)

Hit event:
  distance((px, py), (cx, cy)) < r + tolerance_px
```
**CV Difficulty:** ⭐⭐⭐☆☆ — partial ball occlusion at moment of impact, solved by trajectory extrapolation.

---

## Drill 3: The Figure-8 Blitz

**Pillar:** `dribbling`
**Raw Metric:** `figure8_reps_in_30s`

### User Setup
Place 2 cones ~1 meter apart. Place the phone to the side far enough that both cones AND the full body are in frame.

### Task
Dribble in a continuous figure-8 pattern around both cones for 30 seconds without stopping.
Ball loss (travels more than 1 body-length away from cones) = −1 rep deduction.

### Admin Scoring (Oz Mode)
Play at 0.5× speed. One complete figure-8 = ball goes fully around cone A AND fully around cone B.
Record `figure8_reps_in_30s`. Scoring time: ~2–3 minutes.

Reference benchmarks: Elite = 20+ reps | Strong amateur = 13–17 | Casual = under 10.

### Future CV Pipeline
```text
YOLOv8 (ball + cone detection) → DeepSORT (30s continuous tracking)

Midpoint M = midpoint between cone_A and cone_B in image coordinates

Figure-8 count algorithm:
  1. Track ball X-position over time → oscillation signal
  2. Each time ball crosses M, record direction (left→right or right→left)
  3. One complete figure-8 = 2 midpoint crossings in alternating directions
  4. reps = crossing_pairs

Ball loss flag:
  distance(ball, nearest_cone) > 2.5 × cone_spacing_px → subtract 1 rep
```
**CV Difficulty:** ⭐⭐⭐☆☆ — reduces to counting zero-crossings of a 1D oscillation signal.

---

## Drill 4: The Weak Foot Gauntlet

**Pillar:** `technique`
**Raw Metric:** `weak_foot_max_consecutive`

### User Setup
Open flat ground. Phone to the side, full body from head to toe in frame.
Player self-declares weak foot at the start of the video (e.g., holds up 1 finger = left foot weak).

### Task
Juggle using ONLY the weaker foot. Attempt ends when ball hits the ground OR the strong foot makes contact. Best of 2 attempts.

### Admin Scoring (Oz Mode)
Count consecutive touches with the weak foot only. Record `weak_foot_max_consecutive`.
Scoring time: ~90 seconds.

Reference benchmarks: Elite = 30+ touches | Strong amateur = 10–20 | Casual = under 5.

### Future CV Pipeline
```text
MediaPipe Pose (LEFT_ANKLE / RIGHT_ANKLE keypoints)

Foot identity:
  Dominant foot inferred from Drill 1 ball contact events
  Weak foot = the other ankle keypoint

Weak-foot touch event:
  distance(ball_center, weak_ankle_keypoint) < threshold_px
  AND ball velocity Y-component changes sign (↓ → ↑)
  AND strong_ankle_keypoint NOT within threshold_px simultaneously

Strong-foot violation:
  distance(ball_center, strong_ankle_keypoint) < threshold_px
  → terminate attempt

Output: max_consecutive_weak_foot_touches
```
**CV Difficulty:** ⭐⭐⭐☆☆ — foot identity from Pose Estimation is reliable; edge case when both feet are close together.

---

## Pillar Mapping for `SOCCER_PILLARS`

| Drill | Pillar Key | Metric | Direction |
| :--- | :--- | :--- | :--- |
| The 10M Laser | `pace` | `sprint_10m_seconds` | inverted (lower = better) |
| The Wall Sniper | `shooting` | `wall_hits_out_of_7` | higher = better |
| The Figure-8 Blitz | `dribbling` | `figure8_reps_in_30s` | higher = better |
| The Weak Foot Gauntlet | `technique` | `weak_foot_max_consecutive` | higher = better |

---

## CV Complexity Summary

| Drill | Primary CV Technique | Key Challenge |
| :--- | :--- | :--- |
| The 10M Laser | YOLOv8 + cone calibration | None — clean binary crossing event |
| The Wall Sniper | Hough Circle + trajectory extrap. | Occlusion at wall impact |
| The Figure-8 Blitz | DeepSORT + midpoint crossings | Cone occlusion during tight dribble |
| The Weak Foot Gauntlet | MediaPipe Pose + foot identity | Both feet proximate simultaneously |