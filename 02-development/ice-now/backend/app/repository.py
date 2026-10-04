from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import GameRecord, StandingRecord
from .models import Game, Standing, Team


def team(name: str, short: str, city: str, color: str, mark: str) -> Team:
    return Team(name=name, short=short, city=city, color=color, mark=mark)


TEAMS = {
    'TOR': team('Toronto Maple Leafs', 'TOR', 'Toronto', '#0b6e69', 'T'), 'BOS': team('Boston Bruins', 'BOS', 'Boston', '#d3a21a', 'B'),
    'EDM': team('Edmonton Oilers', 'EDM', 'Edmonton', '#d05a2a', 'O'), 'VAN': team('Vancouver Canucks', 'VAN', 'Vancouver', '#1f6f75', 'V'),
    'NYR': team('New York Rangers', 'NYR', 'New York', '#2f62a0', 'R'), 'DET': team('Detroit Red Wings', 'DET', 'Detroit', '#c54845', 'W'),
    'COL': team('Colorado Avalanche', 'COL', 'Denver', '#8b3343', 'A'), 'DAL': team('Dallas Stars', 'DAL', 'Dallas', '#1f765e', 'S'),
    'MTL': team('Montreal Canadiens', 'MTL', 'Montreal', '#b33b43', 'C'), 'OTT': team('Ottawa Senators', 'OTT', 'Ottawa', '#b44a3e', 'S'),
    'SEA': team('Seattle Kraken', 'SEA', 'Seattle', '#347d83', 'K'), 'NJD': team('New Jersey Devils', 'NJD', 'New Jersey', '#bc3d46', 'D'),
}


def game(game_id, away, home, status, away_score, home_score, detail, venue, start_time):
    return Game(id=game_id, away=TEAMS[away], home=TEAMS[home], status=status, awayScore=away_score, homeScore=home_score, detail=detail, venue=venue, startTime=start_time, updatedAt='Just now')


GAMES_BY_DATE = {
    'yesterday': [game('y1', 'NYR', 'DET', 'final', 4, 2, 'Final', 'Madison Square Garden', '7:00 PM'), game('y2', 'COL', 'DAL', 'final', 2, 3, 'Final', 'Ball Arena', '9:30 PM'), game('y3', 'MTL', 'OTT', 'final', 1, 1, 'Final / SO', 'Bell Centre', '7:30 PM')],
    'today': [game('t1', 'TOR', 'BOS', 'live', 3, 2, '2nd · 08:42', 'Scotiabank Arena', '7:00 PM'), game('t2', 'EDM', 'VAN', 'scheduled', None, None, 'Starts in 38 min', 'Rogers Place', '9:00 PM'), game('t3', 'NYR', 'DET', 'scheduled', None, None, 'Starts in 2 hr 08 min', 'Little Caesars Arena', '7:30 PM'), game('t4', 'COL', 'DAL', 'final', 4, 1, 'Final', 'Ball Arena', '4:00 PM'), game('t5', 'SEA', 'NJD', 'postponed', None, None, 'Postponed', 'Climate Pledge Arena', '8:00 PM')],
    'tomorrow': [game('m1', 'TOR', 'MTL', 'scheduled', None, None, 'Tomorrow · 7:00 PM', 'Scotiabank Arena', '7:00 PM'), game('m2', 'BOS', 'OTT', 'scheduled', None, None, 'Tomorrow · 7:30 PM', 'TD Garden', '7:30 PM'), game('m3', 'EDM', 'SEA', 'scheduled', None, None, 'Tomorrow · 9:00 PM', 'Rogers Place', '9:00 PM')],
}

STANDINGS = [
    Standing(team=TEAMS['TOR'], gp=21, w=14, l=5, otl=2, points=30, differential=18), Standing(team=TEAMS['BOS'], gp=21, w=13, l=6, otl=2, points=27, differential=16),
    Standing(team=TEAMS['NYR'], gp=22, w=13, l=7, otl=2, points=28, differential=12), Standing(team=TEAMS['EDM'], gp=21, w=12, l=7, otl=2, points=26, differential=9),
    Standing(team=TEAMS['COL'], gp=22, w=12, l=8, otl=2, points=26, differential=7), Standing(team=TEAMS['DAL'], gp=21, w=11, l=8, otl=2, points=24, differential=5),
    Standing(team=TEAMS['VAN'], gp=22, w=10, l=9, otl=3, points=23, differential=2), Standing(team=TEAMS['DET'], gp=21, w=9, l=10, otl=2, points=20, differential=-3),
]


def get_games(session: Session, date_key: str) -> list[Game]:
    records = session.scalars(select(GameRecord).where(GameRecord.date_key == date_key)).all()
    return [Game(id=record.id, away=to_team(record.away), home=to_team(record.home), status=record.status, awayScore=record.away_score, homeScore=record.home_score, detail=record.detail, venue=record.venue, startTime=record.start_time, updatedAt=record.updated_at) for record in records]


def get_standings(session: Session) -> list[Standing]:
    records = session.scalars(select(StandingRecord).order_by(StandingRecord.points.desc())).all()
    return [Standing(team=to_team(record.team), gp=record.gp, w=record.wins, l=record.losses, otl=record.otl, points=record.points, differential=record.differential) for record in records]


def to_team(record) -> Team:
    return Team(name=record.name, short=record.short, city=record.city, color=record.color, mark=record.mark)
