from backend.app.service import AnalysisService


def test_analyze_filters_mode_and_deduplicates(db, sample_player, sample_matches):
    from tests.conftest import FakePUBGClient

    client = FakePUBGClient(sample_player, sample_matches + [sample_matches[0]])
    service = AnalysisService(client=client, db=db, mode="solo-fpp")

    import asyncio
    response = asyncio.run(service.analyze("TestPlayer"))

    assert response.analyzed_count == 2
    assert response.summary.matches == 2
    assert [m.match_id for m in response.matches] == ["m2", "m1"]
    assert response.summary.kills_per_match == 3.5


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
