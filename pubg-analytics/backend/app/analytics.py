from collections import defaultdict
from dataclasses import dataclass

from .models import PlayerMatch


@dataclass(frozen=True)
class Summary:
    matches: int
    wins: int
    win_rate: float
    avg_placement: float
    avg_kills: float
    kills_per_death: float
    kills_per_match: float
    avg_damage: float
    avg_assists: float
    avg_survival_time: float


@dataclass(frozen=True)
class Trend:
    recent_matches: int
    previous_matches: int
    placement_delta: float
    kills_delta: float
    damage_delta: float
    survival_delta: float
    early: "TrendStats"
    recent: "TrendStats"


@dataclass(frozen=True)
class TrendStats:
    kills_per_match: float
    avg_damage: float


@dataclass(frozen=True)
class MapStats:
    kills_per_match: float
    win_rate: float
    avg_damage: float


@dataclass(frozen=True)
class MapPerformance:
    map_name: str
    matches: int
    avg_placement: float
    avg_kills: float
    avg_damage: float


@dataclass(frozen=True)
class Insights:
    headline: str
    profile: str
    strengths: list[str]
    weaknesses: list[str]
    next_match_goals: list[str]
    early_death_rate: float
    top_10_rate: float
    kill_rate: float
    trend: Trend
    map_performance: list[MapPerformance]
    by_map: dict[str, MapStats]
    advice: str


def calculate_summary(rows: list[PlayerMatch]) -> Summary:
    count = len(rows)
    if count == 0:
        raise ValueError("Cannot calculate summary for zero matches")

    total_kills = sum(row.kills for row in rows)
    wins = sum(1 for row in rows if row.placement == 1)
    losses = count - wins
    return Summary(
        matches=count,
        wins=wins,
        win_rate=round(wins / count * 100, 2),
        avg_placement=round(sum(row.placement for row in rows) / count, 2),
        avg_kills=round(total_kills / count, 2),
        kills_per_death=round(total_kills / losses, 2) if losses else float(total_kills),
        kills_per_match=round(total_kills / count, 2),
        avg_damage=round(sum(row.damage for row in rows) / count, 2),
        avg_assists=round(sum(row.assists for row in rows) / count, 2),
        avg_survival_time=round(sum(row.survival_time for row in rows) / count / 60, 2),
    )


def calculate_insights(rows: list[PlayerMatch]) -> Insights:
    count = len(rows)
    if count == 0:
        raise ValueError("Cannot calculate insights for zero matches")

    average_survival = sum(row.survival_time for row in rows) / count
    average_placement = sum(row.placement for row in rows) / count
    average_damage = sum(row.damage for row in rows) / count
    average_kills = sum(row.kills for row in rows) / count
    early_deaths = sum(1 for row in rows if row.survival_time < 5 * 60)
    top_10 = sum(1 for row in rows if row.placement <= 10)
    kills = sum(1 for row in rows if row.kills > 0)
    early_death_rate = round(early_deaths / count * 100, 2)
    top_10_rate = round(top_10 / count * 100, 2)
    kill_rate = round(kills / count * 100, 2)

    strengths: list[str] = []
    weaknesses: list[str] = []
    if top_10_rate >= 50:
        strengths.append(f"Топ-10 в {top_10_rate:g}% матчей")
    if average_survival >= 12 * 60:
        strengths.append("Хорошая выживаемость")
    if average_kills >= 2:
        strengths.append(f"В среднем {average_kills:.1f} убийства за матч")
    if average_damage >= 300:
        strengths.append("Уверенное влияние на перестрелки")
    if early_death_rate >= 30:
        weaknesses.append(f"Ранние смерти в {early_death_rate:g}% матчей")
    if average_damage < 250:
        weaknesses.append("Низкий средний урон")
    if average_placement > 25:
        weaknesses.append("Часто не хватает стабильного позиционирования")
    if kill_rate < 50:
        weaknesses.append("Мало матчей с хотя бы одним убийством")
    if not strengths:
        strengths.append("Есть база для роста: статистика уже собирается по каждой катке")
    if not weaknesses:
        weaknesses.append("Явных провалов в последних матчах не видно")

    goals: list[str] = []
    if early_death_rate >= 30:
        goals.append("Пережить первые 5 минут без рискованной перестрелки")
    if average_damage < 250:
        goals.append("Нанести минимум 250 урона")
    if top_10_rate < 50:
        goals.append("Попасть в топ-10")
    if average_kills < 2:
        goals.append("Найти хотя бы один контролируемый бой после первой ротации")
    if not goals:
        goals.append("Сохранить текущую стабильность и искать один дополнительный выигранный бой")

    if early_death_rate >= 30:
        headline = "Главный резерв роста — пережить раннюю игру"
    elif average_damage < 250:
        headline = "Ты выживаешь, но можешь сильнее влиять на бои"
    elif top_10_rate < 50:
        headline = "Следующая цель — стабильнее доходить до топ-10"
    else:
        headline = "Форма выглядит стабильной: пора улучшать качество боёв"

    if average_kills >= 3 and average_placement > 25:
        profile = "Агрессивный игрок: находишь фраги, но иногда теряешь матч после перестрелок"
    elif average_survival >= 12 * 60 and average_damage < 250:
        profile = "Осторожный игрок: хорошо выживаешь, но редко создаёшь давление"
    elif top_10_rate >= 60:
        profile = "Стабильный игрок: позиционирование уже приносит результат"
    else:
        profile = "Развивающийся игрок: результат пока зависит от конкретной катки"

    rows_by_time = sorted(
        rows,
        key=lambda row: row.match.played_at if row.match and row.match.played_at else 0,
    )
    split_index = max(1, count // 2)
    early = rows_by_time[:split_index]
    recent = rows_by_time[split_index:] or early
    previous = early

    def average(items: list[PlayerMatch], attribute: str) -> float:
        return sum(getattr(item, attribute) for item in items) / len(items)

    early_stats = TrendStats(
        kills_per_match=round(average(early, "kills"), 2),
        avg_damage=round(average(early, "damage"), 2),
    )
    recent_stats = TrendStats(
        kills_per_match=round(average(recent, "kills"), 2),
        avg_damage=round(average(recent, "damage"), 2),
    )
    trend = Trend(
        recent_matches=len(recent),
        previous_matches=len(previous),
        placement_delta=round(average(recent, "placement") - average(early, "placement"), 2),
        kills_delta=round(average(recent, "kills") - average(early, "kills"), 2),
        damage_delta=round(average(recent, "damage") - average(early, "damage"), 2),
        survival_delta=round((average(recent, "survival_time") - average(early, "survival_time")) / 60, 2),
        early=early_stats,
        recent=recent_stats,
    )

    kills_change = (recent_stats.kills_per_match - early_stats.kills_per_match) / early_stats.kills_per_match \
        if early_stats.kills_per_match else (1 if recent_stats.kills_per_match else 0)
    damage_change = (recent_stats.avg_damage - early_stats.avg_damage) / early_stats.avg_damage \
        if early_stats.avg_damage else 0
    if kills_change >= 0.2:
        advice = "Отличный прогресс! Ваша эффективность в бою растет. Продолжайте в том же духе."
    elif damage_change <= -0.15:
        advice = "Вы стали наносить меньше урона за матч. Возможно, вы стали осторожничать или чаще гибнуть в начале. Попробуйте активнее участвовать в перестрелках."
    elif abs(kills_change) <= 0.1 and abs(damage_change) <= 0.1:
        advice = "Ваша игра стабильна. Чтобы расти, попробуйте менять стратегию на разных картах."
    else:
        advice = "Сравните последние матчи с ранними и закрепите то, что помогает чаще выигрывать перестрелки."

    grouped: dict[str, list[PlayerMatch]] = defaultdict(list)
    for row in rows:
        grouped[row.match.map_name].append(row)
    map_performance = [
        MapPerformance(
            map_name=map_name,
            matches=len(map_rows),
            avg_placement=round(average(map_rows, "placement"), 2),
            avg_kills=round(average(map_rows, "kills"), 2),
            avg_damage=round(average(map_rows, "damage"), 2),
        )
        for map_name, map_rows in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
    ]
    by_map = {
        map_name: MapStats(
            kills_per_match=round(average(map_rows, "kills"), 2),
            win_rate=round(sum(1 for row in map_rows if row.placement == 1) / len(map_rows) * 100, 2),
            avg_damage=round(average(map_rows, "damage"), 2),
        )
        for map_name, map_rows in sorted(grouped.items())
    }

    return Insights(
        headline=headline,
        profile=profile,
        strengths=strengths[:3],
        weaknesses=weaknesses[:3],
        next_match_goals=goals[:3],
        early_death_rate=early_death_rate,
        top_10_rate=top_10_rate,
        kill_rate=kill_rate,
        trend=trend,
        map_performance=map_performance,
        by_map=by_map,
        advice=advice,
    )
