const teams = {
  tor: { name: 'Toronto Maple Leafs', short: 'TOR', city: 'Toronto', color: '#0b6e69', mark: 'T' },
  bos: { name: 'Boston Bruins', short: 'BOS', city: 'Boston', color: '#d3a21a', mark: 'B' },
  edm: { name: 'Edmonton Oilers', short: 'EDM', city: 'Edmonton', color: '#d05a2a', mark: 'O' },
  van: { name: 'Vancouver Canucks', short: 'VAN', city: 'Vancouver', color: '#1f6f75', mark: 'V' },
  nyr: { name: 'New York Rangers', short: 'NYR', city: 'New York', color: '#2f62a0', mark: 'R' },
  det: { name: 'Detroit Red Wings', short: 'DET', city: 'Detroit', color: '#c54845', mark: 'W' },
  col: { name: 'Colorado Avalanche', short: 'COL', city: 'Denver', color: '#8b3343', mark: 'A' },
  dal: { name: 'Dallas Stars', short: 'DAL', city: 'Dallas', color: '#1f765e', mark: 'S' },
  mtl: { name: 'Montreal Canadiens', short: 'MTL', city: 'Montreal', color: '#b33b43', mark: 'C' },
  ott: { name: 'Ottawa Senators', short: 'OTT', city: 'Ottawa', color: '#b44a3e', mark: 'S' },
  sea: { name: 'Seattle Kraken', short: 'SEA', city: 'Seattle', color: '#347d83', mark: 'K' },
  njd: { name: 'New Jersey Devils', short: 'NJD', city: 'New Jersey', color: '#bc3d46', mark: 'D' }
};

const gamesByDate = {
  yesterday: [
    makeGame('y1', 'nyr', 'det', 'final', 4, 2, 'Final', 'Madison Square Garden', '7:00 PM'),
    makeGame('y2', 'col', 'dal', 'final', 2, 3, 'Final', 'Ball Arena', '9:30 PM'),
    makeGame('y3', 'mtl', 'ott', 'final', 1, 1, 'Final / SO', 'Bell Centre', '7:30 PM')
  ],
  today: [
    makeGame('t1', 'tor', 'bos', 'live', 3, 2, '2nd · 08:42', 'Scotiabank Arena', '7:00 PM'),
    makeGame('t2', 'edm', 'van', 'upcoming', null, null, 'Starts in 38 min', 'Rogers Place', '9:00 PM'),
    makeGame('t3', 'nyr', 'det', 'upcoming', null, null, 'Starts in 2 hr 08 min', 'Little Caesars Arena', '7:30 PM'),
    makeGame('t4', 'col', 'dal', 'final', 4, 1, 'Final', 'Ball Arena', '4:00 PM'),
    makeGame('t5', 'sea', 'njd', 'postponed', null, null, 'Postponed', 'Climate Pledge Arena', '8:00 PM')
  ],
  tomorrow: [
    makeGame('m1', 'tor', 'mtl', 'upcoming', null, null, 'Tomorrow · 7:00 PM', 'Scotiabank Arena', '7:00 PM'),
    makeGame('m2', 'bos', 'ott', 'upcoming', null, null, 'Tomorrow · 7:30 PM', 'TD Garden', '7:30 PM'),
    makeGame('m3', 'edm', 'sea', 'upcoming', null, null, 'Tomorrow · 9:00 PM', 'Rogers Place', '9:00 PM')
  ]
};

function makeGame(id, awayKey, homeKey, status, awayScore, homeScore, detail, venue, startTime) {
  return { id, away: teams[awayKey], home: teams[homeKey], status, awayScore, homeScore, detail, venue, startTime, updatedAt: 'Just now' };
}

export async function getScoreboard(dateKey) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/scoreboard/${dateKey}`);
  if (!response.ok) throw new Error(`Scoreboard request failed: ${response.status}`);
  return response.json();
}

export async function getStandings() {
  return [
    row('tor', 21, 14, 5, 2, 30, 18), row('bos', 21, 13, 6, 2, 27, 16), row('nyr', 22, 13, 7, 2, 28, 12),
    row('edm', 21, 12, 7, 2, 26, 9), row('col', 22, 12, 8, 2, 26, 7), row('dal', 21, 11, 8, 2, 24, 5),
    row('van', 22, 10, 9, 3, 23, 2), row('det', 21, 9, 10, 2, 20, -3)
  ];
}

function row(teamKey, gp, w, l, otl, points, differential) {
  return { team: teams[teamKey], gp, w, l, otl, points, differential };
}
