from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_database, seed_database, utc_now
from .models import ScoreboardResponse
from .repository import GAMES_BY_DATE, STANDINGS, TEAMS, get_games, get_standings


def create_app(database_url: str | None = None) -> FastAPI:
    _, session_factory = create_database(database_url)
    seed_database(session_factory, GAMES_BY_DATE, TEAMS, STANDINGS)
    application = FastAPI(title='IceNow API', version='0.1.0')
    application.state.session_factory = session_factory
    application.add_middleware(
        CORSMiddleware,
        allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
        allow_credentials=True,
        allow_methods=['GET'],
        allow_headers=['*'],
    )

    @application.get('/health')
    def health() -> dict[str, str]:
        return {'status': 'ok'}

    @application.get('/api/scoreboard/{date_key}', response_model=ScoreboardResponse)
    def scoreboard(date_key: Literal['yesterday', 'today', 'tomorrow']) -> ScoreboardResponse:
        with session_factory() as session:
            return ScoreboardResponse(
                dateKey=date_key,
                games=get_games(session, date_key),
                standings=get_standings(session),
                fetchedAt=utc_now(),
            )

    return application


app = create_app()
