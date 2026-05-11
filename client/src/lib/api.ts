import { apiDelete, apiGet, apiPost, apiPatch } from "@/lib/fastapi";

/* ─── TYPES ─────────────────────────────────────────────────── */

export type DbCourt = {
  id: string;
  name: string;
  sport: string;
  current_occupancy: number;
  max_capacity: number;
  lighting_available: boolean;
  lighting_on: boolean;
  is_bookable: boolean;
  surface: string;
  indoor: boolean;
  facility: {
    id: string;
    name: string;
    address_city: string | null;
    address_street: string | null;
    latitude: number | null;
    longitude: number | null;
    opens_at: string | null;
    closes_at: string | null;
    amenities: Record<string, unknown> | null;
  } | null;
};

export type DbMatch = {
  id: string;
  sport: string;
  scheduled_at: string;
  status: string;
  format: string;
  max_players: number;
  min_rating: number | null;
  max_rating: number | null;
  is_private: boolean;
  created_by: string | null;
  facility: { id: string; name: string; address_city: string | null } | null;
  court: { id: string; name: string } | null;
  rosters: { id: string; confirmed: boolean; player: { id: string; display_name: string; user_id: string } | null }[];
};

export type RankedPlayer = {
  id: string;
  user_id: string;
  display_name: string;
  home_city: string | null;
  preferred_sports: string[];
  bio: string | null;
  rating: number;
  wins: number;
  losses: number;
  matches_played: number;
  sport: string;
};

/* ─── RAW API RESPONSE SHAPES ───────────────────────────────── */

type LeaderboardEntry = {
  rank: number;
  player_id: string;
  display_name: string;
  sport: string;
  current_rating: number;
  wins: number;
  losses: number;
};

type MatchRosterRaw = {
  id: string;
  player_id: string;
  team: string;
  confirmed: boolean;
  attended: boolean | null;
  joined_at: string;
};

type MatchRaw = {
  id: string;
  sport: string;
  facility_id: string | null;
  court_id: string | null;
  created_by_id: string | null;
  scheduled_at: string;
  status: string;
  format: string;
  is_private: boolean;
  min_rating: number | null;
  max_rating: number | null;
  max_players: number;
  rosters: MatchRosterRaw[];
};

type FacilityRaw = {
  id: string;
  name: string;
  address_city: string | null;
  address_street: string | null;
  latitude: number | null;
  longitude: number | null;
  opens_at: string | null;
  closes_at: string | null;
};

/* ─── COURTS ────────────────────────────────────────────────── */

export async function fetchCourts(): Promise<DbCourt[]> {
  try {
    const facilities = await apiGet<FacilityRaw[]>("/facilities/");
    // Adapt facilities to the DbCourt shape for map + list display
    return facilities.map((f) => ({
      id: f.id,
      name: f.name,
      sport: "Football",
      current_occupancy: 0,
      max_capacity: 22,
      lighting_available: true,
      lighting_on: false,
      is_bookable: false,
      surface: "grass",
      indoor: false,
      facility: {
        id: f.id,
        name: f.name,
        address_city: f.address_city,
        address_street: f.address_street,
        latitude: f.latitude,
        longitude: f.longitude,
        opens_at: f.opens_at,
        closes_at: f.closes_at,
        amenities: null,
      },
    }));
  } catch {
    return [];
  }
}

export async function fetchCourtDetail(courtId: string): Promise<DbCourt | null> {
  const all = await fetchCourts();
  return all.find((c) => c.id === courtId) ?? null;
}

/* ─── MATCHES ───────────────────────────────────────────────── */

function adaptMatch(m: MatchRaw): DbMatch {
  return {
    id: m.id,
    sport: m.sport,
    scheduled_at: m.scheduled_at,
    status: m.status,
    format: m.format,
    max_players: m.max_players,
    min_rating: m.min_rating,
    max_rating: m.max_rating,
    is_private: m.is_private,
    created_by: m.created_by_id,
    facility: null,
    court: null,
    rosters: m.rosters.map((r) => ({
      id: r.id,
      confirmed: r.confirmed,
      player: { id: r.player_id, display_name: "Player", user_id: r.player_id },
    })),
  };
}

export async function fetchMatches(): Promise<DbMatch[]> {
  const data = await apiGet<MatchRaw[]>("/matches/");
  return data.map(adaptMatch);
}

export async function fetchMatchDetail(matchId: string): Promise<DbMatch | null> {
  const data = await apiGet<MatchRaw>(`/matches/${matchId}`);
  return adaptMatch(data);
}

export async function joinMatch(matchId: string): Promise<void> {
  await apiPost(`/matches/${matchId}/join`);
}

export async function leaveMatch(matchId: string): Promise<void> {
  await apiDelete(`/matches/${matchId}/leave`);
}

export async function cancelMatch(matchId: string): Promise<void> {
  await apiDelete(`/matches/${matchId}/leave`);
}

export async function createMatch(input: {
  sport: string;
  scheduled_at: string;
  format?: string;
  max_players?: number;
  court_id?: string | null;
  facility_id?: string | null;
  min_rating?: number | null;
  max_rating?: number | null;
  is_private?: boolean;
  invite_player_ids?: string[];
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/matches/", {
    sport: input.sport.toLowerCase(),
    scheduled_at: input.scheduled_at,
    format: input.format ?? "pickup",
    max_players: input.max_players ?? 10,
    court_id: input.court_id ?? null,
    facility_id: input.facility_id ?? null,
    min_rating: input.min_rating ?? null,
    max_rating: input.max_rating ?? null,
    is_private: input.is_private ?? false,
  });
}

/* ─── RANKINGS ──────────────────────────────────────────────── */

export async function fetchRankings(opts?: { sport?: string | null; city?: string | null }): Promise<RankedPlayer[]> {
  // Default to soccer for Football MVP; map Lovable sport names → our enum values
  const sportMap: Record<string, string> = {
    Football: "soccer", Padel: "padel", Tennis: "tennis", Basketball: "basketball",
  };
  const sport = opts?.sport ? (sportMap[opts.sport] ?? opts.sport.toLowerCase()) : "soccer";
  const entries = await apiGet<LeaderboardEntry[]>(`/players/leaderboard/${sport}`);
  let rows: RankedPlayer[] = entries.map((e) => ({
    id: e.player_id,
    user_id: e.player_id,
    display_name: e.display_name,
    home_city: null,
    preferred_sports: [e.sport],
    bio: null,
    rating: e.current_rating,
    wins: e.wins,
    losses: e.losses,
    matches_played: e.wins + e.losses,
    sport: e.sport,
  }));
  if (opts?.city) {
    const c = opts.city.toLowerCase();
    rows = rows.filter((p) => (p.home_city ?? "").toLowerCase() === c);
  }
  return rows;
}

/* ─── PLAYER PROFILE ────────────────────────────────────────── */

export async function getMyPlayer() {
  try {
    return await apiGet<{ id: string; display_name: string; home_city: string | null }>("/players/me");
  } catch {
    return null;
  }
}

export async function getMyProfile() {
  try {
    const p = await apiGet<{ id: string; display_name: string; city: string | null; bio: string | null }>("/players/me");
    return { id: p.id, handle: null, display_name: p.display_name, avatar_url: null, city: p.city, bio: p.bio };
  } catch {
    return null;
  }
}

export async function updateMyProfile(input: { display_name?: string; handle?: string; city?: string; bio?: string }) {
  await apiPatch("/players/me", input);
}

export async function fetchPlayerDetail(playerId: string) {
  try {
    const p = await apiGet<{ id: string; display_name: string; city: string | null; bio: string | null; current_rating?: number }>(`/players/${playerId}`);
    return {
      player: { id: p.id, user_id: p.id, display_name: p.display_name, home_city: p.city, preferred_sports: ["soccer"], bio: p.bio, age: null },
      profile: { id: p.id, handle: null, display_name: p.display_name, avatar_url: null, city: p.city, bio: p.bio },
      sports: p.current_rating != null ? [{ sport: "soccer", rating: p.current_rating, wins: 0, losses: 0, matches_played: 0 }] : [],
      followers: 0,
      following: 0,
    };
  } catch {
    return null;
  }
}

/* ─── FOLLOW ────────────────────────────────────────────────── */

export async function getFollowedUserIds(): Promise<Set<string>> {
  return new Set();
}
export async function isFollowing(_targetUserId: string): Promise<boolean> {
  return false;
}
export async function follow(_targetUserId: string): Promise<void> {}
export async function unfollow(_targetUserId: string): Promise<void> {}

export async function searchPlayers(opts: {
  q?: string;
  sport?: string | null;
  city?: string | null;
  followingOnly?: boolean;
  limit?: number;
}): Promise<Array<{ id: string; user_id: string; display_name: string; home_city: string | null; preferred_sports: string[]; bio: string | null }>> {
  try {
    const entries = await apiGet<LeaderboardEntry[]>("/players/leaderboard/soccer");
    let rows = entries.map((e) => ({
      id: e.player_id,
      user_id: e.player_id,
      display_name: e.display_name,
      home_city: null as string | null,
      preferred_sports: [e.sport],
      bio: null as string | null,
    }));
    if (opts.q) {
      const q = opts.q.toLowerCase();
      rows = rows.filter((p) => p.display_name.toLowerCase().includes(q));
    }
    return rows.slice(0, opts.limit ?? 50);
  } catch {
    return [];
  }
}
