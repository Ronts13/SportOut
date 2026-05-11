export type Player = {
  rank: number;
  name: string;
  initial: string;
  sport: string;
  secondarySport?: string;
  city: string;
  rating: number;
  wins: number;
  losses: number;
  bio: string;
  badges: string[];
};

export const PLAYERS: Player[] = [
  { rank:1,  name:'Ron',            initial:'R', sport:'Padel',      secondarySport:'Football', city:'Tel Aviv',  rating:94, wins:38, losses:4,  bio:'🎾 Dominating courts in Tel Aviv | 🏆 #1 Ranked', badges:['🔥 5+ Win Streak','🏆 #1 Ranked','🎯 Sniper'] },
  { rank:2,  name:'Kobi Bar',       initial:'K', sport:'Padel',      city:'Tel Aviv',  rating:89, wins:31, losses:7,  bio:'🎾 Padel addict | 🌟 2× City Champ', badges:['⚡ Net King','🌟 2× Champ'] },
  { rank:3,  name:'Lior Khaytov',   initial:'L', sport:'Padel',      city:'Ramat Gan', rating:80, wins:28, losses:10, bio:'🎾 Spinning winners | 🔥 Rising fast', badges:['🔥 Rising Star','💪 Spin Master'] },
  { rank:4,  name:'Idan Levy',      initial:'I', sport:'Padel',      city:'Herzliya',  rating:78, wins:22, losses:12, bio:'🎾 Court warrior | 🏅 Weekend champion', badges:['🏅 Weekend Champ'] },
  { rank:5,  name:'Liran Malki',    initial:'L', sport:'Padel',      city:'Tel Aviv',  rating:74, wins:18, losses:14, bio:'🎾 Serve & volley king', badges:['⚔️ Court Warrior'] },
  { rank:6,  name:'Ofir Tuti',      initial:'O', sport:'Padel',      city:'Petah Tikva', rating:68, wins:15, losses:16, bio:'🎾 Smashing it in Petah Tikva', badges:[] },
  { rank:7,  name:'Dan Haim Lee',   initial:'D', sport:'Tennis',     city:'Tel Aviv',  rating:63, wins:12, losses:18, bio:'🎾 Serving aces in Tel Aviv', badges:['🎯 Ace Machine'] },
  { rank:8,  name:'Ron Tsemakhman', initial:'R', sport:'Football',   city:'Holon',     rating:59, wins:9,  losses:20, bio:'⚽ Goals & glory in Holon', badges:['⚽ Left-Foot Special'] },
  { rank:9,  name:'Aviram Shuster', initial:'A', sport:'Basketball', city:'Tel Aviv',  rating:55, wins:6,  losses:22, bio:'🏀 Hoops life in Tel Aviv', badges:['🎯 Sharp Shooter'] },
  { rank:10, name:'Nir Cohen',      initial:'N', sport:'Padel',      city:'Givatayim', rating:65, wins:14, losses:17, bio:'🎾 Givatayim padel scene', badges:[] },
  { rank:11, name:'Yoav Ben-David', initial:'Y', sport:'Padel',      city:'Tel Aviv',  rating:62, wins:11, losses:19, bio:'🎾 Early morning grinder', badges:[] },
  { rank:12, name:'Tal Levy',       initial:'T', sport:'Padel',      city:'Herzliya',  rating:59, wins:9,  losses:21, bio:'🎾 Net play specialist', badges:[] },
  { rank:19, name:'Yael Katz',      initial:'Y', sport:'Tennis',     city:'Tel Aviv',  rating:60, wins:10, losses:20, bio:'🎾 Serve & conquer', badges:['🏆 Club Champ'] },
  { rank:24, name:'David Azoulay',  initial:'D', sport:'Football',   city:'Tel Aviv',  rating:71, wins:16, losses:14, bio:'⚽ Central midfield maestro', badges:['🎯 Playmaker'] },
  { rank:25, name:'Yossi Gabay',    initial:'Y', sport:'Football',   city:'Petah Tikva', rating:64, wins:12, losses:18, bio:'⚽ Winger with pace', badges:['💨 Speed Demon'] },
  { rank:31, name:'Rotem Hadad',    initial:'R', sport:'Basketball', city:'Tel Aviv',  rating:68, wins:14, losses:16, bio:'🏀 Point guard vision', badges:['👑 Court General'] },
  { rank:32, name:'Lior Ohana',     initial:'L', sport:'Basketball', city:'Herzliya',  rating:61, wins:10, losses:20, bio:'🏀 Power forward muscle', badges:[] },
  { rank:36, name:'Ido Shemesh',    initial:'I', sport:'Table Tennis', city:'Tel Aviv', rating:72, wins:20, losses:8, bio:'🏓 Spin master', badges:['🌀 Spin King'] },
  { rank:37, name:'Eitan Mor',      initial:'E', sport:'Table Tennis', city:'Holon',   rating:65, wins:14, losses:12, bio:'🏓 Quick reflexes', badges:[] },
  { rank:38, name:'Roi Maman',      initial:'R', sport:'Footvolley', city:'Tel Aviv',  rating:67, wins:11, losses:9, bio:'🏐 Beach acrobat', badges:[] },
  { rank:39, name:'Niv Aroch',      initial:'N', sport:'Footvolley', city:'Tel Aviv',  rating:60, wins:8, losses:11, bio:'🏐 Tel Baruch regular', badges:[] },
  { rank:40, name:'Asaf Klein',     initial:'A', sport:'Boxing',     city:'Ramat Gan', rating:75, wins:14, losses:3, bio:'🥊 Iron jaw', badges:['🥊 Knockout King'] },
];

export type Court = {
  id: number;
  name: string;
  lat: number; lng: number;
  live: boolean;
  sport: string;
  distance: string;
  price: string;
  openHours: string;
  peakHours: string;
  lightsOut: string;
  hasShade: boolean;
  totalCourts: number;
  openCourts: number;
  currentPlayers: number;
  avgRating: number;
  playersCurrentlyOnCourt: number[];
};

export const COURTS: Court[] = [
  { id:0, name:'Sportek Tel Aviv',    lat:32.0856, lng:34.7916, live:true,  sport:'Padel',      distance:'1.2 km', price:'120 ILS/hr', openHours:'06:00 – 23:00', peakHours:'18:00 – 21:00', lightsOut:'23:00', hasShade:true,  totalCourts:4, openCourts:3, currentPlayers:14, avgRating:82, playersCurrentlyOnCourt:[1,2,3,5,10,11] },
  { id:1, name:'Dubnov Park Courts',  lat:32.0801, lng:34.7793, live:true,  sport:'Tennis',     distance:'2.4 km', price:'Free',       openHours:'07:00 – 22:00', peakHours:'17:00 – 20:00', lightsOut:'22:00', hasShade:false, totalCourts:2, openCourts:2, currentPlayers:6,  avgRating:71, playersCurrentlyOnCourt:[7,19] },
  { id:2, name:'Padel Expo Tel Aviv', lat:32.1070, lng:34.8430, live:false, sport:'Padel',      distance:'5.1 km', price:'95 ILS/hr',  openHours:'08:00 – 22:00', peakHours:'19:00 – 21:00', lightsOut:'22:00', hasShade:true,  totalCourts:6, openCourts:0, currentPlayers:0,  avgRating:78, playersCurrentlyOnCourt:[] },
  { id:3, name:'Adidas Court Tel Aviv', lat:32.0968, lng:34.7721, live:true, sport:'Basketball', distance:'2.8 km', price:'Free',      openHours:'08:00 – 22:00', peakHours:'16:00 – 20:00', lightsOut:'22:00', hasShade:false, totalCourts:2, openCourts:2, currentPlayers:8,  avgRating:64, playersCurrentlyOnCourt:[31,32,9] },
  { id:4, name:'Herzliya Marina Padel', lat:32.1641, lng:34.8046, live:true, sport:'Padel',     distance:'9.2 km', price:'150 ILS/hr', openHours:'07:00 – 23:00', peakHours:'17:00 – 21:00', lightsOut:'23:00', hasShade:true,  totalCourts:3, openCourts:2, currentPlayers:10, avgRating:76, playersCurrentlyOnCourt:[4,12] },
  { id:5, name:'Gordon Beach Courts', lat:32.0811, lng:34.7662, live:true,  sport:'Football',   distance:'3.4 km', price:'Free',       openHours:'06:00 – 22:00', peakHours:'17:00 – 20:00', lightsOut:'22:00', hasShade:false, totalCourts:1, openCourts:1, currentPlayers:12, avgRating:58, playersCurrentlyOnCourt:[24,25,8] },
  { id:6, name:'Bloomfield Stadium',  lat:32.0511, lng:34.7570, live:true,  sport:'Football',   distance:'5.6 km', price:'80 ILS/hr',  openHours:'08:00 – 22:00', peakHours:'19:00 – 22:00', lightsOut:'22:00', hasShade:true,  totalCourts:3, openCourts:2, currentPlayers:9,  avgRating:62, playersCurrentlyOnCourt:[8] },
  { id:7, name:'Tel Baruch Beach Arena', lat:32.1127, lng:34.7960, live:true, sport:'Footvolley', distance:'7.4 km', price:'Free',     openHours:'06:00 – 20:00', peakHours:'07:00 – 10:00', lightsOut:'No lights', hasShade:false, totalCourts:2, openCourts:2, currentPlayers:4, avgRating:59, playersCurrentlyOnCourt:[38,39] },
];

export type MatchLobby = {
  id: number;
  sport: string;
  courtIndex: number;
  time: string;
  format: string;
  missingPlayers: number;
  avgRating: number;
  avgAge: number;
  joinedPlayers: number[];
};

export const MATCHES: MatchLobby[] = [
  { id:1, sport:'Padel',      courtIndex:0, time:'18:30', format:'2v2', missingPlayers:1, avgRating:87, avgAge:29, joinedPlayers:[1,2,3] },
  { id:2, sport:'Football',   courtIndex:5, time:'19:00', format:'5v5', missingPlayers:3, avgRating:61, avgAge:25, joinedPlayers:[24,25,8] },
  { id:3, sport:'Padel',      courtIndex:4, time:'20:00', format:'2v2', missingPlayers:2, avgRating:76, avgAge:31, joinedPlayers:[10,11] },
  { id:4, sport:'Basketball', courtIndex:3, time:'21:00', format:'3v3', missingPlayers:1, avgRating:57, avgAge:24, joinedPlayers:[31,32,9] },
  { id:5, sport:'Tennis',     courtIndex:1, time:'17:00', format:'1v1', missingPlayers:1, avgRating:63, avgAge:27, joinedPlayers:[7] },
  { id:6, sport:'Padel',      courtIndex:0, time:'09:00', format:'2v2', missingPlayers:4, avgRating:91, avgAge:26, joinedPlayers:[3,4] },
  { id:7, sport:'Table Tennis', courtIndex:1, time:'16:00', format:'1v1', missingPlayers:1, avgRating:70, avgAge:30, joinedPlayers:[36] },
];

export const SPORT_EMOJI: Record<string, string> = {
  Padel: '🎾', Tennis: '🎾', Football: '⚽', Basketball: '🏀',
  'Table Tennis': '🏓', Footvolley: '🏐', Boxing: '🥊',
};

export const SPORTS = ['All Sports','Padel','Tennis','Football','Basketball','Table Tennis','Footvolley','Boxing'];

export const ME = PLAYERS[0];
