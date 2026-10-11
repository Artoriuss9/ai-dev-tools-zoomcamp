import { analyzePlayer } from './api.js';
import { escapeHtml, formatNumber, formatSeasonTitle } from './presentation.js';

const form = document.getElementById('analyzeForm');
const input = document.getElementById('nickname');
const gameMode = document.getElementById('gameMode');
const analyzeButton = document.getElementById('analyzeButton');
const refreshButton = document.getElementById('refreshButton');
const result = document.getElementById('result');
const errorBox = document.getElementById('error');
const playerName = document.getElementById('playerName');
const analyzedCount = document.getElementById('analyzedCount');
const updatedAt = document.getElementById('updatedAt');
const seasonTitle = document.getElementById('seasonTitle');
const seasonMode = document.getElementById('seasonMode');
const seasonNote = document.getElementById('seasonNote');
const seasonMetrics = document.getElementById('seasonMetrics');
const seasonComparisonCard = document.getElementById('seasonComparisonCard');
const seasonComparison = document.getElementById('seasonComparison');
const recentAnalysis = document.getElementById('recentAnalysis');
const noRecentMatches = document.getElementById('noRecentMatches');
const matchesBody = document.getElementById('matchesBody');
const metrics = document.getElementById('metrics');
const insightHeadline = document.getElementById('insightHeadline');
const goalsList = document.getElementById('goalsList');
const strengthsList = document.getElementById('strengthsList');
const weaknessesList = document.getElementById('weaknessesList');
const rateBars = document.getElementById('rateBars');
const trendGrid = document.getElementById('trendGrid');
const mapPerformance = document.getElementById('mapPerformance');
const insightAdvice = document.getElementById('insightAdvice');
const trendComparison = document.getElementById('trendComparison');
const mapStats = document.getElementById('mapStats');

const metricLabels = {
  matches: 'Matches',
  wins: 'Wins',
  win_rate: 'Win rate',
  avg_placement: 'Avg. placement',
  avg_kills: 'Avg. kills',
  kills_per_death: 'K/D (kills/deaths)',
  kills_per_match: 'K/M',
  avg_damage: 'Avg. damage',
  avg_assists: 'Avg. assists',
  avg_survival_time: 'Avg. survival (min)'
};

const seasonMetricLabels = {
  matches: 'Matches played',
  wins: 'Wins',
  win_rate: 'Win rate',
  top_10_rate: 'Top-10 rate',
  total_kills: 'Total kills',
  kills_per_match: 'Kills per match',
  damage_per_match: 'Damage per match',
  avg_survival_time: 'Avg. survival (min)',
  total_assists: 'Total assists'
};

let lastNickname = '';

function setLoading(isLoading) {
  analyzeButton.disabled = isLoading;
  gameMode.disabled = isLoading;
  refreshButton.disabled = isLoading || !lastNickname;
  analyzeButton.textContent = isLoading ? 'Loading...' : 'Analyze';
}

function clearResult() {
  result.hidden = true;
  matchesBody.innerHTML = '';
  metrics.innerHTML = '';
  seasonMetrics.innerHTML = '';
  seasonComparison.innerHTML = '';
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearError() {
  errorBox.hidden = true;
  errorBox.textContent = '';
}

function render(data) {
  playerName.textContent = data.player.nickname;
  analyzedCount.textContent = data.analyzed_count;
  updatedAt.textContent = new Date(data.updated_at).toLocaleString();
  const selectedModeLabel = gameMode.options[gameMode.selectedIndex].text;
  seasonMode.textContent = selectedModeLabel;

  if (data.season_summary) {
    seasonTitle.textContent = formatSeasonTitle(data.season_summary.season_id);
    seasonNote.textContent = 'Season totals cover all matches reported by PUBG API for this mode.';
    seasonMetrics.innerHTML = Object.entries(data.season_summary)
      .filter(([key]) => key !== 'season_id' && key !== 'mode')
      .map(([key, value]) => {
        const formatted = key.endsWith('_rate') ? `${Number(value).toFixed(2)}%` : Number(value).toFixed(2);
        return `<div class="metric"><div class="metric-label">${seasonMetricLabels[key] || key}</div><div class="metric-value">${formatted}</div></div>`;
      }).join('');
  } else {
    seasonTitle.textContent = 'Current season';
    seasonNote.textContent = 'PUBG API has no season totals for this mode.';
  }

  recentAnalysis.hidden = !data.summary || !data.insights;
  noRecentMatches.hidden = !recentAnalysis.hidden;
  if (data.summary && data.insights) {
    metrics.innerHTML = Object.entries(data.summary).map(([key, value]) => {
      const formatted = value === null
        ? '—'
        : key === 'win_rate' ? `${Number(value).toFixed(2)}%` : Number(value).toFixed(2);
      return `<div class="metric"><div class="metric-label">${metricLabels[key] || key}</div><div class="metric-value">${formatted}</div></div>`;
    }).join('');
    renderInsights(data.insights);
  }

  matchesBody.innerHTML = data.matches.map(match => `
    <tr>
      <td>${new Date(match.played_at).toLocaleString()}</td>
      <td>${escapeHtml(match.map)}</td>
      <td>${escapeHtml(match.mode)}</td>
      <td>${match.placement}</td>
      <td>${match.kills}</td>
      <td>${match.assists}</td>
      <td>${Number(match.damage).toFixed(2)}</td>
      <td>${Number(match.survival_time).toFixed(2)} min</td>
    </tr>`).join('');

  result.hidden = false;
  refreshButton.disabled = false;
}

function renderInsights(insights) {
  insightHeadline.textContent = insights.headline;
  insightAdvice.textContent = insights.advice;
  goalsList.innerHTML = insights.next_match_goals.map(goal => `<li>${escapeHtml(goal)}</li>`).join('');
  strengthsList.innerHTML = insights.strengths.map(item => `<li>${escapeHtml(item)}</li>`).join('');
  weaknessesList.innerHTML = insights.weaknesses.map(item => `<li>${escapeHtml(item)}</li>`).join('');

  const rates = [
    ['Top-10 rate', insights.top_10_rate],
    ['Matches with a kill', insights.kill_rate],
    ['Early death rate', insights.early_death_rate]
  ];
  rateBars.innerHTML = rates.map(([label, value]) => `
    <div class="rate-row">
      <div class="rate-label"><span>${label}</span><strong>${formatNumber(value)}%</strong></div>
      <div class="rate-track"><span class="rate-fill ${label === 'Early death rate' ? 'negative' : ''}" style="width: ${Math.min(value, 100)}%"></span></div>
    </div>`).join('');

  const trend = insights.trend;
  const comparison = insights.season_comparison;
  seasonComparisonCard.hidden = !comparison;
  if (comparison) {
    const formatDelta = value => value === null
      ? 'N/A'
      : `${value > 0 ? '+' : ''}${formatNumber(value)}%`;
    seasonComparison.innerHTML = [
      ['Kills per match', comparison.recent_kills_per_match, comparison.season_kills_per_match, comparison.kills_delta_percent],
      ['Damage per match', comparison.recent_damage_per_match, comparison.season_damage_per_match, comparison.damage_delta_percent]
    ].map(([label, recent, season, delta]) => `
      <div class="comparison-column">
        <strong>${label}</strong>
        <span>Recent (${comparison.recent_matches}) <b>${formatNumber(recent)}</b></span>
        <span>Season avg. <b>${formatNumber(season)}</b></span>
        <span>Difference <b>${formatDelta(delta)}</b></span>
      </div>`).join('');
  }

  trendGrid.innerHTML = [
    ['Placement', trend.placement_delta, 'place'],
    ['Kills', trend.kills_delta, 'number'],
    ['Damage', trend.damage_delta, 'number'],
    ['Survival', trend.survival_delta, 'min']
  ].map(([label, value, kind]) => {
    const improving = label === 'Placement' ? value < 0 : value > 0;
    const sign = value > 0 ? '+' : '';
    const suffix = kind === 'min' ? ' min' : '';
    return `<div class="trend-item"><span>${label}</span><strong class="${improving ? 'positive' : value === 0 ? '' : 'negative'}">${sign}${formatNumber(value)}${suffix}</strong></div>`;
  }).join('');

  trendComparison.innerHTML = [
    [`Previous (${trend.previous_matches})`, trend.early],
    [`Recent (${trend.recent_matches})`, trend.recent]
  ].map(([label, stats]) => `
    <div class="comparison-column">
      <strong>${label}</strong>
      <span>K/M <b>${formatNumber(stats.kills_per_match)}</b></span>
      <span>Avg. damage <b>${formatNumber(stats.avg_damage)}</b></span>
    </div>`).join('');

  mapPerformance.innerHTML = insights.map_performance.map(map => `
    <div class="map-row">
      <div><strong>${escapeHtml(map.map_name)}</strong><span>${map.matches} match${map.matches === 1 ? '' : 'es'}</span></div>
      <span class="map-place">#${formatNumber(map.avg_placement)}</span>
      <span>${formatNumber(map.avg_kills)} K</span>
      <span>${formatNumber(map.avg_damage)} DMG</span>
    </div>`).join('');

  mapStats.innerHTML = Object.entries(insights.by_map).map(([map, stats]) => `
    <div class="map-stat-row">
      <strong>${escapeHtml(map)}</strong>
      <span>K/M <b>${formatNumber(stats.kills_per_match)}</b></span>
      <span>Win <b>${formatNumber(stats.win_rate)}%</b></span>
      <span>DMG <b>${formatNumber(stats.avg_damage)}</b></span>
    </div>`).join('');
}

async function runAnalysis(nickname) {
  clearError();
  clearResult();
  setLoading(true);
  try {
    const data = await analyzePlayer(nickname, gameMode.value);
    render(data);
    lastNickname = nickname;
  } catch (error) {
    lastNickname = nickname;
    showError(error.message || 'Analysis failed');
  } finally {
    setLoading(false);
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const nickname = input.value;
  if (!nickname.trim()) {
    clearResult();
    showError('Enter a nickname.');
    return;
  }
  runAnalysis(nickname);
});

refreshButton.addEventListener('click', () => {
  if (lastNickname) runAnalysis(lastNickname);
});
