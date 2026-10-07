MAP_NAMES = {
    "Baltic_Main": "Erangel",
    "Erangel_Main": "Erangel",
    "Desert_Main": "Miramar",
    "Savage_Main": "Sanhok",
    "DihorOtok_Main": "Vikendi",
    "Summerland_Main": "Karakin",
    "Chimera_Main": "Paramo",
    "Tiger_Main": "Taego",
    "Kiki_Main": "Deston",
    "Range_Main": "Training",
    "Heaven_Main": "Haven",
    "Neon_Main": "Rondo",
}

MODE_NAMES = {
    "solo": "Solo",
    "solo-fpp": "Solo FPP",
    "duo": "Duo",
    "duo-fpp": "Duo FPP",
    "squad": "Squad",
    "squad-fpp": "Squad FPP",
}


def display_map_name(value: str) -> str:
    return MAP_NAMES.get(value, value.replace("_Main", "").replace("_", " "))


def display_mode_name(value: str) -> str:
    return MODE_NAMES.get(value, value.replace("-", " ").title())
