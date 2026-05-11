# 🚀 SportOut Master Roadmap – Path to Launch

> **Business and marketing roadmap.** Technical architecture lives in `CLAUDE.md`. Product spec lives in `PRODUCT_SPEC.md`.

> **MVP Sport: Football (Soccer).** The v1 launch is 100% Football-focused. Padel, Tennis, Basketball are future expansions with schemas already prepared in the codebase.

---

## 🏈 0. MVP Scope — Football First

**Strategic decision (2026-05-11):** Football is the primary and only active sport for the MVP launch. All product, design, and engineering effort is focused on delivering the complete Football loop:

> **Register → Find a Football Match → Play → Submit Stats → Get Your Rating → Climb the Leaderboard**

The AI Combine (4 Football drills: 10M Laser, Wall Sniper, Figure-8 Blitz, Weak Foot Gauntlet) is the core differentiator and must ship as part of the MVP. See `MVP_DRILLS_PLAN.md` for the full drill design and Wizard-of-Oz admin scoring process.

**Why Football first:**
- Largest amateur player base in Israel and globally
- Street football requires no fixed facility — reduces dependency on facility partnerships
- The AI Combine drills are self-filmed (phone + cones) — no Pixellot hardware needed for MVP
- Clear, universal stats (goals, assists, position) — easy for players to self-report

---

## 📱 1. Frontend & UX — Client App / UI

*Goal: Create a seamless Football-first user experience where every object is interconnected.*

**MVP (Football):**
- [ ] Update leaderboard to show **Football players** by default (`sport=soccer`)
- [ ] Wire all leaderboard, match, and profile screens to the real API (`fetch()` calls replacing hardcoded arrays)
- [ ] Match creation form: Football-specific fields (position preference, team size 5v5/7v7/11v11, location)
- [ ] Post-match stat entry: goals, assists, shots on target, minutes played, position
- [ ] AI Combine submission flow: player films their drill, uploads video, sees "Pending Review" status
- [ ] Leaderboard: Dynamic Top 3 Podium, sequential numbering for filtered views

**Post-MVP (all sports):**
- SSO login via Google, Instagram, Facebook
- Notification Center (match invites, cancellations, rating updates)
- Settings & Privacy screens (public/private profile toggles)
- Profile tabs: Game History, Upcoming Matches
- Followers/Following lists linked to player profiles
- Court photo upload feature

---

## ⚙️ 2. Backend, Algorithms & DB — Server & Logic

*Goal: Complete the Football match loop and AI Combine pipeline.*

**MVP (Football) — in priority order:**
- [ ] `POST /api/v1/matches/{id}/stats` — submit per-player Football stats (goals, assists, shots, position)
- [ ] `POST /api/v1/players/{id}/combine-score` — admin manually scores AI Combine pillars (Pace/Shooting/Dribbling/Technique 0–100)
- [ ] Redis + Celery worker in `docker-compose.yml` — enables `recalculate_match_ratings` to actually run
- [ ] Rating display: translate internal Elo (1000-base) to 55–99 scale in leaderboard response
- [ ] Peer review flow: `POST /players/reviews` + `/reviews/{id}/confirm`
- [ ] Rating history endpoint: `GET /players/{id}/rating/soccer`
- [ ] Server-Side Auth: email/password is MVP; Google/Instagram/Facebook are post-MVP

**Post-MVP:**
- `EloV2` engine (pillar-based AI Combine fusion — spec in `ELO_V2_PLAN.md`)
- Rating manipulation detection (PR-08 from PRODUCT_SPEC)
- Positional ratings (PR-10)
- Verified coach/scout role with higher peer review weight
- Cancellation penalty system

---

## 🛠️ 3. DevOps, Infrastructure & Team Setup

*Goal: Establish a professional, secure, and parallel working environment.*

- [ ] Deploy **Staging Environment** on Railway/Render/Fly.io — Football alpha testers connect via mobile
- [ ] Add `redis` + `worker` services to `docker-compose.yml`
- [ ] Define GitHub PR/code review workflow for parallel development
- [x] GitHub repository established (`Ronts13/SportOut`)
- [ ] Set up CI: run `python test_pulse.py` on every push

---

## 💼 4. Business, Marketing & Operations

*Goal: Clear business model, user acquisition, and revenue generation.*

- **Go-to-Market (Football First):** Target 2–3 street football courts in Tel Aviv (e.g., Sportek). Run a "Combine Day" event where players film their 4 drills and get their first AI rating within 48 hours.
- **Pitch Deck:** Update to show the Football AI Combine as the core demo — a player uploads a video, gets back a rating with a pillar breakdown (Pace 78, Shooting 65, Dribbling 82, Technique 71).
- **Formalize Business Model:** Freemium per player vs. B2B per facility. Decision needed before Series A.
- **B2B Partnerships:** Approach football court operators and municipal sports facilities — offer occupancy analytics as the hook.
- **Multi-Sport Expansion (post-MVP):** Padel and Tennis are the next sports after Football, based on survey data. Basketball and Futsal follow.

---

*Last updated: 2026-05-11*
