from sqlalchemy import create_engine, inspect, text

from backend.app.database import ensure_death_type_column, normalize_database_url


def test_normalize_railway_postgres_url_for_psycopg():
    assert normalize_database_url("postgresql://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )
    assert normalize_database_url("postgres://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )


def test_normalize_database_url_preserves_explicit_driver_and_sqlite():
    assert normalize_database_url("postgresql+psycopg://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    assert normalize_database_url("sqlite:///./pubg.db") == "sqlite:///./pubg.db"


def test_ensure_death_type_column_migrates_existing_match_table():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE player_matches (id INTEGER PRIMARY KEY)"))

    ensure_death_type_column(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("player_matches")}
    assert "death_type" in columns
    engine.dispose()
