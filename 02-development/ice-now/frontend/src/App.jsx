import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, Clock3, Info, PanelRight, RefreshCw, X } from 'lucide-react';
import { getScoreboard } from './api/scoreboard';

const dateOptions = [
  { key: 'yesterday', label: 'Yesterday', offset: -1 },
  { key: 'today', label: 'Today', offset: 0 },
  { key: 'tomorrow', label: 'Tomorrow', offset: 1 }
];

const filters = [
  { key: 'all', label: 'All games' },
  { key: 'live', label: 'Live' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'final', label: 'Final' }
];

export function App() {
  const [dateKey, setDateKey] = useState('today');
  const [filter, setFilter] = useState('all');
  const [data, setData] = useState({ games: [], standings: [] });
  const [selectedGame, setSelectedGame] = useState(null);
  const [standingsOpen, setStandingsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);

  async function loadScoreboard({ silent = false } = {}) {
    if (silent) setRefreshing(true); else setLoading(true);
    try {
      const nextData = await getScoreboard(dateKey);
      setData(nextData);
      setLastUpdated(new Date(nextData.fetchedAt));
      setError('');
      localStorage.setItem(`ice-now-${dateKey}`, JSON.stringify(nextData));
    } catch {
      const cached = localStorage.getItem(`ice-now-${dateKey}`);
      if (cached) setData(JSON.parse(cached));
      setError('The live feed is unavailable. Showing the most recent saved scores.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    const cached = localStorage.getItem(`ice-now-${dateKey}`);
    if (cached) {
      setData(JSON.parse(cached));
      setLoading(false);
    }
    loadScoreboard({ silent: Boolean(cached) });
  }, [dateKey]);

  useEffect(() => {
    const timer = window.setInterval(() => loadScoreboard({ silent: true }), 45000);
    return () => window.clearInterval(timer);
  }, [dateKey]);

  const visibleGames = useMemo(() => {
    const priority = { live: 0, scheduled: 1, upcoming: 1, final: 2, postponed: 3, canceled: 4 };
    return data.games
      .filter((game) => filter === 'all' || game.status === (filter === 'upcoming' ? 'scheduled' : filter))
      .sort((a, b) => priority[a.status] - priority[b.status]);
  }, [data.games, filter]);

  const liveCount = data.games.filter((game) => game.status === 'live').length;
  const formattedDate = new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'short', day: 'numeric', timeZone: 'America/New_York' }).format(new Date());
  const updatedText = lastUpdated ? lastUpdated.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) : 'Waiting for feed';

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="IceNow home">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span><strong>Ice</strong>Now</span>
        </a>
        <div className="topbar-meta">
          <span className="timezone">ET / NHL</span>
          <span className="live-count"><b>{liveCount}</b> live now</span>
          <span className="refresh-status"><span className="status-dot" /> Updated {updatedText}</span>
        </div>
      </header>

      <main id="top" className="page-content">
        <section className="hero-row" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">Daily scoreboard <span>•</span> Eastern Time</p>
            <h1 id="page-title">Every game.<br /><em>Right now.</em></h1>
            <p className="hero-copy">A quick read on the league, from the first faceoff to the final horn.</p>
          </div>
          <div className="date-card">
            <CalendarDays size={18} aria-hidden="true" />
            <div><span className="date-label">Selected date</span><strong>{formattedDate}</strong></div>
          </div>
        </section>

        <nav className="date-nav" aria-label="Game date navigation">
          <button aria-label="Previous date" onClick={() => shiftDate(-1)}><ChevronLeft size={17} /></button>
          {dateOptions.map((option) => (
            <button key={option.key} className={dateKey === option.key ? 'active' : ''} onClick={() => setDateKey(option.key)}>
              <span>{option.label}</span><small>{option.key === 'today' ? 'Sep 14' : option.key === 'yesterday' ? 'Sep 13' : 'Sep 15'}</small>
            </button>
          ))}
          <button aria-label="Next date" onClick={() => shiftDate(1)}><ChevronRight size={17} /></button>
        </nav>

        {error && <div className="alert" role="alert"><Info size={17} /><span>{error}</span><button onClick={() => loadScoreboard()}><RefreshCw size={14} /> Retry</button></div>}

        <section className="scoreboard-layout">
          <div className="games-column">
            <div className="section-heading">
              <div><span className="section-kicker">Schedule</span><h2>{dateKey === 'today' ? "Today's games" : `${dateOptions.find((item) => item.key === dateKey)?.label} games`}</h2></div>
              <button className="outline-button" onClick={() => loadScoreboard({ silent: true })} disabled={refreshing}><RefreshCw size={15} className={refreshing ? 'spin' : ''} /> Refresh</button>
            </div>
            <div className="filters" role="group" aria-label="Filter games">
              {filters.map((item) => <button key={item.key} className={filter === item.key ? 'selected' : ''} onClick={() => setFilter(item.key)}>{item.label}<span>{item.key === 'all' ? data.games.length : data.games.filter((game) => game.status === (item.key === 'upcoming' ? 'scheduled' : item.key)).length}</span></button>)}
            </div>
            {loading ? <LoadingCards /> : visibleGames.length ? <div className="game-grid">{visibleGames.map((game) => <GameCard key={game.id} game={game} onClick={() => setSelectedGame(game)} />)}</div> : <EmptyState dateKey={dateKey} onDateChange={setDateKey} />}
          </div>
          <aside className={`standings-panel ${standingsOpen ? 'open' : ''}`} aria-label="NHL standings">
            <div className="standings-header"><div><span className="section-kicker">League snapshot</span><h2>Standings</h2></div><button className="icon-button" onClick={() => setStandingsOpen(false)} aria-label="Close standings"><X size={18} /></button></div>
            <p className="standings-note">Eastern Conference · through Sep 13</p>
            <Standings rows={data.standings} />
          </aside>
        </section>
      </main>

      <button className="mobile-standings" onClick={() => setStandingsOpen(true)}><PanelRight size={17} /> View standings</button>
      {selectedGame && <GameDialog game={selectedGame} onClose={() => setSelectedGame(null)} />}
    </div>
  );

  function shiftDate(direction) {
    const index = dateOptions.findIndex((option) => option.key === dateKey);
    setDateKey(dateOptions[Math.max(0, Math.min(dateOptions.length - 1, index + direction))].key);
  }
}

function GameCard({ game, onClick }) {
  const visualStatus = game.status === 'scheduled' ? 'upcoming' : game.status;
  const label = visualStatus === 'live' ? 'LIVE' : visualStatus === 'final' ? 'FINAL' : visualStatus === 'postponed' ? 'POSTPONED' : 'UPCOMING';
  return <button className={`game-card ${visualStatus}`} onClick={onClick} aria-label={`${game.away.name} at ${game.home.name}, ${label}`}>
    <div className="card-top"><span className={`game-status ${game.status}`}>{game.status === 'live' && <i />} {label}</span><span className="start-time">{game.startTime}</span></div>
    <div className="matchup"><TeamLine team={game.away} score={game.awayScore} /><span className="at">@</span><TeamLine team={game.home} score={game.homeScore} home /></div>
    <div className="card-bottom"><span>{game.detail}</span><span>{game.venue}</span></div>
  </button>;
}

function TeamLine({ team, score, home }) { return <div className="team-line"><span className="team-mark" style={{ '--team-color': team.color }}>{team.mark}</span><span className="team-name"><small>{home ? 'HOME' : 'AWAY'}</small>{team.city}</span><strong>{score ?? '—'}</strong></div>; }
function Standings({ rows }) { return <div className="standings-table"><div className="table-row table-head"><span># / TEAM</span><span>GP</span><span>W</span><span>L</span><span>OTL</span><span>PTS</span></div>{rows.map((row, index) => <div className="table-row" key={row.team.short}><span><b>{String(index + 1).padStart(2, '0')}</b><i style={{ '--team-color': row.team.color }}>{row.team.mark}</i>{row.team.short}</span><span>{row.gp}</span><span>{row.w}</span><span>{row.l}</span><span>{row.otl}</span><strong>{row.points}</strong></div>)}</div>; }
function LoadingCards() { return <div className="game-grid">{[1, 2, 3].map((item) => <div className="skeleton-card" key={item}><span /><span /><span /></div>)}</div>; }
function EmptyState({ onDateChange }) { return <div className="empty-state"><span className="empty-icon"><CalendarDays size={21} /></span><h3>No games on this date</h3><p>Take a look at the adjacent slate for more NHL action.</p><div><button onClick={() => onDateChange('yesterday')}>Yesterday</button><button onClick={() => onDateChange('tomorrow')}>Tomorrow</button></div></div>; }
function GameDialog({ game, onClose }) { const visualStatus = game.status === 'scheduled' ? 'upcoming' : game.status; return <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="game-dialog-title" onMouseDown={(event) => event.stopPropagation()}><button className="dialog-close" aria-label="Close game summary" onClick={onClose}><X size={19} /></button><span className={`game-status ${visualStatus}`}>{game.status === 'live' && <i />} {visualStatus === 'upcoming' ? 'UPCOMING' : game.status.toUpperCase()}</span><h2 id="game-dialog-title">{game.away.short} <span>at</span> {game.home.short}</h2><div className="dialog-score"><div><b>{game.awayScore ?? '—'}</b><span>{game.away.name}</span></div><strong>:</strong><div><b>{game.homeScore ?? '—'}</b><span>{game.home.name}</span></div></div><div className="detail-grid"><span><Clock3 size={15} /> {game.detail}</span><span><CalendarDays size={15} /> {game.startTime} ET</span><span><Info size={15} /> {game.venue}</span><span><RefreshCw size={15} /> Updated {game.updatedAt}</span></div></section></div>; }
