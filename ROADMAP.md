# 🚀 SportOut Master Roadmap – Path to Launch

> This document is the canonical reference for all technical, architectural, and business decisions.
> All future development must align with the vision defined here.

---

## 📱 1. Frontend & UX — Client App / UI

*Goal: Create a seamless user experience where every object is interconnected.*

- Develop fast SSO login/registration via **Google**, **Instagram**, and **Facebook**.
- Dynamic linking of Followers/Following lists to actual player profiles (clickable).
- Develop a **Notification Center** for real-time data push (new followers, match invites, cancellations).
- Create **Settings & Privacy** screens (public/private profile toggles, notification management).
- Add scrollable tabs to user profiles: **Game History** and **Upcoming Matches**.
- Add optional profile fields allowing players to link their Instagram and Facebook accounts directly.
- **Leaderboards:** Set default view to prioritize players the user follows (Following list).
- **Leaderboards:** Develop a re-indexing function so any filtered view (sport/region/friends) always numbers sequentially from 1.
- **Leaderboards:** Dynamic Top 3 Podium that auto-updates based on filters, populated strictly by active players.
- **Matches (LFG):** Match details screen must display the full roster of currently registered/active players.
- **Matches (LFG):** Make match cards fully interactive (clickable player avatars, direct links to court profiles).
- **Courts:** Populate 30 real-world courts with precise geo-locations, lighting hours, and crowd-level data for a live heatmap.
- **Courts:** Develop a feature allowing users to upload real photos from the courts directly to the court profile.

---

## ⚙️ 2. Backend, Algorithms & DB — Server & Logic

*Goal: Move data logic out of the browser and establish a secure, centralized "brain".*

- Develop **Server-Side Auth** supporting secure Google, Instagram, and Facebook logins.
- Code the **Core Rating Algorithm** in FastAPI/Python, translating match results into a **55–99 scale**, including a badge/trophy system (e.g., win streaks).
- Specify **manual result reporting** logic: define the "Accept/Reject" workflow (who inputs, who verifies).
- **Rating Weights Permissions:** Define logic where verified coaches, scouts, or "verified players" have a higher impact on others' ratings.
- Develop an **enforcement and penalty mechanism** for last-minute cancellations, unfair play, or falsified data reporting.
- **Database Schema Design:** Relational tables for Users, Courts, Matches, and their relationships (followers, match participants).
- **Strict Profile Fields Validation:** Clear DB-level separation between mandatory and optional fields (like social links).
- Set up **Cloud Storage** infrastructure to receive and store user-uploaded court photos.
- Create **RESTful API Endpoints** (GET/POST) to serve all the above data to the Frontend.

---

## 🛠️ 3. DevOps, Infrastructure & Team Setup

*Goal: Establish a professional, secure, and parallel working environment.*

- Create professional **LinkedIn profiles** for all co-founders.
- Create **GitHub profiles** for all co-founders.
- Establish the official **SportOut GitHub Repository** (Master).
- Define **GitHub workflows** (Pull Requests, Code Review) to enable parallel work without code overrides.
- Deploy a **Staging Environment** (Live Demo server) for Alpha testers to connect via mobile and update live data.

---

## 💼 4. Business, Marketing & Operations

*Goal: Clear business model, user acquisition, and revenue generation.*

- **Pitch Deck Upgrade:** Redesign the investor deck to reflect the current app experience and sharply highlight SportOut's unique differentiator.
- **Formalize the Business Model:** Define exact revenue streams (subscriptions, transaction fees, ads, partnerships).
- **Pro Integration Strategy:** Define how coaches and scouts enter the platform (e.g., "Coach" profiles offering paid training sessions).
- **Go-to-Market (Field Ops):** Target 2–3 strategic courts (e.g., Sportek) and build a hyper-local physical community to ensure constant match "liquidity".
- **B2B Partnerships:** Meet with sports complex managers to pitch collaborations aimed at increasing their court occupancy during off-peak hours.

---

*Last updated: 2026-04-19*
