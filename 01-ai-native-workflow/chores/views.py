from pathlib import Path

from django.conf import settings
from django.shortcuts import render


CHECKBOX_PREFIXES = ("- [ ] ", "- [x] ", "- [X] ")


def _read_chores(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    chores = []
    for line in path.read_text(encoding="utf-8").splitlines():
        for prefix in CHECKBOX_PREFIXES:
            if line.startswith(prefix):
                chores.append(
                    {
                        "name": line[len(prefix) :].strip(),
                        "done": prefix != "- [ ] ",
                    }
                )
                break
    return chores


def chore_list(request):
    chores = _read_chores(Path(settings.BASE_DIR) / "chores.md")
    return render(request, "chores/chore_list.html", {"chores": chores})
