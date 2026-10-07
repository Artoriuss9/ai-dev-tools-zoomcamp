from datetime import datetime, timezone

from backend.app.analytics import calculate_insights, calculate_summary
from backend.app.models import Match, PlayerMatch


def make_row(placement, kills, assists, damage, survival):
    return PlayerMatch(
        player_id="p",
        match_id=f"m{placement}",
        placement=placement,
        kills=kills,
        assists=assists,
        damage=damage,
        survival_time=survival,
    )


def test_calculate_summary_rounds_and_counts():
    summary = calculate_summary([
        make_row(1, 4, 1, 500, 600),
        make_row(5, 2, 3, 200, 300),
    ])
    assert summary.matches == 2
    assert summary.wins == 1
    assert summary.win_rate == 50.0
    assert summary.avg_placement == 3.0
    assert summary.avg_kills == 3.0
    assert summary.kills_per_death == 6.0
    assert summary.kills_per_match == 3.0
    assert summary.avg_damage == 350.0
    assert summary.avg_assists == 2.0
    assert summary.avg_survival_time == 7.5


def test_calculate_insights_creates_actionable_guidance():
    rows = [
        make_row(35, 3, 0, 180, 180),
        make_row(8, 1, 1, 260, 720),
        make_row(4, 0, 0, 100, 200),
        make_row(12, 2, 0, 300, 840),
    ]
    for index, row in enumerate(rows):
        row.match = Match(
            match_id=f"match-{index}",
            map_name="Baltic_Main" if index < 2 else "Desert_Main",
            game_mode="solo-fpp",
            played_at=None,
        )

    insights = calculate_insights(rows)

    assert insights.early_death_rate == 50.0
    assert insights.top_10_rate == 50.0
    assert "пережить раннюю игру" in insights.headline
    assert insights.next_match_goals
    assert len(insights.map_performance) == 2


def test_calculate_insights_returns_map_stats_trend_and_advice():
    rows = [
        make_row(10, 1, 0, 100, 300),
        make_row(2, 3, 0, 300, 600),
        make_row(1, 3, 0, 250, 700),
        make_row(5, 2, 0, 200, 500),
    ]
    maps = ["Erangel_Main", "Miramar_Main", "Erangel_Main", "Miramar_Main"]
    for index, row in enumerate(rows):
        row.match = Match(
            match_id=f"trend-match-{index}",
            map_name=maps[index],
            game_mode="solo-fpp",
            played_at=datetime(2026, 9, index + 1, tzinfo=timezone.utc),
        )

    insights = calculate_insights(rows)

    assert insights.by_map["Erangel_Main"].kills_per_match == 2.0
    assert insights.by_map["Erangel_Main"].win_rate == 50.0
    assert insights.by_map["Erangel_Main"].avg_damage == 175.0
    assert insights.trend.early.kills_per_match == 2.0
    assert insights.trend.recent.kills_per_match == 2.5
    assert insights.trend.early.avg_damage == 200.0
    assert insights.trend.recent.avg_damage == 225.0
    assert "Отличный прогресс" in insights.advice
