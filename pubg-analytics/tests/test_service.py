from backend.app.service import AnalysisService


def test_analyze_filters_mode_and_deduplicates(db, sample_player, sample_matches):
    from tests.conftest import FakePUBGClient

    client = FakePUBGClient(sample_player, sample_matches + [sample_matches[0]])
    service = AnalysisService(client=client, db=db, mode="solo-fpp")

    import asyncio
    response = asyncio.run(service.analyze("TestPlayer"))

    assert response.analyzed_count == 2
    assert response.summary.matches == 2
    assert response.summary.kills_per_death == 7.0
    assert response.mode == "solo-fpp"
    assert response.season_summary is not None
    assert response.season_summary.matches == 2
    assert response.season_summary.wins == 1
    assert response.insights is not None
    assert response.insights.season_comparison is not None
    assert response.insights.season_comparison.recent_matches == 2
    assert [m.match_id for m in response.matches] == ["m2", "m1"]
    assert response.summary.kills_per_match == 3.5


def test_analyze_accepts_selected_mode_and_returns_season_totals(db, sample_player, sample_matches):
    from tests.conftest import FakePUBGClient
    import asyncio

    client = FakePUBGClient(sample_player, sample_matches)
    service = AnalysisService(client=client, db=db, mode="solo-fpp")
    response = asyncio.run(service.analyze("TestPlayer", "squad-fpp"))

    assert response.mode == "squad-fpp"
    assert response.analyzed_count == 1
    assert response.summary is not None
    assert response.summary.matches == 1
    assert response.season_summary is not None
    assert response.season_summary.matches == 1
    assert response.season_summary.total_kills == 7
    assert response.insights is not None
    assert response.insights.season_comparison is not None
    assert response.insights.season_comparison.kills_delta_percent == 0


def test_analyze_compares_recent_performance_with_season_average(db, sample_player, sample_matches):
    from tests.conftest import FakePUBGClient
    from backend.app.pubg_client import APIGameModeStats, APIPlayerSeason
    import asyncio

    class SeasonBenchmarkClient(FakePUBGClient):
        async def get_current_season_player(self, player_id: str, mode: str) -> APIPlayerSeason:
            return APIPlayerSeason(
                season_id="season",
                match_ids=["m1", "m2"],
                stats=APIGameModeStats(
                    matches=10,
                    wins=1,
                    top_10s=4,
                    kills=10,
                    damage=2000,
                    survival_time=6000,
                    assists=0,
                ),
            )

    service = AnalysisService(SeasonBenchmarkClient(sample_player, sample_matches), db, "solo-fpp")
    response = asyncio.run(service.analyze("TestPlayer"))

    assert response.insights is not None
    comparison = response.insights.season_comparison
    assert comparison is not None
    assert comparison.recent_kills_per_match == 3.5
    assert comparison.season_kills_per_match == 1
    assert comparison.kills_delta_percent == 250
    assert comparison.recent_damage_per_match == 375
    assert comparison.season_damage_per_match == 200
    assert comparison.damage_delta_percent == 87.5


def test_analyze_returns_season_totals_when_no_recent_match_details(db, sample_player, sample_matches):
    from tests.conftest import FakePUBGClient
    import asyncio
    from backend.app.pubg_client import APIPlayerSeason

    client = FakePUBGClient(sample_player, sample_matches)
    class SeasonStatsWithoutRecentMatches(FakePUBGClient):
        async def get_current_season_player(self, player_id: str, mode: str) -> APIPlayerSeason:
            season = await super().get_current_season_player(player_id, mode)
            return APIPlayerSeason(season.season_id, [], season.stats)

    client = SeasonStatsWithoutRecentMatches(sample_player, sample_matches)
    service = AnalysisService(client=client, db=db, mode="solo-fpp")

    response = asyncio.run(service.analyze("TestPlayer"))

    assert response.season_summary is not None
    assert response.season_summary.matches == 2
    assert response.summary is None
    assert response.insights is None
    assert response.matches == []


def test_upsert_updates_existing_match(db, sample_player, sample_matches):
    from tests.conftest import FakePUBGClient
    import asyncio

    from backend.app.pubg_client import APIPlayer
    player = APIPlayer(player_id=sample_player.player_id, nickname=sample_player.nickname, match_ids=["m1", "m2"])
    client = FakePUBGClient(player, sample_matches[:2])
    service = AnalysisService(client=client, db=db, mode="solo-fpp")
    asyncio.run(service.analyze("TestPlayer"))

    updated = sample_matches[0].__class__(
        "m1", "Baltic_Main", "solo-fpp", sample_matches[0].played_at, 2, 9, 0, 777, 1200
    )
    client.matches["m1"] = updated
    asyncio.run(service.analyze("TestPlayer"))

    from sqlalchemy import select
    from backend.app.models import PlayerMatch
    row = db.scalar(select(PlayerMatch).where(PlayerMatch.player_id == "account.test", PlayerMatch.match_id == "m1"))
    assert row is not None
    assert row.kills == 9
    assert row.damage == 777
